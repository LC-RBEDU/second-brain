# Plán: Export follow-upy (hierarchy, CAS, parse signály)

## Zadání a požadavky

R1 — `projects[].hierarchy` musí sedět s `collect_projects` a s tím, co vrací `get_context`. Když export vrací `true` všude a snapshot jen u pěti projektů, boolean se opraví. Těch pět slugů se nehardcoduje. Slim reader nesmí brát `project_uses_hierarchy()` (vždy `true`). Zdroj: bod 1 briefu, navázání na B31 / A4 schváleného plánu.

R2 — Odmítnutý `expect_oid` u `update_task` (MCP i REST) vrátí strukturovanou chybu `error_reason: oid_mismatch` a aktuální `oid`. Důvod se nesmí ztratit v obecném „Error executing tool“. Do vaultu se nezapisuje. Zdroj: bod 2. Rozsah Q2: jen `update_task`. Q4: MCP klient `call_tool` i protokolový handler musí ty dvě pole dostat v těle výsledku, ne v `__cause__`.

R3 — `filename_title_mismatch` po normalizaci na písmena a čísla. Kosmetika (lomítko vs pomlčka, pomlčky vs mezery, zkrácení bez změny písmen a číslic) není mismatch. Tyto čtyři zůstanou mismatch: **AF15 — Nový formát Allfred budgetu — jedna struktura šablony**, **AF37 — přehodit planned expenses Our Work→Production**, **F-S63 — Sledovat: Honza × Luboš — potvrzení net odměny 120k**, **RBU-S99 — Delivery karta projektu — Lucie skill vs Universe**. Soubory se nepřejmenovávají. Zdroj: bod 3.

R4 — `parent_closed` (Q1, varianta 2) patří sem: rodič není v `id_index` a jeho ID je ve kmeni souboru v `07-ARCHIV/tasks-done/`; nebo rodič v `id_index` je jen proto, že ho tohle volání načetlo z archivu (`include_closed_days` > 0) a je terminál. Aktivní `Done`/`Cancelled`, jehož soubor pořád leží v `02-PROJEKTY/<slug>/tasks/`, `parent_closed` nedostane a dál nemá `parent_not_found` (A7 schváleného plánu / B25). `parent_not_found` zůstane, když rodič není v aktivních (včetně terminálů přečtených do indexu) ani ve kmenech archivu. Tasky se nepřesouvají. Zdroj: bod 4 + Q1. Ověřené dvojice: **F-T161** → **F-S71**, **F-T176** → **F-S82**, **FP-T136** → **FP-S51**, **IAD-T129** → **IAD-S47**, **RBU-T142** → **RBU-S113**. Všechny rodiče jsou `type: story`, `status: Done`, soubor jen v `07-ARCHIV/tasks-done/`.

R5 — `since` nejdřív ověřit proti kódu a A5 schváleného plánu. Když už platí sjednocení (a) frontmatter `updated` a (b) `git log --since`, chybějící `updated` samo task s commitem po `since` nevynechá a cursor od `vault_head` se nezavádí. `vault_head` zůstává lokální HEAD. Zdroj: bod 5.

R6 — Chybějící ICE není chyba. `parse_errors` ani nová kontrola nesmí ICE vyžadovat. `null` zůstává (A1 schváleného plánu). Non-goal. Zdroj: bod 6.

R7 — **S-S33 — Inspirace: review pripravmese.cz** má ID story (`S-S33`) a `type: task`. Nový kód v `parse_errors`: `id_type_mismatch`. Jen když raw `type` je `epic`, `story` nebo `task` a písmeno levelu v ID říká něco jiného. Chybějící type kód nepřidá. Neznámý type zůstává `unknown_type`. Soubor se nepřepisuje, `type` se nemění. Zdroj: bod 7 + Q3.

R8 — **RBU-S117** YAML řeší jiný agent jako opravu dat. V tomhle plánu není kódová změna. Export ho smí dál vrátit s `parse_errors`, když YAML nejde. Zdroj: bod 8.

Mimo rozsah: jen otevřené tasky v default exportu; aktivní `Done`/`Cancelled` ve `tasks` nejsou; `find_tasks` strop 50; read session nefetchuje a necommituje; D1 (quoted ISO v archivu) se neopravuje; dashboard BFF a dialog se nestaví; Alembic, RBAC, Celery, frontend, `qa_gate.mjs`, Playwright. Tester se nespouští (`TESTER: přeskočeno`, profil SECOND_BRAIN). `docs/agent_playbooks/quality-checklists.md` v tomhle repu není. Ostatní MCP nástroje na `oid_mismatch` nepřecházejí.

