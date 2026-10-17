#!/usr/bin/env bash
# Mac → coolify-dev: sync MrLUC vault (or subset) for cron jobs on VPS.
set -euo pipefail

# Legacy rsync. Live vault sync is git push to GIT_VAULT_ROOT=/data/vault.
VAULT_PATH="${VAULT_PATH:-$HOME/GitHub/second-brain-vault}"
VPS_HOST="${VPS_HOST:-coolify-dev}"
REMOTE="${REMOTE:-/data/mrluc-second-brain}"
SYNC_INBOX_ONLY="${SYNC_INBOX_ONLY:-0}"

if [[ ! -d "$VAULT_PATH" ]]; then
  echo "Vault not found: $VAULT_PATH"
  exit 1
fi

if [[ "$SYNC_INBOX_ONLY" == "1" ]]; then
  echo "Syncing 01-INBOX only → $VPS_HOST:$REMOTE/01-INBOX/"
  rsync -avz --delete "$VAULT_PATH/01-INBOX/" "$VPS_HOST:$REMOTE/01-INBOX/"
else
  echo "Syncing full vault → $VPS_HOST:$REMOTE/"
  rsync -avz --delete \
    --exclude '.obsidian/' \
    --exclude '.trash/' \
    "$VAULT_PATH/" "$VPS_HOST:$REMOTE/"
fi

echo "Done. Cron on VPS reads VAULT_PATH=/data/mrluc (volume mount)."
