---
name: agenda-work
description: "Use this skill when the user wants to work on a specific AGENDA topic — creating or updating documents, mindmaps, calculations, scripts, MCPs, or other outputs. Triggers: 'jdeme na <slug>', 'pracujeme na <slug>', 'otevři <slug>', 'pokračujeme v <slug>', 'udělej mi dokument pro <slug>', 'aktualizuj výstupy <slug>'. Also trigger when user wants to update the task list inside a topic ('uprav úkoly', 'přidej task', 'uzavři task', 'co zbývá v <slug>'). Reads the AGENDA topic file + scans VÝSTUPY/<slug>/ for existing outputs, then presents a clear starting point. NEVER modifies AGENDA files or outputs without user confirmation of what to do."
---

# agenda-work

> Otevři téma, zorientuj se, udělej výstup. Spojuje AGENDA (úkoly, kontext) s VÝSTUPY (dokumenty, mindmapy, kalkulace, skripty...).

## Kdy spouštět

- "Jdeme na <slug>" / "Pracujeme na <slug>" / "Otevři <slug>"
- "Pokračujeme v <slug>" / "Co zbývá v <slug>"
- "Udělej mi dokument / mindmapu / kalkulaci pro <téma>"
- "Aktualizuj výstupy <slug>"
- "Uprav úkoly v <slug>" / "Přidej task" / "Uzavři task"

---

## Workflow

### 1. Načti kontext

Před tím než cokoli uděláš:

1. Přečti `CLAUDE COWORK/O MNĚ/about-me.md` (pokud ještě v session ne)
2. Přečti `MrLUC/02-PROJEKTY/<slug>.md` (kontext, aktivní úkoly, backlog, materiály)
3. Projdi `MrLUC/02-PROJEKTY/<slug>/` — seznam existujících souborů s typem a odhadovaným stářím (datum z názvu nebo mtime)

Pokud slug není jasný z uživatelovy zprávy → zobraz seznam aktivních témat z `00-System/Index.md` a ptej se.

### 2. Ukaž orientační přehled

Vždy na začátku session zobraz:

```
═══════════════════════════════════════════════
TÉMA: <Název tématu> [<slug>]
═══════════════════════════════════════════════

📋 AKTIVNÍ ÚKOLY (<N>)
  • [Q1, S=18] Název úkolu — vrátit se: dnes
  • [Q2, S=12] Název úkolu — vrátit se: 2026-05-10
  ...

📁 EXISTUJÍCÍ VÝSTUPY
  • report-q1-2026.docx (Word dokument, 2026-04-15)
  • architektura-rb-universe.md (Mermaid mindmapa, 2026-04-20)
  • kalkulace-naklady.xlsx (Excel, 2026-04-01)
  [prázdné — žádné výstupy zatím]

💡 BACKLOG (nápady bez akce): <N> položek

═══════════════════════════════════════════════
Co chceš dělat?
  [N] Nový výstup
  [U] Aktualizovat existující výstup
  [T] Upravit úkoly (přidat / uzavřít / změnit metadata)
  [D] Detail tématu (celý AGENDA soubor)
```

Pokud uživatel zadal konkrétní instrukci hned (např. "udělej mi mindmapu procesu onboarding"), přeskoč výběr a jdi rovnou na krok 3 s tím, co žádal.

### 3. Proveď práci

#### 3A — Nový nebo aktualizovaný výstup

Typy výstupů a kde je uložit:

| Typ | Formát | Kde ukládat |
|-----|--------|-------------|
| Dokument (zpráva, analýza, memo) | `.docx` (použij docx skill) | `VÝSTUPY/<slug>/` |
| Mindmapa / diagram | interaktivní HTML widget v chatu NEBO `.mermaid` soubor | `VÝSTUPY/<slug>/` |
| Kalkulace / tabulka | `.xlsx` (použij xlsx skill) | `VÝSTUPY/<slug>/` |
| Strukturovaná poznámka / framework | `.md` | `VÝSTUPY/<slug>/` |
| Skript (Python, JS, GAS...) | `.py` / `.js` / `.gs` | `VÝSTUPY/<slug>/` |
| MCP / n8n workflow | `.json` nebo složka | `VÝSTUPY/<slug>/` |
| PDF | `.pdf` (použij pdf skill) | `VÝSTUPY/<slug>/` |

