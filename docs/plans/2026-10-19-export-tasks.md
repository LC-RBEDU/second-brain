# Plán: Brain `export_tasks`

## Zadání a požadavky

R1 — Jedno volání vrátí kompletní snapshot tasků ve vaultu (frontmatter, bez těla) pro dashboard (strom, Radar napříč projekty, pohled na projekt). Klient filtruje lokálně. Zápisy dál jdou přes `update_task` / `create_task` s CAS. Zdroj: brief „Cíl“.

R2 — MCP tool `export_tasks` a REST `GET /v1/tasks/export`. Auth jako ostatní read cesty: human OAuth cookie nebo service Bearer. Handler je read-only. Zdroj: brief „Rozhraní“ + rozhodnutí „Nasazení cílí na Brain“.

R3 — Parametry: `include_closed_days` int default 0; `projects_csv` string default `""`; `fields` string default `"standard"` (`full` přidá `materials`, `blocked_by`, `company_priorities`, `source`); `since` ISO datetime nebo null. Zdroj: brief „Parametry“.

R4 — Výstup je objekt: `generated_at`, `vault_head`, `focus_week`, `count`, `projects[{slug, title, status, hierarchy}]`, `tasks[…]` s poli z briefu. Pole `open_count` se nezavádí. U MCP je `structuredContent` ten objekt, ne string a ne obal `{"result": "…"}`. `count == len(tasks)`. Žádný strop. Zdroj: brief „Výstup“ + Q1.

R5 — `parent` je holé ID (`parse_parent_id`). `oid` je stejný identifikátor jako `update_task(expect_oid=…)`. `steps_*` jsou checkboxy v `## Operativní kroky`. `filename_title_mismatch` když stem souboru není `<ID> — <title>`. `parse_errors` je seznam; rozbitý task ve výstupu zůstane. Zdroj: brief „Poznámky k polím“.

R6 — Odpověď do ~1 s pro ~600 tasků (frontmatter + odpočet checkboxů). Read-only, bez rebuildu `agent-context`. Zdroj: brief „Poznámky“ + rozhodnutí o výkonu. Q3 a Q4=A: na hostu se pod 1 s vejde, když z read requestu zmizí fetch i `commit_if_dirty` (`git add -A`) a export navíc neskenuje celý strom statusem.

R7 — Při defaultu (`include_closed_days=0`, prázdné `projects_csv`, `since` null) je `count == len(tasks)` a ten počet je **definice** `total_open_tasks` v okamžiku běhu: ne-terminální soubory v `02-PROJEKTY/<slug>/tasks/`, prázdný status jako `Next`, pauza projektu počet nesnižuje. Číslo 539 je stav k 19. 10., ne konstanta. Shoda se nebere z warm JSON `get_context` (TTL 15 min, `update_task` snapshot neinvaliduje). Live `get_context` se v QA porovnává jen když vrátí `mode=rebuild`. `Done` a `Cancelled` v aktivní složce ve výstupu nejsou a žádný parametr je odtud nevrátí. `include_closed_days` přidává jen soubory z `07-ARCHIV/tasks-done/` v okně N dní. AC2 (shoda `status`, `parent`, `deadline` s `find_tasks`) platí pro ne-terminální aktivní tasky. Pro aktivní `Done`/`Cancelled` neplatí: `find_tasks` je pořád může vrátit, export ne. `oid` projde `update_task(dry_run=true)`. Rozbitý frontmatter má neprázdné `parse_errors`. Pytest: prázdný vault, task bez parenta, parent jako wikilink i holé ID, archivované Done v okně `include_closed_days`. Zdroj: brief „Akceptační kritéria“ + Q1 + C3.

R8 — `find_tasks` se nemění (strop, offset). Mimo rozsah je dashboard BFF, zápis do vaultu, rebuild `agent-context`, n8n. Pipeline hierarchie `docs/plans/2026-10-16-hierarchy-cross-project.md` se nepřepisuje. Dirty soubory v repu (grammar-nazi, gmail, Playwright) do změny nepatří. Zdroj: brief „Mimo rozsah“ + omezení.

Mimo rozsah: Alembic, RBAC, subnav, `qa_gate.mjs`, Celery, frontend, Playwright T6. Tester se nevolá (`TESTER: přeskočeno`, profil SECOND_BRAIN). `docs/agent_playbooks/quality-checklists.md` v tomhle repu není — chování je v B#, výkon v P.

## Předpoklady

A1 — Zavřeno. Chybějící ICE se v exportu nevyplňuje. Snapshot to dělá jen ve `task_to_dict`: task se všemi třemi ICE prázdnými dostane 0/0/1, jinak chybějící složka spadne na default 5 a `ice_e` se zvedne na aspoň 1 (`vps/second-brain-hub/lib/agent_context_build.py` řádky 93–97 a 148–154). Export to nepřebírá. Chybějící složka je `null`, `priority_score` je `null`, dokud nejsou všechny tři celá čísla a `ice_e != 0`. Vzorec jen pak: `round((ice_i * ice_c) / ice_e, 2)`. `ice_e == 0` zůstane 0 a skóre je `null`.

