#!/usr/bin/env bash
# afterFileEdit hook — debounced rebuild of agent-context.json + stale Work-Context markers
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VAULT="${SECOND_BRAIN_VAULT:-$REPO/OBSIDIAN}"
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

# Cheap stale invalidation for Work-Context bundles (VC7-8)
WC_DIR="$VAULT/00-System/Work-Context"
if [ -d "$WC_DIR" ]; then
  for bundle in "$WC_DIR"/*.md; do
    [ -f "$bundle" ] || continue
    slug="$(basename "$bundle" .md)"
    touch "$WC_DIR/${slug}.stale"
  done
fi