## Předpoklady

A1 — R1 není lež exportu. Všech 17 charterů v `02-PROJEKTY/*.md` má `hierarchy: true`. `00-System/agent-context.json` (`generated_at` 2026-10-19T13:30) má `"hierarchy": true` u všech 17 projektů, protože to mají chartery. Pětice Finance, Firemní procesy, IT AI Data, RB Universe, Vibe coding není to, co snapshot vrací. Boolean se nemění. Kdyby se měl řídit seznamem pěti slugů, rozjel by se od `collect_projects` i od `get_context`.

A2 — Zavřeno Q1, varianta 2. `parent_closed` nepatří aktivnímu Done/Cancelled (`_Rec.archived` je `False`). Patří terminálu načtenému z archivu do `id_index` a ID, které v `id_index` není a je ve kmeni archivu. Kdyby platila varianta „i aktivní Done“, B38 by u K1 `parent_closed` čekalo.

A3 — Archivní hit mimo index je podle ID ve kmeni jména, ne podle frontmatteru. Těla archivu se nečtou. Soubor v `07-ARCHIV` s jiným `id:` uvnitř se počítá podle jména. Soubor, jehož jméno ID nemá, zůstane `parent_not_found`, i když ho má uvnitř. U pěti ověřených rodičů je ID na začátku jména. Terminál už načtený do `id_index` se posuzuje podle `archived` a statusu, ne podruhé podle jména.

A4 — R3 je rovnost řetězce písmen a číslic v pořadí (NFC, pak `casefold`, pak jen `isalnum()`), ne matematická množina a ne prefix. Množina by spletla `120` a `012`. Prefix by smazal **F-S63**, protože `(socko/zdrávko)` je jen v `title` a kmen souboru je po alnum prefixem očekávaného kmene. „Zkrácení“, které ubere písmena nebo číslice, zůstane mismatch. Diakritika zůstává písmeno (`š` ≠ `s`).

A5 — Na Drive je `oid` vždy `null` a `expect_oid` se ignoruje. `oid_mismatch` se projeví na GitVault.

A6 — Zavřeno Q4, předchozí věta „banner je klient“ neplatí. Tahle verze knihovny z `Exception` uvnitř toolu udělá `UnexpectedToolError("Error executing tool {name}")` a původní text nechá jen v `__cause__` (`tools/base.py` 211–213, docstring `exceptions.py` 61–71). Protokolový handler pak do `CallToolResult` dává `str(exc)` (`server.py` 445–456), tedy banner bez JSON. Dashboard bere MCP. Smlouva je vrácený `CallToolResult` (`is_error`, text = JSON, `structured_content`), ne `__cause__`. REST dál vrací `as_dict()` a banner neskládá.

A7 — Zavřeno Q2. `oid_mismatch` a klíč `oid` jen u odmítnutého `expect_oid` v `update_task` (MCP i REST). Mtime CAS a `DriveConflictError` bez oid konfliktu zůstávají `cas_conflict`. `edit_task_body`, `append_task_note` a `set_focus` se nemění.

A8 — Zavřeno Q3. `id_type_mismatch` jen při raw `type` `epic` | `story` | `task`, když písmeno levelu nesedí. Chybějící type kód nepřidá. Neznámý type zůstává jen `unknown_type`. **S-S33** má `type: task` explicitně, takže se chytí.

## Současný stav (ověřeno v kódu)

`vps/second-brain-hub/lib/task_export.py` 337–342 — `_project_hierarchy`: `True`, řetězec `true|1|yes`, nebo `fm["slug"] == "rb-universe-development"`. `project_uses_hierarchy` se v souboru nevolá (import na řádcích 21–27 ho nemá).

`vps/second-brain-hub/lib/agent_context_build.py` 185–232 — `collect_projects`, který skládá snapshot pro Brain. `hierarchy` je stejný boolean z frontmatteru (plus slug ve frontmatteru). `build_and_write_context_bundle` 346 a 363–365 dopočítá `open_tasks_count` a `open_epics_count` a `hierarchy` nepřepisuje.

`vps/second-brain-brain/app/tools/get_context.py` 16–21 a 58 — `get_context` volá `build_and_write_context_bundle` z `agent_context_build`. Post-pass v `scripts/build_agent_context.py` 528–529 (`open_epics_count > 0` → `hierarchy = True`) není cesta `get_context`. Dnešní `agent-context.json` má `hierarchy: true` u všech 17 kvůli charterům, ne kvůli tomu post-passu.

