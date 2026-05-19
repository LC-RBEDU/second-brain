#!/bin/sh
set -eu

mkdir -p /data/mrluc/01-INBOX/slack \
  /data/mrluc/01-INBOX/sembly \
  /data/mrluc/01-INBOX/email \
  /data/mrluc/01-INBOX/daily \
  /data/mrluc/00-System/Triage-Pending \
  /data/mrluc/00-System/Triage-Applied \
  /data/mrluc/02-Projekty \
  /var/log/second-brain

if [ -f "${LEGACY_TASKS}" ] || [ -d "${VAULT_PATH}/02-Projekty" ]; then
  python3 /app/cron/build_dashboard.py >> /var/log/second-brain/build.log 2>&1 || true
fi

echo "second-brain-hub: supercronic only (no public HTTP)"
exec supercronic /app/crontab
