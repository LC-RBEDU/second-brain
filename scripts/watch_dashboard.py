#!/usr/bin/env python3
"""Watch MrLUC vault sources and rebuild Dashboard.html on change."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

VAULT = Path(
    os.environ.get(
        "VAULT_PATH",
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
    )
)
REPO = Path(__file__).resolve().parents[1]
HUB = REPO / "vps/second-brain-hub"
DEBOUNCE_SEC = float(os.environ.get("DASHBOARD_WATCH_DEBOUNCE", "2"))
POLL_SEC = float(os.environ.get("DASHBOARD_WATCH_POLL", "1.5"))

WATCH_DIRS = (
    VAULT / "02-PROJEKTY",
    VAULT / "01-INBOX",
    VAULT / "00-System/Triage-Pending",
)
WATCH_FILES = (
    VAULT / "00-System/dashboard-tasks-source.json",
    VAULT / "00-System/Index.md",
)


def iter_paths() -> list[Path]:
    out: list[Path] = [p for p in WATCH_FILES if p.exists()]
    for d in WATCH_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                if p.suffix in {".md", ".json"} or p.name == "dashboard-tasks-source.json":
                    out.append(p)
    return out


def snapshot() -> dict[str, tuple[int, int]]:
    snap: dict[str, tuple[int, int]] = {}
    for p in iter_paths():
        try:
            st = p.stat()
            snap[str(p)] = (int(st.st_mtime_ns), st.st_size)
        except OSError:
            pass
    return snap


def fingerprint(snap: dict[str, tuple[int, int]]) -> str:
    h = hashlib.sha256()
    for k in sorted(snap):
        h.update(k.encode())
        h.update(str(snap[k]).encode())
    return h.hexdigest()


def rebuild() -> None:
    env = os.environ.copy()
    env.setdefault("VAULT_PATH", str(VAULT))
    env.setdefault("DASHBOARD_HTML", str(VAULT / "00-System/Dashboard.html"))
    env.setdefault("LEGACY_TASKS", str(VAULT / "00-System/dashboard-tasks-source.json"))
    subprocess.run(
        [sys.executable, str(HUB / "cron/sync_tasks_from_projekty.py")],
        cwd=HUB,
        env=env,
        check=False,
    )
    subprocess.run(
        [sys.executable, str(HUB / "cron/build_dashboard.py")],
        cwd=HUB,
        env=env,
        check=True,
    )


def main() -> None:
    html = VAULT / "00-System/Dashboard.html"
    print("Watching MrLUC →", html, flush=True)
    print("Dirs:", ", ".join(str(d) for d in WATCH_DIRS), flush=True)
    last_fp = fingerprint(snapshot())
    pending = False
    last_change = 0.0

    # initial build
    rebuild()
    print(
        "Live: http://127.0.0.1:8765/Dashboard.html (run serve_dashboard.sh)",
        flush=True,
    )

    while True:
        time.sleep(POLL_SEC)
        fp = fingerprint(snapshot())
        if fp != last_fp:
            last_fp = fp
            pending = True
            last_change = time.time()
        if pending and (time.time() - last_change) >= DEBOUNCE_SEC:
            pending = False
            try:
                rebuild()
                print("rebuilt", html, flush=True)
                print(
                    "Live: http://127.0.0.1:8765/Dashboard.html (run serve_dashboard.sh)",
                    flush=True,
                )
            except subprocess.CalledProcessError as e:
                print("rebuild failed:", e, flush=True)


if __name__ == "__main__":
    main()
