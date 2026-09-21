#!/bin/sh
set -eu

mkdir -p /var/log/second-brain

# v2: žádný HTML dashboard build (Obsidian Bases reads frontmatter live).
# Initial agent-context refresh — stateless. Tolerated to fail; cron retries.
python3 /app/cron/build_agent_context.py >> /var/log/second-brain/agent-context.log 2>&1 || true

echo "second-brain-hub v2: supercronic"
exec /usr/local/bin/supercronic -passthrough-logs /app/crontab
