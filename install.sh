#!/usr/bin/env bash
# Install voice2anki for the current user.
#   ./install.sh                      link the command, install the flush timer, create a config
#   ./install.sh --hotkey '<Super>z'  also bind a GNOME keyboard shortcut to "voice2anki toggle"
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin/voice2anki"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/voice2anki"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$(dirname "$BIN")" "$CONFIG_DIR" "$UNIT_DIR"
chmod +x "$APP_DIR/voice2anki"
ln -sfn "$APP_DIR/voice2anki" "$BIN"
echo "linked $BIN"

if [ ! -f "$CONFIG_DIR/config.sh" ]; then
  cp "$APP_DIR/config.example.sh" "$CONFIG_DIR/config.sh"
  echo "created $CONFIG_DIR/config.sh (edit it)"
fi

cat >"$UNIT_DIR/voice2anki-flush.service" <<EOF
[Unit]
Description=voice2anki: push queued cards into Anki

[Service]
Type=oneshot
ExecStart=$BIN flush
EOF
cat >"$UNIT_DIR/voice2anki-flush.timer" <<EOF
[Unit]
Description=voice2anki: push queued cards into Anki every 2 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=2min

[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now voice2anki-flush.timer
echo "timer voice2anki-flush.timer enabled"

if [ "${1:-}" = "--hotkey" ] && [ -n "${2:-}" ]; then
  schema=org.gnome.settings-daemon.plugins.media-keys
  path=/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/voice2anki/
  current="$(gsettings get $schema custom-keybindings)"
  if [[ "$current" != *"$path"* ]]; then
    if [ "$current" = "@as []" ] || [ "$current" = "[]" ]; then new="['$path']"
    else new="${current%]}, '$path']"; fi
    gsettings set $schema custom-keybindings "$new"
  fi
  kb="$schema.custom-keybinding:$path"
  gsettings set "$kb" name "voice2anki"
  gsettings set "$kb" command "$BIN toggle"
  gsettings set "$kb" binding "$2"
  echo "GNOME shortcut $2 -> voice2anki toggle"
fi
