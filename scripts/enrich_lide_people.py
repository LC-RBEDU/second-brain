#!/usr/bin/env python3
"""Enrich 05-RESOURCES/lide person profiles from vault + Gmail/Calendar.

Kontakty (e-mail, jméno) se doplňují z:
  1. Hub charterů a materiálů ve vaultu (kurátorované PERSON_PROFILES)
  2. Gmail MCP — search_gmail_messages + metadata hlaviček (From/To/Cc)
  3. Google Calendar MCP — get_events(detailed=true) účastníci pozvánek

Google Contacts / People API se nepoužívá — uživatel tam kontakty nemá.

Run after migrate_lide_persons.py / before or after sync_lide_people.py.
Preserves existing ## Zmínky table; fills frontmatter (email, slack, …) + Témata, Projekty.
Kontakty a významná data jsou jen ve frontmatter — ne duplicitně v body.

Usage:
  python3 scripts/enrich_lide_people.py
  python3 scripts/enrich_lide_people.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LIDE = REPO / "OBSIDIAN" / "05-RESOURCES" / "lide"
SKIP = {"_ŠABLONA-person.md", "_index.md"}

sys.path.insert(0, str(REPO / "scripts"))
from lide_person_template import (  # noqa: E402
    build_person_document,
    normalize_person_file,
    parse_frontmatter,
    parse_person_body,
    split_frontmatter,
)
from sync_lide_people import KNOWN_META, NICKNAMES  # noqa: E402

# Curated from hub ## Lidé / spolupráce, finance analýza, archiv e-mailů
PERSON_PROFILES: dict[str, dict] = {
    "Dominik Holíček": {
        "email": "dominik@redbuttonedu.cz",
        "role": "Finance specialist (~50 %)",
        "slack": "Domča",
        "projects": ["Finance", "Allfred", "Firemní procesy"],
        "topics": [
            "Provozní finance — fakturace, platby, cashflow",
            "Allfred — forecast nákladů, hygiena dat",
            "Finance sync s Lukášem (pondělní rytmus)",
        ],
        "projekty": "- [[Finance]] — finanční specialista (~50 %)\n- [[Allfred]] — finance operativa v nástroji\n- [[Firemní procesy]] — finance kroky v handover mapě",
    },
    "Luboš Malý": {
        "email": "lubos@redbuttonedu.cz",
        "role": "Co-strategist / CEO, principal Learning Designer",
        "slack": "Luboš",
        "projects": ["Strategy", "Owners"],
        "topics": [
            "Strategy tým — CEO, learning design",
            "1:1 s členy Strategy (S7)",
            "PNL H2 pracovní skupina",
        ],
        "projekty": "- [[Strategy]] — CEO a principal Learning Designer\n- [[Owners]] — spolumajitel / strategie",
    },
    "Martin Ruman": {
        "email": "martin.ruman@redbuttonedu.cz",
        "role": "Procesní architekt / Delivery & Operations",
        "slack": "Martin R.",
        "projects": ["Firemní procesy", "Sales a Business Development", "Strategy", "M&A Odyssey"],
        "topics": [
            "Sales/Delivery handover — procesní mapa (Miro → RB Universe)",
            "Procesní architekt modul v RB Universe",
            "Odyssey prodej podílu (prodávající)",
        ],
        "projekty": "- [[Firemní procesy]] — procesní architekt\n- [[Sales a Business Development]] — delivery handover\n- [[Strategy]] — Delivery & Operations\n- [[M&A Odyssey]] — prodávající (Odyssey)",
    },
    "Lenka Turečková": {
        "email": "lenka.tureckova@rainfellows.cz",
        "role": "Externí finanční konzultant (Rainfellows, ad-hoc)",
        "projects": ["Finance"],
        "topics": [
            "Úzká spolupráce s Martinou Maškovou — mzdy, DPFO, DPPO",
            "Pondělní finance meetingy (od 5. 5. 2026)",
            "Daňová témata — ubytování externistů (F33)",
        ],
        "projekty": "- [[Finance]] — externí konzultant (Rainfellows)",
    },
    "Lenka Vašková": {
        "email": "lenka@redbuttonedu.cz",
        "role": "People & Culture (Strategy tým)",
        "projects": ["Strategy"],
        "topics": [
            "People agenda napříč RB EDU",
            "Strategy tým — People&Culture",
        ],
        "projekty": "- [[Strategy]] — People&Culture",
    },
    "Martina Mašková": {
        "email": "martina@redbuttonedu.cz",
        "role": "Účetní (RBA)",
        "projects": ["Finance"],
        "topics": [
            "Statutární účetnictví RBA — DPH, DPPO, banky",
            "Párování plateb, měsíční reporting",
            "Stripe v účetní rovině",
        ],
        "projekty": "- [[Finance]] — účetní RBA",
    },
    "Pavel Kroupa": {
        "email": "pavel@redbuttonedu.cz",
        "role": "Delivery / PM (RB Universe)",
        "slack": "Pavel K.",
        "projects": ["RB Universe development", "Firemní procesy"],
        "topics": [
            "RB Universe development — PM",
            "Sales/Delivery handover — delivery strana",
        ],
        "projekty": "- [[RB Universe development]] — PM\n- [[Firemní procesy]] — delivery v handover procesu",
    },
    "Lukáš Dzuroška": {
        "email": "lukas.dzuroska@redbuttonedu.cz",
        "role": "CCO — Commercial (Sales + Marketing)",
        "projects": ["Strategy", "Sales a Business Development", "Exponential Summit"],
        "topics": [
            "Sales lead — akademie + EDU",
            "Exponential Summit — partners, sales, sponzor",
            "OB pro akademie, EDUtéka revize",
        ],
        "projekty": "- [[Strategy]] — Commercial (Sales + Marketing)\n- [[Sales a Business Development]] — Sales lead\n- [[Exponential Summit]] — partners & sponzor",
    },
    "Jan Mašek": {
        "email": "jan@redbutton.cz",
        "role": "Growth (Strategy tým)",
        "slack": "Honza",
        "projects": ["Strategy", "M&A Odyssey"],
        "topics": [
            "Growth agenda Strategy týmu",
            "Odyssey varianta s Lubošem (MO13)",
            "1:1 s Lukášem (S7)",
        ],
        "projekty": "- [[Strategy]] — Growth\n- [[M&A Odyssey]] — spolupráce na variantě Odyssey",
    },
    "Jarda Fulnek": {
        "email": "jaromir.fulnek@redbuttonedu.cz",
        "role": "Expertní konzultant (GS/GAS, odchází)",
        "slack": "Jarda",
        "projects": ["Finance"],
        "topics": [
            "Autor stávajícího Google Sheets / GAS řešení",
            "Postupný handover na Allfred",
            "Účast jen při přechodu",
        ],
        "projekty": "- [[Finance]] — legacy GS/GAS (odchází)",
    },
    "Michal Šrajer": {
        "email": "michal.srajer@redbuttonedu.cz",
        "role": "Dramaturgie eventu / speakers (Exponential Summit)",
        "projects": ["Exponential Summit", "RB Universe development"],
        "topics": [
            "Exponential Summit — dramaturgie, speakers",
            "Edutéka UI patterns (Mejzlík) — RBU31",
            "Universe — data o lidech z workshopů / LinkedIn",
        ],
        "projekty": "- [[Exponential Summit]] — dramaturgie, speakers\n- [[RB Universe development]] — UI patterns / people data",
    },
    "Michaela Valdéz": {
        "email": "michaela@redbuttonedu.cz",
        "role": "Event management, produkce (Michaela González Valdés)",
        "projects": ["Exponential Summit"],
        "aliases_extra": ["Michaela González Valdés"],
        "topics": [
            "Exponential Summit — event management a produkce",
            "Logistika konference (posun na únor 2027)",
            "Osobní e-mail: michaela@gonzalez-valdes.cz",
        ],
        "projekty": "- [[Exponential Summit]] — event management, produkce",
    },
    "Saša Gallisová": {
        "email": "alex@allfred.io",
        "role": "Allfred support (Alexandra Gallisová, Allfred.io)",
        "projects": ["Allfred"],
        "aliases_extra": ["Alexandra Gallisová"],
        "topics": [
            "Allfred support — API, planned expenses, bug tickety",
            "Komunikace s Domčou a Lukášem k Allfredu",
        ],
        "projekty": "- [[Allfred]] — Allfred support",
    },
    "Ondra Suchý": {
        "email": "ondrej.suchy@sudety.cz",
        "role": "Externí spolupracovník (Sudety — Equilibrium / Human in AI)",
        "projects": ["Vibe coding"],
        "aliases_extra": ["Ondřej Suchý"],
        "topics": [
            "Equilibrium diskuse — učící koncepty (Fayman)",
            "Human in AI setkání",
        ],
        "projekty": "- [[Vibe coding]] — AI / učení setkání",
    },
    "Veronika Kuncová": {
        "email": "veronika.kuncova@redbuttonedu.cz",
        "role": "Sales Ops / PRE-SALES, KAM",
        "slack": "Verča K.",
        "projects": ["Sales a Business Development", "Firemní procesy"],
        "topics": [
            "PRE-SALES swimlane v Sales/Delivery handover",
            "Akademie design nabídky (#akademie-design-nabidky)",
        ],
        "projekty": "- [[Sales a Business Development]] — Sales Ops / PRE-SALES\n- [[Firemní procesy]] — PRE-SALES v handover mapě",
    },
    "Veronika Hanzalová": {
        "email": "veronika@redbuttonedu.cz",
        "role": "EDUtéka / EC komunita",
        "slack": "Verča",
        "projects": ["Strategy", "Firemní procesy"],
        "topics": [
            "EDUtéka komunita (EC) — onboarding klientů",
            "Budget eventů na komunity (F32)",
            "GDPR evidence akcí — složky komunit",
        ],
        "projekty": "- [[Strategy]] — EDUtéka / EC komunita\n- [[Firemní procesy]] — EDUtéka onboarding v handover",
    },
    "Kateřina Bayerová": {
        "email": "katerina@redbuttonedu.cz",
        "role": "Strategy / People (schůzky, Town Hall)",
        "slack": "Káťa",
        "projects": ["Strategy", "RB Universe development"],
        "topics": [
            "Strategy tým — koordinace schůzek, Town Hall",
            "RB Universe — project lead (dovolené, profil, Signi)",
        ],
        "projekty": "- [[Strategy]] — Strategy / People\n- [[RB Universe development]] — project lead (profil, dovolené, Signi)",
    },
}


def _merge_profile(existing_fm: dict, profile: dict) -> dict:
    merged = dict(existing_fm)
    for key in ("email", "role", "slack"):
        val = profile.get(key)
        if val and val not in ("—", ""):
            merged[key] = val
    if profile.get("projects"):
        merged["projects"] = profile["projects"]
    # frontmatter topics = PARA tag (lide); obsah jde do ## Témata
    if not merged.get("topics"):
        merged["topics"] = ["lide"]
    return merged


def enrich_file(path: Path, dry_run: bool) -> bool:
    profile = PERSON_PROFILES.get(path.stem)
    if not profile:
        return False

    text = path.read_text(encoding="utf-8")
    fm_raw, body = split_frontmatter(text)
    existing_fm = parse_frontmatter(fm_raw) if fm_raw else {}
    _, nickname_line, sections = parse_person_body(body)

    merged_fm = _merge_profile(existing_fm, profile)
    for alias in profile.get("aliases_extra") or []:
        aliases = merged_fm.setdefault("aliases", [])
        if isinstance(aliases, list) and alias not in aliases:
            aliases.append(alias)
    meta = KNOWN_META.get(path.stem, {})
    if not merged_fm.get("role") or merged_fm.get("role") == "—":
        merged_fm["role"] = meta.get("role") or merged_fm.get("role")
    if not merged_fm.get("slack") and meta.get("slack"):
        merged_fm["slack"] = meta.get("slack")

    if profile.get("topics"):
        sections["## Témata"] = "\n".join(f"- {t}" for t in profile["topics"])
    if profile.get("projekty"):
        sections["## Projekty a tasky"] = profile["projekty"]

    new_text = build_person_document(
        path.stem,
        sections=sections,
        mentions_rows=None,
        existing_fm=merged_fm,
        known_meta=meta,
        nicknames=NICKNAMES.get(path.stem),
        nickname_line=nickname_line,
    )

    if new_text == text:
        return False
    if dry_run:
        print(f"would enrich: {path.name}")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"enriched: {path.name}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    n = 0
    for p in sorted(LIDE.glob("*.md")):
        if p.name in SKIP:
            continue
        if enrich_file(p, args.dry_run):
            n += 1
    print(f"enrich_lide_people: {n} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