A2 — Zavřeno, Q1 varianta 2. Výchozí `tasks` jsou soubory v `02-PROJEKTY/<slug>/tasks/*.md`, jejichž status po pravidle snapshotu (`prázdný → "Next"`, `agent_context_build.py` řádek 162) není v `TERMINAL_STATUSES` (`Done`, `Cancelled`, `focus.py` 37). Aktivní `Done`/`Cancelled` se přečtou kvůli indexu rodičů (A7), do `tasks` nejdou, a to při jakémkoli `include_closed_days` a `since`. `count` je `len(tasks)`, samostatné `open_count` není. Při defaultních parametrech se `count` rovná definici `total_open_tasks`, ne warm cache.

A3 — Zavřeno. `task.project` je slug složky (`02-PROJEKTY/<slug>/tasks/…` nebo `07-ARCHIV/tasks-done/<slug>/…`), stejně jako `file_project` u `get_tree`. `find_tasks` bere `slug` z frontmatteru; AC2 ho neporovnává. `projects_csv` filtruje složkový slug, ne alias hubu.

A4 — Zavřeno. `projects[].hierarchy` je stejný boolean jako `collect_projects` (frontmatter / slug `rb-universe-development`), ne `project_uses_hierarchy()`, které vrací vždy true. Pravidla parentů pořád platí všude; tenhle boolean je vlajka charteru.

A5 — Zavřeno. `since` je sjednocení: (a) frontmatter `updated` je >= `since`; date-only `updated` platí pro celý pražský kalendářní den; (b) cesta souboru je v `git log --since` (commit po `since`). Větev (b) porovnává `rel_path` s cestou, kterou git vrátí bez `core.quotePath` octal (C2). Samotné `updated` nestačí: `toggle_step` i `edit_task_body` commitnou tělo a `updated` neposunou. Nevalidní `since` je 400. Slučovací klíč inkrementu na klientovi je `path`, ne `oid`. `since` nehlásí smazané cesty: chybějící path v inkrementu není tombstone. Smazání je vidět jen v plném exportu (`since` null).

A6 — Zavřeno. Samostatný read-only scope neexistuje (`app/auth_deps.py` `require_auth`). Export použije stejný principal jako `GET /v1/tasks/item`. „Read-only“ = handler nezapisuje a read session nezavolá `commit_if_dirty` (Q4=A).

A7 — Zavřeno. `parent_not_found` se počítá proti indexu tohoto volání: všechny soubory přečtené z aktivních `tasks/` (včetně terminálů, které do `tasks` nejdou) plus archiv zařazený do tohoto volání. `projects_csv` a `since` index nezužují, takže křížový rodič v jiném projektu není chyba a aktivní `Done` rodič taky ne, i když v `tasks` není. Rodič, který leží jen v archivu mimo okno, je `parent_not_found`.

A8 — Zavřeno. Vault je git (`VAULT_BACKEND` default `git`, Brain Dockerfile kopíruje `second-brain-hub/lib`). `oid` na Drive je vždy `null` (`drive_io.py` řádek 379). AC3 se ověřuje na `GitVault`.

A9 — Zavřeno. Číslo 539 se v testech nefixuje. Shoda je `count` proti definici `total_open_tasks` na stejných souborech (T6). Warm `get_context` se proti exportu jako fail nepoužívá (C3).

A10 — Q3 a Q4=A (Lukáš 2026-10-19, varianta A). `git fetch origin` v `begin_session` (`git_io.py` 209) aktualizuje jen remote-tracking refy. `vault_head` je `rev-parse HEAD` (365–370) a fetch ho nemění. Úspěšná session, která není `skipped` a není `dry_run`, v `end_session` (225–229) volá `commit_if_dirty`. Ta vždy spustí `git add -A` (689–693), i když `diff --cached --quiet` pak nic necommitne. Brain má `GIT_VAULT_PUSH=1`, takže vzniklý commit se pushne (701–708). Export je taková session: na čistém klonu dirty check projde a `git add -A` leží v těch ~1,0 s, které zbyly po odečtení fetche (curl ~2,2 s minus fetch ~1,2 s). Ten zbytek tedy nejsou jen `git status` (340–342), druhé čtení v `read_text` (357–360 a 536–541) a `collect_projects` (185–232). Q4=A: každý `mode="read"` `commit_if_dirty` nevolá, takže `git add`, commit i push z read zmizí. Export navíc vynechá dirty check a vrátí bajty z disku (B30). Ostatní read dirty check nechají (503). Mutate a rebuild nechají fetch, dirty check i commit. Jedno čtení a `_projects` bez `collect_projects` zůstávají. Strop < 1000 ms (T27) se nemění. QA `git add` zvlášť neměřila.

## Současný stav (ověřeno v kódu)

`vps/second-brain-brain/app/mcp_app.py` 182–194 — `export_tasks` vrací `ExportTasksResult` (TypedDict), ne `str` a ne `CallToolResult`. Ostatní nástroje dál jdou přes `_call`.

`vps/second-brain-brain/app/main.py` 260–273 — `GET /v1/tasks/export` je `AuthPrincipal` a volá stejný tool. Špatný typ query nechá FastAPI na 422.

`vps/second-brain-hub/lib/task_query.py` 9–11, 90 — `FIND_MAX_LIMIT = 50`. `find_tasks` statusem na otevřené nefiltruje a archiv nečte. Export je u terminálů užší (R7). Strop se nemění.

