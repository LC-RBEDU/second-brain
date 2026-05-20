#!/usr/bin/env python3
"""Phase 2 migration (2026-05-20):

- rb-universe-development: T -> RBU (keep numbers)
- obecna-inspirace:        I -> OI (keep numbers)
- obchodni-podminky-rb-edu -> moved into NEW project sales-a-business-development (SBD)
  - OP5 -> SBD1 (most recent)
  - OP4 -> SBD2
  - OP3 -> SBD3
  - source file deleted, json entries reslugged
- create empty Osobní project (slug: osobni, tag: PRV)
"""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

VAULT = Path(
    os.environ.get(
        "VAULT_PATH",
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
    )
)
PROJEKTY = VAULT / "02-Projekty"
SOURCE_JSON = VAULT / "00-System/dashboard-tasks-source.json"

HEAD_RE = re.compile(
    r"(^###\s+(?:~~)?)([A-Z]+\d+[a-z]?)(?=\s*[—–-])",
    re.MULTILINE,
)
HOTOVO_BULLET_RE = re.compile(r"(^-\s+\*\*)([A-Z]+\d+[a-z]?)(\*\*)", re.MULTILINE)
WORD_RE = re.compile(r"\b([A-Z]+\d+[a-z]?)\b")


def t_to_rbu_map() -> dict[str, str]:
    # T1..T10, T12..T27 currently exist. We map every T<n> -> RBU<n>.
    out = {}
    for n in range(1, 28):
        out[f"T{n}"] = f"RBU{n}"
    return out


def i_to_oi_map() -> dict[str, str]:
    return {f"I{n}": f"OI{n}" for n in range(1, 20)}


def op_to_sbd_map() -> dict[str, str]:
    # Markdown order in obchodni-podminky-rb-edu.md is OP5, OP4, OP3
    return {"OP5": "SBD1", "OP4": "SBD2", "OP3": "SBD3"}


def rewrite_markdown_ids(slug: str, mapping: dict[str, str]) -> int:
    path = PROJEKTY / f"{slug}.md"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8")

    def head_sub(m: re.Match) -> str:
        return f"{m.group(1)}{mapping.get(m.group(2), m.group(2))}"

    def bullet_sub(m: re.Match) -> str:
        return f"{m.group(1)}{mapping.get(m.group(2), m.group(2))}{m.group(3)}"

    def word_sub(m: re.Match) -> str:
        return mapping.get(m.group(1), m.group(1))

    new = HEAD_RE.sub(head_sub, text)
    new = HOTOVO_BULLET_RE.sub(bullet_sub, new)
    new = WORD_RE.sub(word_sub, new)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return sum(1 for k in mapping if k in text and k != mapping[k])


def split_op_to_sbd() -> None:
    """Move obchodni-podminky-rb-edu tasks into a new sales-a-business-development.md."""
    src = PROJEKTY / "obchodni-podminky-rb-edu.md"
    if not src.is_file():
        print("  [skip] obchodni-podminky-rb-edu.md missing")
        return
    src_text = src.read_text(encoding="utf-8")
    # rename IDs OP3/4/5 -> SBD3/2/1 within source content (will be moved verbatim)
    sbd_map = op_to_sbd_map()
    new_text = src_text

    def head_sub(m: re.Match) -> str:
        return f"{m.group(1)}{sbd_map.get(m.group(2), m.group(2))}"

    def bullet_sub(m: re.Match) -> str:
        return f"{m.group(1)}{sbd_map.get(m.group(2), m.group(2))}{m.group(3)}"

    def word_sub(m: re.Match) -> str:
        return sbd_map.get(m.group(1), m.group(1))

    new_text = HEAD_RE.sub(head_sub, new_text)
    new_text = HOTOVO_BULLET_RE.sub(bullet_sub, new_text)
    new_text = WORD_RE.sub(word_sub, new_text)

    # Extract ## Aktivní úkoly section content
    def extract_section(text: str, header: str) -> str:
        m = re.search(rf"^##\s+{re.escape(header)}\s*$", text, re.MULTILINE)
        if not m:
            return ""
        start = m.end()
        nxt = re.search(r"^##\s+", text[start:], re.MULTILINE)
        end = start + nxt.start() if nxt else len(text)
        return text[start:end].strip("\n")

    aktivni = extract_section(new_text, "Aktivní úkoly")
    backlog = extract_section(new_text, "Backlog (nápady, ještě ne aktivní)")
    materialy = extract_section(new_text, "Materiály a poznámky")

    today = date.today().isoformat()
    sbd_md = f"""# Téma: Sales a Business development

**Slug**: `sales-a-business-development`
**Vznik**: {today}
**Posledně aktualizováno**: {today}
**Owner**: Lukáš

## Kontext

Aktivity směrem ven — sales, business development, smluvní rámec ke klientům, partnerství. Sem patří:

- VOP a smluvní šablony (B2B kontrakty na akademie, EDUtéka, jednorázovky)
- storno podmínky, GDPR, autorské licence, NDA
- benchmarking konkurence (QED, Odyssey, …) a partnerských OB
- onboarding nových klientů, pilotní zakázky, partnerské dohody

**Hranice**:
- vůči `firemni-procesy.md` — tady je smluvní rámec ven; tam jsou interní procesy (jak věci děláme uvnitř)
- vůči `ma-odyssey.md` — tam je konkrétní akviziční projekt; tady běžné B2B kontrakty
- vůči `strategy.md` — strategy = co děláme; SBD = jak to prodáváme a kontraktujeme

---

## Aktivní úkoly

{aktivni or "_(žádné)_"}

---

## Backlog (nápady, ještě ne aktivní)

{backlog or "_(žádné)_"}

---

## Otevřené otázky / čeká na data

_(žádné)_

---

## Materiály a poznámky

{materialy or "_(žádné)_"}

---

## Recently moved to HOTOVO

_(žádné)_
"""
    target = PROJEKTY / "sales-a-business-development.md"
    target.write_text(sbd_md, encoding="utf-8")
    src.unlink()
    print(f"  created {target.name} (from obchodni-podminky-rb-edu, OP3/4/5 -> SBD3/2/1)")
    print("  deleted obchodni-podminky-rb-edu.md")


