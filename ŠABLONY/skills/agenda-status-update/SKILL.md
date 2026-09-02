---
name: agenda-status-update
description: "Single-task status flip in MrLUC Second Brain v2: hotovo, zruš (Cancelled), odlož, čekat do, do fokusu týdne. Reads 02-PROJEKTY/<slug>/tasks/<ID> — *.md frontmatter (human-readable filename, em-dash U+2014) and patches status/deadline/waitUntil. Subtask reference syntax: `<ID>-N` (např. PD4-3 = 3. checkbox v ## Operativní kroky). ALWAYS preview before write. Bulk operace řeší agenda-work / agenda-co-ted / agenda-priority-review; tohle je one-off tap."
---

# agenda-status-update (v2)

> Rychlá změna stavu jednoho tasku. Pro hromadné operace použij `agenda-work` nebo `agenda-co-ted`. Pro re-prioritizaci napříč vault použij `agenda-priority-review`.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Hotovo <ID>" / "Done <ID>" / "Uzavři <ID>"
- "Odlož <ID> do YYYY-MM-DD" / "Čekat <ID>"
- "do fokusu <ID>" / "tenhle týden <ID>"
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

Přečti task `.md`, ukaž current status. V chatu vždy **`ID — title`** z frontmatter (ne samotné ID). Viz `.cursor/rules/task-mention-convention.mdc`.

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
| "hotovo" / "done" | `status: Done`, `waitUntil:` prázdné, `updated: <today>`, body append `## Poznámky / log\n- <today>: Done — <důvod, pokud řekl>`. **U `type: epic` potvrď výslovně** — epic se z checkboxů / GitHubu neauto-Done. |
| "hotovo PD4-3" / "hotovo RBU62-1" | flip checkbox `**ID-N**` v `## Operativní kroky` na `[x]` (single subtask); v chatu uveď parent **ID — title** + text kroku |
| "do fokusu" / "tenhle týden" | `focus: <aktuální ISO týden>`, `waitUntil:` prázdné, `updated: <today>`. **Odmítni u epic.** Nejdřív spočítej fokus (limit 5). |
| "pryč z fokusu" | `focus:` prázdné, `updated: <today>` |
| "odlož do YYYY-MM-DD" | `status: Waiting`, `waitUntil: <date>`, `updated: <today>` |
| "ztím čekat" (bez data) | `status: Waiting`, `waitUntil: <today + 3 dny>`, `updated: <today>` |
| kanban / ruční Waiting bez data | cron `lifecycle_waiting_default_waituntil` (every 2h :02) doplní `waitUntil: dnes + 3` |
| "zruš" / "cancel" | `status: Cancelled`, `waitUntil:` prázdné, `updated: <today>`, body append `- <today>: **ZRUŠENO** — <důvod>`. **Nemaž soubor** — cron ho archivuje jako Done a `Cancelled` drží rozdíl mezi splněným a odepsaným. |
| "sloučeno do X" | totéž jako zruš, v logu wikilink na cílový úkol |
| "deadline YYYY-MM-DD" | `deadline: <date>`, `updated: <today>` |
| "ICE I8 C7 E5" | `ice_i: 8, ice_c: 7, ice_e: 5`, `updated: <today>` (ne u epic) |
| status → Next / Backlog / Doing | `waitUntil:` prázdné (pole platí **jen** pro `Waiting`) |

### 4. Preview (povinné)

```
Navrhuju patch:

  02-PROJEKTY/rb-universe-development/tasks/RBU30 — Název úkolu.md
  - focus: (prázdné) → 2026-W32
  - updated: 2026-05-25
  - body: + "## Poznámky / log\n  - 2026-05-25: Do fokusu týdne 32 — deadline 2026-05-30"

OK? (ano / uprav / cancel)
```

### 5. Zápis

- Patch frontmatter (CAS-aware: read → modify → write)
- Append do body sekce `## Poznámky / log` pokud relevantní
- **Pokud `status: Done`**: cron `archive_done_tasks.py` (every 2h :05) přesune do `07-ARCHIV/tasks-done/<slug>/`. Manuální archiv hned: přesun + update `open_tasks_count` v hub.
- Bases dashboard se aktualizuje sám.

### 5b. Hub narativ (volitelně, preview)

Po status flipu s dopadem na projekt (Done významného tasku, nový fokus, změna deadline u klíčového tasku) **nabídn** 1–2 větný patch `## Kontext` v hubu + bump `updated:`. Sekci `## Stav (auto)` needituj.

### 6. Refresh agent context

Po každém zápisu spusť:
```bash
python3 scripts/build_agent_context.py
```

### 7. Hláška

```
✅ Patch aplikován: RBU30 focus → 2026-W32. Updated 2026-05-25. Agent context refreshed.
```

## Pravidla

- Pouze single-task ops; bulk přes `agenda-work` / `agenda-co-ted` / `agenda-priority-review`
- **`waitUntil` platí jen pro `status: Waiting`.** Při flipu na Next / Backlog / Doing / Done / Cancelled vždy nastav `waitUntil:` prázdné (YAML null). Cron `lifecycle_waituntil_hygiene.py` (every 2h :03) vyčistí opomenutí z manuálních editací. Cron `lifecycle_waiting_default_waituntil.py` (every 2h :02) doplní `waitUntil = dnes + 3 dny`, pokud je Waiting bez data.
- **Do `focus` nikdy nesahá cron.** Je to jediné pole ve vaultu, které je čistě lidským rozhodnutím. Když je fokus pod pěti, `build_agent_context.py` naplní `focus_suggestions[]` — ty je smíš **nabídnout**, ne aplikovat.
- **Limit fokusu je 5.** Před přidáním spočítej aktuální stav; při překročení se zeptej, co z fokusu vypadne.
- **Zrušený úkol není `Done`.** Používej `Cancelled` — jinak „recently done" tvrdí, že jsi udělal práci, kterou jsi odepsal.
- Nikdy nemaž ostatní frontmatter pole, jen patchni / přidávej
- "Zruš" → potvrď s userem (mazání je destruktivní)
- Recurring tasky (`recurring:` blok ve frontmatteru) — Done flip spustí cron `lifecycle_recurring.py` (vytvoří next instance) — ne dělej manuálně
- **Epic** (`type: epic`): status Done jen ručně po tvé explicitní vůli; focus/ICE na epic nepatří. Auto z GitHubu / checkboxů epic nezavře.
- **RBU GitHub:** odškrtnutí `ID-N` z `Closes` na `dev` dělá cron — manuálně duplikuj jen když cron nestihl / konflikt CAS.