`vps/second-brain-hub/lib/hierarchy.py` 101–109 — `project_uses_hierarchy` vrací vždy `True`.

`vps/second-brain-hub/tests/test_task_export.py` 551–604 — T28 srovnává čtyři pole s `collect_projects` a zakazuje volání `collect_projects` ze slim readeru.

`vps/second-brain-hub/lib/task_export.py` 39–46, 194 a 222 — `_Rec.archived`. Aktivní soubor má `archived=False`, archivní `archived=True`.

`vps/second-brain-hub/lib/task_export.py` 74–78 a 295–298 — `since`: cesta v `changed_paths_since`, jinak `_updated_in_since`. `None` a prázdný `updated` v (a) vrací `False` (301–304), (b) task stejně pustí.

`vps/second-brain-hub/lib/git_io.py` 380–401 — `changed_paths_since` je `git log -z --since` s `core.quotepath=false`, cesty pod `02-PROJEKTY` a `07-ARCHIV/tasks-done`. `head_sha` (373–378) je `rev-parse HEAD`.

`vps/second-brain-hub/lib/task_export.py` 454–488 — `parent_not_found`, když `parent` není v `id_index`. Index (263–270) je aktivní soubory včetně terminálů plus archiv zařazený do volání. Do `tasks` terminály filtruje 81–84. T6 (`test_task_export.py` 247–282) drží A7: dítě aktivního Done nemá `parent_not_found`.

`vps/second-brain-hub/tests/test_task_export.py` 60–67 a 257 — `_md` má default `work_type="task"`. D1 v T6 je Done bez jiného type, K1 je task s `parent: D1`. `hierarchy.py` 136–137 pak vrací `parent_not_story`. Existující assert T6 (řádek 279) ten kód nehlídá; v `parse_errors` u K1 je už dnes. Pytest v tomhle kole neběžel, závěr je z fixture a z `parent_type_error`.

`vps/second-brain-hub/lib/task_export.py` 597–601 a `task_identity.py` 51–57 — mismatch je `_norm(stem) != _norm(expected_stem)`. `_norm` je NFC a sbalení mezer. `sanitize_title` mění `:` a `/` na straně title, ne na kmeni souboru. Rotace `<ID>-YYYY-MM-DD` je `False`.

`vps/second-brain-hub/lib/task_export.py` 549–566 — `_ice_int(None)` a prázdný řetězec jsou `(None, False)`. `ice_not_int` jen u ne-int hodnoty, která tam je. T15 to má.

`vps/second-brain-hub/lib/hierarchy.py` 22–24 a 46–51 — ID `PREFIX-E|S|T<n>`. Chybějící nebo neznámý `type` se normalizuje na `task`. Proto se `id_type_mismatch` nesmí věšet na normalizovaný type (A8).

Vault, jen čtení: `S-S33` má `type: task` a `title: Inspirace: review pripravmese.cz`. Čtyři názvy z R3 se od kmenů souborů liší slovy nebo číslicí `(1)`, ne jen separátorem.

`vps/second-brain-brain/app/tools/update_task.py` 115–120 a 174–183 — `expect_oid != oid` i oid `DriveConflictError` jsou v implementaci `oid_mismatch` / 409 s klíčem `oid` (pracovní strom, T33 prošel). Zápis při pre-checku neproběhne. Ostatní `DriveConflictError` zůstávají `cas_conflict`.

`vps/second-brain-hub/lib/git_io.py` 474–483 — `_check_cas` předá `current` do `DriveConflictError.oid`. `list_dir` (505–538) u souborů volá `_meta_for_path(..., compute_oid=False)`.

`vps/second-brain-brain/app/errors.py` 83–87 — `as_dict` má `error_reason`, `message` a při nastaveném `oid` i klíč `oid`. REST handler (`main.py` 131–133) to vrací jako tělo 409. T34 REST část prošla (`oid=live-oid`, `write_text` se nezavolal).

`vps/second-brain-brain/app/mcp_app.py` 38–50 — `_call` z `BrainClientError` udělá `RuntimeError` s JSON `as_dict()`. Komentář na řádku 49 říká, že `MCPServer` z toho udělá `CallToolResult(is_error=True, text=str(exc))`. Tahle knihovna to nedělá.

