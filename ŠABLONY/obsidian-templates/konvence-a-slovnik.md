# Konvence a slovník — Second Brain v2

> Single source of truth pro identifikátory napříč vaultem. Tento soubor zrcadlí sekci 2.1 plánu `second-brain-v2-bases`. Pokud se rozejde, plán vyhrává a tento soubor aktualizujeme.

## Slovník

### slug

- **Definice:** Primary key projektu. kebab-case, latin-only (unidecode), stabilní (nepřejmenovává se).
- **Použití:** Frontmatter wikilinky, filesystem path (`02-PROJEKTY/<slug>/`), Bases filtry.
- **Příklady:** `strategy`, `rb-universe-development`, `kratky-potlesk`, `ma-odyssey`, `firemni-procesy`.
- **Generování:** Manuálně při založení projektu; pak konstantní.

### hub filename

- **Definice:** Markdown soubor projektu v `02-PROJEKTY/`. Lidský název s diakritikou. **Nestabilní** — lze přejmenovat (přejmenování slugu je naopak destruktivní operace přes migration script).
- **Příklady:** `Strategy.md`, `RB Universe.md`, `Krátký potlesk.md`.

### hub alias

- **Definice:** Pole `aliases:` v hub frontmatteru, aby `[[<slug>]]` resolvovalo na hub.
- **Příklad:** `aliases: [strategy]` v `Strategy.md` umožní `[[strategy]]` resolvovat na `Strategy.md` napříč vaultem.

### wikilink target (frontmatter)

- **Pravidlo:** **Vždy bare alias** = `[[<slug>]]`, NE `[[02-PROJEKTY/Strategy]]`.
- **Výjimky:** AREAS, RESOURCES, Memory, Templates — path-style linky (`[[03-AREAS/Firemní strategie]]`, `[[05-RESOURCES/inspirace/<title>]]`).
- **Důvod:** Slug je stabilní, hub filename ne. Pokud uživatel přejmenuje hub, alias bare-link funguje dál.
- **Příklady:**
  - `project: "[[strategy]]"` v task frontmatteru.
  - `area: "[[03-AREAS/Firemní strategie]]"` v hub frontmatteru.
  - `materials: ["[[agenda-strategicka-schuzka]]"]` v task frontmatteru (alias-only, materiál má unique slug).

### task ID

- **Schéma:** Per-slug prefix + číslo. Prefix je legacy (`S`, `F`, `T`, `RBU`, `AF`, `OPS`, `PERS`, …). Vault-wide max+1 přes scan-then-max algoritmus (viz `id-generation-spec.md`).
- **Nové ID se nikdy neurčuje od oka** — `python3 scripts/next_task_id.py <slug>`. Všech osm duplicitních ID z léta 2026 vzniklo ručním odhadem při triáži; pravidla byla správná, jen je nic nevymáhalo.
- **Zrušený úkol se ruší, ne maže** (`status: Cancelled` + archiv). Smazaný soubor své ID neubrání a `max+1` ho přidělí něčemu jinému, zatímco odkazy pořád míří na starý význam (tak přišly o identitu `S21` a `PD5`).
- **Kontrola:** `python3 scripts/check_task_identity.py` (a `--fix` na rozjeté názvy souborů). Běží i jako součást `agent-context.json` → `health.task_identity_issues`.
- **Příklady:** `S2`, `F13`, `OPS2`, `RBU29`, `AF7`, `PERS3`.

### task filename

- **Schéma:** `<ID> — <sanitize(title)>.md` (em-dash U+2014 obklopený mezerou; diakritika + emoji zachovány). Pokud má task prázdný title, fallback `<ID>.md`.
- **`sanitize_title()`:** filesystem-safe substituce special chars (viz `filename-normalization.md`).
- **Příklady:**
  - `S2 — Hierarchie cílů obrat vs. ziskovost vs. dopad.md`
  - `OPS2 — Nahrát EDU news ♻️ weekly (čtvrtek).md`
  - `F13 — Kapsičky jednatelů proklikat v Alfrédu + testovat na datech.md`
  - `PD4 — Ninjabot projít smlouvy - služby, rozhodnout vypověď.md`

### task aliases

- **Pravidlo:** `aliases: [<ID>]` ve frontmatteru každého tasku. Umožňuje psát `[[<ID>]]` z body a Obsidian najde správný soubor i po případné změně titulu.
- **Migrace:** `scripts/rename_tasks_to_human_filenames.py` doplňuje idempotentně.

### task subtask číslování

