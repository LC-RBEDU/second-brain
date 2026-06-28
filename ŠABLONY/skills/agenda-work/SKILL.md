---
name: agenda-work
description: "Use when user works on a MrLUC Second Brain v2 project — 'jdeme na <slug>', 'otevři <slug>', documents/outputs, task updates. Reads 02-PROJEKTY/<HubName>.md (Cíl, Scope, Kontext, Otevřené otázky, Aktivní úkoly via Bases) + 02-PROJEKTY/<slug>/tasks/*.md (file-per-task) + 02-PROJEKTY/<slug>/ outputs. NEVER modifies files without confirmation."
---

# agenda-work (v2)

> Otevři projekt, zorientuj se, udělej výstup. Hub `02-PROJEKTY/<HubName>.md` (charter), tasky `02-PROJEKTY/<slug>/tasks/<ID>-<slug>.md`, outputs v `02-PROJEKTY/<slug>/`.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Jdeme na <slug>" / "Pracujeme na <slug>" / "Otevři <slug>"
- "Pokračujeme v <slug>" / "Co zbývá v <slug>"
- "Založ projekt" / "Nový projekt <název>" — viz **Nový projekt** níže
- "Udělej mi dokument / mindmapu / kalkulaci pro <téma>"
- "Aktualizuj výstupy <slug>"
- "Uprav úkoly v <slug>" / "Přidej task" / "Uzavři task"

## Workflow

### 1. Načti kontext (v2)

