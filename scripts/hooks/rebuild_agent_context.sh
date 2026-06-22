#!/usr/bin/env bash
# afterFileEdit hook — debounced rebuild of agent-context.json
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LOCK="/tmp/sb-agent-context-rebuild.lock"
DEBOUNCE_SEC=3

touch "$LOCK"
LAST=$(stat -f %m "$LOCK" 2>/dev/null || stat -c %Y "$LOCK")
sleep "$DEBOUNCE_SEC"
NOW=$(stat -f %m "$LOCK" 2>/dev/null || stat -c %Y "$LOCK")
if [ "$NOW" != "$LAST" ]; then
  exit 0
fi

cd "$REPO"
python3 scripts/build_agent_context.py >> /tmp/sb-agent-context.log 2>&1 || true
python3 scripts/build_sources_routing.py >> /tmp/sb-agent-context.log 2>&1 || true
