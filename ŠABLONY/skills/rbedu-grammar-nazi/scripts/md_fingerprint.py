#!/usr/bin/env python3
"""Structural fingerprint for meeting-note markdown (rbedu-grammar-nazi gate).

CLI (A33):
  capture --md PATH --out PATH.json   exit 0 OK, 2 invalid
  compare --before PATH.json --md PATH  exit 0 match, 1 mismatch, 2 invalid after
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

H2_RE = re.compile(r"^## (.+)$", re.M)
H3_RE = re.compile(r"^### (.+)$", re.M)
ID_RE = re.compile(r"^-\s+\*\*id:\*\*\s*`?([^`\n]+)`?\s*$", re.M)
FIELD_RE = re.compile(r"^-\s+\*\*(status|owner|key_people):\*\*\s*(.+?)\s*$", re.M)
TASKS_NONE_RE = re.compile(
    r"\*\*tasks\*\*\s*[—–-]\s*žádné", re.I
)
BULLET_RE = re.compile(r"^[-*]\s+(?:\[[ xX]\]\s+)?(.+)$")


def _split_fm(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    for line in fm_raw.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        if key:
            meta[key] = val
    # name_aliases: keep raw block marker presence + line count under key if indented
    if "name_aliases" in fm_raw:
        aliases: dict[str, str] = {}
        in_aliases = False
        for line in fm_raw.splitlines():
            if line.strip().startswith("name_aliases"):
                in_aliases = True
                if ":" in line and line.split(":", 1)[1].strip():
                    # inline map unlikely
                    pass
                continue
            if in_aliases:
                if line.startswith(" ") or line.startswith("\t") or line.startswith("-"):
                    m = re.match(r"^\s*-\s*(.+?):\s*(.+)$", line) or re.match(
                        r"^\s+(.+?):\s*(.+)$", line
                    )
                    if m:
                        aliases[m.group(1).strip().strip("'\"")] = m.group(
                            2
                        ).strip().strip("'\"")
                elif line.strip() and not line[0].isspace():
                    in_aliases = False
        meta["name_aliases"] = aliases
    return meta, body


def _section_bodies(body: str) -> list[tuple[str, str]]:
    """Return list of (h2_title, section_text including following content until next h2)."""
    matches = list(H2_RE.finditer(body))
    if not matches:
        return [("", body)]
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        out.append((m.group(1).strip(), body[start:end]))
    return out


def _top_level_bullets(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        if line.startswith("  ") or line.startswith("\t"):
            continue
        m = BULLET_RE.match(line)
        if m:
            items.append(m.group(1).strip())
    return items


def _extract_block_after(heading: str, text: str) -> str:
    """Text after a bold heading like **Co zaznělo** until next **…** or ### or ##."""
    pat = re.compile(
        rf"\*\*{re.escape(heading)}\*\*\s*\n(.*?)(?=\n\*\*[^*]+\*\*|\n### |\n## |\Z)",
        re.S | re.I,
    )
    m = pat.search(text)
    return m.group(1) if m else ""


def fingerprint(text: str) -> dict[str, Any]:
    meta, body = _split_fm(text)
    h2 = [m.group(1).strip() for m in H2_RE.finditer(body)]
    ids = [m.group(1).strip() for m in ID_RE.finditer(body)]

    cards: dict[str, dict[str, Any]] = {}
    # Split by ### that look like card headers (contain id nearby)
    parts = re.split(r"(?=^### )", body, flags=re.M)
    for part in parts:
        if not part.startswith("### "):
            continue
        id_m = ID_RE.search(part)
        if not id_m:
            continue
        cid = id_m.group(1).strip()
        fields = {m.group(1): m.group(2).strip() for m in FIELD_RE.finditer(part)}
        co = _extract_block_after("Co zaznělo", part)
        co_count = len(_top_level_bullets(co))
        if TASKS_NONE_RE.search(part):
            tasks_count = 0
        else:
            tasks_block = _extract_block_after("tasks", part)
            tasks_count = len(_top_level_bullets(tasks_block))
        cards[cid] = {
            "status": fields.get("status", ""),
            "owner": fields.get("owner", ""),
            "key_people": fields.get("key_people", ""),
            "co_zaznelo_count": co_count,
            "tasks_count": tasks_count,
        }

    # Highlights under ### Highlights
    hl_count = 0
    hl_m = re.search(
        r"^### Highlights\s*\n(.*?)(?=^### |^## |\Z)", body, re.S | re.M
    )
    if hl_m:
        hl_count = len(_top_level_bullets(hl_m.group(1)))

    # Consolidated table rows
    table_rows = 0
    tm = re.search(
        r"^## Konsolidovaný seznam úkolů\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M
    )
    if tm:
        for line in tm.group(1).splitlines():
            if not line.strip().startswith("|"):
                continue
            if re.match(r"^\|\s*[-:]+", line):
                continue
            if re.match(r"^\|\s*Kdo\s*\|", line, re.I):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and any(cells):
                table_rows += 1

    variant = (meta.get("variant") or meta.get("extraction_rules") or "full").lower()
    if "shared" in variant or variant == "shared":
        variant_norm = "shared"
    else:
        variant_norm = "full"

    return {
        "h2": h2,
        "ids": sorted(ids),
        "id_count": len(ids),
        "cards": {k: cards[k] for k in sorted(cards)},
        "highlights_count": hl_count,
        "has_highlights_block": hl_m is not None,
        "table_rows": table_rows,
        "yaml_keys": sorted(k for k in meta if k != "name_aliases"),
        "name_aliases": meta.get("name_aliases") or {},
        "variant": variant_norm,
        "title": meta.get("title", ""),
        "status_values": sorted(
            {c["status"] for c in cards.values() if c.get("status")}
        ),
    }