`vps/second-brain-hub/lib/task_io.py` 86–96 a 105–113 — `iter_active_tasks` bere z `list_dir(02-PROJEKTY, include_folders=True)` jen `is_folder` a chybějící `tasks/` chytá `DriveNotFoundError` a `continue`. `iter_archive_tasks(vault, slug)` stejně přeskočí chybějící složku slugu. Export ten iterátor jako parser nepoužívá a stejný skip má sám (C1).

`vps/second-brain-hub/lib/git_io.py` `list_dir` 497–508 — na neexistující cestu `DriveNotFoundError`, na soubor `DriveVaultError` „Not a folder“. Charter `02-PROJEKTY/Strategy.md` nesmí dostat `list_dir(.../tasks)`.

`vps/second-brain-hub/lib/task_io.py` 66–72 — `parse_task_text` při `YAMLError` vrátí `frontmatter={}` a chybu zahodí. Export ho nevolá.

`vps/second-brain-hub/lib/git_io.py` 307–338 — `_git` skládá `["git", *args]`, příkaz ukládá do `_git_cmds` a stdout dekóduje jako text. `\0` i `\n` v `str` zůstanou. Em dash U+2014 je `task_identity.py` řádek 25, `SEPARATOR = " — "`.

`drive_io.py` 190–197 — `_norm_rel` dělá `replace("\\", "/")` a `strip("/")`. Nový řádek neubere.

Git 2.47, `Documentation/diff-options.txt`, větev `ifdef::git-log[]` u `-z`: NUL odděluje commity. Ukončení cest NULem platí jen pro `--raw` a `--numstat`. Parser v `git_io.py` `_parse_log_name_only_z` (90+) kus po `\0` řeže na LF a teprve řádek jde do `_norm_rel`.

`vps/second-brain-brain/app/tools/get_context.py` 45–53 — při `needs_rebuild` false vrátí uložený JSON `mode=warm`. `context_freshness.py` 8–9 a 31–37: stale až po více než 15 minutách. Export `get_context` nevolá.

`vps/second-brain-hub/lib/agent_context_build.py` 162, 367–371, 550 — `total_open_tasks` počítá aktivní ne-terminály. Pauza řeže jen `queue_tasks`.

`vps/second-brain-hub/lib/operational_steps.py` 38–48, 131–138 — `is_operational_header` skládá diakritiku, `## Operativní kroky` sedí. Sekce končí dalším `## `.

`vps/second-brain-hub/lib/hierarchy.py` 71–94 — `parse_parent_id` umí wikilink i holé ID.

`vps/second-brain-brain/app/tools/export_tasks.py` 84–100 — `build_export` běží uvnitř `with brain_vault`. Neplatné `since` je `ValueError`, které se uvnitř toho `with` přeloží na `BrainClientError` 400 `invalid_since`.

`vps/second-brain-brain/app/vault_deps.py` 88–92 — každý `brain_vault` dnes předá `discard_dirty_on_error=True`. Řádky 139–150: výjimka z těla `with` jde do `cm.__exit__(type, exc, tb)`. Úspěch jde do `__exit__(None, None, None)` (148–150).

`vps/second-brain-hub/lib/git_io.py` 193–219 — `begin_session` vždy: flock, `git fetch origin` (`check=False`), `git status --porcelain`. Fetch worktree ani HEAD neposune.

`vps/second-brain-hub/lib/git_io.py` 221–238 a 689–699 — `end_session` na session, která není `skipped`, není `dry_run` a nemá `exc_type`, volá `commit_if_dirty`. Ta vždy udělá `git add -A`. Když `exc_type` není `None`, commit se přeskočí, ale finally při `discard_dirty_on_error` a neskipnuté session spustí `git reset --hard HEAD` (231–238). Reset tracked soubor nesmaže. Vrátí jeho obsah z HEAD. Untracked soubor by zůstal, proto C4 chce tracked soubor a porovnání bajtů.

`vps/second-brain-hub/lib/git_io.py` 357–360 a 536–541 — `read_text` hashuje prvním `read_bytes` a text bere druhým.

`vps/second-brain-hub/lib/task_export.py` 337–351 — `_projects` volá `collect_projects` (`agent_context_build.py` 185–232). Ven jdou čtyři pole.

`vps/second-brain-hub/tests/test_task_export.py` 519–527 — T23 startuje hodiny až po `with vault` a session končí až po měření. Hostí curl to nekryje.

Latence na hostu (QA, image `82c5afd2cb129d4bd32f55d88d0462f14cc6eb2b`): default export 2214 / 2177 / 2119 / 2221 ms, `count` 538 == `len(tasks)`, `vault_head` `9a69e0406a77cc358b3e1fe98beb84b2497f5bf7`. MCP 2178 ms. `projects_csv=finance` 1989 ms. Dva `git fetch origin` bez nových objektů: 1224 ms a 1178 ms.

Nasazení: Brain `watch_paths` obsahuje `vps/second-brain-hub/lib/**` (`vps/second-brain-brain/deploy/setup-coolify.sh` 67–69). Hub má auto-deploy a base `/vps/second-brain-hub`, v INSERT není `watch_paths` (`vps/second-brain-hub/deploy/setup-coolify.sh` 10, 80–91).

