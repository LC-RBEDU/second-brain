#!/usr/bin/env bash
# Serve git vault 00-System (~/GitHub/second-brain-vault) on :8765 — live poll of dashboard-data.json / build stamp.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
export VAULT_PATH="${VAULT_PATH:-$HOME/GitHub/second-brain-vault}"
export DASHBOARD_PORT="${DASHBOARD_PORT:-8765}"

exec python3 "$REPO/scripts/serve_dashboard.py" --port "$DASHBOARD_PORT"
