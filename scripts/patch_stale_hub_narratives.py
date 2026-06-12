#!/usr/bin/env python3
"""One-off narrative refresh for stale hub charters (2026-06-13)."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HUBS = REPO / "OBSIDIAN" / "02-PROJEKTY"
TODAY = date.today().isoformat()

# filename -> (kontext markdown, otevřené otázky markdown or None to skip)
PATCHES: dict[str, tuple[str, str | None]] = {
    "Allfred.md": (
        """Allfred je primární nástroj pro Project Governance a Financial Management pro RB EDU. PM vs. finance práva a eurofakturace zůstávají otevřené produktové otázky.

**Červen 2026 — operativní fronta:**
- **AF12** (ASAP) — forecast nákladů v Alfrédu; navazuje na Finance sync 11. 6. a spolupráci s Domčou
- **AF2** — eurofakturace krok 2 (deadline prošel, stále otevřené)
- **AF11** hotovo 10. 6. — Planned Expenses / API call se Sašou; další kroky v AF12 a procesu closing (AF9)
- Dlouhodobě: Request for Invoicing práva (AF1), IBAN párování (AF5), fakturační kroky s Dominikem (AF8), project closing (AF9)

**Klíčové zdroje:**
- [[02-PROJEKTY/allfred/materials/allfred-notebooklm-knowledge-base|NotebookLM knowledge base]]
- [[02-PROJEKTY/allfred/materials/allfred-gdoc-key-source|Projektový log (schůzky se Sašou Jan–Jun 2026)]]""",
        """- Co konkrétně může PM editovat / schválit v Request for Invoicing? — [[AF1 — Otestovat Request for Invoicing proces v Alfrédu (PM vs. finance práva)]]
- Eurofakturace s manuálním kurzem — kdy je hotová? — [[AF2 — Alfred eurofakturace proklikat krok 2 s Domčou]]
- IBAN párování — stav po reportu? — [[AF5 — Ověřit -nahlásit Alfrédu bug IBAN párování]]
- Forecast nákladů — kdo dělá co v červnu? — [[AF12 — Rozchodit forecast nákladů v Alfrédu (Lukáš krok 1, červen)]]""",
    ),
    "Finance.md": (
        """Téma pokrývá fungování a rozvoj finančního týmu. Hranice vůči [[Firemní procesy]]: Finance = lidi a týmová agenda. Hranice vůči [[Allfred]]: nastavení/bugy nástroje → [[Allfred]].

**Červen 2026 — operativní fronta:**
- **F4** (ASAP) — cashflow forecast v Alfrédu (propojení s AF12)
- **F21** — CFO commentary před strategickou schůzkou (deadline dnes/zítra)
- **F19** — Šuplíčky Happiness: srovnání + mock + proces (deadline 14. 6.)
- **F35** — Money S3 XML vs. Allfred export faktur
- **F33** — sledovat Lenku / daňař červen (3 témata)
- Pondělní finance sync s Domčou + Lenkou běží; **F2** (analýza Q1 zakázek) hotovo 9. 6.

**Tým — složení a zodpovědnosti** (evergreen, viz [[02-PROJEKTY/finance/outputs/2026-05-21-analyza-financni-tym-naplně]]):