## Návrh

### Sdílená lib — oid, since, session

`vps/second-brain-hub/lib/git_io.py` (R5, R6, C2, Q3, Q4, C4)

- `git_blob_oid` zůstává. `hash-object` se nevrací. `oid` sedí s `git hash-object` na stejných bajtech.
- `read_text` čte soubor jednou. `oid` je `git_blob_oid` těch bajtů, `size` je jejich délka. Chybějící cesta je `DriveNotFoundError`, složka je `DriveVaultError`. B9 se nemění.
- `head_sha()` zůstává `git rev-parse HEAD`. Není to `origin/<branch>`.
- `changed_paths_since` beze změny příkazu i parseru (C2).
- `GitVault.__init__` dostane `fetch_on_begin: bool = True`, `check_dirty_on_begin: bool = True` a `commit_on_end: bool = True`. `begin_session` fetch a `git status --porcelain` spustí jen při příslušném flagu. `end_session` zavolá `commit_if_dirty` jen při `commit_on_end`. Defaulty True: hub cron a `test_dirty_skip_at_start_no_reset` se nemění.
- `mode="read"` má `commit_on_end=False` a `discard_dirty_on_error=False`. `end_session` nevolá `commit_if_dirty` a finally nespustí `reset --hard HEAD`, ani když z těla `with` uteče `BrainClientError` (C4). Mutate a rebuild mají `commit_on_end=True`, fetch, dirty check i `discard_dirty_on_error=True`.

`parse_task_text` a `iter_active_tasks` se nemění.

### Sestavení snapshotu

`vps/second-brain-hub/lib/task_export.py` zůstává read-only a nevolá `get_context` ani `build_and_write_context_bundle`. Průchod aktivních tasků a archivu (C1, Q1, A7) se nemění. Parser `since` se nemění (C2).

`_projects` přestane volat `collect_projects` (Q3). Seznam `02-PROJEKTY/*.md`:

- název na `_` se přeskočí
- `type` jiné než `project` se přeskočí
- `slug` = frontmatter, jinak stem lower s mezerami na `-` (`collect_projects` řádek 203)
- `title` = `HUB_TITLE_RE` (`agent_context_build.py` 76), jinak frontmatter `title`, jinak stem
- `status` = frontmatter nebo `active`
- `hierarchy` = stejný boolean jako `collect_projects` 228–232 (`True`, řetězec `true|1|yes`, nebo slug `rb-universe-development`)

Excerpty sekcí charty se nepočítají. `oid` charty se nepočítá. Pořadí podle `slug`. Při `projects_csv` jen ty slugy. Aktivní soubory se kvůli A7 čtou celé i při `projects_csv`.

### Brain

`vps/second-brain-brain/app/vault_deps.py` — `open_vault` předá tři flagy. `brain_vault`:

- `mutate` a `rebuild`: `fetch_on_begin=True`, `check_dirty_on_begin=True`, `commit_on_end=True`, `discard_dirty_on_error=True`. Volající je nevypne.
- `read`: `fetch_on_begin=False`, `commit_on_end=False`, `discard_dirty_on_error=False`. `check_dirty_on_begin` default True.
- argument `check_dirty: bool = True`. `export_tasks` volá `brain_vault(mode="read", check_dirty=False)`.

Každý read `commit_if_dirty` nevolá (Q4=A). Ostatní read na špinavém stromu dál 503 `vault_dirty_start`. Export dirty check vynechá. Větev 200 i větev 400 nechají bajty tracked souboru být (B30, C4).

`export_tasks.py`, `mcp_app.py`, `main.py`, README: chování B1–B27 beze změny, kromě toho, že read session nezapisuje. MCP dál vrací `ExportTasksResult`.

