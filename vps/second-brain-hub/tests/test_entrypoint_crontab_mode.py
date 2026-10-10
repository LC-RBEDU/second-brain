"""T2: entrypoint picks crontab.pause vs crontab from CRONTAB_MODE / PAUSED."""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

ENTRY = Path(__file__).resolve().parents[1] / "deploy" / "entrypoint.sh"


def _run_entry(extra: dict) -> subprocess.CompletedProcess:
    log_dir = tempfile.mkdtemp(prefix="sb-entry-log-")
    script = f"""
set -eu
FAKE=$(mktemp -d)
cat > "$FAKE/supercronic" <<'EOF'
#!/bin/sh
echo "SUPERCRONIC_ARGV:$*"
exit 0
EOF
chmod +x "$FAKE/supercronic"
cat > "$FAKE/python3" <<'EOF'
#!/bin/sh
exit 0
EOF
chmod +x "$FAKE/python3"
export PATH="$FAKE:$PATH"
ENTRY_COPY=$(mktemp)
sed -e 's|/usr/local/bin/supercronic|supercronic|g' \\
    -e 's|python3 /app/cron/build_agent_context.py|python3|g' \\
    -e 's|/var/log/second-brain|{log_dir}|g' \\
    "{ENTRY}" > "$ENTRY_COPY"
chmod +x "$ENTRY_COPY"
sh "$ENTRY_COPY"
"""
    return subprocess.run(
        ["sh", "-c", script],
        env={**os.environ, **extra},
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "extra,expect",
    [
        ({}, "/app/crontab"),
        ({"CRONTAB_MODE": "live", "VAULT_WRITERS_PAUSED": "0"}, "/app/crontab"),
        ({"CRONTAB_MODE": "pause", "VAULT_WRITERS_PAUSED": "0"}, "/app/crontab.pause"),
        ({"CRONTAB_MODE": "live", "VAULT_WRITERS_PAUSED": "1"}, "/app/crontab.pause"),
        ({"CRONTAB_MODE": "pause", "VAULT_WRITERS_PAUSED": "1"}, "/app/crontab.pause"),
    ],
)
def test_entrypoint_crontab_selection(extra, expect):
    r = _run_entry(extra)
    assert r.returncode == 0, r.stderr + r.stdout
    assert expect in r.stdout, r.stdout
