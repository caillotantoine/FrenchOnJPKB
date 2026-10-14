#!/usr/bin/env python3
"""Add/remove FrenchOnJPKB's layout to GNOME without dropping other sources.

Preserves existing US/French/Japanese/Mozc and IBus input sources.
Run as the signed-in GUI user (NOT with sudo).
"""

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys

SCHEMA = 'org.gnome.desktop.input-sources'
TARGET = ('xkb', 'frk68')


def gsettings(*args: str) -> str:
    return subprocess.check_output(['gsettings', *args], text=True).strip()


def parse_sources(value: str) -> list[tuple[str, str]]:
    # gsettings returns a GVariant representation. For a(ss), after removing
    # the optional type annotation, the syntax is a Python literal.
    value = re.sub(r'^@a\(ss\)\s*', '', value.strip())
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list) or not all(
        isinstance(item, tuple) and len(item) == 2 and
        all(isinstance(x, str) for x in item) for item in parsed
    ):
        raise ValueError(f'Unexpected GNOME input-source format: {value}')
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove', action='store_true', help='Deactivate this layout')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Do NOT use sudo; gsettings must run in your GNOME session.')
    if not shutil.which('gsettings'):
        parser.error('gsettings not found; select the layout in desktop Keyboard Settings.')

    try:
        sources = parse_sources(gsettings('get', SCHEMA, 'sources'))
        old = list(sources)
        if args.remove:
            sources = [item for item in sources if item != TARGET]
            if not sources:
                sources = [('xkb', 'us')]
        elif TARGET not in sources:
            if not sources:
                # Keep a working standard layout as a recovery option.
                sources = [('xkb', 'us')]
            sources.append(TARGET)

        if sources != old:
            # repr(list of 2-tuples of strings) is accepted as GVariant a(ss).
            subprocess.run(['gsettings', 'set', SCHEMA, 'sources', repr(sources)], check=True)
        if not args.remove:
            # Makes custom (non-default-language) sources easier to discover.
            subprocess.run(['gsettings', 'set', SCHEMA, 'show-all-sources', 'true'], check=True)
        print('GNOME sources:', sources)
        if not args.remove:
            print('Use Super+Space to select French (K68, Mac-style accents).')
            print('If it is missing, log out and back in, then try again.')
        else:
            print('FrenchOnJPKB K68 source removed from GNOME.')
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.error(f'Could not adjust GNOME input sources: {exc}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
