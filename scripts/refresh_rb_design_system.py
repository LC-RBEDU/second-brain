#!/usr/bin/env python3
"""Refresh Red Button brand design-system snapshot from Claude artifact.

Local SSOT: ŠABLONY/design-system/ (manifest.json + snapshot/).

Exit codes:
  0 — unchanged (or updated successfully when not --check)
  1 — error
  2 — --check only: remote/content differs from manifest (caller should refresh)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DS_DIR = REPO_ROOT / "ŠABLONY" / "design-system"
MANIFEST_PATH = DS_DIR / "manifest.json"
SNAPSHOT_MD = DS_DIR / "snapshot" / "design-system.md"
ASSETS_ROOT = DS_DIR / "snapshot" / "assets"
SOURCE_URL_FILE = DS_DIR / "SOURCE.url"

PUBLIC_ASSET_SUFFIXES = (
    "project/tokens.json",
    "project/tokens.css",
    "project/components/bundle.css",
    "project/components/bundle.js",
)

PUA_RE = re.compile(r"[\ue000-\uf8ff]+")
FRAME_URL_RE = re.compile(r"https://[0-9a-f-]+\.frame\.claudeusercontent\.com/_f/[^/\s\"'<>]+/[^\s\"'<>]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def source_url(manifest: dict[str, Any]) -> str:
    if SOURCE_URL_FILE.exists():
        line = SOURCE_URL_FILE.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if line:
            return line
    return str(manifest.get("source_url") or "")


def normalize_markdown(md: str) -> str:
    start = md.find("# Red Button Design System")
    if start >= 0:
        md = md[start:]
    md = PUA_RE.sub("", md)
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    if not md.endswith("\n"):
        md += "\n"
    return md


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundle_hash(md: str, asset_files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    h.update(md.encode("utf-8"))
    for path in sorted(asset_files):
        h.update(path.encode("utf-8"))
        h.update(asset_files[path])
    return h.hexdigest()


def local_assets() -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    if not ASSETS_ROOT.exists():
        return out
    for p in ASSETS_ROOT.rglob("*"):
        if p.is_file() and p.name != "_fetch_report.json":
            rel = p.relative_to(ASSETS_ROOT).as_posix()
            out[rel] = p.read_bytes()
    return out


def firecrawl_api_key() -> str | None:
    key = os.environ.get("FIRECRAWL_API_KEY") or os.environ.get("FIRECRAWL_KEY")
    if key:
        return key.strip()
    env_path = Path.home() / ".config" / "second-brain" / "firecrawl.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() in {"FIRECRAWL_API_KEY", "FIRECRAWL_KEY"}:
                    return v.strip().strip('"').strip("'")
    return None


def firecrawl_scrape(url: str, api_key: str) -> dict[str, Any]:
    payload = json.dumps(
        {
            "url": url,
            "formats": ["markdown", "links"],
            "onlyMainContent": False,
            "waitFor": 8000,
            "timeout": 90000,
            "maxAge": 0,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SECOND_BRAIN-refresh_rb_design_system/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if not body.get("success"):
        raise RuntimeError(f"Firecrawl scrape failed: {body}")
    data = body.get("data") or {}
    return data


def http_get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 SECOND_BRAIN-refresh_rb_design_system/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def extract_frame_base(md: str, fallback: str | None) -> str | None:
    for m in FRAME_URL_RE.finditer(md):
        url = m.group(0)
        parts = url.split("/")
        # https://host/_f/id/...
        try:
            i = parts.index("_f")
            return "/".join(parts[: i + 2])
        except ValueError:
            continue
    return fallback


def fetch_public_assets(frame_base: str) -> tuple[dict[str, bytes], list[dict[str, str]]]:
    ok: dict[str, bytes] = {}
    fail: list[dict[str, str]] = []
    for rel in PUBLIC_ASSET_SUFFIXES:
        url = f"{frame_base.rstrip('/')}/{rel}"
        try:
            ok[rel] = http_get(url)
        except Exception as exc:  # noqa: BLE001 — collect per-file errors
            fail.append({"path": rel, "error": str(exc)})
    return ok, fail


def parse_from_firecrawl_json(path: Path) -> str:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "markdown" in raw:
        return str(raw["markdown"])
    if isinstance(raw, dict) and isinstance(raw.get("data"), dict) and "markdown" in raw["data"]:
        return str(raw["data"]["markdown"])
    raise ValueError("JSON must contain markdown or data.markdown")


def write_assets(assets: dict[str, bytes]) -> None:
    ASSETS_ROOT.mkdir(parents=True, exist_ok=True)
    for rel, data in assets.items():
        dest = ASSETS_ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


def update_manifest(
    manifest: dict[str, Any],
    *,
    content_hash: str,
    b_hash: str,
    frame_base: str | None,
    md_chars: int,
    md_lines: int,
    assets_ok: int,
    assets_fail: int,
) -> None:
    manifest["fetched_at"] = utc_now()
    manifest["content_hash"] = content_hash
    manifest["bundle_hash"] = b_hash
    if frame_base:
        manifest["frame_base"] = frame_base
    remote = manifest.setdefault("remote_meta", {})
    remote["md_chars"] = md_chars
    remote["md_lines"] = md_lines
    remote["assets_ok"] = assets_ok
    remote["assets_forbidden_or_missing"] = assets_fail
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_snapshot(
    manifest: dict[str, Any],
    md: str,
    assets: dict[str, bytes],
    *,
    frame_base: str | None,
    assets_fail: int,
) -> tuple[str, str]:
    md = normalize_markdown(md)
    c_hash = sha256_text(md)
    b_hash = bundle_hash(md, assets)
    SNAPSHOT_MD.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_MD.write_text(md, encoding="utf-8")
    write_assets(assets)
    update_manifest(
        manifest,
        content_hash=c_hash,
        b_hash=b_hash,
        frame_base=frame_base,
        md_chars=len(md),
        md_lines=md.count("\n") + 1,
        assets_ok=len(assets),
        assets_fail=assets_fail,
    )
    return c_hash, b_hash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare only; exit 2 if changed")
    parser.add_argument("--force", action="store_true", help="Write even if hashes match")
    parser.add_argument("--from-markdown", type=Path, help="Use local markdown instead of network scrape")
    parser.add_argument("--from-firecrawl-json", type=Path, help="MCP/API scrape JSON with markdown field")
    parser.add_argument("--skip-assets", action="store_true", help="Do not re-fetch public frame assets")
    args = parser.parse_args()

    try:
        manifest = load_manifest()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    url = source_url(manifest)
    if not url:
        print("ERROR: missing source_url", file=sys.stderr)
        return 1

    prev_content = manifest.get("content_hash")
    prev_bundle = manifest.get("bundle_hash")

    md: str | None = None
    if args.from_firecrawl_json:
        try:
            md = parse_from_firecrawl_json(args.from_firecrawl_json)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    elif args.from_markdown:
        md = args.from_markdown.read_text(encoding="utf-8")
    else:
        api_key = firecrawl_api_key()
        if api_key:
            try:
                data = firecrawl_scrape(url, api_key)
                md = str(data.get("markdown") or "")
                if not md:
                    print("ERROR: Firecrawl returned empty markdown", file=sys.stderr)
                    return 1
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR: Firecrawl scrape failed: {exc}", file=sys.stderr)
                print(
                    "Hint: scrape via MCP firecrawl_scrape then "
                    "--from-firecrawl-json /path.json",
                    file=sys.stderr,
                )
                return 1
        else:
            # Lightweight probe: public tokens.json only (weak signal without full MD)
            frame_base = manifest.get("frame_base")
            if not frame_base:
                print(
                    "ERROR: no FIRECRAWL_API_KEY and no --from-markdown; "
                    "cannot fetch full artifact text. "
                    "Use Firecrawl MCP scrape + --from-firecrawl-json, "
                    "or set ~/.config/second-brain/firecrawl.env",
                    file=sys.stderr,
                )
                return 1
            try:
                remote_tokens = http_get(f"{frame_base.rstrip('/')}/project/tokens.json")
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR: token probe failed: {exc}", file=sys.stderr)
                return 1
            local_tokens_path = ASSETS_ROOT / "project" / "tokens.json"
            local_tokens = local_tokens_path.read_bytes() if local_tokens_path.exists() else b""
            tokens_changed = sha256_bytes(remote_tokens) != sha256_bytes(local_tokens)
            if args.check:
                if tokens_changed:
                    print("CHANGED: project/tokens.json differs from local (full MD not re-scraped)")
                    return 2
                print("UNCHANGED: tokens.json matches (note: full markdown not revalidated without Firecrawl)")
                return 0
            if not tokens_changed and not args.force:
                print("UNCHANGED: tokens.json matches; pass --force or provide --from-markdown to rewrite MD")
                return 0
            print(
                "ERROR: cannot update full snapshot without markdown source "
                "(Firecrawl key or --from-markdown)",
                file=sys.stderr,
            )
            return 1

    assert md is not None
    md_norm = normalize_markdown(md)
    c_hash = sha256_text(md_norm)

    frame_base = extract_frame_base(md_norm, manifest.get("frame_base"))
    assets = local_assets()
    assets_fail = 0
    if not args.skip_assets and frame_base:
        fetched, fails = fetch_public_assets(frame_base)
        assets_fail = len(fails)
        assets.update(fetched)
        for f in fails:
            print(f"WARN asset: {f['path']}: {f['error']}", file=sys.stderr)

    b_hash = bundle_hash(md_norm, assets)
    changed = c_hash != prev_content or b_hash != prev_bundle

    if args.check:
        if changed:
            print(f"CHANGED: content_hash {prev_content} -> {c_hash}")
            print(f"         bundle_hash  {prev_bundle} -> {b_hash}")
            return 2
        print(f"UNCHANGED: content_hash={c_hash}")
        return 0

    if not changed and not args.force:
        print(f"UNCHANGED: content_hash={c_hash} (pass --force to rewrite)")
        return 0

    apply_snapshot(
        manifest,
        md_norm,
        assets,
        frame_base=frame_base,
        assets_fail=assets_fail,
    )
    print(f"UPDATED: content_hash={c_hash}")
    print(f"         bundle_hash={b_hash}")
    print(f"         wrote {SNAPSHOT_MD.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
