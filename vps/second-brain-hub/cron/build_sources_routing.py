#!/usr/bin/env python3
"""VPS: Generate sources-routing.json on Drive from Zdroje-katalog.md."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:
    sys.exit(1)

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, credentials_from_env  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
CATALOG_REL = "00-System/Zdroje-katalog.md"
OUTPUT_REL = "00-System/sources-routing.json"
_YAML_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def catalog_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_catalog(text: str) -> dict[str, dict]:
    routes: dict[str, dict] = {}
    for block in _YAML_FENCE_RE.findall(text):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        tag = str(data.get("tag") or "").strip()
        if not tag:
            continue
        routes[tag] = {k: v for k, v in data.items() if k != "tag"}
    return routes


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    catalog_text, _ = vault.read_text(CATALOG_REL)
    routes = parse_catalog(catalog_text)
    payload = {
        "version": 1,
        "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "catalog_path": CATALOG_REL,
        "catalog_sha256": catalog_sha256(catalog_text),
        "tags": sorted(routes.keys()),
        "routes": routes,
    }
    vault.write_text(OUTPUT_REL, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"sources-routing: {len(routes)} tags → {OUTPUT_REL}")


if __name__ == "__main__":
    main()
