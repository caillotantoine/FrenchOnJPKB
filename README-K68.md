# Ubuntu — French on Ziyoulang K68 (ANSI QWERTY)

This branch adds a **separate XKB layout** named **French (K68, Mac-style accents)**, adapted from the original FrenchOnJPKB Japanese JIS layout. It leaves ordinary QWERTY characters and shortcuts intact, and makes French accents and scientific symbols available using **Right Alt (AltGr)**.

Works with **Ubuntu GNOME on Wayland or X11** (you may need to log out and back in to register the new input source). The layout is Mac-*like*, not an exact Apple layout clone. In particular, K68's compact ANSI design lacks the Japanese Henkan/Kana keys and a dedicated grave/tilde key.

## Fast installation

Run these commands in a terminal:

    sudo apt install git
    git clone https://github.com/caillotantoine/FrenchOnJPKB.git
    cd FrenchOnJPKB
    git switch feature/ubuntu-k68-mac-french
    bash scripts/install-ubuntu.sh
    python3 scripts/activate-gnome.py

**Important:** run the last command as your normal GNOME desktop user, **without sudo**. Switch to the new layout with **Super+Space**, or choose it under **Settings → Keyboard → Input Sources**. If it is missing or inactive, **log out and log back in**. The activation script *appends* a source; it **does not remove** any existing US, French, Japanese/Mozc or IBus inputs.

The installer compiles the layout first, then adds a standalone file at /usr/share/X11/xkb/symbols/frk68 and a small marked registration block to /usr/share/X11/xkb/rules/evdev.xml. It does **not** overwrite the installed French symbols file, replace Ubuntu's entire registry, modify IBus files, or install input-remapper.

If neither xkbcli nor xkbcomp is available, install the validator with:

    sudo apt install libxkbcommon-tools

## Typing reference

Right Alt acts like a macOS Option modifier. A **dead key** is pressed and released, then you type the next character.

| Shortcut | Result |
| --- | --- |
| Right Alt + 3; Right Alt + Shift + 3 | é; É |
| Right Alt + 7; Right Alt + 8; Right Alt + 9 | è; à; ç |
| Right Alt + C; Right Alt + Shift + C | ç; Ç |
| Right Alt + Q; Right Alt + A; Right Alt + 2 | œ; æ; € |
| Right Alt + E, then E | é |
| Right Alt + E, then Shift + E | É |
| Right Alt + I, then E | ê |
| Right Alt + U, then E | ë |
| Right Alt + -, then E | è |
| Right Alt + N, then N | ñ |
| Right Alt + [; Right Alt + ] | «; » |
| Right Alt + Space | Nonbreaking space |
| Right Alt + P; M; F; D | π; μ; ∫; δ |
| Right Alt + G; V; R | ∈; √; → |
| Right Alt + Z; X; Shift+X | ℕ; ℂ; ℝ |
| Right Alt + K; Shift+K | ≤; ≥ |

Note: on this compact K68 keyboard, the normal backtick/grave key is **Fn+Esc**, and tilde is typically **Fn+Shift+Esc**. To avoid needing a three-key chord for the grave dead key, the custom layout assigns **Right Alt + -** (then e gives è). Some K68 firmware can also produce the grave key using Fn+Esc, which keeps Right Alt + grave usable.

The base keys stay US QWERTY: ordinary numbers, apostrophe, punctuation and Ctrl shortcuts. Other scientific symbols from the original layout are available in the third and fourth levels; see [layouts/frk68](layouts/frk68).

## Validation and troubleshooting

    bash tests/check-layout.sh
    python3 -m unittest discover -s tests -p 'test_*.py'
    echo "$XDG_SESSION_TYPE"
    gsettings get org.gnome.desktop.input-sources sources

The first command compiles the keymap without modifying the machine. The second exercises install/uninstall logic against a temporary directory.

Try typing in a text editor:

    Salut, ça va ? Déjà Noël ! L'œuvre coûte 15 €. π ∈ ℝ

If the third-level characters do not appear, verify you are using **French (K68, Mac-style accents)** instead of US, and that the physical right-side Alt key sends **Right Alt**. On Wayland, you can inspect keycodes with **wev** (sudo apt install wev); on X11, use **xev -event keyboard**. Some keyboards reserve or change keys in Mac/Fn firmware modes. The hardware's Fn key itself is not visible to XKB.

Wayland GNOME sessions are **not** reconfigured with setxkbmap; use the GNOME Settings input-source picker or the provided activation script instead. If you install an Ubuntu xkb-data package upgrade and lose the custom registration entry, **rerun the installer**.

## Remove and restore

First select a standard input source using **Super+Space**, then run:

    bash scripts/uninstall-ubuntu.sh

The uninstaller removes only the marked layout registration, the standalone frk68 symbols file (if it has not been edited), and the GNOME input source. Other layouts and input methods are preserved. The scripts create **timestamped backups** of the registry under /var/backups/frenchon-jpkb before each modification; they intentionally do not blindly restore an outdated complete registry snapshot.

For a quick temporary rollback, simply switch back to your previous input source. A GNOME logout/login may be needed for registry changes.

## Files in this branch

- layouts/frk68 — new ANSI-compatible four-level XKB layout.
- scripts/install-ubuntu.sh — compilation validation and system installation.
- scripts/xkb_registry.py — targeted, idempotent XKB registry edits.
- scripts/activate-gnome.py — preserve existing input sources when activating.
- scripts/uninstall-ubuntu.sh — targeted removal.
- tests/check-layout.sh, tests/test_registry.py — keyboard and installer checks.

**Testing status:** XKB compilation and installer unit tests passed in a Linux test environment. The physical K68 and your actual Ubuntu GNOME session have not yet been tested. No changes are made to the keyboard's firmware.
