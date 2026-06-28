---
name: agenda-triage
description: "INBOX triage in MrLUC Second Brain v2 vault, pending batch approval from cron, or re-priority. Triggers: projeď inbox, schval pending triáž, apply batch, udělejme triage. Modes: BATCH, DEEP, PENDING (read 00-System/Triage-Pending/*.json with v2 schema). Creates task files in 02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md (human-readable filename, em-dash U+2014; subtasks číslované **<ID>-N**), archives to 07-ARCHIV/inbox-processed/. ALWAYS preview before write."
---

# agenda-triage (v2)

> Pravidelný průchod nasbíraného. Capture ukládá rychle, triage pročistí. **V2:** vytváří `task .md` soubory v `02-PROJEKTY/<slug>/tasks/` (file-per-task), Bases dashboard se aktualizuje sám.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Projeď inbox" / "udělejme triage" / "co tam mám nasbíráno"
- V `01-INBOX/*` je >5 nezpracovaných položek
- "Schval pending triáž" / "apply batch" → mód **PENDING**

## Módy

```
Mám N položek v INBOXu.
  [B]atch — rychlý souhrn, potvrzení najednou
  [D]eep — položka po položce
  [P]ending — schválení 00-System/Triage-Pending/*.json (cron návrh)
  [R]e-priority — delegace na agenda-priority-review

Default: B (nebo P pokud uživatel žádá pending).
```

## Triage routing (PARA)

| Typ obsahu | Kam |
|------------|-----|
| Lukášův akční krok | `add_task` → `02-PROJEKTY/<slug>/tasks/` |
| Referenční materiál | `05-RESOURCES/<kategorie>/` nebo project `materials/` + `topics:` |
| Zodpovědnostní postřeh bez akce | `area_log` → `03-AREAS/<area>.md` sekce `## Log rozhodnutí` |
| Neznámá osoba ve zdroji | `add_person` → `05-RESOURCES/lide/<Jméno>.md` ze `_ŠABLONA-person.md` |
| Nová info o známé osobě | `update_person` → patch frontmatter/sekcí person souboru |

Pravidla Resources: `.cursor/rules/resources-para.mdc`. Přílohy: co-located binárka + sidecar `.md` v `materials/<téma>/` (viz PARA rule); parsuj `## Přílohy` z INBOX `.md`; po apply spusť `extract_material_text.py`.

## Lidé — automatická detekce (každý zdroj)

Pro každý INBOX / pending zdroj:
1. Extrahuj zmíněné osoby (jména + aliasy z `05-RESOURCES/lide/` frontmatter).
2. **Neznámá** → proposal `add_person` (role/org/email z textu).
3. **Nový kontakt/narozeniny/role/téma** u známé → proposal `update_person`.
4. Preview v batchi; apply až po schválení. Po apply spusť `sync_lide_people.py`.

## Hub narativ po apply

Po schválení batch s novými tasky pro projekt **nabídn** doplnění `## Kontext` hubu (nové téma z triáže) + `updated:`.

Pokud batch vyžaduje **nový projekt** (nový slug): naved na [[00-System/Templates/new-project-workflow]] — nejdřív hub + `## Zdroje dat`, pak tasky.

## Auto-routing „komplexních" zdrojů

V BATCH i PENDING módu skill **automaticky** detekuje komplexní materiál a routuje ho do DEEP, místo aby ho mlel přes default add_task flow.

**Komplexní materiál** = ten, ze kterého se zákonitě bude rozsekávat víc tasků nebo se z něj stane samostatný materiál. Sdílená heuristika `vps/second-brain-hub/lib/triage_complexity.py` (volá ji i cron `triage_run.py`); pravidla v OR:

- Subdir `01-INBOX/sembly/` → **vždy** DEEP (přepisy meetingů).
- Subdir `01-INBOX/email/sent/` → **nikdy** DEEP (commitment fast-path).
- Subdir `01-INBOX/Clippings/` → BATCH nebo DEEP dle `triage_complexity` (dlouhé clipy); viz `01-INBOX/Clippings/README.md`.
- `word_count > 800` nebo `line_count > 100`.
- 3+ H2/H3 headingů v těle.
- 5+ otevřených checkboxů `- [ ]`.
- Sekce `## Přílohy` s alespoň jednou položkou → **DEEP** (materiály + sidecar).
- **Inline odkaz** na Google Docs/Sheets/Slides nebo pdf/docx v těle → **DEEP** (materializace při interaktivním DEEP flow).
- Signální fráze: „Action items", „Akční kroky", „Úkoly", „Závěry", „Decision points", „Rozhodnutí", „Next steps", „Další kroky".
- Override v souboru: `<!-- triage:deep -->` nebo `<!-- triage:simple -->` má precedenci přede vším ostatním.

Cron označuje takový návrh `requires_deep_analysis: true`, `kind: "deep"`, `proposalType: "deep_analysis"`, `target_path: null`, `frontmatter: null`, `body: "DEEP analysis required..."` a v summary `…-summary.md` přidává sekci **DEEP candidates** s důvody.

## Batch

1. Načti `01-INBOX/*/`
2. Pro každou položku zavolej **`is_complex_source(rel, body)`** (`vps/second-brain-hub/lib/triage_complexity.py`).
3. Komplexní zdroj → automaticky DEEP flow pro ten jeden zdroj (viz níže), zbytek dál v BATCH.
4. Pro non-DEEP položku: extrahuj, navrhni projekt + ICE + status (Next/ASAP/Backlog/Waiting)
5. Generuj ID (scan `02-PROJEKTY/<slug>/tasks/` + `07-ARCHIV/tasks-done/<slug>/`)
6. Preview všech BATCH položek najednou + výpis DEEP candidates (skill agenda-capture struktura)
7. Po OK: zápis task `.md` souborů, archiv source → `07-ARCHIV/inbox-processed/YYYY/MM/`

### Odeslané e-maily (`01-INBOX/email/sent/`)

- Capture: n8n `workspace-sent-to-inbox.json` (Workspace `lukas@redbuttonedu.cz`, frontmatter `source: sent`)
- Cron `triage_run.py` + `triage_commitments.py`: závazky (`kind: commitment`) nebo fallback u mailu bez závazku
- **Drop list** (`triage_commitments._SENT_INBOX_DROP_RULES`): shoda `to` + `subject` → **n8n neukládá** do INBOX (`workspace-sent-to-inbox.json`); cron `purge_dropped_sent_inbox` **smaže** případné staré soubory (+ přílohy `stem__*`) bez triáže. Aktuálně: `finance@redbutton.cz` + `Fakturace dealu`.
- **Manuální triáž (agenda-triage):** při BATCH/DEEP/PENDING — pokud soubor v `01-INBOX/email/sent/` odpovídá drop listu (normalizovaný `to` + `subject` z frontmatter / hlavičky, stejná logika jako `should_drop_sent_from_inbox` v `workspace-sent-format-markdown.js`), použij **`proposalType: drop`**: **smaž** zdroj + přílohy `stem__*`, **ne** archivuj, **ne** vytvářej task. V preview uveď „DROP (sent inbox rule)" — apply bez dalšího potvrzení, pokud user schválil batch obsahující drop.
- Každý návrh v batchi má **`proposalType`**:
  - `add_task` — vytvoří `02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md` (em-dash U+2014, sanitized title) + frontmatter `aliases: [<ID>]` + očíslované subtasky `**<ID>-N**`
  - `update_task` — patchne frontmatter / body existujícího task souboru
  - `archive_only` — jen přesune source do archivu
- Souhrn: `00-System/Triage-Pending/YYYY-MM-DD-HHMM-summary.md` — české odrážky po souborech (typ, projekt, archiv po schválení)
- **`archiveAfterApply`**: default `true` — po schválení `add_task` z odeslaného mailu přesuň zdroj do `07-ARCHIV/inbox-processed/` + `**ZPRACOVÁNO**` v hlavičce
- PENDING: u commitmentů zkontroluj `notes` (citace) a `confidence`