`vps/second-brain-brain/.venv/lib/python3.14/site-packages/mcp/server/mcpserver/tools/base.py` 208–213 — `ToolError` se přebalí na `ToolError("Error executing tool {name}: {exc}")`. Jakákoli jiná `Exception` (včetně `RuntimeError`) je `UnexpectedToolError("Error executing tool {name}")` bez textu příčiny. JSON zůstane v `__cause__`.

`…/mcp/server/mcpserver/server.py` 437–456 a 533–548 — `call_tool` výjimku nechytá a vyhodí ji volajícímu. `_handle_call_tool` z ní udělá `CallToolResult(content=[TextContent(text=str(exc))], is_error=True)` a `structured_content` nenastaví. U `UnexpectedToolError` je `str(exc)` jen banner.

`…/mcp/server/mcpserver/utilities/func_metadata.py` 186–226 — úspěch `export_tasks` (návrat `ExportTasksResult`, TypedDict) jde přes `convert_result` do `CallToolResult` se `structured_content`. Když tool vrátí už hotový `CallToolResult` a `is_error` je true, validace output schématu se přeskočí a objekt se vrátí jak je (204–207). `update_task` je anotovaný `-> str`, takže úspěch je obalený `{"result": "<json string>"}`. Chybový `CallToolResult` s `is_error=True` tohle schéma nevaliduje.

`vps/second-brain-brain/tests/test_export_tasks.py` 220–227 — T14 čte `result.is_error` a `result.structured_content` z návratu `call_tool`, ne z výjimky.

`vps/second-brain-hub/tests/test_task_export.py` 110–148 — `MemVault.list_dir` `recursive` zahazuje a vrací jen přímé děti. Sken archivu musí být dvouúrovňový jako `_read_archive` (200–229), ne jeden `recursive=True`.

`vps/second-brain-hub/lib/task_export.py` 250–260 — rozbitý YAML je `yaml_error` a prázdný frontmatter. **RBU-S117** tím projde bez zvláštního kódu.

## Návrh

RBAC, Alembic, Celery, frontend, subnav: netýká se.

### R1 — žádná změna booleanu

`_project_hierarchy` se nemění. Pět slugů se nikam nepíše. Do T28 se přidá assert, že zdroják `task_export.py` neobsahuje `project_uses_hierarchy`. Export se neopravuje podle `scripts/build_agent_context.py` 528–529. `get_context` ten post-pass nevolá (A1).

### R3 — alnum kmen

V `task_export._filename_mismatch`: po dosavadních výjimkách (prázdné id/title, `ROTATION_RE`) porovnat řetězce `_alnum(stem)` a `_alnum(expected_stem(task_id, title))`. `_alnum` = NFC, `casefold`, znaky s `isalnum()` v původním pořadí. `120` a `012` se nerovnají. `sanitize_title` zůstane uvnitř `expected_stem`. Do `parse_errors` se příznak dál nedává. Soubory se nepřejmenovávají. Čtyři ID se neallowlistují; v testu jsou jen fixture.

### R7 — `id_type_mismatch`

V `_parse_errors`, vedle `unknown_type`, ale ne místo něj. Fullmatch `^[A-Za-z]+-([EST])\d+[a-z]?$` na `task_id` (písmeno levelu case-insensitive). Mapa `E→epic`, `S→story`, `T→task`. Kód se přidá jen když raw `type` po `strip` a `lower` je `epic`, `story` nebo `task` a mapa s ním nesedí. Porovnání nejde přes `normalise_work_type`. ID bez level písmene kontrola nebere. Chybějící type: nic. Neznámý type: jen `unknown_type`. Výstupní pole `type` se nemění. Soubor se nezapisuje.

### R4 — `parent_closed`

V `_parse_errors`. `parent_missing` pořád blokuje druhé `parent_not_found` z `parent_type_error` (`hierarchy.py` 130–131).

1. Rodič je v `id_index` a `archived` je `False`: ani `parent_closed`, ani `parent_not_found`. Typové kontroly jedou dál.
2. Rodič je v `id_index`, `archived` je `True` a status je `Done` nebo `Cancelled`: `parent_closed`, ne `parent_not_found`. `parent_missing` zůstane false.
3. Rodič je v `id_index`, `archived` je `True` a status není terminál: ani jeden z těch dvou kódů.
4. Rodič v `id_index` není a jeho ID je ve kmenech `07-ARCHIV/tasks-done/`: `parent_closed`, `parent_missing = True`.
5. Jinak: `parent_not_found`.

