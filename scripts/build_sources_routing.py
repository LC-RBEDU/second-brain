#!/usr/bin/env python3
"""Generate sources-routing.json from Zdroje-katalog.md (SSOT).

Usage:
  python3 scripts/build_sources_routing.py
  python3 scripts/build_sources_routing.py --check   # drift guard (exit 1 if stale)
  python3 scripts/build_sources_routing.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pip3 install pyyaml\n")
    sys.exit(1)

DEFAULT_VAULT = Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"
CATALOG_REL = "00-System/Zdroje-katalog.md"
OUTPUT_REL = "00-System/sources-routing.json"

_YAML_FENCE_RE = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def catalog_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_catalog(text: str) -> dict[str, dict]:
    """Extract routing entries from fenced yaml blocks; tag from yaml `tag` field."""
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
        entry = {k: v for k, v in data.items() if k != "tag"}
        routes[tag] = entry
    return routes


def build_payload(catalog_path: Path, routes: dict[str, dict]) -> dict:
    catalog_text = catalog_path.read_text(encoding="utf-8")
    return {
        "version": 1,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "catalog_path": CATALOG_REL,
        "catalog_sha256": catalog_sha256(catalog_text),
        "tags": sorted(routes.keys()),
        "routes": routes,
    }


def load_existing(out_path: Path) -> dict | None:
    if not out_path.exists():
        return None
    try:
        return json.loads(out_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def is_stale(catalog_path: Path, out_path: Path) -> tuple[bool, str]:
    if not catalog_path.exists():
        return True, "catalog missing"
    if not out_path.exists():
        return True, "routing json missing"
    catalog_text = catalog_path.read_text(encoding="utf-8")
    current_sha = catalog_sha256(catalog_text)
    existing = load_existing(out_path)
    if not existing:
        return True, "routing json unreadable"
    if existing.get("catalog_sha256") != current_sha:
        return True, "catalog_sha256 mismatch"
    routes = parse_catalog(catalog_text)
    if set(existing.get("tags") or []) != set(routes.keys()):
        return True, "tag set mismatch"
    return False, "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--check", action="store_true", help="Exit 1 if JSON stale vs catalog")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    catalog_path = args.vault / CATALOG_REL
    out_path = args.vault / OUTPUT_REL

    if not catalog_path.exists():
        sys.stderr.write(f"ERROR: catalog not found: {catalog_path}\n")
        return 1

    routes = parse_catalog(catalog_path.read_text(encoding="utf-8"))
    if not routes:
        sys.stderr.write("ERROR: no yaml routing blocks parsed from catalog\n")
        return 1

    stale, reason = is_stale(catalog_path, out_path)
    if args.check:
        if stale:
            sys.stderr.write(f"sources-routing STALE: {reason}\n")
            return 1
        print("sources-routing: OK (in sync with catalog)")
        return 0

    payload = build_payload(catalog_path, routes)

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:1500])
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"sources-routing: {len(routes)} tags → {out_path.relative_to(args.vault)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