1. **PRIMARY:** `OBSIDIAN/00-System/agent-context.json` → najdi `projects[]` podle `slug`; briefing pole: `charter_cil`, `charter_scope`, `charter_definition_of_done`, `charter_people`, `charter_kontext`, status, area, open_tasks_count, top tasks ze `top_priority` filtered by slug, **`sources`**, `notebooklm`
2. **Work-context bundle:** `OBSIDIAN/00-System/Work-Context/<slug>.md` — **freshness check:** pokud chybí, nebo existuje `<slug>.stale`, nebo `generated_at` je starší než nejnovější mtime tasků v `02-PROJEKTY/<slug>/tasks/` → spusť `python3 scripts/build_work_context.py <slug>`. Při práci na konkrétním tasku: `python3 scripts/build_work_context.py --task <ID>` (efemérní stdout, nepersistuje).
3. (1× per session) `OBSIDIAN/00-System/Memory/about-me.md`
4. Hub `OBSIDIAN/02-PROJEKTY/<HubName>.md` — frontmatter + body (Scope, Kontext, ## Zdroje dat)
5. Tasky `OBSIDIAN/02-PROJEKTY/<slug>/tasks/*.md`
6. Outputs + Materials (sidecar `type: attachment` s `## Extrahovaný text`)
7. **MCP enrichment (povinný):** `python3 scripts/build_sources_routing.py --check` → regeneruj pokud stale; načti `sources-routing.json`; pro každý hub `sources:` tag volej MCP/CLI dle routes

Pokud slug není jasný → zobraz seznam aktivních projektů z `00-System/Index.md` (Bases embed) a ptej se.

### 2. Ukaž orientační přehled

```
═══════════════════════════════════════════════
PROJEKT: <HubName> [<slug>]
Status: <active/paused> | Area: <area>
═══════════════════════════════════════════════

🎯 CÍL: <z agent-context.json charter_cil nebo ## Cíl>

📋 SCOPE (In/Out): <charter_scope nebo ## Scope>

✅ DEFINITION OF DONE: <charter_definition_of_done nebo ## Definition of done>

👥 LIDÉ: <charter_people nebo ## People — top wikilinks + role>

📎 KONTEXT (zkráceně): <charter_kontext>

❓ OTEVŘENÉ OTÁZKY: <count>
  • ...

📋 AKTIVNÍ ÚKOLY (<N>)
  • [ASAP, Score=18.0] RBU30 — Název úkolu — deadline 2026-05-30
  • [Next, Score=14.0] RBU15 — Filtrace pohledů
  ...

📁 EXISTUJÍCÍ VÝSTUPY (mimo tasks/, materials/)
  • report-q1-2026.docx (2026-04-15)
  • architektura-rb-universe.md (2026-04-20)

💡 BACKLOG: <N> tasků se status: Backlog
═══════════════════════════════════════════════
Co chceš dělat?
  [N] Nový výstup
  [U] Aktualizovat existující výstup
  [T] Upravit úkoly (přidat / uzavřít / změnit metadata / status flip)
  [D] Detail tématu (celý hub + jeden task)
```

Pokud uživatel zadal konkrétní instrukci hned, přeskoč výběr a jdi rovnou na krok 3.

### 3. Proveď práci

#### 3A — Nový nebo aktualizovaný výstup

| Typ | Formát | Kde ukládat |
|-----|--------|-------------|
| Dokument (zpráva, analýza, memo) | `.docx` | `02-PROJEKTY/<slug>/` |
| Mindmapa / diagram | `.mermaid` / HTML | `02-PROJEKTY/<slug>/` |
| Proces pro Architekta | `.md` | `02-PROJEKTY/firemni-procesy/procesy/` (skill `agenda-proces`) |
| Kalkulace / tabulka | `.xlsx` | `02-PROJEKTY/<slug>/` |
| Strukturovaná poznámka | `.md` | `02-PROJEKTY/<slug>/` |
| Skript | `.py` / `.js` | `02-PROJEKTY/<slug>/` |
| MCP / n8n | `.json` | `02-PROJEKTY/<slug>/` |
| **Material** (M:N) | `.md` s frontmatter `type: material` | `02-PROJEKTY/<slug>/materials/` (project-specific) NEBO `05-RESOURCES/<kategorie>/` (cross-project) |

#### 3B — Úprava úkolů (file-per-task)

```
Návrh změn v 02-PROJEKTY/<slug>/tasks/:

✅ Uzavřít → status: Done (cron archive_done_tasks.py přesune do 07-ARCHIV/tasks-done/<slug>/):
  • RBU13 — Onboarding checklist Pavla — všechny subtasky [x]

➕ Přidat (nový file): 02-PROJEKTY/<slug>/tasks/<NEXT_ID>-<slugify(title)>.md
  • Status: Next | ICE I7 C6 E5 = 8.4
  • Deadline: 2026-05-15 | Source: ...

✏️ Update existujícího:
  • RBU15 — status: Next → ASAP (důvod: deadline 2026-05-29)
  • RBU6 — waitUntil: → 2026-06-30 (Káťa potvrdila timing)

OK? (ano / uprav)
```

Proveď zápis až po potvrzení. Vždy preview → confirm → write.

### 4. Ulož výstupy

- Output do `02-PROJEKTY/<slug>/<output_filename>.<ext>`
- Pojmenuj výstižně: `<popis>-<YYYY-MM-DD>.<ext>` nebo bez data pro living dokument
- V hubu **## Materiály** pomocí Bases embed `![[All-materials.base#ProjectMaterials]]` — pokud výstup chceš mít v Bases, ulož jako material soubor (s `type: material` frontmatter v `02-PROJEKTY/<slug>/materials/`)
- Jinak prostý odkaz `[[02-PROJEKTY/<slug>/<output_filename>]]` v sekci ## Materiály mimo Bases embed

### 5. Aktualizuj task soubory + hub (narativní vrstva)

- Uzavřené tasky → status `Done` ve frontmatteru (cron archivuje)
- Nové tasky → vytvoř nové `.md` soubory v `tasks/`
- Update `open_tasks_count` v hub frontmatteru
- **`updated:` v hub frontmatteru** → dnešní datum po schváleném zápisu do hubu
- **Po uzavření/přidání tasků nebo významném výstupu** vždy navrhni patch:
  - `## Kontext` — 1–3 věty co se posunulo (preview diff)
  - `## Otevřené otázky` — přidat/uzavřít otázky pokud relevantní
- Sekce `## Stav (auto)` **needituj** — generuje cron `lifecycle_hub_state.py`

Vždy jako preview, vždy čekej na potvrzení.

### 5c. Nový projekt

Když téma nepatří do existujícího slugu:

1. Načti [[00-System/Templates/new-project-workflow]] + [[00-System/Index]].
2. Preview parametrů: `slug`, `hub-name`, `area`, `id-prefix`, basename kolize s `03-AREAS/`.
3. Spusť scaffold (preview first):

```bash
python3 scripts/create_project_hub.py \
  --slug <slug> --hub-name "<HubName>" \
  --area "03-AREAS/<oblast>" --id-prefix <PREFIX> --dry-run
```

4. Po schválení — stejný příkaz bez `--dry-run`.
5. Doplň charter (`## Cíl`, `## Scope`, `## Zdroje dat` s konkrétními URL). **Nepoužívej** `workspace:` ani `sources: google-workspace` (GWS globální — [[agenda-system]] §6).
6. První task(y) přes capture/triage s `project: "[[<HubName>]]"`.

### 5b. Refresh agent context (po každém zápisu task / hub)

```bash
python3 scripts/build_agent_context.py
python3 scripts/build_work_context.py <slug>
```

### 6. Hláška na konci

```
Hotovo. Vytvořen: architektura-rb-universe.md.
Uzavřen 1 task (RBU13), přidán 1 nový (RBU30, Score 8.4).
02-PROJEKTY/rb-universe-development/ — celkem N souborů.
```

## Pravidla

- **Nikdy nepřepisuj soubory bez náhledu** — vždy ukáž co chceš změnit
- **Nikdy neupravuj task soubory bez potvrzení**
- **Výstupy do `02-PROJEKTY/<slug>/` (root projektu); tasky do `tasks/`; materials do `materials/`**
- **Při nejasném zadání** — polož 1 konkrétní otázku, nezačínej hádat
- **Provenance:** ve výstupu uveď, které materiály/zdroje jsi použil (wikilink nebo cesta). Pokud klíčový zdroj chyběl v bundlu, explicitně to napiš.
- **Tone:** `OBSIDIAN/00-System/Memory/anti-ai-writing-tools.md`