## Deep

Pro každou položku (přímo spuštěnou v DEEP módu **nebo** auto-routnutou z BATCH/PENDING):

1. Read sourceFile naplno (ne jen prvních pár řádků).
2. Shrnutí 3–5 bullety: o čem to je, klíčové entity, decision points.
3. Návrh **více tasků** + případných **materiálů** + cross-linků (`materials: [[...]]`) — **při extrakci aplikuj Lukáš-only filter (viz níže)**.
4. Projdi s uživatelem po jednom: OK / uprav / přeskoč / drop.
5. Zápis task `.md` + materiál `.md` souborů; archiv source → `07-ARCHIV/inbox-processed/YYYY/MM/`.

## Lukáš-only filter (vault je single-user)

Vault patří **jednomu uživateli (Lukáš)**. Tasky v `02-PROJEKTY/<slug>/tasks/` jsou **operativní akce, které Lukáš sám provede / drží míček**. Ne todo list pro celou firmu, ne sumář meetingu. Aplikuj **před** přípravou návrhů (krok 3 v Deep, BATCH extrakce, i v PENDING reviewu).

**Lukášův task = ano**, pokud:
- Lukáš je commitment owner ("já udělám", "musím", "připravím", "zavolám", "potvrdím", "domluvím", "rozhodnu")
- Lukáš je svolavatel / zodpovědný (i když exekuci deleguje — drží termín a follow-up)
- Strategický krok, kde Lukáš drží rozhodnutí

**Lukášův task = NE**, pokud:
- Akci dělá někdo jiný (Luboš připraví, Pavel implementuje, Slávek napíše, klient dodá)
- Je to volně zmíněná oblast bez konkrétního Lukášova kroku
- Je to názor / postoj v diskusi bez akce
- Jde o cizí projekt / téma, kde Lukáš jen poslouchal

**Hraniční (Waiting / sledovat)** — pokud Lukáš čeká na výstup od konkrétní osoby a chce to evidovat:
- Status: `Waiting`, `waitUntil: <date>`, title: `Sledovat: <kdo> dodá <co>`
- Pokud je to nepodstatné nebo informace bez follow-up, vynech.

**Cizí akce → kontext**, ne task:
- Patří do `## Poznámky / log` souvisejícího Lukášova tasku, nebo do `materials/` jako záznam meetingu, nebo do `## Otevřené otázky` projektu.
- NIKDY nevytvářej task soubor `<ID> — <Cizí osoba akce>.md`.

**Preview report konvence:**
- Pro každý nalezený signál uveď "**Drží míček:** Lukáš / Luboš / Pavel / …"
- Tasky s "Drží míček: Lukáš" → preview k apply.
- Ostatní → vlož do "Vyřazeno z preview (cizí míček)" sekce.
- User pak může explicitně říct "i tenhle uložit jako Waiting" — apply pouze po konfirmaci.

**Zmínka tasku v chatu (povinné):** vždy **`ID — title`** z frontmatter, ne samotné ID (`SBD4` bez názvu = špatně). Tabulky: sloupce ID + Název. Viz `.cursor/rules/task-mention-convention.mdc`.

## PENDING (cron)

1. Načti nejnovější `00-System/Triage-Pending/*-batch.json`.
2. Rozděl proposals na **2 fronty**:
   - `simple_queue` — `requires_deep_analysis != true` (default BATCH apply route).
   - `deep_queue` — `requires_deep_analysis == true` (`kind: "deep"`, `proposalType: "deep_analysis"`).
3. Pokud `deep_queue` není prázdná, řekni uživateli:
   > Nalezeno N návrhů (M simple, K DEEP). Začneme DEEP, protože vyžadují víc pozornosti. Pokračovat? [yes/skip-deep/simple-only]
4. **DEEP fronta**: pro každý zdroj projet DEEP analysis flow s pre-loaded `sourceFile` z Pending JSONu. Po schválení DEEP zápisu:
   - Smazat ten proposal z Pending JSONu (CAS write s `expect_mtime`).
   - Přesunout zdroj do `07-ARCHIV/inbox-processed/YYYY/MM/`.
