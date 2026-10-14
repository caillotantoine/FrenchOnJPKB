#!/usr/bin/env python3
"""Install/remove the standalone frk68 XKB layout without replacing vendor files.

The --xkb-root override is for tests and alternative installations.
"""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET

NAME = 'frk68'
BEGIN = '<!-- BEGIN FrenchOnJPKB frk68 (managed by xkb_registry.py) -->'
END = '<!-- END FrenchOnJPKB frk68 -->'
REGISTRY = f'''{BEGIN}
    <layout>
      <configItem>
        <name>{NAME}</name>
        <shortDescription>fr</shortDescription>
        <description>French (K68, Mac-style accents)</description>
        <languageList>
          <iso639Id>fra</iso639Id>
          <iso639Id>eng</iso639Id>
        </languageList>
      </configItem>
      <variantList/>
    </layout>
{END}'''
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / 'layouts' / NAME
SYSTEM_ROOT = Path('/usr/share/X11/xkb')


def write_atomic(path: Path, content: bytes, mode: int) -> None:
    """Write in the same directory, then atomically rename into place."""
    fd, pathname = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(content)
        os.chmod(pathname, mode)
        os.replace(pathname, path)
    finally:
        if os.path.exists(pathname):
            os.unlink(pathname)


def patch_registry(original: str, install: bool) -> str:
    has_begin, has_end = BEGIN in original, END in original
    if has_begin != has_end or original.count(BEGIN) > 1 or original.count(END) > 1:
        raise ValueError('Inconsistent frk68 markers in XKB registry; refusing to edit.')

    if has_begin:
        a = original.index(BEGIN)
        b = original.index(END, a) + len(END)
        output = original[:a] + (REGISTRY if install else '') + original[b:]
        if install:
            return output
        return output

    if not install:
        return original
    if f'<name>{NAME}</name>' in original:
        raise ValueError('An unmanaged frk68 XKB entry already exists; refusing to overwrite.')
    if original.count('</layoutList>') != 1:
        raise ValueError('Expected exactly one </layoutList> element in evdev.xml.')
    return original.replace('</layoutList>', REGISTRY + '\n  </layoutList>', 1)


def backup(original_path: Path, root: Path) -> Path:
    backup_dir = (Path('/var/backups/frenchon-jpkb') if root == SYSTEM_ROOT
                  else root / '.frenchon-jpkb-backups')
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = backup_dir / f'{original_path.name}.{stamp}.bak'
    shutil.copy2(original_path, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'uninstall'))
    parser.add_argument('--xkb-root', type=Path, default=SYSTEM_ROOT,
                        help='XKB directory (default: /usr/share/X11/xkb)')
    args = parser.parse_args()
    root = args.xkb_root.resolve()
    if root == SYSTEM_ROOT and os.geteuid() != 0:
        parser.error('System-wide changes require sudo/root. Run install-ubuntu.sh.')

    symbols = root / 'symbols' / NAME
    registry = root / 'rules' / 'evdev.xml'
    if not registry.is_file() or not symbols.parent.is_dir():
        parser.error(f'No XKB registry or symbols directory found under {root}')

    src = SOURCE.read_bytes()
    if not src.startswith(b'// FrenchOnJPKB:'):
        parser.error('Unexpected layout source; refusing to install.')
    if symbols.exists() and symbols.read_bytes() != src:
        current = symbols.read_bytes()
        if not current.startswith(b'// FrenchOnJPKB:'):
            parser.error(f'Existing unmanaged layout at {symbols}; refusing to overwrite.')
        if args.action == 'uninstall':
            parser.error(f'{symbols} contains local changes; refusing to delete.')

    original = registry.read_text(encoding='utf-8')
    try:
        updated = patch_registry(original, args.action == 'install')
        ET.fromstring(updated)
    except (ValueError, ET.ParseError) as exc:
        parser.error(str(exc))

    if updated != original:
        saved = backup(registry, root)
        old_mode = stat.S_IMODE(registry.stat().st_mode)
        write_atomic(registry, updated.encode('utf-8'), old_mode)
        print(f'Updated {registry} (backup: {saved})')
    else:
        print('XKB registry already in requested state.')

    if args.action == 'install':
        if not symbols.exists() or symbols.read_bytes() != src:
            write_atomic(symbols, src, 0o644)
            print(f'Installed {symbols}')
        else:
            print(f'XKB symbols already up to date: {symbols}')
    elif symbols.exists():
        if symbols.read_bytes() == src:
            symbols.unlink()
            print(f'Removed {symbols}')
        else:
            parser.error(f'Unexpected layout at {symbols}.')
    print('Done. A GNOME session restart may be needed for layout discovery.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