RBAC, Alembic, Celery, frontend, subnav: netýká se.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | vault bez `02-PROJEKTY` | `tasks=[]`, `projects=[]`, `count=0`, bez `open_count`, HTTP 200 | R7 | T1 |
| B26 | vedle složky leží `02-PROJEKTY/Strategy.md`; jiný slug má jen `materials/`, žádné `tasks/`; třetí slug má jeden otevřený task. Totéž u archivu: slug bez složky při N>0 | 200, ve výstupu je jen ten jeden task, `count=1`. Chybějící `tasks/` ani chybějící archivní složka slugu není 500 | R7 | T1 |
| B2 | 51 ne-terminálních aktivních tasků a jeden aktivní `Done` | 51 tasků, `count=51`, `Done` ve výstupu není | R4, R7 | T2 |
| B3 | aktivní task, status `Next`, bez parenta, `type` task | `parent=null`, bez `parent_required` | R5, R7 | T3 |
| B4 | parent wikilink `[[IAD-E4 — Security & Performance]]` a holé `IAD-E4` | obojí `parent="IAD-E4"` | R5, R7 | T4 |
| B5 | archiv `Done` v okně N; druhý starší; N=0 | v okně jen při N>0; při 0 archiv chybí | R3, R7 | T5 |
| B6 | aktivní `Done` nebo `Cancelled`, N=0 i N velké, `since` sedí | ve `tasks` není | R7 | T6 |
| B7 | mix: prázdný status, `Next`, `ASAP`, aktivní `Done`, pauznutý hub | `count == len(tasks)` a rovná se definici `total_open_tasks` na těch souborech. Nečte se warm JSON. `open_count` chybí | R7 | T6 |
| B8 | `find_tasks` bez filtru | ne-terminální řádky sedí ve `status`, `parent`, `deadline` (prázdný status zůstane `""`). Aktivní `Done`/`Cancelled` z `find_tasks` v exportu nejsou | R7 | T7 |
| B9 | GitVault soubor, i s rozbitým YAML | `oid` == `git hash-object` těch bajtů, které `read_text` vrátil; `update_task(dry_run=true, expect_oid=oid)` nevrátí 409 | R5, R7 | T8, T9 |
| B10 | soubor bez `---` nebo s `YAMLError` | task ve výstupu (když není terminál), `parse_errors` má `missing_frontmatter` nebo `yaml_error` | R5, R7 | T9 |
| B11 | `fields=standard` / `full` | standard nemá `materials` ani zbylé tři; full je má | R3 | T10 |
| B12 | `projects_csv` | jen ty složky; rodič v jiném projektu není `parent_not_found`; `count=len(tasks)` | R3, A7 | T11 |
| B13 | soubor `X1 — Nadpis.md` (em dash), `updated` starší než `since`, commit těla po `since` (frontmatter `updated` se neposune) | task ve výstupu je. Cesta z gitu není quoted octal. Starší soubor bez commitu po `since` ve výstupu není. Smazaná cesta není tombstone. Nevalidní since → 400 `invalid_since` | R3, A5 | T12 |
| B14 | `## Operativní kroky` a jeden checkbox mimo sekci | počítá se jen sekce | R5 | T13 |
| B15 | chybějící ICE; 5/5/5; `ice_e=0` | `null` a skóre `null`; skóre 5.0; `ice_e=0` a skóre `null` | A1 | T15 |
| B16 | stem ≠ `<ID> — <title>`; rotace `<ID>-YYYY-MM-DD` | `filename_title_mismatch` true / false | R5 | T16 |
| B17 | volání exportu, i na čistém klonu s `GIT_VAULT_PUSH=1` | `get_context` ani `build_and_write_context_bundle` se nevolají; mode je `read`; v `_git_cmds` není `fetch`, `status`, `add`, `commit` ani `push`. `commit_if_dirty` se nezavolá | R6, Q3, Q4 | T17, T25, T26 |
| B18 | MCP přes `MCPServer.call_tool` | `structured_content` má top-level `tasks` a `count`, `count=len(tasks)`, není `{"result": "<string>"}` | R4 | T14 |
| B19 | REST bez auth / se service tokenem | 401 / 200 | R2 | T18 |
| B20 | `fields=nope`, záporné `include_closed_days` | 400 `invalid_fields` / `invalid_include_closed_days` | R3 | T19 |
| B21 | story bez parenta; task pod epicem; epic s parentem; cyklus | task zůstane, příslušný kód v `parse_errors` | R5 | T20 |
| B22 | dva nerotační soubory, jedno ID | oba ve výstupu, oba `duplicate_id` | R4 | T21 |
| B23 | obálka | `focus_week` je aktuální ISO týden Prahy; `generated_at` má offset; na GitVault je `vault_head` SHA lokálního HEAD | R4 | T22 |
| B24 | pauznutý hub | jeho otevřené tasky jsou v `count` | R7 | T6 |
| B25 | rodič je aktivní `Done` | dítě ve výstupu je, `parent_not_found` nemá | A7, R7 | T6 |
| B27 | `get_context` vrátí `mode=warm` a `stats.total_open_tasks` jiné než export `count` | to není chyba exportu. Export `get_context` nevolá. Shoda definice je T6. Live shoda jen při `mode=rebuild` a beze změny souborů mezi voláními | R7 | T24 |
| B28 | `brain_vault(mode="read")` na čistém klonu s pushem zapnutým; zvlášť `mode="mutate"` a `rebuild`, které zapíšou soubor | read v `_git_cmds` nemá `fetch`, `add`, `commit` ani `push`. `vault_head` exportu se rovná `git rev-parse HEAD` před voláním a po něm. mutate a rebuild mají `fetch` a po zápisu `add` i `commit`. Samotný `git fetch origin` HEAD nemění | R6, Q3, Q4, A10 | T25 |
| B29 | nasazený Brain, default parametry, ~600 otevřených tasků, cold i další tři warm requesty | curl `time_total` každého < 1000 ms. `count==len(tasks)`. `vault_head` se rovná `git rev-parse HEAD` v kontejneru a mezi requesty se nemění, když nikdo nezapisuje. Request nespustí `git fetch`, `git status`, `git add`, `commit` ani `push` | R6, Q3, Q4 | T27 |
| B30 | (a) export na klonu s necommitnutým souborem v `02-PROJEKTY` a `GIT_VAULT_PUSH=1`; jiný read tool na tom samém stromu. (b) tracked soubor: obsah je v HEAD, worktree má jiné bajty; export s `since=not-a-date` | (a) export 200, task z těch bajtů ve výstupu je, `git rev-parse HEAD` se nezměnil, v `_git_cmds` není `fetch`, `status`, `add`, `commit` ani `push`. Jiný read je 503 `vault_dirty_start`. Mutate na default session dirty pořád skipne a nezapíše ho. (b) `BrainClientError` 400 `invalid_since` vznikne uvnitř `with brain_vault` (`export_tasks.py` 84–100), takže `__exit__` dostane výjimku (`vault_deps.py` 139–150). Bajty souboru se rovnají worktree před voláním, ne obsahu z HEAD. V `_git_cmds` není `reset --hard`. Větev 200 ani pouhá existence souboru to nehlídá: úspěch volá `__exit__(None)` (148–150), reset se tam nespustí ani při dnešním `discard_dirty_on_error=True` (91), a `reset --hard HEAD` (`git_io.py` 231–238) soubor nesmaže, jen vrátí HEAD | Q3, Q4, C4 | T26 |
| B31 | fixture s `hierarchy: true`, řetězcem `yes` a slugem `rb-universe-development` bez flagu | `projects[]` má stejné `slug`, `title`, `status`, `hierarchy` jako `collect_projects` na tom vaultu | A4, Q3 | T28 |