Kmeny se staví jen když aspoň jeden rodič v `chosen` v `id_index` chybí. `projects_csv` a `since` je nezužují. Dvouúrovňový `list_dir`, žádný `read_text`. Při N=0 pět rodičů ve `tasks` není, děti jsou a dostanou `parent_closed` z větve 4.

### R5 — bez změny `since`

(a) i (b) v kódu jsou. Cursor od `vault_head` se nezavádí. Mezera: commit starší než `since` a prázdné `updated` → v inkrementu task není, v plném exportu je. `vault_head` zůstává `rev-parse HEAD`.

### R6 a R8 — non-goal

Žádný `ice_missing`. Žádná větev pro **RBU-S117**. `yaml_error` stačí.

### R2 — `oid_mismatch`

Jen `update_task` (A7). REST je hotový: pre-check a oid větev `DriveConflictError` dávají 409 a `as_dict()` s `error_reason=oid_mismatch` a `oid`. `write_text` se při pre-checku nezavolá. `edit_task_body`, `append_task_note` a `set_focus` zůstávají `cas_conflict`.

MCP se `_call` pro tuhle chybu nesmí použít. `RuntimeError` knihovna sežere (A6). `ToolError` by taky nestačil: `base.py` 208–210 ho přebalí na `Error executing tool update_task: {text}`, `call_tool` ho vyhodí a handler nastaví jen ten text, bez `structured_content`.

V `mcp_app.update_task` (`mcp_app.py` 89–104): zavolej `update_task_tool.update_task` přímo. Když výjimka je `BrainClientError` a `error_reason == "oid_mismatch"`, vrať `CallToolResult` (`from mcp.types import CallToolResult, TextContent`):

- `is_error=True`
- `content=[TextContent(type="text", text=json.dumps(exc.as_dict(), ensure_ascii=False))]`
- `structured_content=exc.as_dict()`

`convert_result` ten objekt pustí dál, protože `is_error` je true (`func_metadata.py` 204–207). `call_tool` ho vrátí, nevyhodí (`server.py` 548). `_handle_call_tool` ho při absenci výjimky vrátí beze změny (441–442). Dashboard čte `structured_content` a stejně tak text, který je čistý JSON, ne banner.

Jiná `BrainClientError` z `update_task` (prázdný patch, `deadline_order`, …) dál jde přes `_call` → `RuntimeError` → `UnexpectedToolError` s bannerem. `_call` se behaviorálně nemění. Komentář na řádku 49 se přepíše na to, co knihovna opravdu dělá, ať příští úprava znovu nepočítá s `str(exc)` v textu výsledku.

