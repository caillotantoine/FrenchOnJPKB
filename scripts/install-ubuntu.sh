#!/usr/bin/env bash
# Ubuntu: validate the source before changing system XKB data.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$repo_dir/tests/check-layout.sh"
if (( EUID == 0 )); then
    python3 "$repo_dir/scripts/xkb_registry.py" install
else
    sudo python3 "$repo_dir/scripts/xkb_registry.py" install
fi
printf '\nNext (as your normal user, NOT sudo):\n  python3 scripts/activate-gnome.py\n'
