#!/usr/bin/env python3
"""Sync 05-RESOURCES/lide person profiles: wikilinks in vault + backlinks tables.

Usage:
  python3 scripts/sync_lide_people.py [--dry-run]
  python3 scripts/sync_lide_people.py --incremental --paths "02-PROJEKTY/foo/tasks/X.md,07-ARCHIV/..."
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VAULT = REPO / "OBSIDIAN"
LIDE = VAULT / "05-RESOURCES" / "lide"

# canonical name -> plain-text aliases (longest match wins; inflected forms use PIPE_ALIASES)
ALIASES: dict[str, list[str]] = {
    "Dominik Holíček": ["Dominik Holíček", "Domča"],
    "Luboš Malý": ["Luboš Malý", "Luboš"],
    "Martin Ruman": ["Martin Ruman", "Martin R."],
    "Lenka Turečková": ["Lenka Turečková", "Lenka T."],
    "Lenka Vašková": ["Lenka Vašková"],
    "Martina Mašková": ["Martina Mašková"],
    "Pavel Kroupa": ["Pavel Kroupa", "Pavel K."],
    "Lukáš Dzuroška": ["Lukáš Dzuroška"],
    "Jan Mašek": ["Jan Mašek", "Honza Mašek", "Honza"],
    "Jarda Fulnek": ["Jarda Fulnek"],
    "Michal Šrajer": ["Michal Šrajer"],
    "Michaela Valdéz": ["Michaela Valdéz", "Michaela González Valdés"],
    "Saša Gallisová": ["Saša Gallisová", "Alexandra Gallisová"],
    "Ondra Suchý": ["Ondra Suchý", "Ondřej Suchý"],
    "Veronika Kuncová": [
        "Veronika Kuncová",
        "Verča Kuncová",
        "Verča K.",
        "VerčaK.",
    ],
    "Veronika Hanzalová": [
        "Veronika Hanzalová",
        "Verča H.",
        "Verči H.",
    ],
    "Kateřina Bayerová": ["Kateřina Bayerová", "Kateřina Bayer"],
}

# alias -> person; wikilink keeps alias as display ([[Person|alias]])
PIPE_ALIASES: list[tuple[str, str]] = [
    ("Verčou Kuncovou", "Veronika Kuncová"),
    ("Verčiným", "Veronika Kuncová"),
    ("Verčanem", "Veronika Kuncová"),
    ("Honzou Maškem", "Jan Mašek"),
    ("Verčin", "Veronika Kuncová"),
    ("Verčou", "Veronika Kuncová"),
    ("Verču", "Veronika Kuncová"),
    ("Honzou", "Jan Mašek"),
    ("Honzovi", "Jan Mašek"),
    ("Honzu", "Jan Mašek"),
    ("Honzi", "Jan Mašek"),
    ("Luboše", "Luboš Malý"),
    ("Lubošem", "Luboš Malý"),
    ("Lubošom", "Luboš Malý"),
    ("Lubošovi", "Luboš Malý"),
    ("Luboša", "Luboš Malý"),
]

# regex alias -> person (display = matched text)
REGEX_ALIASES: list[tuple[str, str]] = [
    (r"Verča\s*\(EC\)", "Veronika Hanzalová"),
    (r"Verča\s+za\s+EC", "Veronika Hanzalová"),
]

# Fix prior linkify runs that split inflection suffixes from wikilinks
BROKEN_REPAIRS: list[tuple[str, str]] = [
    (r"\[\[Luboš Malý\]\]([a-záčďéěíňóřšťúůýž]+)", r"[[Luboš Malý|Luboš\1]]"),
    (r"\[\[Veronika Kuncová\]\]ým", "[[Veronika Kuncová|Verčiným]]"),
    (r"\[\[Veronika Kuncová\]\] Kuncovou", "[[Veronika Kuncová|Verčou Kuncovou]]"),
    (r"\[\[Jan Mašek\]\] Maškem", "[[Jan Mašek|Honzou Maškem]]"),
    (r"\[\[Veronika Hanzalová\]\] komunitu", "[[Veronika Hanzalová|Verča za EC]] komunitu"),
]

# Extra nicknames stored in person frontmatter (Obsidian aliases)
NICKNAMES: dict[str, list[str]] = {
    "Jan Mašek": ["Honza"],
    "Veronika Hanzalová": ["Verča"],
}

KNOWN_META: dict[str, dict[str, str | list[str]]] = {
    "Luboš Malý": {
        "role": "Co-strategist / CEO, principal Learning Designer",
        "org": "Red Button EDU",
        "email": "lubos@redbuttonedu.cz",
        "slack": "Luboš",
        "projects": ["Strategy", "Owners"],
    },
    "Dominik Holíček": {
        "role": "Finance specialist (~50 %)",
        "org": "Red Button EDU",
        "email": "dominik@redbuttonedu.cz",
        "slack": "Domča",
        "projects": ["Finance", "Allfred", "Firemní procesy"],
    },
    "Martin Ruman": {
        "role": "Procesní architekt / Delivery & Operations",
        "org": "Red Button EDU",
        "email": "martin.ruman@redbuttonedu.cz",
        "slack": "Martin R.",
        "projects": ["Firemní procesy", "Sales a Business Development", "Strategy", "M&A Odyssey"],
    },
    "Pavel Kroupa": {
        "role": "Delivery / PM (RB Universe)",
        "org": "Red Button EDU",
        "email": "pavel@redbuttonedu.cz",
        "slack": "Pavel K.",
        "projects": ["RB Universe development", "Firemní procesy"],
    },
    "Lukáš Dzuroška": {
        "role": "CCO — Commercial (Sales + Marketing)",
        "org": "Red Button EDU",
        "email": "lukas.dzuroska@redbuttonedu.cz",
        "projects": ["Strategy", "Sales a Business Development", "Exponential Summit"],
    },
    "Jan Mašek": {
        "role": "Growth (Strategy tým)",
        "org": "Red Button EDU",
        "email": "jan@redbutton.cz",
        "slack": "Honza",
        "projects": ["Strategy", "M&A Odyssey"],
    },
    "Veronika Kuncová": {
        "role": "Sales Ops / PRE-SALES, KAM",
        "org": "Red Button EDU",
        "email": "veronika.kuncova@redbuttonedu.cz",
        "slack": "Verča K.",
        "projects": ["Sales a Business Development", "Firemní procesy"],
    },
    "Veronika Hanzalová": {
        "role": "EDUtéka / EC komunita",
        "org": "Red Button EDU",
        "email": "veronika@redbuttonedu.cz",
        "slack": "Verča",
        "projects": ["Strategy", "Firemní procesy"],
    },
    "Kateřina Bayerová": {
        "role": "Strategy / People (schůzky, Town Hall)",
        "org": "Red Button EDU",
        "email": "katerina@redbuttonedu.cz",
        "slack": "Káťa",
        "projects": ["Strategy", "RB Universe development"],
    },
    "Lenka Turečková": {
        "role": "Externí finanční konzultant (Rainfellows, ad-hoc)",
        "org": "Rainfellows",
        "email": "lenka.tureckova@rainfellows.cz",
        "projects": ["Finance"],
    },
    "Lenka Vašková": {
        "role": "People & Culture (Strategy tým)",
        "org": "Red Button EDU",
        "email": "lenka@redbuttonedu.cz",
        "projects": ["Strategy"],
    },
    "Martina Mašková": {
        "role": "Účetní (RBA)",
        "org": "Red Button EDU",
        "email": "martina@redbuttonedu.cz",
        "projects": ["Finance"],
    },
    "Jarda Fulnek": {
        "role": "Expertní konzultant (GS/GAS, odchází)",
        "org": "Red Button EDU",
        "email": "jaromir.fulnek@redbuttonedu.cz",
        "slack": "Jarda",
        "projects": ["Finance"],
    },
    "Michal Šrajer": {
        "role": "Dramaturgie eventu / speakers (Exponential Summit)",
        "org": "Red Button EDU",
        "email": "michal.srajer@redbuttonedu.cz",
        "projects": ["Exponential Summit", "RB Universe development"],
    },
    "Michaela Valdéz": {
        "role": "Event management, produkce (Michaela González Valdés)",
        "org": "Red Button EDU",
        "email": "michaela@redbuttonedu.cz",
        "projects": ["Exponential Summit"],
    },
    "Saša Gallisová": {
        "role": "Allfred support (Alexandra Gallisová, Allfred.io)",
        "org": "Allfred.io",
        "email": "alex@allfred.io",
        "projects": ["Allfred"],
    },
    "Ondra Suchý": {
        "role": "Externí spolupracovník (Sudety — Equilibrium / Human in AI)",
        "org": "Sudety",
        "email": "ondrej.suchy@sudety.cz",
        "projects": ["Vibe coding"],
    },
}


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        m = re.match(r"---\n.*?\n---\n", text, re.S)
        if m:
            return m.group(0), text[m.end() :]
    return "", text


def in_fence_or_fm(full: str, pos: int, fm_len: int) -> bool:
    if pos < fm_len:
        return True
    return full[:pos].count("```") % 2 == 1


def inside_wikilink(full: str, pos: int) -> bool:
    before = full[:pos]
    return before.rfind("[[") > before.rfind("]]")


def extract_date(path: Path, content: str) -> str:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
    if m:
        return m.group(1)
    for key in ("updated:", "created:", "date:"):
        m = re.search(rf"^{key}\s*['\"]?(20\d{2}-\d{2}-\d{2})", content, re.M)
        if m:
            return m.group(1)
    return "—"


def classify(path: Path) -> str:
    rel = path.relative_to(VAULT).as_posix()
    if "/tasks/" in rel:
        return "task"
    if "/materials/" in rel or "/outputs/" in rel:
        return "materiál"
    if rel.startswith("05-RESOURCES/inspirace"):
        return "inspirace"
    if rel.startswith("02-PROJEKTY/") and rel.count("/") == 1:
        return "hub"
    if rel.startswith("03-AREAS/"):
        return "area"
    if rel.startswith("07-ARCHIV/"):
        return "archiv"
    if "slack" in rel or "sembly" in rel:
        return "capture"
    if rel.startswith("01-INBOX/"):
        return "inbox"
    return "poznámka"


def kontext_snippet(text: str, person: str, aliases: list[str]) -> str:
    idx = text.find(f"[[{person}]]")
    if idx == -1:
        idx = text.find(f"[[{person}|")
    if idx == -1:
        for a in aliases:
            idx = text.find(a)
            if idx != -1:
                break
    if idx < 0:
        return ""
    sn = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", text[max(0, idx - 30) : idx + 90])
    return re.sub(r"\s+", " ", sn).strip()[:90]


def _wikilink(person: str, display: str | None = None) -> str:
    if display and display != person:
        return f"[[{person}|{display}]]"
    return f"[[{person}]]"


def _replace_at(text: str, idx: int, length: int, person: str, display: str | None = None) -> str:
    repl = _wikilink(person, display)
    return text[:idx] + repl + text[idx + length :]


def _apply_repairs(text: str) -> str:
    for pattern, repl in BROKEN_REPAIRS:
        text = re.sub(pattern, repl, text)
    return text


def _replace_plain_alias(text: str, alias: str, person: str, fm_len: int) -> str:
    """Plain alias replace; bare 'Luboš' must not match inside inflected forms."""
    start = 0
    while True:
        idx = text.find(alias, start)
        if idx == -1:
            break
        if in_fence_or_fm(text, idx, fm_len) or inside_wikilink(text, idx):
            start = idx + len(alias)
            continue
        if alias == "Luboš":
            after = text[idx + len(alias) : idx + len(alias) + 1]
            if after and after.lower() in "aáeéiíoóuúyýěščřžďťň":
                start = idx + len(alias)
                continue
        text = _replace_at(text, idx, len(alias), person)
        start = idx + len(_wikilink(person))
    return text


def _linkify_patterns() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    pipe_patterns = sorted(PIPE_ALIASES, key=lambda x: len(x[0]), reverse=True)
    plain_patterns: list[tuple[str, str]] = []
    for person, aliases in ALIASES.items():
        for a in aliases:
            plain_patterns.append((a, person))
    plain_patterns.sort(key=lambda x: len(x[0]), reverse=True)
    return pipe_patterns, plain_patterns


def linkify_file(
    fpath: Path,
    *,
    dry_run: bool,
    pipe_patterns: list[tuple[str, str]] | None = None,
    plain_patterns: list[tuple[str, str]] | None = None,
) -> bool:
    if "05-RESOURCES/lide" in fpath.as_posix():
        return False
    if pipe_patterns is None or plain_patterns is None:
        pipe_patterns, plain_patterns = _linkify_patterns()

    text = fpath.read_text(encoding="utf-8")
    orig = text
    fm_block, _ = split_frontmatter(text)
    fm_len = len(fm_block)

    text = _apply_repairs(text)

    for alias, person in pipe_patterns:
        start = 0
        while True:
            idx = text.find(alias, start)
            if idx == -1:
                break
            if in_fence_or_fm(text, idx, fm_len) or inside_wikilink(text, idx):
                start = idx + len(alias)
                continue
            text = _replace_at(text, idx, len(alias), person, alias)
            start = idx + len(_wikilink(person, alias))

    for pattern, person in REGEX_ALIASES:
        search_from = 0
        while True:
            m = re.search(pattern, text[search_from:])
            if not m:
                break
            idx = search_from + m.start()
            if in_fence_or_fm(text, idx, fm_len) or inside_wikilink(text, idx):
                search_from = idx + m.end() - m.start()
                continue
            text = _replace_at(text, idx, m.end() - m.start(), person, m.group(0))
            search_from = idx + len(_wikilink(person, m.group(0)))

    for alias, person in plain_patterns:
        text = _replace_plain_alias(text, alias, person, fm_len)

    if text == orig:
        return False
    if not dry_run:
        fpath.write_text(text, encoding="utf-8")
    return True


def resolve_vault_paths(raw_paths: list[str], vault: Path) -> list[Path]:
    resolved: list[Path] = []
    seen: set[str] = set()
    for raw in raw_paths:
        raw = raw.strip()
        if not raw:
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = vault / raw
        try:
            p = p.resolve()
            p.relative_to(vault.resolve())
        except ValueError:
            print(f"skip: outside vault: {raw}", file=sys.stderr)
            continue
        if not p.is_file() or p.suffix != ".md":
            print(f"skip: not a markdown file: {raw}", file=sys.stderr)
            continue
        key = p.as_posix()
        if key in seen:
            continue
        seen.add(key)
        resolved.append(p)
    return resolved


def linkify_vault(dry_run: bool, *, paths: list[Path] | None = None) -> int:
    pipe_patterns, plain_patterns = _linkify_patterns()
    if paths is None:
        targets = sorted(
            p for p in VAULT.rglob("*.md") if "05-RESOURCES/lide" not in p.as_posix()
        )
    else:
        targets = paths

    modified = 0
    for fpath in targets:
        if linkify_file(
            fpath,
            dry_run=dry_run,
            pipe_patterns=pipe_patterns,
            plain_patterns=plain_patterns,
        ):
            modified += 1
    return modified


def rebuild_person_files(dry_run: bool) -> dict[str, int]:
    sys.path.insert(0, str(REPO / "scripts"))
    from lide_person_template import build_person_document, normalize_person_file  # noqa: E402

    mentions: dict[str, dict[str, dict]] = {p: {} for p in ALIASES}
    for fpath in VAULT.rglob("*.md"):
        rel = fpath.relative_to(VAULT).as_posix()
        if rel.startswith("05-RESOURCES/lide/"):
            continue
        text = fpath.read_text(encoding="utf-8")
        link = f"[[{fpath.stem}]]"
        for person, aliases in ALIASES.items():
            hit = f"[[{person}]]" in text or f"[[{person}|" in text
            if not hit:
                hit = any(a in text for a in aliases)
            if not hit:
                hit = any(p == person for a, p in PIPE_ALIASES if a in text)
            if not hit:
                for pat, p in REGEX_ALIASES:
                    if p == person and re.search(pat, text):
                        hit = True
                        break
            if not hit:
                continue
            mentions[person][rel] = {
                "date": extract_date(fpath, text),
                "typ": classify(fpath),
                "link": link,
                "kontext": kontext_snippet(text, person, aliases) or fpath.stem[:70],
            }

    counts = {}
    for person, rows_by_path in mentions.items():
        rows = sorted(rows_by_path.values(), key=lambda r: r["date"], reverse=True)
        counts[person] = len(rows)
        pf = LIDE / f"{person}.md"
        if pf.exists():
            new_text = normalize_person_file(
                pf,
                mentions_rows=rows,
                known_meta=KNOWN_META.get(person),
                nicknames=NICKNAMES.get(person),
            )
        else:
            new_text = build_person_document(
                person,
                mentions_rows=rows,
                known_meta=KNOWN_META.get(person),
                nicknames=NICKNAMES.get(person),
            )
        if not dry_run:
            pf.write_text(new_text, encoding="utf-8")
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--incremental",
        action="store_true",
        help="Linkify only --paths; always rebuild lide/*.md tables",
    )
    ap.add_argument(
        "--paths",
        default="",
        help="Vault-relative .md paths (with --incremental); odděluj středníkem (;). Čárka v názvu souboru je OK.",
    )
    ap.add_argument("--vault", default="", help="Vault root (default: OBSIDIAN/ in repo)")
    args = ap.parse_args()

    global VAULT, LIDE
    if args.vault:
        VAULT = Path(args.vault).expanduser().resolve()
        LIDE = VAULT / "05-RESOURCES" / "lide"

    link_paths: list[Path] | None = None
    if args.incremental:
        sep = ";" if ";" in args.paths else "\n"
        chunks = [c.strip() for c in args.paths.split(sep) if c.strip()]
        if not chunks and args.paths.strip():
            chunks = [args.paths.strip()]
        link_paths = resolve_vault_paths(chunks, VAULT)
    elif args.paths:
        ap.error("--paths requires --incremental")

    n = linkify_vault(args.dry_run, paths=link_paths if args.incremental else None)
    counts = rebuild_person_files(args.dry_run)
    mode = "incremental" if args.incremental else "full"
    print(f"lide_sync: mode={mode} linkified_files={n} profiles_rebuilt={len(counts)}")
    for p, c in sorted(counts.items(), key=lambda x: -x[1]):
        if c > 0:
            print(f"  {p}: {c}")


if __name__ == "__main__":
    main()
