#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if (( EUID == 0 )); then
    python3 "$repo_dir/scripts/xkb_registry.py" uninstall
    echo 'To remove the GNOME source, run as the normal user: python3 scripts/activate-gnome.py --remove'
else
    python3 "$repo_dir/scripts/activate-gnome.py" --remove || \
      echo 'Could not update GNOME sources automatically. Check them in Settings > Keyboard.' >&2
    sudo python3 "$repo_dir/scripts/xkb_registry.py" uninstall
fi