5. **Simple fronta**: stávající BATCH apply (per-proposal `proposalType`).
6. JSON v2 schema (každý návrh):

```json
{
  "proposalType": "add_task" | "update_task" | "archive_only" | "deep_analysis" | "add_person" | "update_person" | "area_log",
  "target_path": "02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md",
  "frontmatter": {
    "id": "RBU30",
    "type": "task",
    "title": "Titulek lidsky čitelný",
    "project": "[[RB Universe]]",
    "slug": "rb-universe-development",
    "aliases": ["RBU30"],
    "status": "Next",
    "ice_i": 7, "ice_c": 8, "ice_e": 5,
    "materials": ["[[some-material]]"],
    "source": "...",
    "deadline": null,
    "waitUntil": null
  },
  "body": "...",
  "sourceFile": "01-INBOX/...",
  "archiveAfterApply": true,
  "confidence": 0.85,
  "notes": "...",
  "requires_deep_analysis": false,
  "deep_reasons": [],
  "needs_link": false
}
```

**`needs_link` (cron):** pokud návrh nemá `project:` + `materials:` pro DEEP zdroj, nastav `needs_link: true` a **neaplikuj automaticky** (stejně jako `deep_analysis`).

Body návrhu musí mít subtasky se prefixem `**<ID>-N**` v `## Operativní kroky`.

7. Ukaž změny podle `proposalType`. **Nikdy neaplikuj bez explicitního „ano" / „apply"**.
8. Po schválení:
   - `add_task` → vytvoř `target_path` se YAML frontmatterem + body.
   - `update_task` → patchne frontmatter + append do body (CAS-aware).
   - `archive_only` → přesun source.
   - `deep_analysis` → **nikdy se neaplikuje automaticky**; přepni do DEEP flow (krok 4) pro daný `sourceFile`.
   - **Archiv batch: oba soubory** — `*-batch.json` **a** `*-summary.md` se stejným prefixem (`YYYY-MM-DD-HHMM-`) přesunout z `00-System/Triage-Pending/` do `00-System/Triage-Applied/`. Nikdy nenech v Pending jen md bez JSONu (sirotek). Naming: pokud byl batch jen zavřen bez nového apply manifestu, použij sufix `-closed` (`*-batch-closed.json`, `*-summary-closed.md`).
   - **Sanity check**: po apply zkontroluj, že `Triage-Pending/` neobsahuje žádné `*.md` ani `*.json` se starším datem než dnešek (sirotci z předchozích triage).

## Hygiena tasků (RE-ID / přesun mezi projekty / přejmenování hubu)

Při jakékoli z těchto operací **vždy** projeď post-flight checklist, jinak nechá vault stale references a Obsidian při otevření hodí "nespecifikovanou chybu":

**1. Wikilinky v vault.** Hromadně updatni cesty / názvy:
- `[[02-PROJEKTY/<slug>/<file>]]` → nová cesta (např. po přesunu do `materials/` / `outputs/`)
- `[[<starý-id>]]` → `[[<nový-id>]]` po RE-ID (active i archived tasks)
- `project: '[[<starý hub>]]'` → `project: '[[<nový hub>]]'` po přejmenování hubu (frontmatter všech tasků v `02-PROJEKTY/<slug>/tasks/` i `07-ARCHIV/tasks-done/<slug>/`)
- `projects: ['[[<starý hub>]]']` v materials/outputs frontmatteru
- **POZOR na kolizi basename**: nový hub filename **nesmí kolidovat** s žádným souborem v `03-AREAS/` — viz [[00-System/Templates/wikilink-convention]] sekce "Pravidlo unikátnosti basename". Pokud kolize, přejmenuj area soubor s suffixem ` (oblast)` (např. `03-AREAS/Marketing (oblast).md`) a updatuj všechny `[[03-AREAS/Marketing]]` references na `[[03-AREAS/Marketing (oblast)]]`.