Úspěch `update_task` zůstává `return _call(...)` (řetězec JSON). Úspěch `export_tasks` se nemění.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B32 | charter `hierarchy: true` u všech hubů; fixture T28 | stejná čtyři pole jako hub `collect_projects`. Zdroják neobsahuje `project_uses_hierarchy` | R1 | T29 |
| B33 | čtyři reálné kmeny vs title z R3 | `filename_title_mismatch` true | R3 | T30 |
| B34 | lomítko vs ` -`; mezery vs ` —`; rotace; ZZ1; `120` vs `012` | kosmetika a rotace false; ZZ1 true; `120` ≠ `012`. Není v `parse_errors` | R3 | T30 |
| B35 | `S-S33` + `type: task`; stejné ID bez type; `type: widget`; story ID + story; ploché ID + task; `RBU-E1` + task | `id_type_mismatch` jen u `S-S33`+task a u `RBU-E1`+task. Bez type kód není. `widget` má jen `unknown_type` | R7 | T31 |
| B36 | N=0, rodič jen jako kmen v archivu, uvnitř třeba jiné `id:` | dítě ve `tasks`, `parent_closed`, ne `parent_not_found`. Archiv ve `tasks` není. `read_text` na archiv se nezavolá | R4 | T32 |
| B37 | rodič nikde (ID, které parser vezme, ne `NOPE`) | `parent_not_found`, ne `parent_closed` | R4 | T32 |
| B38 | T6: K1 pod aktivním Done D1 (`archived=False`, `_md` default type task); Cancelled v aktivní složce | bez `parent_not_found`, bez `parent_closed`. U K1 je `parent_not_story` | R4 | T32 |
| B45 | N>0, terminál načtený z archivu (`archived=True`) | `parent_closed`, ne `parent_not_found`. Story rodič + task dítě: bez `parent_not_story` | R4 | T32 |
| B46 | N>0, archivní rodič ve okně, status Next | ani `parent_closed`, ani `parent_not_found` | R4 | T32 |
| B39 | `since` a commit těla bez posunu `updated`; soubor bez commitu a bez `updated` | první ve výstupu. Druhý ne. `vault_head` je HEAD | R5 | T12 |
| B40 | chybějící ICE; `ice_i: n/a` | null bez `ice_not_int`; `n/a` má `ice_not_int` | R6 | T15 |
| B41 | YAML, který `safe_load` shodí | `yaml_error`, task ve výstupu | R8 | T9 |
| B42 | `update_task` s jiným `expect_oid`, i `dry_run=true` | 409, `as_dict` má `oid_mismatch` a `oid` z čtení. `write_text` se nezavolá | R2 | T33 |
| B43 | pre-check projde, zápis vyhodí `DriveConflictError` s `oid`; zvlášť volání bez `expect_oid` | s `expect_oid`: `oid_mismatch` a `oid` z výjimky. Bez něj: `cas_conflict` a klíč `oid` v dictu není | R2 | T33 |
| B44 | `await mcp.call_tool("update_task", …)` se starým `expect_oid` | nehodí `UnexpectedToolError`. Návrat je `CallToolResult`: `is_error` true, `structured_content["error_reason"]=="oid_mismatch"`, `structured_content["oid"]` je aktuální oid, `content[0].text` je JSON téhož objektu a nezačíná na `Error executing tool`. `__cause__` se neassertuje. REST 409 z T33 platí dál. Jiná chyba téhož toolu (prázdný patch) pořád vyhodí `UnexpectedToolError` s textem přesně `Error executing tool update_task` | R2, Q4 | T34 |

Checklist A:

- Authn: beze změny.
- RBAC / scope: netýká se.
- Validace: B35, B42. `since` parser se nemění.
- Prázdný výsledek: beze změny (staré B1).
- Idempotence čtení: export pořád nic nezapíše.
- Částečný zápis: B42, zápis oid konfliktu neproběhne.
- Tvar chyby: REST B42–B43. MCP oid konflikt je B44 (`structured_content` + text JSON). Ostatní MCP chyby zůstávají banner `UnexpectedToolError` (A6).
- Side effect: read session pořád bez fetch/commit. Archivní sken je `list_dir` bez `read_text`.
- Tiché ořezání: strop exportu se nezavádí. `find_tasks` strop 50 se nemění.
- Časová zóna: `since` beze změny.
- CAS zápis: B42–B44, jen `update_task`. `expect_mtime` mimo oid konflikt zůstává `cas_conflict`.
- Kompatibilita: klient 409 `update_task` čte `oid_mismatch`. MCP klient čte `structured_content` nebo text JSON, ne banner a ne `__cause__`. Ostatní nástroje se nemění. Aktivní Done `parent_closed` nedostane.

## Výkonový rozpočet (P)

Endpointy: MCP/REST `export_tasks` a `update_task` při 409. Q4 nepřidává I/O.

1. SQL: netýká se.
2. Indexy DB: netýká se.
3. N+1: default export bez chybějícího rodiče archiv neotevírá. Když rodič v `id_index` chybí, jeden průchod jmen `07-ARCHIV/tasks-done/<slug>/*.md`, `compute_oid=False`, žádný `read_text`. `git log` jen při `since`. `update_task` 409: jedno `read_text`, nula zápisů. MCP větev jen složí `CallToolResult` z výjimky, která už vznikla.
4. Payload: chybový MCP výsledek je malý JSON v textu i ve `structured_content` (`error_reason`, `message`, `oid`). Export se o kódy v `parse_errors` prodlouží jako dřív.
5. Ořez: strop exportu není. `find_tasks` strop 50 se nemění.
6. Cache: žádná nová.
7. Latence: default export &lt; 1000 ms (staré B29 / T27). T23 &lt; 1500 ms, nula `hash-object`, archiv nevolá, když rodiče v indexu jsou. `update_task` 409 je jedno čtení; složení `CallToolResult` k tomu čas nepřidá.
8. Archiv ve `tasks`: při N=0 se těla nečtou. Jména se listují jen kvůli B36.
9. Zámek: stávající flock. Chybová větev nezapisuje.
10. Paměť: množina ID z kmenů, ne obsah souborů. Chybový dict je jeden objekt.
11. Externí volání: žádná. Read pořád bez fetch a push.