Checklist A:

- Authn: B19.
- RBAC / scope: netýká se (A6).
- Validace: B20, B13.
- Prázdný výsledek a díra ve stromu složek: B1, B26. Není 404 ani 500.
- Idempotence: dvě čtení beze změny vaultu vrátí stejné tasky a stejný `vault_head`. `generated_at` se smí lišit. Read mezi nimi neudělá commit (B28).
- Částečný zápis: B30(b). Read při 400 nesmí `reset --hard` vrátit tracked soubor na HEAD (C4). `commit_if_dirty` read nevolá (Q4=A).
- Tvar chyby: `BrainClientError` → `{error_reason, message}` (`main.py` 125–132).
- Side effect: B17, B28, B30. Read nefetchuje, nevolá `commit_if_dirty` a nespouští rebuild contextu. Export nedělá status. Výjimka uvnitř export session nespustí `reset --hard`. Mutate a rebuild fetchují, kontrolují dirty a commitují.
- Tiché ořezání: B2. Vyhození aktivního `Done` je R7, ne strop.
- Časová zóna: Praha, B5, B13, B23.
- CAS zápis: netýká se. Čte se oid (B9).
- Kompatibilita: `find_tasks` beze změny (B8). Warm `get_context` smí mít jiný `total_open_tasks` (B27). `vault_head` zůstává lokální HEAD (B28).

## Výkonový rozpočet (P)

Endpoint jeden: MCP `export_tasks` a `GET /v1/tasks/export`.

1. SQL: netýká se.
2. Indexy DB: netýká se.
3. N+1: `hash-object` se nevrací. Default export (N=0, `since` prázdné) smí spustit jeden `rev-parse --show-object-format` a jeden `rev-parse HEAD`. Nesmí spustit `git fetch`, `git status`, `git add`, `git commit`, `git push` ani `git log`. `since` smí přidat jeden `git log -z`. Skip složky bez `tasks/` je jeden `list_dir`, který skončí `DriveNotFoundError`. Každý task je jedno čtení disku. `commit_if_dirty` se nezavolá, takže na čistém klonu neběží `git add -A` (A10).
4. Payload: standard ~600 otevřených tasků řádově 250–400 kB. Bez stránkování.
5. Ořez: žádný strop. `count` po filtrech sedí s `len(tasks)`.
6. Cache: žádná. Export nečte `agent-context.json`. Fetch se na pozadí nedohání.
7. Latence: cold i warm curl `time_total` < 1000 ms na Brain hostu pro ~600 aktivních tasků, N=0, `since` prázdné, čtyři opakování (B29, T27). Fetch je ~1,2 s. Zbytek ~1,0 s obsahuje `git add -A` z `end_session` a není jen status, druhé čtení a `collect_projects` (A10). Pytest T23 dál měří sestavení 600 souborů < 1500 ms a nula `hash-object`; session exportu navíc nemá `fetch`, `status`, `add`, `commit` ani `push`. T23 není důkaz hosta, protože hodiny startují až po `begin_session` a před `end_session` (`test_task_export.py` 519–527).
8. Archiv: při N=0 se nečte. Při N>0 jeden průchod, chybějící slug se přeskočí. SLO 1 s pro tuhle větev neplatí.
9. Zámek: stávající flock. Nový lock není.
10. Paměť: jedno čtení souboru se použije na YAML, kroky i `oid`. Druhé čtení se nedělá.
11. Externí volání: žádný Allfred, Gmail, Slack, `get_context`. Read nemá `git fetch` ani push. Mutate a rebuild fetchují a při zápisu commitují, kvůli `is_tip_ahead` a ff-only push.

`projects_csv` nešetří čtení aktivních souborů (A7). Šetří payload a archiv. Jeho hostí čas je ve stejném stropu 1 s.