Použij Python skript s replace logikou (ne sed — kvůli diakritice a non-ASCII filenames).

**2. Bases `kanbanState`.** `00-System/Bases/All-tasks.base` má v `kanbanState.cardOrders.note.status.<column>:` ručně přetažené pořadí karet — list cest k task souborům. Po RE-ID / přesunu / smazání tasku tam zůstanou stale references na neexistující soubory. Když Obsidian rendruje kanban a klikne na stale link, hodí "nespecifikovanou chybu".

Fix: po každé migraci tasků (RE-ID, přesun, smazání) **smaž celý `kanbanState` blok** z `All-tasks.base`. Bases se vrátí na default order (`order:` + `sort:` config). Nový state si user postaví organicky přetahováním karet.

```yaml
# All-tasks.base — sekce ProjectKanban
- type: kanban
  name: ProjectKanban
  filters: ...
  groupBy: ...
  order: ...
  # ⬇ smaž tento blok kompletně:
  # kanbanState:
  #   cardOrders:
  #     note.status:
  #       Next:
  #         - 02-PROJEKTY/<starý>/<task>.md
  #         ...
```

**3. Hub frontmatter `aliases`.** Pokud přejmenováváš hub `<starý>.md` → `<nový>.md`, přidej `<starý>` do `aliases` v novém hubu — body wikilinky `[[<starý>]]` v ostatních souborech zůstanou funkční:

```yaml
aliases:
- <slug>
- <starý hub název>
- <nový hub název>
```

**4. Hub sekce `## Materiály` / `## Výstupy`.** Manuální seznamy odkazů aktualizuj na nové cesty / přesuň do správné sekce (materials vs. outputs).

**5. `agent-context.json`.** Přebuduj přes `python3 scripts/build_agent_context.py` (vault root).

**6. Final sanity grep.** Před uzavřením operace:

```bash
# žádné staré cesty / IDs ve frontmatteru ani body
grep -rl --include='*.md' --include='*.json' -F "[[<starý>]]" \
  02-PROJEKTY/ 07-ARCHIV/ 00-System/

# žádné stale refs v Bases
grep -F "kanbanState" 00-System/Bases/All-tasks.base
```

## Refresh dashboard + agent context

V2 — žádný cron build pro dashboard nepotřebuje. **Bases dashboard** (`OBSIDIAN/Dashboard.md`) čte přímo z task `.md` frontmatterů.

**Po každém zápisu** (apply triage batch / commit task changes):

1. (Volitelně) update `open_tasks_count` v hub `.md` frontmatteru pro každý dotčený slug
2. **Vždy spusť** `sync_lide_people` — wikilinky v nových/změněných souborech + rebuild tabulek `05-RESOURCES/lide/*.md`:

```bash
python3 scripts/sync_lide_people.py --incremental --paths "<vault-relative cesty, čárkou>"
```

`--paths` = vše z batchi: nové/aktualizované tasky, materiály, archivované capture (`02-PROJEKTY/...`, `07-ARCHIV/inbox-processed/...`). Více cest odděl **středníkem** (`;`) — čárka v názvu souboru je jinak OK. Přeskoč JSON/summary v `Triage-Pending/`.

3. **Vždy spusť** `python3 scripts/build_agent_context.py` (vault root) — refresh `00-System/agent-context.json` pro Cursor agenta
4. V chatu uveď výsledek: `tasks_created=N tasks_updated=M archived=K lide_sync: linkified=L profiles_rebuilt=P agent_context_refreshed=yes`

## Refresh Index

Po triage update `00-System/Index.md` — list aktivních projektů (Bases embed udělá většinu, manuální texty doplň pokud potřeba).

## Re-prioritizace

"Eisenhower přepočítej" → skill `agenda-priority-review` nebo projdi aktivní task soubory (po termínu, ASAP dnes, Next top 3).

## Kontext před startem

- `00-System/Memory/about-me.md`
- `00-System/Index.md`
- `00-System/Templates/konvence-a-slovnik.md`
- `00-System/Templates/task-convention.md`