def create_osobni() -> None:
    target = PROJEKTY / "osobni.md"
    if target.exists():
        print("  [skip] osobni.md already exists")
        return
    today = date.today().isoformat()
    content = f"""# Téma: Osobní

**Slug**: `osobni`
**Vznik**: {today}
**Posledně aktualizováno**: {today}
**Owner**: Lukáš

## Kontext

Osobní agenda mimo pracovní role — zdraví, rodina, finance, vzdělávání, koníčky, drobné věci k zařízení. Tag úkolů: **PRV**.

**Hranice**:
- pracovní úkoly patří do příslušného pracovního projektu (strategy, finance, …)
- inspirace a obsah ke čtení/sledování → `obecna-inspirace.md`

---

## Aktivní úkoly

_(žádné)_

---

## Backlog (nápady, ještě ne aktivní)

_(žádné)_

---

## Otevřené otázky / čeká na data

_(žádné)_

---

## Materiály a poznámky

_(žádné)_

---

## Recently moved to HOTOVO

_(žádné)_
"""
    target.write_text(content, encoding="utf-8")
    print(f"  created {target.name} (slug=osobni, tag=PRV)")


def remap_source_json() -> tuple[int, int, int]:
    if not SOURCE_JSON.is_file():
        return 0, 0, 0
    data = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))

    full_map: dict[str, dict[str, str]] = {
        "rb-universe-development": t_to_rbu_map(),
        "obecna-inspirace": i_to_oi_map(),
    }
    op_to_sbd = op_to_sbd_map()

    renamed = 0
    moved = 0
    dropped = 0
    seen: set[tuple[str, str]] = set()
    out_tasks: list[dict] = []
    for t in data.get("tasks", []):
        slug = t.get("proj") or ""
        old_id = t.get("id") or ""
        # Move OP -> SBD (slug change + id remap)
        if slug == "obchodni-podminky-rb-edu":
            new_slug = "sales-a-business-development"
            new_id = op_to_sbd.get(old_id, old_id)
            t["proj"] = new_slug
            t["id"] = new_id
            moved += 1
        else:
            mapping = full_map.get(slug, {})
            new_id = mapping.get(old_id, old_id)
            if new_id != old_id:
                t["id"] = new_id
                renamed += 1
        key = (t["proj"], t["id"])
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        t.pop("displayId", None)
        t.pop("projPrefix", None)
        out_tasks.append(t)
    data["tasks"] = out_tasks

    # proj_order: replace obchodni-podminky-rb-edu with sales-a-business-development; add osobni
    order = list(data.get("proj_order", []))
    if "obchodni-podminky-rb-edu" in order:
        idx = order.index("obchodni-podminky-rb-edu")
        order[idx] = "sales-a-business-development"
    if "sales-a-business-development" not in order:
        order.append("sales-a-business-development")
    if "osobni" not in order:
        order.append("osobni")
    data["proj_order"] = order

    projects = data.setdefault("projects", {})
    if "obchodni-podminky-rb-edu" in projects:
        old = projects.pop("obchodni-podminky-rb-edu")
        projects.setdefault(
            "sales-a-business-development",
            {
                "name": "Sales a Business development",
                "acc": old.get("acc", "r"),
                "watch": old.get("watch", []),
                "materials": old.get("materials", []),
                "done": old.get("done", []),
            },
        )
    projects.setdefault(
        "osobni",
        {"name": "Osobní", "acc": "gr", "watch": [], "materials": [], "done": []},
    )

    SOURCE_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return renamed, moved, dropped


def main() -> None:
    print(f"Vault: {VAULT}")

    # 1. T -> RBU in rb-universe-development.md
    n = rewrite_markdown_ids("rb-universe-development", t_to_rbu_map())
    print(f"  md  rb-universe-development.md   {n} ids T->RBU")

    # 2. I -> OI in obecna-inspirace.md
    n = rewrite_markdown_ids("obecna-inspirace", i_to_oi_map())
    print(f"  md  obecna-inspirace.md          {n} ids I->OI")

    # 3. OP -> SBD: split file
    split_op_to_sbd()

    # 4. Create Osobní
    create_osobni()

    # 5. JSON remap
    renamed, moved, dropped = remap_source_json()
    print(f"  json renamed={renamed}, op_moved={moved}, dropped(dup)={dropped}")
    print("done.")


if __name__ == "__main__":
    main()