## Testy (T#)

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-hub/tests/test_task_export.py` | B1 a B26 |
| T2 | pytest | gate | stejný | B2 |
| T3 | pytest | gate | stejný | B3 |
| T4 | pytest | gate | stejný | B4 |
| T5 | pytest | gate | stejný | B5 |
| T6 | pytest | gate | stejný | B6, B7, B24, B25 |
| T7 | pytest | gate | `vps/second-brain-brain/tests/test_export_tasks.py` | B8 |
| T8 | pytest | gate | hub `test_git_io.py` nebo `test_task_export.py` na `git_repo` | B9; oid z jednoho čtení |
| T9 | pytest | gate | hub `test_task_export.py` | B10 a oid rozbitého YAML |
| T10 | pytest | gate | stejný | B11 |
| T11 | pytest | gate | stejný | B12 |
| T12 | pytest | gate | hub GitVault | B13 beze změny: soubor `X1 — Nadpis.md`, `updated` starší než `since`, druhý commit změní jen tělo, task ve výstupu je. Příkaz obsahuje `-c`, `core.quotepath=false` a `-z` |
| T13 | pytest | gate | hub | B14 |
| T14 | pytest | gate | brain `test_export_tasks.py` | B18 přes `MCPServer.call_tool` |
| T15 | pytest | gate | hub | B15 |
| T16 | pytest | gate | hub | B16 |
| T17 | pytest | gate | brain | B17 |
| T18 | pytest | gate | brain | B19 |
| T19 | pytest | gate | brain | B20 |
| T20 | pytest | gate | hub | B21 |
| T21 | pytest | gate | hub | B22 |
| T22 | pytest | gate | hub GitVault | B23 |
| T23 | pytest | gate | hub GitVault, 600 souborů | P: < 1500 ms, nula `hash-object`. Session s flagem exportu (`fetch_on_begin` false, `check_dirty_on_begin` false, `commit_on_end` false) nemá v `_git_cmds` `fetch`, `status`, `add`, `commit` ani `push` |
| T24 | ruční po deployi | gate (QA verifier) | `https://brain.cyprovi.cz` | MCP `tools/list` obsahuje `export_tasks`. `GET /v1/tasks/export` má `count==len(tasks)`. Warm `get_context` s jiným `total_open_tasks` není fail (B27). Latence hosta je T27, ne tenhle bod |
| T25 | pytest | gate | brain `test_export_tasks.py` nebo hub `test_git_io.py` | B28. Read s `GIT_VAULT_PUSH=1`: v `_git_cmds` není `fetch`, `add`, `commit` ani `push`. Mutate a rebuild po zápisu `fetch`, `add` i `commit` mají |
| T26 | pytest | gate | brain + GitVault | B30. (a) Špinavý export je 200, `git rev-parse HEAD` se nezměnil, v `_git_cmds` není `add` ani `commit`. Jiný read je 503. (b) Tracked soubor, worktree bajty jiné než HEAD, volání exportu s `since=not-a-date` přes `brain_vault`. Výsledek 400 `invalid_since`. Bajty souboru se byte po byte rovnají stavu před voláním, ne HEAD. V `_git_cmds` není `reset --hard`. Existence souboru ani větev (a) nestačí |
| T27 | ruční po deployi | gate (QA verifier) | Brain kontejner, curl jako Q3 | B29. Čtyři default exporty, každý `time_total` < 1000 ms. `vault_head` == `git rev-parse HEAD` v kontejneru |
| T28 | pytest | gate | hub `test_task_export.py` | B31 |

Playwright-smoke a Playwright-T6-full: netýká se. Tester se nevolá.

Lokální gate: `vps/second-brain-brain/.venv`, pytest `vps/second-brain-brain/tests` a `vps/second-brain-hub/tests` (dotčené soubory).

## Pořadí implementace

F1–F5 jsou na `82c5afd2` hotové (oid, export, MCP, REST, pytest). Znovu se neotevírají.

F6 — flagy session včetně `commit_on_end=False` a `discard_dirty_on_error=False` pro každý `mode="read"`, jedno čtení v `read_text`, `_projects` bez `collect_projects`, T25, T26 včetně větve 400 na tracked souboru (C4), T28 a doplněk T23. Push `main` až po diff reviewerovi a po zeleném T8, T12, T23, T25, T26, T28. QA T27 po Brain deployi. T24 zůstává. Hub cron default flagy nemění.

## Rizika a zpětná kompatibilita