- **Pravidlo:** checkboxy v `## Operativní kroky` (a podobných sekcích — `## Akční kroky`, `## Subtasky`, `## Steps`, `## Akční položky`) jsou prefixovány `**<ID>-N**`, kde N = 1-indexed pořadí v sekci.
- **Příklad:** `- [x] **PD4-1** Inventář 6 dokumentů + platba — 2026-05-21`
- **Odkazovatelné:** subtask lze citovat z jiných míst (chat, task body, hub) přes `PD4-3` syntaxi.

### material kind (`material_kind`)

Frontmatter pole **`material_kind`** (Bases sloupec „Kind"). **Nepoužívat `kind:`** — historicky neexistuje.

| material_kind | Zdroj |
|---|---|
| `gdoc` | Google Doc / Sheet / Slides |
| `sembly` | Sembly transkript schůzky |
| `slack` | Slack message capture |
| `slack-capture` | Slack capture (alias) |
| `email` | Email sent / received |
| `meeting-notes` | Zápis schůzky / meeting notes |
| `note` | Manuální poznámka / analyze výstup |
| `url` | Externí odkaz / článek |
| `linkedin` | LinkedIn profil / post |
| `clipping` | Výstřižek / clipping |

**Syrové zdroje** (filtr v `All-materials.base#ProjectMaterials` je negativní — skrývá jen tyto hodnoty; chybějící `material_kind` zůstává viditelné): `sembly`, `gdoc`, `slack`, `slack-capture`, `email`, `meeting-notes`.

**Identita pro dedup (VC7):** volitelně `source_id` / `source_url` — stabilní klíč (Drive file ID, Slack permalink, transcript filename).

### material summary (`## Shrnutí`)

Každý materiál by měl mít sekci **`## Shrnutí`** (3–5 bullet: o čem, entity, decision points). Zdroj pro vrstvu B v `build_work_context.py`.

Legacy konvence (migrovat na `## Shrnutí`): blockquote teaser (`> …` pod H1), `## TL;DR`.

### hub charter sections (kanonické názvy)

Povinné sekce v project hubu (`02-PROJEKTY/<Hub>.md`):

- `## Cíl`
- `## Scope` (In / Out uvnitř)
- `## Definition of done`
- `## People`
- `## Kontext`
- `## Zdroje dat`
- `## Otevřené otázky`

Legacy **zrušeno** (0 hubů): `## Lidé / spolupráce`, `## Hranice / vymezení`, `## Metriky / KPI` — nahrazeno `## People` a In/Out v `## Scope`.

Povolené extra sekce: `## Progress`, `## Tým …`, `## Stav (auto)`, `## Aktivní úkoly`, `## Materiály`, `## Výstupy`, `## Recently done`.

### Tři osy priority (model v2, od 4. 8. 2026)

Prioritu nenese jeden sloupec, ale tři nezávislé otázky:

| Otázka | Nositel | Pole |
|---|---|---|
| Udělám to vůbec? | ty | `status` |
| Kdy to musí být hotové? | svět | `deadline` — **jen reálný externí závazek**, jinak prázdné |
| Na co se soustředím teď? | ty | `focus` — ISO týden, max 5 úkolů |

„Chci to mít do pátku" **není deadline**, to je fokus týdne.

### status

- **Hodnoty:** `Doing` | `Next` | `Backlog` | `Waiting` | `Done` | `Cancelled`
- **Sémantika:**
  - `Doing` — rozpracované, právě na tom dělám.
  - `Next` — udělám, čeká ve frontě.
  - `Backlog` — nápad, není teď aktivní.
  - `Waiting` — blokované; vyžaduje `waitUntil:` datum (kdy to znovu zkontrolovat).
  - `Done` — hotovo. Po `ARCHIVE_DONE_DAYS` (default 90) se přesune do `07-ARCHIV/tasks-done/<slug>/`.
  - `Cancelled` — zrušeno nebo pohlceno jiným úkolem. Archivuje se stejně jako `Done`, ale **nepočítá se do „recently done"** — jinak statistika tvrdí, že jsi udělal práci, kterou jsi ve skutečnosti odepsal.
- **`ASAP` zrušeno** (4. 8. 2026). Byl to druhý inbox: tři crony do něj tlačily a žádný z něj netahal ven. Nahrazuje ho `focus`.

### project status (hub)

- **Hodnoty:** `active` | `paused` (prázdné = `active`)
- **`active`** — projekt žije; tasky soutěží o TOP / Rozhodni / focus suggestions; cron přepisuje `## Stav (auto)`.
- **`paused`** — vědomě odložený projekt. Zůstává v `projects[]` a open counts, ale tasky **nejsou** v `top_priority_today` / `top_priority` / `needs_decision` / `due_soon` / `focus_suggestions`, a `lifecycle_hub_state` hub nepřepisuje. Po unpause se znovu zapojí automaticky.
- Příklady paused: [[Krátký potlesk]], [[AI & Vibe coding]], [[Pipedrive a další nástroje]].

### focus

- **Hodnota:** ISO týden, `YYYY-Www` — např. `2026-W32`. Prázdné = mimo fokus.
- **Max 5 úkolů** na týden. Rituály (recurring) o místo nesoutěží.
- **Nastavuje výhradně člověk.** Je to jediné pole ve vaultu, do kterého žádný cron nesmí zapsat.
- Co si v pondělí znovu nevybereš, vypadne z fokusu samo — týdenní razítko řeší zatuhnutí bez úklidu.
- Zdroj `top_priority_today` v `agent-context.json`. Když je fokus pod pěti, `build_agent_context.py` naplní `focus_suggestions[]` návrhy — nikdy ale nepatchuje tasky.

### agent

- **Hodnoty:** `none` | `assist` | `solo`. Default `none`.
- `none` — udělá jen člověk (např. vlastní Culture Canvas).
- `assist` — agent připraví podklad, člověk rozhodne.
- `solo` — agent udělá celé.
- Vyplňuje agent při triáži, člověk případně přepíše.
- U `solo` se ICE effort počítá za agenta, ne za člověka.
- **Drobná `solo` práce se nezakládá jako task.** Když ji agent vyřeší v jedné session a nikdo venku na to nečeká, vzniká záznam v `00-System/Agent-Log/YYYY-MM.md` s wikilinkem na projekt. Ukáže se v backlinks hubu, ale nezabírá místo ve frontě.

### Zdroje dat (hub charter)

Tři vrstvy — **bez duplicit**. Detail: [[00-System/Templates/agenda-system]] §6.

| Vrstva | Kde | Co |
|--------|-----|-----|
| Konkrétní pointery | `## Zdroje dat` (tabulka v hub body) | URL Drive/Docs, dashboardy, vault cesty, platformy |
| Google Workspace | Globální (bootstrap) | Gmail, Calendar, Drive u všech projektů — **ne** per-project `workspace:` |
| Strojové hooky | Hub frontmatter | `sources:` (MCP tagy z [[00-System/Zdroje-katalog]]), `notebooklm:` (UUID), volitelně `context_source:` |

- **`sources:`** = tag integrace pro MCP/CLI routing (`rb-mcp`, `pipedrive`, `github`, …). **Ne** URL, **ne** `google-workspace`.
- **`notebooklm:`** = seznam `UUID — popisek` pro `scripts/notebooklm_query.py`.
- **`workspace:`** = **zrušeno** (dříve gmail/calendar/drive filtry — nepoužíváme).

## Důsledky pro migraci

- `[[02-PROJEKTY/Strategy]]` (current convention v `wikilink-convention.md` před F0.2) **se v F3.3 globálně mění** na `[[strategy]]`.
- Migration script (`scripts/migrate_h3_tasks_to_files.py`) přečte mapping table (`scripts/migration-mapping.json`) a provede find/replace napříč celým vaultem.
- AREAS, Memory, Templates, RESOURCES kategorie zůstávají s path-style linky (alias-only by mohl kolidovat s task / project sluggem).

## Status změn ve frontmatteru

- **Capture (n8n / agenda-capture):** task vzniká se `status: Next` (nebo `Backlog` při nízkém `ice` skóre). Do `focus` capture nesahá.
- **Triage (chat `agenda-triage` BATCH/DEEP):** navrhne `status` dle decision rules; apply až po schválení.
- **Lifecycle cron:** Mění `status` automaticky:
  - `lifecycle_waiting_to_next.py` — `Waiting` → `Next` po `waitUntil` (F6.2). Probuzení není priorita, proto Next a ne fokus.
  - `lifecycle_done_from_checkboxes.py` — propose `Done` z 100% inline checkboxů (F6.1) → user approve.
  - `lifecycle_recurring.py` — Done recurring → archiv + nová instance (F7.2).
- **User v Obsidianu / mobil:** Properties UI (frontmatter editor) — flip mezi hodnotami.
- **Cursor agenda skills:** `agenda-status-update`, `agenda-work` flippují `status` přes CAS write.

## Reference

- Plán: `~/.cursor/plans/second-brain-v2-bases_32262fd1.plan.md`
- Filename normalization: [[00-System/Templates/filename-normalization]]
- ID generation: [[00-System/Templates/id-generation-spec]]
- Wikilink convention: [[00-System/00-System/Templates/wikilink-convention]]
- Task convention: [[00-System/00-System/Templates/task-convention]]
- Task template: [[00-System/Templates/task-template]]
- Material template: [[00-System/Templates/material-template]]
- Topic template (hub v2): [[00-System/Templates/topic-template-v2]]
- Nový projekt: [[00-System/Templates/new-project-workflow]]
