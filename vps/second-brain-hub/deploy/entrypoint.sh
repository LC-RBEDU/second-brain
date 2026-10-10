#!/bin/sh
set -eu

mkdir -p /var/log/second-brain

# CRONTAB_MODE: live (default) | pause — independent of VAULT_WRITERS_PAUSED (A33).
# pause OR PAUSED=1 → heartbeat crontab; skip initial agent-context.
MODE=$(printf '%s' "${CRONTAB_MODE:-live}" | tr '[:upper:]' '[:lower:]')
PAUSED=$(printf '%s' "${VAULT_WRITERS_PAUSED:-0}" | tr '[:upper:]' '[:lower:]')

use_pause=0
case "$MODE" in
  pause|paused|1|true|yes|on) use_pause=1 ;;
esac
case "$PAUSED" in
  1|true|yes|on) use_pause=1 ;;
esac

if [ "$use_pause" -eq 1 ]; then
  echo "second-brain-hub: CRONTAB_MODE=${CRONTAB_MODE:-live} PAUSED=${VAULT_WRITERS_PAUSED:-0} → crontab.pause"
  exec /usr/local/bin/supercronic -passthrough-logs /app/crontab.pause
fi

# v2: žádný HTML dashboard. Initial agent-context — tolerated to fail; cron retries.
python3 /app/cron/build_agent_context.py >> /var/log/second-brain/agent-context.log 2>&1 || true

echo "second-brain-hub v2: supercronic (live crontab)"
exec /usr/local/bin/supercronic -passthrough-logs /app/crontab
