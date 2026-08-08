#!/usr/bin/env bash
# Deprecated wrapper — prefer install_agenda_skills.sh (symlinks).
# Kept so old docs/hooks don't break; delegates to install script.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$REPO_ROOT/scripts/install_agenda_skills.sh"
