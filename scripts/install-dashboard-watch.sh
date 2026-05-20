#!/usr/bin/env bash
# Install launchd agent: auto-rebuild Dashboard.html on vault changes.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$REPO/vps/second-brain-hub/deploy/com.rbedu.mrluc-dashboard-watch.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.rbedu.mrluc-dashboard-watch.plist"
VAULT="${VAULT_PATH:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC}"

sed "s|REPO_PATH|$REPO|g; s|VAULT_PATH|$VAULT|g" "$PLIST_SRC" > "$PLIST_DST"
launchctl bootout "gui/$(id -u)/com.rbedu.mrluc-dashboard-watch" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.rbedu.mrluc-dashboard-watch"
launchctl kickstart -k "gui/$(id -u)/com.rbedu.mrluc-dashboard-watch"
echo "Installed: $PLIST_DST"
echo "Logs: /tmp/mrluc-dashboard-watch.log"
echo ""
echo "Live dashboard (auto-refresh in browser):"
echo "  $REPO/scripts/serve_dashboard.sh"
echo "  → http://127.0.0.1:8765/Dashboard.html"