Počet souborů v archivu jsem nepočítal. Rozpočet stojí na tom, že se nečtou těla. Kdyby T27 po nasazení přelezl 1 s, zúžení je pořád jen jména, ne návrat k `read_text`.

## Testy (T#)

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T29 | pytest | gate | `vps/second-brain-hub/tests/test_task_export.py` (rozšíření T28) | B32 |
| T30 | pytest | gate | stejný | B33, B34 |
| T31 | pytest | gate | stejný | B35 |
| T32 | pytest | gate | stejný, `MemVault` | B36, B37, B38, B45, B46. U K1 `parent_closed` nečekat a `parent_not_story` čekat. B37 používá ID, které `parse_parent_id` vezme (`ZZ9`), ne `NOPE` |
| T12 | pytest | gate | beze změny | B39 |
| T15 | pytest | gate | beze změny | B40 |
| T9 | pytest | gate | beze změny | B41 |
| T33 | pytest | gate | `vps/second-brain-brain/tests/test_update_task_cas.py` | B42, B43. Už prošel |
| T34 | pytest | gate | `vps/second-brain-brain/tests/test_export_tasks.py` | B44. `await build_mcp().call_tool("update_task", …)` **vrátí** výsledek. Assert `is_error`, `structured_content["error_reason"]`, `structured_content["oid"]` a `json.loads(content[0].text)` se stejnými poli. Žádný `pytest.raises(UnexpectedToolError)` a žádné čtení `__cause__`. Druhý případ: prázdný patch vyhodí `UnexpectedToolError` s `str(exc) == "Error executing tool update_task"`. REST 409 nechat, jak T33/T34 REST už prošly |

Playwright-smoke a Playwright-T6-full: netýká se. Tester se nevolá.

Lokální gate: `python3 -m pytest vps/second-brain-hub/tests/test_task_export.py vps/second-brain-brain/tests/test_update_task_cas.py vps/second-brain-brain/tests/test_export_tasks.py -q`. Žádný zápis do vaultu. T27 (curl &lt; 1 s) až po nasazení R4.

## Pořadí implementace

F1 — T30 a `_alnum` (R3). Hotovo v pracovním stromu.

F2 — T31 a `id_type_mismatch` (R7). Hotovo.

F3 — T32 a `parent_closed` (R4). Hotovo.

F4a — REST `oid_mismatch` (`errors.py`, `drive_io.py`, `git_io.py`, `update_task.py`, T33). Hotovo.

F4b — MCP návrat `CallToolResult` jen pro `oid_mismatch` v `mcp_app.update_task`, oprava komentáře u `_call`, přepis T34 (Q4). `_call` dál hází `RuntimeError`.

F5 — assert v T28 (R1). Hotovo, pokud T29 prošel.

F6 — gate pytest výše, pak teprve commit. R5, R6, R8 nemají další kód.

`build_agent_context.py` se nespouští. Vault se needituje.

## Rizika a zpětná kompatibilita

1. Klient 409 `update_task`, který přepíná na `cas_conflict`, u `expect_oid` čte `oid_mismatch` a `oid`. Mtime konflikty a ostatní tři nástroje `cas_conflict` zůstávají.
2. Kosmetické `filename_title_mismatch: true` zmizí. Čtyři skutečné rozdíly zůstávají. Prefix by schoval **F-S63**. Množina znaků by spletla `120` a `012`.
3. Děti aktivního Done/Cancelled v `02-PROJEKTY/.../tasks/` `parent_closed` nedostanou. U T6 K1 zůstane `parent_not_story`.
4. Archivní soubor bez ID v kmeni jména zůstane `parent_not_found` (A3).
5. `parent_closed` z větve 4 neříká `parent_not_story`. Větev 2 typ zná.
6. Sken jmen na živém vaultu přidá `list_dir` k default exportu. Těla a `hash-object` nepřibudou. Strop 1 s hlídá T27 po deployi.
7. R1 se neopravuje kódem. `get_context` `hierarchy` podle počtu epiců nepřepisuje.
8. **RBU-S117** pořád přijde s `yaml_error`, dokud ho neopraví druhý agent.
9. Ostatní MCP chyby (`_call` → `RuntimeError`) pořád končí bannerem `Error executing tool {name}` a JSON mají jen v `__cause__`. To Q4 nemění. Kdyby se `_call` přepsal na `ToolError`, knihovna text obalí prefixem a `structured_content` pořád nevznikne (`base.py` 208–210, `server.py` 456).

