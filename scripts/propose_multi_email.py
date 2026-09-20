#!/usr/bin/env python3
"""Propose multi-email additions for 05-RESOURCES/lide/ — never writes.

Scans archived mail frontmatter, calendar-events.json, and Sembly notes for
addresses that likely belong to an existing person (same display name or same
local-part across domains). Prints a review table for Lukáš.

Usage:
  python3 scripts/propose_multi_email.py
  python3 scripts/propose_multi_email.py --vault PATH
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml required\n")
    sys.exit(1)

REPO = Path(__file__).resolve().parents[1]
_LIB = REPO / "vps" / "second-brain-hub" / "lib"
sys.path.insert(0, str(_LIB))

from people import (  # noqa: E402
    COMPANY_DOMAINS,
    load_person_from_file,
    normalize_email,
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
NAME_EMAIL_RE = re.compile(
    r"([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^<\n]{1,80}?)\s*<([^>]+@[^>]+)>",
    re.I,
)


def _fm(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _local(email: str) -> str:
    return email.split("@", 1)[0].lower()


def collect_from_emails(vault: Path) -> list[tuple[str, str | None, str]]:
    """(email, display_name_or_None, source)."""
    hits: list[tuple[str, str | None, str]] = []
    root = vault / "07-ARCHIV" / "inbox-processed"
    if not root.exists():
        return hits
    for path in root.rglob("*.md"):
        if "/email/" not in path.as_posix() and path.parent.name != "email":
            # still allow any archived capture that looks like mail
            pass
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _fm(text)
        rel = path.relative_to(vault).as_posix()
        for key in ("from", "to", "cc", "sender", "email"):
            raw = fm.get(key)
            if not raw:
                continue
            if isinstance(raw, list):
                values = raw
            else:
                values = [raw]
            for val in values:
                s = str(val)
                for name, addr in NAME_EMAIL_RE.findall(s):
                    norm = normalize_email(addr)
                    if norm:
                        hits.append((norm, name.strip(), f"{rel}:{key}"))
                for addr in EMAIL_RE.findall(s):
                    norm = normalize_email(addr)
                    if norm:
                        hits.append((norm, None, f"{rel}:{key}"))
        # body fallback — only explicit mailto / angle addresses
        for name, addr in NAME_EMAIL_RE.findall(text[:4000]):
            norm = normalize_email(addr)
            if norm:
                hits.append((norm, name.strip(), f"{rel}:body"))
    return hits


def collect_from_calendar(vault: Path) -> list[tuple[str, str | None, str]]:
    path = vault / "00-System" / "calendar-events.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    hits: list[tuple[str, str | None, str]] = []
    events = data if isinstance(data, list) else data.get("events") or data.get("items") or []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        for att in ev.get("attendees") or []:
            if isinstance(att, str):
                norm = normalize_email(att)
                if norm:
                    hits.append((norm, None, "calendar-events.json"))
                continue
            if not isinstance(att, dict):
                continue
            norm = normalize_email(att.get("email"))
            if norm:
                hits.append(
                    (
                        norm,
                        (att.get("displayName") or att.get("name") or None),
                        "calendar-events.json",
                    )
                )
    return hits


def collect_from_sembly(vault: Path) -> list[tuple[str, str | None, str]]:
    hits: list[tuple[str, str | None, str]] = []
    root = vault / "01-INBOX" / "sembly"
    if not root.exists():
        return hits
    for path in root.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = path.relative_to(vault).as_posix()
        fm = _fm(text)
        for key in ("participants", "attendees", "emails"):
            raw = fm.get(key)
            if not raw:
                continue
            values = raw if isinstance(raw, list) else [raw]
            for val in values:
                s = str(val)
                norm = normalize_email(s)
                if norm:
                    hits.append((norm, None, f"{rel}:{key}"))
                else:
                    for addr in EMAIL_RE.findall(s):
                        n = normalize_email(addr)
                        if n:
                            hits.append((n, None, f"{rel}:{key}"))
        for addr in EMAIL_RE.findall(text[:3000]):
            norm = normalize_email(addr)
            if norm:
                hits.append((norm, None, f"{rel}:body"))
    return hits


def _norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def propose(vault: Path) -> list[dict]:
    lide = vault / "05-RESOURCES" / "lide"
    people = []
    for path in sorted(lide.glob("*.md")):
        if path.name.startswith("_"):
            continue
        p = load_person_from_file(path)
        if p:
            people.append(p)

    known: dict[str, set[str]] = {
        p.name: set(p.all_emails()) for p in people
    }
    by_name: dict[str, str] = {}
    for p in people:
        by_name[_norm_name(p.name)] = p.name
        for a in p.aliases:
            by_name[_norm_name(a)] = p.name
    by_local: dict[str, list[str]] = defaultdict(list)
    for p in people:
        for addr in p.all_emails():
            by_local[_local(addr)].append(p.name)

    observations: dict[tuple[str, str], set[str]] = defaultdict(set)
    # (person_name, new_email) → sources

    all_hits = (
        collect_from_emails(vault)
        + collect_from_calendar(vault)
        + collect_from_sembly(vault)
    )

    for email, display, source in all_hits:
        owner = None
        if display:
            owner = by_name.get(_norm_name(display))
        if owner is None:
            locals_ = by_local.get(_local(email)) or []
            # same local-part, different domain → candidate only if unique person
            uniq = sorted(set(locals_))
            if len(uniq) == 1:
                # only propose when domain differs from what they already have
                existing = known.get(uniq[0], set())
                if email not in existing:
                    # require at least one existing addr or company domain crossover
                    if existing or email.split("@")[-1] in COMPANY_DOMAINS:
                        owner = uniq[0]
        if owner is None:
            continue
        if email in known.get(owner, set()):
            continue
        observations[(owner, email)].add(source)

    proposals = []
    for (person, email), sources in sorted(observations.items()):
        proposals.append(
            {
                "person": person,
                "new_email": email,
                "known_emails": sorted(known.get(person, set())),
                "sources": sorted(sources)[:8],
                "source_count": len(sources),
            }
        )
    return proposals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--vault",
        type=Path,
        default=REPO / "OBSIDIAN",
    )
    args = ap.parse_args()
    vault = args.vault.expanduser().resolve()
    if not vault.exists():
        sys.stderr.write(f"vault not found: {vault}\n")
        return 1

    proposals = propose(vault)
    print(f"# multi-email proposals ({len(proposals)}) — NIKAM NEZAPSÁNO\n")
    if not proposals:
        print("Žádní kandidáti. Lidé s `emails:` už pokrytí, nebo zdroje nic nového nedaly.")
        return 0
    for p in proposals:
        print(f"## {p['person']}")
        print(f"- known: {', '.join(p['known_emails']) or '—'}")
        print(f"- propose: `{p['new_email']}`")
        print(f"- evidence: {p['source_count']} hits")
        for s in p["sources"]:
            print(f"  - {s}")
        print()
    print("Schválení: doplň `emails:` do person souboru ručně / řekni agentovi které řádky zapsat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