Při **aktualizaci existujícího souboru**:
- Přečti soubor, identifikuj, co je zastaralé nebo neúplné
- Navrhni konkrétní změny PŘED zápisem
- Přidej do názvu verzi nebo datum jen pokud uživatel chce archivovat původní (default: přepiš)

Při **tvorbě nového výstupu**:
- Zeptej se na rozsah a účel, pokud není jasný
- Navrhni obsah / osnovu před výrobou
- Postupuj iterativně u delších dokumentů (část → schválení → část)

#### 3B — Úprava úkolů

Ukáž aktuální úkoly a navrhni změny:

```
Návrh změn v AGENDA/<slug>.md:

✅ Uzavřít (přesunout do "Recently moved to HOTOVO"):
  • [Q2, S=14] Přidat retry do FIO syncu

➕ Přidat:
  • [Q2, ICE 7/6/5, S=8.4] Napsat tech spec pro ReBeL Slack integraci
    Vrátit se: 2026-05-15 | Blokováno: nic

✏️ Upravit metadata:
  • [Q1] Sales dashboard → přesunout do Q2 (deadline splněn)

OK? (ano / uprav)
```

Proveď zápis až po potvrzení.

### 4. Ulož výstupy

- Výstup ulož do `VÝSTUPY/<slug>/`
- Pojmenuj soubor výstižně: `<popis>-<YYYY-MM-DD>.<ext>` nebo bez data pokud jde o living document, který se bude přepisovat
- V sekci "Materiály a poznámky" v `AGENDA/<slug>.md` přidej odkaz: `viz VÝSTUPY/<slug>/<soubor>`

### 5. Aktualizuj AGENDA soubor

Po dokončení práce navrhni update `AGENDA/<slug>.md`:
- Uzavřené úkoly → přesuň do "Recently moved to HOTOVO" (s datem)
- Nové úkoly → přidej s metadaty
- Odkaz na nový/aktualizovaný výstup → do sekce Materiály
- Update `00-System/Index.md` (počet aktivních, top priorita, datum)

Vždy jako preview, vždy čekej na potvrzení.

### 6. Hláška na konci

Krátká, konkrétní, bez patosu:

```
Hotovo. Vytvořen: architektura-rb-universe.md (Mermaid diagram).
Uzavřen 1 úkol, přidán 1 nový [Q2, S=9].
VÝSTUPY/rb-universe-development/ — celkem 3 soubory.
```

---

## Propojení s triage

Pokud uživatel přijde s větou typu "po triage chci aktualizovat výstupy ke <slug>":

1. Přečti `AGENDA/<slug>.md` — zejména sekci "Recently moved to HOTOVO" a nové úkoly
2. Projdi existující výstupy v `VÝSTUPY/<slug>/`
3. Navrhni, které výstupy jsou zastaralé nebo neúplné vzhledem k nové informaci
4. Postupuj jako v kroku 3A

---

## Pravidla

- **Nikdy nepřepisuj soubory bez náhledu** — vždy ukáž co chceš změnit
- **Nikdy neupravuj AGENDA soubor bez potvrzení**
- **Výstupy jdou vždy do `VÝSTUPY/<slug>/`** — nikdy jinam
- **Při nejasném zadání** — polož 1 konkrétní otázku, nezačínej hádat
- **Mindmapy prioritně jako HTML widget v chatu** — soubor jen pokud uživatel chce archivovat
- **U skriptů a MCP** — vždy přidej stručný komentář do souboru, co to dělá a kdy vzniklo
- **Tone:** viz `O MNĚ/anti-ai-writing-tools.md` — informálně, konkrétně, bez AI frází