def validate_for_capture(fp: dict[str, Any]) -> str | None:
    """Return error message if invalid for capture (exit 2), else None."""
    if not fp["h2"]:
        return "missing ## headings"
    if "0. Meta" not in fp["h2"][0] and not any(
        h.startswith("0.") for h in fp["h2"]
    ):
        # allow if any Meta-like
        if not any("Meta" in h for h in fp["h2"]):
            return "missing ## 0. Meta"
    if fp["variant"] == "full":
        if not fp["has_highlights_block"]:
            return "full variant missing ### Highlights"
        if fp["highlights_count"] != 3:
            return f"full variant requires 3 highlights, got {fp['highlights_count']}"
    elif fp["has_highlights_block"] and fp["highlights_count"] != 3:
        return f"shared with Highlights requires 3, got {fp['highlights_count']}"
    return None


def compare_fps(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    diffs: list[str] = []

    def check(path: str, a: Any, b: Any) -> None:
        if a != b:
            diffs.append(f"{path}: {a!r} -> {b!r}")

    check("h2", before.get("h2"), after.get("h2"))
    check("ids", before.get("ids"), after.get("ids"))
    check("id_count", before.get("id_count"), after.get("id_count"))
    check("table_rows", before.get("table_rows"), after.get("table_rows"))
    check("yaml_keys", before.get("yaml_keys"), after.get("yaml_keys"))
    check("name_aliases", before.get("name_aliases"), after.get("name_aliases"))
    check("status_values", before.get("status_values"), after.get("status_values"))

    # highlights: only if before had block or full
    if before.get("has_highlights_block") or before.get("variant") == "full":
        check(
            "highlights_count",
            before.get("highlights_count"),
            after.get("highlights_count"),
        )
        check(
            "has_highlights_block",
            before.get("has_highlights_block"),
            after.get("has_highlights_block"),
        )

    b_cards = before.get("cards") or {}
    a_cards = after.get("cards") or {}
    check("cards.keys", sorted(b_cards), sorted(a_cards))
    for cid in sorted(set(b_cards) | set(a_cards)):
        if cid not in b_cards:
            diffs.append(f"cards[{cid}]: missing in before")
            continue
        if cid not in a_cards:
            diffs.append(f"cards[{cid}]: missing in after")
            continue
        for field in (
            "status",
            "owner",
            "key_people",
            "co_zaznelo_count",
            "tasks_count",
        ):
            check(f"cards[{cid}].{field}", b_cards[cid].get(field), a_cards[cid].get(field))
    return diffs


def cmd_capture(md: Path, out: Path) -> int:
    try:
        text = md.read_text(encoding="utf-8")
    except OSError as e:
        print(f"read error: {e}", file=sys.stderr)
        return 2
    fp = fingerprint(text)
    err = validate_for_capture(fp)
    if err:
        print(err, file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def cmd_compare(before: Path, md: Path) -> int:
    try:
        before_fp = json.loads(before.read_text(encoding="utf-8"))
        text = md.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as e:
        print(f"read error: {e}", file=sys.stderr)
        return 2
    after_fp = fingerprint(text)
    err = validate_for_capture(after_fp)
    # For compare, invalid after is exit 2; but shared without highlights that had none before is OK
    if err and after_fp.get("variant") == "full":
        print(err, file=sys.stderr)
        return 2
    if err and after_fp.get("has_highlights_block"):
        print(err, file=sys.stderr)
        return 2
    diffs = compare_fps(before_fp, after_fp)
    if diffs:
        for d in diffs:
            print(d, file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Meeting MD structural fingerprint")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("capture")
    c.add_argument("--md", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)

    m = sub.add_parser("compare")
    m.add_argument("--before", type=Path, required=True)
    m.add_argument("--md", type=Path, required=True)

    args = p.parse_args(argv)
    if args.cmd == "capture":
        return cmd_capture(args.md, args.out)
    if args.cmd == "compare":
        return cmd_compare(args.before, args.md)
    return 2


if __name__ == "__main__":
    sys.exit(main())