### Lukáš Cypra — vedení týmu, banky, smlouvy, Strategy link
### [[Dominik Holíček]] — finanční specialista (~50 %)
### [[Martina Mašková]] — účetní RBA
### [[Lenka Turečková]] — externí konzultant (Rainfellows)
### Jarda — GS/GAS legacy, odchází""",
        """- **F19** — dokončit šuplíčky Happiness do 14. 6.?
- **F4 + AF12** — kdy bude cashflow forecast v Alfrédu použitelný pro Strategy?
- **F33** — výsledek daňových témat s Lenkou (ubytování externistů, …)
- Kontokorent FIO — stav po žádosti (F17 v archivu) — sledovat v bankovní agendě""",
    ),
    "Firemní procesy.md": (
        """Pokrývá obecné interní procesy a pravidla napříč firmou. Klíčový partner: [[Martin Ruman]] (procesní architekt, sales/delivery handover).

**Červen 2026 — stav:**
- Handover mapa z Mira (WIP) — aktivní **FP14** (finance kroky v Alfredovi)
- Nové fronty: onboarding manuály (**FP22**), švárc/smlouvy kontraktory (**FP16**), kurzová politika faktur (**FP20**), PM progress vs. finance (**FP19**), AI procesní řízení (**FP18**)
- FP1 (handover rollout) — mimo open tasks; focus je na doplnění mapy a rollout do týmu

## Procesní architekt (RB Universe)

- **URL:** https://dev-universe.redbuttonedu.cz (Procesní architekt modul)
- **MCP:** https://mcp.redbuttonedu.cz/mcp (`rb-universe` v Cursor MCP)
- **Workflow:** draft v `02-PROJEKTY/firemni-procesy/procesy/*.md` → import — skill `agenda-proces`""",
        """- **FP14** — jak doplnit FINANCE swimlane v handover mapě (Miro → Alfred kroky)?
- **FP22** — onboarding checklist a manuály: co je MVP?
- **FP16** — smlouvy s kontraktory / švárc: právní rámec a proces
- Sladění s [[Sales a Business Development]] (storno, VOP) a [[Finance]] (karty, doklady)""",
    ),
    "M&A Odyssey.md": (
        """EDU kupuje 100 % zbytku Odyssey. Klíčoví aktéři: [[Martin Ruman]] (prodávající), Jan Lokajíček (právník RB EDU).

**Timeline:**
- Cash záloha 500k → odeslána (MO8 v archivu)
- Podílová část → 2. polovina června 2026 (jsme v termínu), záložně srpen 2026
- **MO13** hotovo 12. 6. — varianta Luboš + Honza doladěna

**Červen 2026 — aktivní fronta (3× ASAP):**
- **MO14** — naplánovat owners setkání červen (Odyssey + zápisy); propojení s [[Owners]]
- **MO5** — spustit DD (rozsah + dokumenty)
- **MO15** — sledovat banku / kontokorent 1 M Kč (Odyssey fallback)
- **MO7** — další hovor s Lokajíčkem (SPA, DD, jednatel, FITCOIN)

**FITCOIN:** mimo deal, hibernace.""",
        """- **MO5** — finální scope DD (úvěry, garance, smlouvy, dotace)?
- **MO7** — termín hovoru s Lokajíčkem a agenda (SPA, jméno jednatele Odyssey)
- **MO14 + OWN1** — jedno owners setkání nebo dva paralelní formáty?
- Podílová část — stav k polovině června 2026""",
    ),
    "Operations.md": (
        """Provozní a technické úkoly mimo produktové/finanční projekty. Lukáš jako „mistr" pro ad-hoc technické implementace.

**Recurring OPS2 — EDU news (weekly, čtvrtek):** ~30s video, témata max 5, auto-refresh v 8:00 (`lifecycle_extra_edu_news.py`). Jediný otevřený task = rotace OPS2 (Waiting do 17. 6.).""",
        None,
    ),
    "Owners.md": (
        """Pravidelná setkání owners. **Červen 2026:** příprava formátu a agendy před setkáním.

**Aktivní chain:**
- **OWN2** — šablona setkání (blokuje OWN3)
- **OWN1** — agenda červnového Owners (obrat × ziskovost × RB Index), deadline **15. 6.**
- **OWN3** — rozeslat požadavek na doplnění šablony (po OWN2)
- **OWN6** — owners experience / onboarding a feedback loop

**Cross-hub:** [[MO14 — Naplánovat owners setkání červen — Odyssey a zápisy]] (M&A Odyssey) — sladit s OWN1.""",
        """- **OWN2 → OWN3** — kdy je šablona hotová k rozeslání?
- **OWN1** vs. **MO14** — jedna schůzka nebo oddělené agendy?
- **OWN6** — scope onboarding/feedback loop pro nové owners formáty""",
    ),
    "RB Universe development.md": (
        """Stack: FastAPI + PostgreSQL + React + Coolify. Tady je **development** (features, tech debt, architektura).

**Červen 2026 — fáze po pre-pilotu:**
- Hotovo nedávno: **RBU1** MCP data integrity (10. 6.), **RBU40** fin. shrnutí projekťákům, **RBU36** scoring Veronika (12. 6.)
- Pre-pilot hotové dříve: RBU5 profil, RBU4 dovolené, RBU29 fin. přehled nákladů
- **TOP teď:** **RBU37** brand launch na townhallu (26. 6.), **RBU33** feedback Michal Poppe, **RBU21** enrichment profilů lidí
- Backlog fronty: filtrace (**RBU15**), Signi (**RBU6**, čeká Káťu), PM features (**RBU7**), alokace/scoring (**RBU16–17**), externisté (**RBU23**), Sembly enrichment (**RBU27**), onboarding board (**RBU35**)""",
        """- **RBU37** — co přesně launchneme 26. 6. na townhallu?
- **RBU6** — Signi: blocker stále u Káty / šablon smluv?
- **RBU15** — filtrace: HubSpot model vs. vlastní?
- **RBU21** — enrichment lidí: LinkedIn + akce — SSOT vault vs. Universe?""",
    ),
    "Red Button Network.md": (
        """Síť externích spolupracovníků RB.

**Květen 2026:** Akcelerační panel pilot (21. 5.) — Kateřina + Tomáš, formát opakovatelný ([[02-PROJEKTY/rb-network/outputs/2026-05-21-akceleracni-panel-pilot|zápis]]).

**Červen 2026 — aktivní fronta:**
- **RBN3** (ASAP) — dotazník Equilibrium 2026 (Typeform)
- **RBN1** (Backlog) — katalog Network: první podoba, schůzka s Adélou stále otevřená otázka""",
        """- **RBN3** — Equilibrium dotazník: kdo vyplňuje, deadline?
- **Adéla** — katalog Network: podoba, cíl, RB Universe vs. jiný nástroj (RBN1)
- Opakování akceleračního panelu — kdy a pro koho?""",
    ),
    "Sales a Business Development.md": (
        """Sales a B2B kontrakty.

**Červen 2026 — open fronty:**
- **SBD1** (Next) — ověřit podmínky QED a Odyssey v materiálech od Martina
- **SBD4** (Waiting) — Česká spořitelna: rozšíření rámcovky (dodatek)
- Storno podmínky / VOP revize — v procesní mapě ([[Martin Ruman]]), orphan ref SBD2 bez tasku
- OB akademie + EDUtéka revize (Lukáš D.) — **SBD3** v Backlogu, ne aktivní open task""",
        """- **SBD4** — ČS dodatek: co čekáme a od koho?
- **SBD1** — kde jsou finální materiály QED/Odyssey OP?
- Sladění storno podmínek VOP vs. delivery průvodce — potřeba nový task nebo FP14?
- **SBD3** — kdy aktivovat OB revizi akademií?""",
    ),
    "Strategy.md": (
        """**SSOT:** [Strategy — Priority a follow-up (Google Doc)](https://docs.google.com/document/d/1ww0bP_K1FvgJ_eTfqYt3aBVTo7uvKo3L7HLB3HWg-2k/edit) — TOP 5, follow-up tabulka, zápisy.

Tým: CEO ([[Luboš Malý]]) + 5 rolí. Poslední strategická schůzka **28. 4. 2026**; **S13** hotovo 9. 6. (Strategy 1. 6. — fin. přehled, režijní rozpočty).

**Červen 2026 — posun na H2 plánování:**
- **S7** (ASAP, deadline 15. 6.) — 1:1 s členy Strategy týmu + KPIs do dashboardu
- **S12** — pracovní skupina PNL H2 (týden 13.–17. 7.)
- **S11** — Strategy Activation workshop H2 (20.–21. 8.)
- **S2**, **S5**, **S8** — hierarchie cílů, Summit posun, externí spolupráce balíček

**Watch:** L&D budget cuts / globální tarify. Exponential Summit → únor 2027.""",
        """- **S7** — KPIs do dashboardu: co je MVP do 15. 6.?
- **S12** — kdo je v PNL H2 working group a co je výstup?
- **S2** — hierarchie obrat × ziskovost × dopad při trade-off?
- **S5** — Q4 kapacita po posunu Exponential Summit
- Jak měřit „dopad" jako KPI Strategy týmu?""",
    ),
    "Vibe coding.md": (
        """Praktická / osobní rovina vibe-coding a internal AI agents. Inspirace: AI Meetup (Ondra Tyl, 20. 5.), [[Pavel Kroupa]] (Hermes Agent / Samo SATO).

**Červen 2026 — aktivní fronta:**
- **VC7** (ASAP) — doplnit Obsidian / Cursor agent context (scope projektů, DoD) — přímo souvisí se stale huby a Second Brain v2
- **VC8** (Next) — Equilibrium AI agents manuál: use-casy pro vault

Backlog inspirace: VC4 (meetup tooling), VC2 (Samo SATO na VPS).""",
        """- **VC7** — definition of done pro agent context refresh?
- **VC8** — které use-casy z Equilibrium manuálu adoptovat do vaultu?
- VC2 / VC4 — kdy přesunout z Backlogu na Next?""",
    ),
}