## Otevřené otázky pro uživatele

Žádná blokující. Q1 je varianta 2 (A2). Q2 je A7. Q3 je A8. Q4 rozhoduje plán: návrat `CallToolResult`, ne výjimka.

## Delta vůči schválenému plánu exportu

Schválený plán exportu se needituje.

- Boolean `hierarchy` a `_projects` beze změny. T28 zakazuje `project_uses_hierarchy`.
- `since`, `vault_head`, ICE null, `yaml_error`, skladba default `tasks`, strop `find_tasks`, read session: beze změny.
- `_filename_mismatch` je rovnost řetězce alnum v pořadí.
- `_parse_errors` má `id_type_mismatch` (jen raw type epic/story/task) a `parent_closed` (jen archiv). Aktivní Done/Cancelled v `tasks/` `parent_closed` nedostane.
- `update_task` u oid CAS vrací `oid_mismatch` a `oid`. Ostatní nástroje zůstávají `cas_conflict`. MCP tuhle jednu chybu vrací jako `CallToolResult`, neschovává ji do `UnexpectedToolError`.

## Body 1–7

| # | Stav | Proč |
|---|---|---|
| 1 hierarchy | hotovo bez změny booleanu | Export i hub `collect_projects` berou vlajku charteru. `get_context` epic post-pass nevolá. T29 |
| 2 CAS | REST hotové; MCP se dodělá podle Q4 | REST 409 má `oid_mismatch` a `oid` (T33, REST část T34). MCP musí vrátit `CallToolResult`, ne `RuntimeError` |
| 3 filename | hotovo | Alnum řetězec v pořadí. Čtyři fixture true. Soubory se nepřejmenovávají |
| 4 parent_closed | hotovo, Q1 varianta 2 | Kmen v archivu, nebo terminál s `archived=True`. Aktivní Done kód nedostane. U T6 K1 zůstane `parent_not_story` |
| 5 since | non-goal | (b) už v kódu. Cursor od `vault_head` se nezavádí |
| 6 ICE null | non-goal | T15 |
| 7 ID vs type | hotovo | Jen raw type epic/story/task. **S-S33** má `type: task` |

## Delta pro implementaci

Oproti verzi plánu, kterou kritik schválil (otevření #1). Kód R1, R3, R4, R7 a REST R2 se nemění.

1. `vps/second-brain-brain/app/mcp_app.py`, funkce `update_task`: při `BrainClientError` s `error_reason == "oid_mismatch"` nevolat `_call` a neházet `RuntimeError`. Vrátit `CallToolResult(is_error=True, content=[TextContent(type="text", text=<JSON as_dict>)], structured_content=<as_dict>)`. Import z `mcp.types`.
2. `_call` nechává `raise RuntimeError(_err_text(exc))` pro všechny ostatní chyby všech toolů. Komentář na řádku 49 se opraví: `RuntimeError` skončí jako `UnexpectedToolError` s textem jen `Error executing tool {name}` (`tools/base.py` 211–213). JSON v `__cause__` klient nevidí.
3. `update_task.py`, `errors.py`, `drive_io.py`, `git_io.py` se kvůli Q4 neupravují. T33 zůstává zelený.
4. T34: smazat očekávání, že `call_tool` hodí chybu a text bude JSON. Assertovat návratovou hodnotu (`is_error`, `structured_content`, text bez prefixu `Error executing tool`). Druhý assert: jiná chyba `update_task` pořád hodí `UnexpectedToolError` s přesně tím bannerem. `__cause__` není akceptační kritérium.
5. `edit_task_body`, `append_task_note`, `set_focus` se neupravují.

## Q4 → jak vyřešeno

| Q4 | Jak vyřešeno |
|---|---|
| Q4 | Vyřešeno změnou plánu, ne kódu v tomhle kole. A6, věta R2 o MCP, B44 a T34. `RuntimeError` z `_call` knihovna schová (`base.py` 211–213, `server.py` 456). `update_task` při `oid_mismatch` vrátí `CallToolResult`: `is_error`, text = JSON `as_dict()`, `structured_content` se stejnými poli. `call_tool` to vrátí a protokol to pošle dál (`func_metadata.py` 204–207, `server.py` 441–442 a 548). `__cause__` dashboardu nestačí a test ho nečte. REST 409 se nemění. `_call` a ostatní nástroje se behaviorálně nemění. |
