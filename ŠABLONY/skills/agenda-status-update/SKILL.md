---
name: agenda-status-update
description: "Single-task status flip in MrLUC Second Brain v2: hotovo, zruš, odlož, čekat do, ASAP. Reads 02-PROJEKTY/<slug>/tasks/<ID> — *.md frontmatter (human-readable filename, em-dash U+2014) and patches status/deadline/waitUntil. Subtask reference syntax: `<ID>-N` (např. PD4-3 = 3. checkbox v ## Operativní kroky). ALWAYS preview before write. NEW skill in F4.5 — pre-existing skills (agenda-co-ted, agenda-work) handle bulk operations; this is for one-off taps."
---

# agenda-status-update (v2)

> Rychlá změna stavu jednoho tasku. Pro hromadné operace použij `agenda-work` nebo `agenda-co-ted`. Pro re-prioritizaci napříč vault použij `agenda-priority-review`.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Hotovo <ID>" / "Done <ID>" / "Uzavři <ID>"
- "Odlož <ID> do YYYY-MM-DD" / "Čekat <ID>"
- "ASAP <ID>" / "Urgent <ID>"
- "Zruš <ID>" / "Cancel <ID>"

## Workflow

### 1. Najdi task soubor

1. ID syntax: `[A-Z]+\d+[a-z]?` (S2, AF7, RBU29, OPS2 atd.)
2. Hledej (filename po F-fundamental refactoru = `<ID> — <Title>.md`, em-dash U+2014):
   - `OBSIDIAN/02-PROJEKTY/*/tasks/<ID> — *.md` (nebo `<ID>.md` jako fallback) — pokud match, použij
   - `OBSIDIAN/07-ARCHIV/tasks-done/*/<ID> — *.md` — pokud archived, varuj a ptej se zda zpět aktivovat
3. Pokud více matchů → ptej se který slug
4. Při odkazu z chatu / jiných tasků: uživatel může psát `[[<ID>]]` (resolvuje přes `aliases: [<ID>]` ve frontmatteru) nebo `<ID>-N` pro konkrétní subtask

### 2. Načti frontmatter

Přečti task `.md`, ukaž current status:

```
RBU30 — Název úkolu
Status: Next → ?  (ICE I7 C6 E5 = 8.4)
Deadline: 2026-05-30
WaitUntil: —
Updated: 2026-05-25
```

### 3. Navrhni patch

Mapping user intent → frontmatter změna:

| User intent | Patch |
|-------------|-------|
| "hotovo" / "done" | `status: Done`, `waitUntil:` prázdné, `updated: <today>`, body append `## Poznámky / log\n- <today>: Done — <důvod, pokud řekl>` |
| "hotovo PD4-3" | flip checkbox `**PD4-3**` v `## Operativní kroky` na `[x]` (single subtask) |
| "ASAP" / "urgent" | `status: ASAP`, `waitUntil:` prázdné, `updated: <today>` |
| "odlož do YYYY-MM-DD" | `status: Waiting`, `waitUntil: <date>`, `updated: <today>` |
| "ztím čekat" (bez data) | `status: Waiting`, `waitUntil: <today + 3 dny>`, `updated: <today>` |
| kanban / ruční Waiting bez data | cron `lifecycle_waiting_default_waituntil` (every 2h :02) doplní `waitUntil: dnes + 3` |
| "zruš" / "cancel" | Confirm s userem; pak smazat soubor (NE archive) |
| "deadline YYYY-MM-DD" | `deadline: <date>`, `updated: <today>` |
| "ICE I8 C7 E5" | `ice_i: 8, ice_c: 7, ice_e: 5`, `updated: <today>` |
| status → Next / Backlog / Doing | `waitUntil:` prázdné (pole platí **jen** pro `Waiting`) |

### 4. Preview (povinné)

```
Navrhuju patch:

  02-PROJEKTY/rb-universe-development/tasks/RBU30-...md
  - status: Next → ASAP
  - updated: 2026-05-25
  - body: + "## Poznámky / log\n  - 2026-05-25: Eskalováno na ASAP — deadline 2026-05-30"

OK? (ano / uprav / cancel)
```

### 5. Zápis

- Patch frontmatter (CAS-aware: read → modify → write)
- Append do body sekce `## Poznámky / log` pokud relevantní
- **Pokud `status: Done`**: cron `archive_done_tasks.py` (every 2h :05) přesune do `07-ARCHIV/tasks-done/<slug>/`. Manuální archiv hned: přesun + update `open_tasks_count` v hub.
- Bases dashboard se aktualizuje sám.

### 6. Refresh agent context

Po každém zápisu spusť:
```bash
python3 scripts/build_agent_context.py
```

### 7. Hláška

```
✅ Patch aplikován: RBU30 status Next → ASAP. Updated 2026-05-25. Agent context refreshed.
```

## Pravidla

- Pouze single-task ops; bulk přes `agenda-work` / `agenda-co-ted` / `agenda-priority-review`
- **`waitUntil` platí jen pro `status: Waiting`.** Při flipu na ASAP / Next / Backlog / Doing / Done vždy nastav `waitUntil:` prázdné (YAML null). Cron `lifecycle_waituntil_hygiene.py` (every 2h :03) vyčistí opomenutí z manuálních editací. Cron `lifecycle_waiting_default_waituntil.py` (every 2h :02) doplní `waitUntil = dnes + 3 dny`, pokud je Waiting bez data.
- **`ASAP` backfill:** cron `lifecycle_asap_backfill.py` (hourly 10:00–02:00) — pokud je v vaultu méně než 3 otevřené ASAP, promote nejvyšší `Next` podle `today_score` (stejná logika jako dashboard TOP 3).
- Nikdy nemaž ostatní frontmatter pole, jen patchni / přidávej
- "Zruš" → potvrď s userem (mazání je destruktivní)
- Recurring tasky (`recurring:` blok ve frontmatteru) — Done flip spustí cron `lifecycle_recurring.py` (vytvoří next instance) — ne dělej manuálně