PROGRESS_RB = """## Progress

- **2026-06-12:** RBU40 fin. shrnutí projekťákům; RBU36 scoring Veronika; RBU1 MCP data integrity hotovo.
- **2026-06-10:** RBU1 MCP rozšíření dokončeno.
- **2026-05-24:** RBU5 profil, RBU4 dovolené, RBU29 fin. přehled nákladů (pre-pilot).
- **2026-05-07:** Follow-up s Káťou — dovolené, profil, Signi ([[02-PROJEKTY/rb-universe-development/materials/2026-05-07-sembly-follow-up-k-appce|transkript]])."""


def replace_section(body: str, header: str, new_content: str) -> str:
    pattern = re.compile(
        rf"(^{re.escape(header)}\s*\n)(.*?)(?=^## |\Z)",
        re.M | re.S,
    )
    m = pattern.search(body)
    if not m:
        return body
    return body[: m.start()] + m.group(1) + new_content.rstrip() + "\n\n" + body[m.end() :]


def patch_hub(path: Path, kontext: str, otazky: str | None) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    text = re.sub(r"^updated:\s*\d{4}-\d{2}-\d{2}\s*$", f"updated: {TODAY}", text, count=1, flags=re.M)
    fm_end = text.find("\n---", 4)
    body = text[fm_end + 4 :] if fm_end >= 0 else text
    body = replace_section(body.lstrip("\n"), "## Kontext", kontext)
    if otazky is not None:
        body = replace_section(body, "## Otevřené otázky", otazky)
    if path.name == "RB Universe development.md":
        body = replace_section(body, "## Progress", PROGRESS_RB.replace("## Progress\n\n", ""))
    new_text = text[: fm_end + 4] + "\n" + body if fm_end >= 0 else body
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    if new_text != orig:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> int:
    n = 0
    for fname, (kontext, otazky) in PATCHES.items():
        p = HUBS / fname
        if not p.exists():
            print(f"MISSING {fname}")
            continue
        if patch_hub(p, kontext, otazky):
            print(f"patched {fname}")
            n += 1
    print(f"patch_stale_hub_narratives: {n} hub(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