1. Špatný in-process blob SHA rozbije `expect_oid` v Brainu i v cronu. Pojistka je jedno čtení a test rovnosti s `git hash-object` (B9) před pushem.
2. `export_tasks` musí dál vrátit `TypedDict` dict (B18).
3. `priority_score` u neúplných ICE se se snapshotem rozejde schválně (A1).
4. `projects[].hierarchy` zůstává vlajka charteru (A4, B31). Slim reader ji nesmí zjednodušit na `project_uses_hierarchy()`.
5. Aktivní `Done` rodič ve `tasks` není, `parent_not_found` ale nedostane (B25).
6. Rituál `<ID>.md` s neprázdným title dostane `filename_title_mismatch=true`. Rotace s datem ne.
7. Velké `include_closed_days` čte celý archiv. SLO 1 s platí pro N=0.
8. Commit těla bez posunu `updated` task vrátí, když řádek z `git log -z --name-only` po `_norm_rel` sedí na `rel_path` (B13).
9. Warm `get_context` smí mít jiný `stats.total_open_tasks` (B27). Export rebuild nespouští.
10. Read nástrojů kromě exportu na dirty klonu je 503 `vault_dirty_start` a `commit_if_dirty` nevolají. Export dirty check nevolá. Větev 200 commit neudělá, ale dnešní `discard_dirty_on_error=True` se na ní neprojeví, protože úspěch volá `__exit__(None)`. Zámek flagu je B30(b) / T26: 400 na tracked špíně, bajty před a po se rovnají, v `_git_cmds` není `reset --hard` (C4). `vault_head` zůstane HEAD. Mutate na default session dirty pořád skipne.
11. `find_tasks` se nemění a dál umí vrátit aktivní terminál, který v exportu není (B8).
12. Setup skript hubu ukazuje repo `LC-RBEDU/claude-cowork`. Když živý app sleduje jiný remote, tenhle push hub nenasadí. Brain watch na `lib/**` platí podle skriptu Brainu.
13. `vault_head` je lokální HEAD i po F6. `git fetch` ho neposouvá (A10). Read ho neposune commitem (Q4=A) ani resetem při 400 (C4). Commit, který je jen na originu, se v exportu objeví, až se HEAD tohoto klonu posune zápisem mutate/rebuild nebo resetem mimo read session.
14. Dnešní úspěšný read na čistém klonu dělá `git add -A` a při nečekané špíně by soubor commitnul a při `GIT_VAULT_PUSH=1` pushnul. Po F6 to read nedělá. Hub cron default `commit_on_end=True` si nechá.

## Otevřené otázky pro uživatele

Žádné. Q1 a A1–A9 jsou zavřené. Q4 je zavřené variantou A. A10 je předpoklad k Q3 a Q4, ne otázka. D1 (quoted ISO v archivním okně) se v tomhle kole neřeší.

## C# → jak vyřešeno

| ID | Verdikt | Kde v plánu |
|---|---|---|
| C1 | vyřešeno, beze změny | Průchod bere jen `is_folder`. Chybějící `tasks/` i chybějící archivní složka slugu se přeskočí. Charter `*.md` se jako složka neotevírá. B26 / T1. |
| C2 | vyřešeno, beze změny | `git log -z --name-only` odděluje NULem commity. Parser řeže LF řádky a teprve řádek jde do `_norm_rel`. B13 / T12 beze změny. |
| C3 | vyřešeno, beze změny | Shoda s `total_open_tasks` je definice na souborech (T6). `mode=warm` není fail (B27, T24). |
| Q3 | vyřešeno | A10, B17, B28–B31, P3, P7, P10, P11, T23, T25–T28, F6. Fetch z read zmizí. Export navíc bez `git status`, bez druhého čtení a bez `collect_projects`. Strop < 1000 ms. |
| Q4 | vyřešeno, varianta A | `commit_on_end=False` pro každý read. B17, B28, T25 zakazují `add` / `commit` / `push`. Mutate a rebuild commit nechají. |
| C4 | vyřešeno | B30(b), T26(b), riziko 10, checklist částečný zápis, delta bod 2 a 5. Tracked soubor, `since=not-a-date` → 400 uvnitř `with`. Bajty se rovnají stavu před voláním, ne HEAD. V `_git_cmds` není `reset --hard`. Větev 200 to nehlídá (`vault_deps.py` 148–150 versus 139–140, `git_io.py` 231–238). |

## Delta pro implementaci

Kód na `82c5afd2cb129d4bd32f55d88d0462f14cc6eb2b` znovu nestavět. Parser `since` a D1 nesahat.

1. `GitVault.__init__`: `fetch_on_begin=True`, `check_dirty_on_begin=True`, `commit_on_end=True`. `begin_session` (`git_io.py` 193–219) spustí fetch a `_is_dirty` jen při flagu. `end_session` (225–229) zavolá `commit_if_dirty` jen při `commit_on_end`. Defaulty True.
2. `brain_vault`: mutate a rebuild vždy fetch, dirty check, `commit_on_end=True`, `discard_dirty_on_error=True`. Read má fetch vypnutý, `commit_on_end=False` a `discard_dirty_on_error=False`. Jinak finally (`git_io.py` 231–238) při výjimce vrátí tracked soubor na obsah z HEAD. `export_tasks` volá `brain_vault(mode="read", check_dirty=False)`.
3. `read_text` čte soubor jednou. `oid` je `git_blob_oid` těch bajtů.
4. `_projects` nevolá `collect_projects`. Čtyři pole stejná jako `collect_projects` (slug 203, `HUB_TITLE_RE` 76, `hierarchy` 228–232).
5. T25: read nemá v `_git_cmds` `fetch`, `add`, `commit` ani `push`. Mutate a rebuild po zápisu `fetch`, `add` i `commit` mají. T26 má dvě větve. (a) Špinavý export je 200, HEAD se nezměnil, není `add` ani `commit`, jiný read je 503. (b) Tracked soubor s jinými bajty než HEAD, `since=not-a-date` → 400 `invalid_since`. Bajty souboru se rovnají stavu před voláním. V `_git_cmds` není `reset --hard`. Existence souboru ani větev 200 nestačí (C4). T23 bez `fetch`/`status`/`add`/`commit`/`push`. T27 čtyři curl pod 1000 ms.
6. `vault_head` zůstává lokální HEAD. Read ho commitem neposouvá a při 400 ho resetem nepřepíše.
