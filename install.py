#!/usr/bin/env python3
"""Install/uninstall FrenchOnJPKB without replacing the entire distro XKB files."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
SYMBOLS = Path("/usr/share/X11/xkb/symbols/fr")
RULES = Path("/usr/share/X11/xkb/rules/evdev.xml")
START = "// BEGIN FrenchOnJPKB managed block"
END = "// END FrenchOnJPKB managed block"
ENTRY = """        <variant>
          <configItem>
            <name>frjp</name>
            <description>French (JP, JIS keyboard)</description>
          </configItem>
        </variant>
"""

def source_variant():
    source = (ROOT / "fr").read_text()
    match = re.search(r'(?m)^hidden partial alphanumeric_keys\s*\nxkb_symbols "frjp"\s*\{.*?^\};', source, re.S | re.M)
    if not match:
        raise RuntimeError("Cannot find frjp variant in repository fr file")
    return match.group(0)

def modify_symbols(original, install):
    if START in original and END not in original:
        raise RuntimeError("Incomplete managed symbols block: refusing to alter it")
    if install:
        if START in original:
            original = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", original, flags=re.S)
        elif re.search(r'(?m)^xkb_symbols "frjp"\s*\{', original):
            raise RuntimeError("An unmanaged frjp layout already exists; restore original distro files before installation")
        return original.rstrip() + "\n\n" + START + "\n" + source_variant() + "\n" + END + "\n"
    return re.sub(r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", "\n", original, flags=re.S)

def french_layout_bounds(xml):
    match = re.search(r'<layout>\s*<configItem>\s*<name>fr</name>.*?</configItem>\s*<variantList>', xml, re.S)
    if not match:
        raise RuntimeError("Cannot find French variantList in evdev.xml")
    close = xml.find("</variantList>", match.end())
    if close < 0:
        raise RuntimeError("Malformed evdev.xml: missing French variantList closing tag")
    return match.end(), close

def modify_rules(xml, install):
    start, end = french_layout_bounds(xml)
    section = xml[start:end]
    expression = r'\s*<variant>\s*<configItem>\s*<name>frjp</name>.*?</configItem>\s*</variant>'
    if install:
        if re.search(expression, section, re.S):
            return xml  # Preserve existing entry (legacy setup).
        return xml[:end] + ENTRY + xml[end:]
    return xml[:start] + re.sub(expression, "", section, flags=re.S) + xml[end:]

def atomic_write(path, content):
    fd, temp = tempfile.mkstemp(prefix=".frenchonjp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        shutil.copymode(path, temp)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall", "check"))
    args = parser.parse_args()
    if args.action != "check" and os.geteuid() != 0:
        parser.error("install/uninstall require sudo")
    if not SYMBOLS.exists() or not RULES.exists():
        parser.error("XKB system files not found")
    if args.action == "check":
        source_variant()
        s, x = SYMBOLS.read_text(), RULES.read_text()
        start, end = french_layout_bounds(x)
        print("frjp symbols installed:", START in s or bool(re.search(r'(?m)^xkb_symbols "frjp"\s*\{', s)))
        print("frjp registered:", "<name>frjp</name>" in x[start:end])
        print("Session:", os.environ.get("XDG_SESSION_TYPE", "unknown"))
        if shutil.which("xkbcli"):
            print("Tip: xkbcli compile-keymap --layout fr --variant frjp")
        return
    old_symbols, old_rules = SYMBOLS.read_text(), RULES.read_text()
    new_symbols = modify_symbols(old_symbols, args.action == "install")
    new_rules = modify_rules(old_rules, args.action == "install")
    # Preserve snapshots so that normal system-file repairs are possible.
    for file, content in ((SYMBOLS, old_symbols), (RULES, old_rules)):
        backup = file.with_name(file.name + ".frenchonjp.bak")
        if not backup.exists():
            backup.write_text(content)
            shutil.copymode(file, backup)
    try:
        if new_symbols != old_symbols:
            atomic_write(SYMBOLS, new_symbols)
        if new_rules != old_rules:
            atomic_write(RULES, new_rules)
    except Exception:
        atomic_write(SYMBOLS, old_symbols)
        atomic_write(RULES, old_rules)
        raise
    print(args.action.capitalize(), "complete. Log out and back in, then select French (JP, JIS keyboard).")
    print("Note: xkb-data upgrades may replace system files; rerun the installer.")

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as exc:
        sys.exit(str(exc))
