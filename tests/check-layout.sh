#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
layout="$repo_dir/layouts/frk68"
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
mkdir -p "$temp/symbols"
cp "$layout" "$temp/symbols/frk68"

if command -v xkbcli >/dev/null 2>&1; then
    xkbcli compile-keymap --include "$temp" --include-defaults \
        --rules evdev --model pc104 --layout frk68 >/dev/null
elif command -v xkbcomp >/dev/null 2>&1; then
    cat > "$temp/test.xkb" <<'KEYMAP'
xkb_keymap {
    xkb_keycodes { include "evdev+aliases(qwerty)" };
    xkb_types { include "complete" };
    xkb_compatibility { include "complete" };
    xkb_symbols { include "pc+frk68(basic)+inet(evdev)" };
    xkb_geometry { include "pc(pc104)" };
};
KEYMAP
    xkbcomp -w 2 -I"$temp" -xkb "$temp/test.xkb" "$temp/compiled.xkb"
else
    echo 'Install libxkbcommon-tools or x11-xkb-utils to validate XKB first.' >&2
    exit 1
fi

echo 'XKB layout frk68: compilation OK'
