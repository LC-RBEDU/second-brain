# Plán: Second Brain dashboard (MVP)

## Zadání a požadavky

R1 — Obrazovky MVP: Radar, Chybně zadané, Mapa, Projekt (seznam + kanban), Detail, Nový task, Úklid. Mindmapa a hromadný posun deadlinů mimo Úklid jsou fáze 2. Kanban mění jen status. Parent se mění v detailu. Přetažení na jiný epic parenta nemění. Pauznuté projekty jsou defaultně schované a jeden přepínač je vrátí (Q4, Q14). Náhled zavření přidá otevřené potomky i z pauznutého projektu (Q18). Done, Cancelled a řádek s `path` pod `07-ARCHIV/` se v přehledu nezobrazí na žádné obrazovce. Sloupec Done na kanbanu není (Q40). Hotovo u souboru, který pořád leží ve `02-PROJEKTY/<slug>/tasks`, je pořád PATCH jen se `status`. Zdroj: handoff §4, Q2, Q4, Q14, Q18, Q34, Q40.

R2 — Klasifikace běží v prohlížeči nad exportem otevřených tasků. Dlaždice mají vlastní počty. Čitatel Focus je `count_focus_slots`. Chybně zadané = tasky s červenou chybou, bez `no_date`. Stale = jen Next nebo Doing s pravidlem `stale`. Hierarchie je `projects[].hierarchy`. `today` je den Evropy/Prahy. Zdroj: spec v0.3, Q5, Q15.

R3 — Prohlížeč Brain nevolá. Jeden task je `PATCH /v1/tasks`. Víc položek je `bulk_update`. Zdroj: handoff §3.

R4 — Zápis jde s `expect_oid`. Po úspěchu se export načte znovu. U jednoho tasku je 409 `oid_mismatch` dialog Q9. Úklid dialog Q9 nepoužívá. V jedné dávce se seberou všechny neshody oid, pořadí podle kódových jednotek `id`, `write_text` se nezavolá (Q35). První neúspěch Brainu, včetně 404 a 5xx, zastaví další dávky; už commitnutá dávka se nevrací (Q36). Závod uprostřed smyčky je 409 se stejným `detail.failures` jako neshoda oid, ne HTTP 500 (C10). `deadline_order` a otevřené dítě dialog Q9 neotevřou. Zdroj: handoff §3 a §7, Q1, Q9, Q35, Q36, C10.

R5 — Waiting jen s `waitUntil`. Neprázdný `deadline` maže `review_deadline`. Zrušení je `Cancelled`. `focus` jen přes propose a apply. V UI je `ID — title` z exportu. Doing bez deadlinu a Waiting bez `waitUntil` UI nezapíše, kromě názvu, Hotovo a Zrušit u existujícího Doing bez deadlinu. Next a Backlog bez data UI pustí. Zdroj: handoff §5, Q10, Q27.

R6 — Úklid zavře otevřené potomky. Potomek, který je sám Done, Cancelled nebo v archivu, v náhledu není (Q40). Do `child_ids` patří jen předek, kterého tahle dávka zavírá (Q30, C2). Vlastní datum se předvyplní z `review_deadline` (Q29). Ruční přepis je vlastní datum (C1). Smazání a ruční datum platí do zavření náhledu (Q31). Potvrzení předvyplněného dne posílá jen `review_deadline` a `updated` nemění (Q32). Po 400 otevřeného dítěte zůstane obrazovka a UI ukáže `ID — title` (Q33). Tři režimy pořadí, brána dne, obsazenost po náhledu, rodina nad 80 (Q16, Q17, Q20, Q23). Zdroj: handoff §4 bod 7, Q16–Q33, Q40.

R7 — `needs_decision` je jen prošlá review date u tasku bez deadlinu. Prošlý deadline je Overdue. Zdroj: 04-brain-opravy bod 5.

R8 — Třetí Coolify aplikace `second-brain-dashboard` v projektu `0e0b062b15bfef0bff7f7c45`, sslip, service token, autor commitu Brain. Druhé redirect URI na stávajícím Google klientovi (Q38). Zdroj: Q8, Q38.

Mimo rozsah: follow-upy a YAML **RBU-S117**. Mindmapa, hromadný posun deadlinů mimo Úklid, ICE. `rbu-tester`. Nový hub, `AGENTS.md`. Alembic, RBAC, Celery, subnav, `qa_gate.mjs`. Přesun z `07-ARCHIV/` zpět do `tasks/`. Sloupec Done. Doplnění `updated` jen kvůli oknu exportu. Druhé `brain_vault()` v session, která vault už drží (C9).

## Předpoklady

A1 — Implementace nezačne, dokud `docs/plans/2026-10-19-export-followups.pipeline.md` není DONE. Po DONE `update_task` vrací `oid_mismatch` + `oid`. `projects[].hierarchy` je boolean.

A2 — Prohlížeč stáhne `GET /v1/tasks/export?include_closed_days=0`. `since` dashboard nevolá. Dialog Q9 bere rozdíl z `GET /v1/tasks/item`. Refresh nepřepíše lokální smazání ani ruční datum nezapsaného řádku (A25). `include_closed_days=7` prohlížeč nevolá.

A3 — Chybí-li `hierarchy`, `story_no_epic` se neaplikuje. Pětice slugů v kódu není.

A4 — `02-classify.js` řádek 119 se nepřebírá. Platný parent v prohlížeči je jen Doing, Next, Backlog nebo Waiting v tom exportu, který prohlížeč dostal. Done v datech prohlížeče není. `parse_errors` s důvodem `parent_closed` se přeskočí stejně jako `parent_not_found` (A32). Jediný červený důvod chybějícího parenta je `parent_missing_or_closed`. Serverový export se kvůli tomu nemění. Dlaždice počítá task, ne počet důvodů.

A5 — Dlaždice Q5 a Q15. Hledání je id, název, slug projektu a parent id. Bez MiniSearch/Fuse. Počty neobsahují Done ani Cancelled.

A6 — Build context `vps/`, Dockerfile `second-brain-dashboard/Dockerfile`, sslip jako Brain (`setup-coolify.sh` 47–48 a 89–90). Vault se nemountuje.

A7 — BFF volá Brain s `BRAIN_SERVICE_TOKEN`. Autor commitu zůstává Brain. Session e-mail je jen ve stdout.

A8 — Když `expect_oid` pošle aspoň jedna položka, musí ho mít každá. Všechny neshody jdou do `detail.failures` jako `{id, path, oid}`, seřazené podle kódových jednotek `id`. Jedna neshoda je seznam o jednom prvku. `write_text` se nezavolá (Q35).

A9 — Rozprostření počítá klient. Jeden checkbox Q7 jen pro frontu. Den je Evropa/Praha. Obsazenost je stav po náhledu. Konkrétní datum se počítá i mimo Od–Do a přes max. Smazané předvyplnění den v mapě nedrží. Done a Cancelled den neobsadí, protože v datech prohlížeče nejsou.

A10 — Jedna dávka je jedna session a jeden commit. BFF skládá po nejvýše 40, rodinu nerozdělí, strop 80. První odpověď, která není úspěch, včetně 404 a 5xx, další dávku nepošle (Q36). Už commitnutá dávka se nevrací. Úklid vrátí `written`, `failed`, `pending`.

A11 — Ponechat jen u řádku bez deadlinu a ne u Doing bez deadlinu ani u Waiting bez `waitUntil`. Next a Backlog bez data UI pustí. Vyplněný deadline do create review nepošle.

A12 — Allfred a Pipedrive se netýkají. Checklist v `docs/agent_playbooks/` v repu není. Checklist A je z profilu SECOND_BRAIN.

A13 — Jeden přepínač pauzy, výchozí vypnutý. `projects[].status` jiné než `active` a prázdné je pauza (`today_priority.py` 64–72).

A14 — Kanban má sloupce Doing, Next, Waiting a Backlog. Sloupec Done není (Q40). Drop mezi těmi čtyřmi mění jen status. Hotovo na kartě, jejíž soubor je ve `02-PROJEKTY/<slug>/tasks`, je PATCH jen `{status: Done}`. Parent se v kanbanu neposílá. Drop s otevřeným potomkem z A21 PATCH neodešle.

A15 — Čitatel Focus je port `count_focus_slots` (`today_priority.py` 292–314): nejdřív pauza, pak story s otevřeným taskem. Slug je `task.project`.

A16 — Dialog Q9 srovná `title`, `status`, `deadline`, `review_deadline`, `waitUntil` a `parent`. Jen pro `oid_mismatch` jednoho tasku.

A17 — Tři režimy pořadí. `0` je skóre, prázdné jde nakonec. Srovnání id je podle kódových jednotek. ICE se nepočítá.

A18 — Náhled zavření přidá jen otevřené potomky (Doing, Next, Backlog, Waiting), které chod vidí v datech prohlížeče. Done, Cancelled a archivní řádek se jako řádek k zavření nepřidá (Q40). Bližší uzavření vyhraje (Q21, Q25). Do patche zamčeného potomka jde jen status.

A19 — Dokud ponechaný řádek, který den potřebuje, den nemá, neodejde nic. Od, Do, max a checkbox drží bránu jen u neprázdné fronty. Max výchozí 8, minimum 1.

A20 — Předkontrola `deadline_order` v prohlížeči bere jen otevřené uzly jeho exportu. Server dál čte `iter_active_tasks`. Archivní Done v tom serverovém grafu most `deadline_order` netvoří, protože `iter_active_tasks` archiv nečte (B50). Done pořád ve složce `tasks` mostí (`deadline_order.py` 119–121, B52). Po 409 není automatický retry. „Přesto uložit“ na tom panelu není.

A21 — Hop otevřeného dítěte na serveru jde přes `task_export.export_tasks(vault, include_closed_days=7)` na vaultu, který session už drží (C9). Nástroj `app.tools.export_tasks.export_tasks` se z té session nevolá: otevřel by druhé `brain_vault` (`export_tasks.py` 76–84) a flock není reentrantní (`git_io.py` 40 a 289–303, timeout 5 s; `vault_deps.py` 27–29 a 138–151, 3 pokusy). Bez okna 7 dní by archivní story hop nebyla (`task_export.py` 71–91) a otevřené dítě za ní by server neviděl (B44). Do `child_ids` patří jen předek, kterého tahle dávka zavírá. Dítě kryje jen patch Done nebo Cancelled. Prohlížeč ten archivní hop v datech nemá, takže ho sám nepřidá; server ho pořád vrátí jako 400.

A22 — Rodina nad 80 se nezapíše a nerozkrojí. Ani suchý běh neodejde.

A23 — První Ponechat předvyplní neprázdné `review_deadline`, pokud ho uživatel ještě nesmazal. Ruční přepis je vlastní datum. Po smazání starý den z mapy zmizí hned. Potvrzení pošle jen `review_deadline`. Klíč `updated` v patchi není (`update_task.py` 42–61).

A24 — Dva a víc předků, které dávka zavírá a kterým chybí dítě: HTTP 400, jen `detail.failures`. Jeden rodič: `detail.parent_id` a `detail.child_ids`. Tvar `oid_mismatch` je jiný (A8).

A25 — Smazání a ruční datum platí do zavření náhledu. Přepnutí zpět ani refresh je nevrátí. Nové otevření předvyplní znovu.

A26 — Kdyby přišel `path` začínající `07-ARCHIV/`, BFF na PATCH, na položce bulk a na focus vrátí 400 `archive_readonly` a Brain nezavolá. Smíšená dávka s takovou položkou Brain taky nezavolá. Přesun zpět do `tasks/` v plánu není. V přehledu takový řádek není, protože export pro prohlížeč archiv neobsahuje (Q40). Q34 a Q37 tím pro zobrazení padají: není co otevírat, táhnout ani číst v UI.

A27 — Stejná věta jako A26 pro UI. R1, B57 a T8 říkají, že archivní řádek v prohlížeči není. BFF 400 zůstává.

A28 — Redirect URI nového sslip se přidá na stávajícího Google klienta. Nový klient ani vlastní doména do plánu nepatří.

A29 — `failures[].oid` je aktuální oid souboru. Úklid po 409 označí jako uložené jen řádky, které v exportu po refreshi zůstaly otevřené (A31). Done a Cancelled se nikde nevykreslí. Řádky z neúspěšné dávky i neodeslané, které v exportu pořád jsou, zůstanou předvybrané. U neshod se `expect_oid` vymění za `failures[].oid` a další požadavek odejde až na nový klik. Sám se nezapíše. Dialog Q9 se neukáže. Tvar s `oid` jen na vrcholu, bez `failures`, se pro bulk nepoužije (C10). Náhled se zavře, až když `failed` i `pending` jsou prázdné. Detail právě zavřeného úkolu se zavře a vrátí se na seznam, odkud se otevřel.

A30 — Cancelled se v přehledu nezobrazuje stejně jako Done. Kód to neláme: `TERMINAL_STATUSES` jsou Done a Cancelled (`focus.py` 37) a `task_export.py` 87–89 je při skládání exportu ze složky `tasks` přeskočí. Archiv se při `include_closed_days=0` nečte (`task_export.py` 71–74).

A31 — Po úspěšné dávce se export načte znovu. Done a Cancelled v přehledu nejsou: žádná karta, žádný detail, žádný sloupec. `written` je počet a id v odpovědi, bez karet. Jako uložený jde označit jen řádek, který v exportu zůstal otevřený. `failed` a `pending`, které v exportu pořád jsou, zůstanou předvybrané. Náhled se zavře, až když `failed` i `pending` jsou prázdné. Detail právě zavřeného úkolu se zavře (grill g=10).

A32 — Prohlížeč u `parse_errors` přeskočí `parent_closed` stejně jako `parent_not_found`. Jediný červený důvod chybějícího parenta je `parent_missing_or_closed`. U parenta Done, který pořád leží ve `tasks/`, `parent_closed` nevznikne. Serverový export se nemění. Dlaždice počítá task (grill g=10).

## Současný stav (ověřeno v kódu)

`app/tools/export_tasks.py` 76–84 — nástroj `export_tasks()` nemá parametr vault a v 84 volá `brain_vault(mode="read")`, pak `task_export.export_tasks`.

`lib/task_export.py` 55–63 — `export_tasks(vault, *, include_closed_days=0, …)` bere už otevřený vault. 71–74 — archiv jen při N > 0. 87–91 — terminál ve složce `tasks` do `chosen` nejde, archiv se připojí až potom.

`lib/git_io.py` 40 — `FLOCK_TIMEOUT_S = 5.0`. 289–303 — druhý fd bere `LOCK_EX | LOCK_NB` a při obsazeném zámku čeká do timeoutu. 474–484 — `write_text` s `expect_oid` porovná oid a při neshodě hodí `DriveConflictError` s aktuálním oid. Bez `expect_oid` se tahle větev nespustí.

`app/vault_deps.py` 27–29 a 138–151 — `vault_flock_busy` se zkusí 3×, mezi pokusy spánek 0,15 s, pak 503.

`app/tools/bulk_update.py` 46 — tělo už je v `brain_vault`. 116–118 — `write_text` bez `expect_oid` a bez `except DriveConflictError`.

`app/tools/update_task.py` 42–61 — patch nepřidá `updated`. 176–192 — `write_text` dostane `expect_oid` a `DriveConflictError` je 409 `oid_mismatch` s `oid` na vrcholu.

`app/main.py` 126–133 — handler zná jen `BrainVaultError` a `BrainClientError`. Jiná výjimka z CAS je 500.

`lib/task_io.py` 86–102 — `iter_active_tasks` archiv nečte. `cron/archive_done_tasks.py` 53–67 — přesun do `07-ARCHIV/tasks-done/`, `updated` nenastavuje.

`lib/deadline_order.py` 119–121 — Done, který v seznamu uzlů je, mostí. 79–84 — chybějící mezičlánek řetěz nepřemostí.

`tests/test_git_io.py` 84–109 — držený flock session přeskočí.

Frontend v repu není.

## Návrh

RBAC, Alembic, Celery, subnav, `qa_gate.mjs`: netýká se.

### Brain (R4, R5, R6, R7, C9, C10)

`needs_decision` je True jen bez deadlinu, s prošlou review a mimo Waiting a terminál. `count_focus_slots` se nemění.

`update_task.py` a `bulk_update.py` při kontrole otevřeného dítěte zavolají `task_export.export_tasks(vault, include_closed_days=7)` na vaultu z `brain_vault`, který už drží. Ta kontrola běží i pro čisté Done nebo Cancelled. `needs_forest` dnes pro samotný status Done vrací false (`parent_link.py` 117–123) a tahle kontrola se o něj neopře, jinak B12 nedá 400. Druhé `brain_vault()` nezaloží. Nástroj v `app/tools/export_tasks.py` se tu nevolá. `deadline_order` dál bere `iter_active_tasks`. `updated` se nedoplňuje.

`bulk_update` před řádkem 113 sbírá všechny neshody oid (A8) a otevřené dítě (A21). Ostrá smyčka volá `write_text(..., expect_oid=…)`. `DriveConflictError` se chytí jako v `update_task.py` 179–192 a vrátí `BrainClientError` 409 `oid_mismatch`. `detail.failures` je seznam `{id, path, oid}` té položky, ne `oid` jen na vrcholu. Session necommitne a `discard_dirty_on_error` vrátí soubory té session. Suchý běh při úspěchu kontrol dál vrací `{dry_run: true, count}`.

`create_task.py`: `waitUntil`, exclusive deadline, Waiting bez `waitUntil` je 400 před `mkdir`. 409 `deadline_order` zůstává před `mkdir`.

`main.py`: `POST /v1/tasks` doplní `dry_run`, `deadline`, `review_deadline` a `waitUntil`. `POST /v1/tasks/bulk` volá `bulk_update`. `PATCH` se nemění. GET export pro prohlížeč zůstává nástroj, který si vault otevře sám; to není vnořené volání.

`mcp_app.py`: `bulk_update` při `oid_mismatch`, včetně 409 ze závodu v `write_text`, vrací `CallToolResult`. `_call` se pro tuhle 409 nepoužije.

### BFF (R3, R8, Q40)

Prohlížeč dostane export s `include_closed_days=0`. BFF tělo dál nefiltruje: Done, Cancelled i archiv v něm nejsou (`task_export.py` 71–91). `path` pod `07-ARCHIV/` na zápisu je 400 `archive_readonly` a Brain se nezavolá (A26). První neúspěch dávky zastaví zbytek (A10). Z patche se smaže `focus` a `updated`. Redirect URI sslip jde na stávajícího Google klienta (A28).

### Klient (R1, R2, R6, Q40)

Vite + React + Tailwind. Text je `ID — title` z exportu.

Kanban: Doing, Next, Waiting, Backlog. Sloupec Done se nestaví. Radar, Chybně zadané, Mapa, seznam, Detail, Nový a Úklid iterují jen řádky exportu. Archivní karta, read-only režim ani „Otevřít celý task“ pro archiv se nestaví.

Úklid přidá otevřeného potomka, kterého chod vidí mezi otevřenými řádky. Done a archivní potomek v náhledu není. Serverové 400 pro dítě za archivním hopem se ukáže jako B56; ten otevřený task v seznamu je, protože sám Done není.

Ostatní chování Q2–Q33, Q35, Q36 a C1–C8 zůstává: dialog Q9, panel A20, předvyplnění review, tři pořadí, rodina nad 80, `written` / `failed` / `pending`.

### Docs

`vps/second-brain-dashboard/README.md` — třetí Coolify app, prohlížeč bere export bez zavřených, vault v kontejneru není.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | Dvě červené chyby, jen `no_date`, `stale`, `stale_unknown` | Chybně zadané = 1. Stale = 1. `no_date` je dlaždice Bez termínu | R2 | T1, T8 |
| B2 | Next bez data; Doing bez deadlinu; prošlý deadline; prošlá review | Bez termínu; Doing; jen Overdue; jen K rozhodnutí | R2, R7 | T1 |
| B3 | `hierarchy: true` jen u jednoho slugu | `story_no_epic` jen tam | R2 | T1 |
| B4 | V serverovém exportu s N=7 je parent Done v archivu, dítě má `parse_errors` `parent_closed`. Prohlížeč dostane N=0, parent v něm není | `parent_closed` se přeskočí. Červený důvod je jen `parent_missing_or_closed`. Obrazovka toho Done parenta neukáže. Dlaždice počítá task jednou | R2, R1 | T1, T8 |
| B5 | Pauza vypnutá. Zrušit otevřenou story. Otevřené děti ve stejném projektu, v jiném a v pauze | náhled má ty otevřené děti jako Cancelled, checkbox nejde vypnout. Done dítě v náhledu není | R6 | T2, T8 |
| B6 | Fronta přes víkend, svátek a 24. 12. Pauznutý otevřený task má review | checkbox zapnutý ty dny vynechá. Pauznutý den obsadí | R6 | T3 |
| B7 | Řádek s novým datem a starým review jinde | obsadí jen nový den | R6 | T3 |
| B8 | (1) jedna neshoda oid. (2) `C-2` a `C-10` nesedí, `C-A` sedí | (1) 409, `failures` má jeden prvek. (2) `C-10` pak `C-2`. `write_text` se nezavolá | R4 | T4 |
| B9 | Druhý `write_text` v session hodí `DriveConflictError`, aktuální oid je `oid-new` | 409 `oid_mismatch`. `detail.failures` je jeden prvek `{id, path, oid: oid-new}`, stejný tvar jako B8. `oid` jen na vrcholu se nepoužije. Session necommitne, první soubor té session je zpět na HEAD. MCP vrátí `CallToolResult`, ne text `Error executing tool`. HTTP není 500 | R4 | T4 |
| B10 | Dávka bez oid; oid jen u první položky | první projde; druhá 400 i na sucho | R4 | T4 |
| B11 | Jeden rodič, otevřené dítě v exportu N=7 není v dávce; oba Done; čistý Done bez dětí | první 400 s `parent_id` a `child_ids`, a to i na sucho, bez 503 `vault_flock_busy`; druhé suché vrátí count; třetí zapíše | R6 | T5 |
| B12 | `update_task` story s dítětem v množině N=7 na Done, patch je jen `status`; story bez dítěte | první 400 bez druhého zámku, i když `needs_forest` pro čisté Done vrací false; druhé Done a `evaluate_deadline_order` se nevolá. `iter_active_tasks` u čistého Done je 0 | R6 | T5 |
| B13 | Deadline a staré review; smazané `waitUntil` při Waiting; title u Waiting s datem | první zapíše deadline a prázdné review; druhý 400; třetí title | R5 | T6 |
| B14 | Create Waiting bez `waitUntil`; sucho s `waitUntil` a `detail`; zápis s deadlinem a review | 400 a soubor nevznikne; sucho vrátí id; ostrý zápis má `detail` a prázdné review | R1, R5 | T6 |
| B15 | MCP `bulk_update` se špatným oid před zápisem i se závodem v `write_text` | obě jsou `CallToolResult` a `oid_mismatch` | R4 | T4 |
| B16 | Deadline včera; review včera; Waiting s review včera | False; True; False | R7 | T7 |
| B17 | Bez cookie; cizí e-mail; patch s `focus`; jeden task | 401; 403; patch bez `focus`; volá se PATCH | R3 | T9 |
| B18 | Druhá dávka 409, pak stejný řez s 404 a s 500. První dávka už 200 a její řádky jsou teď Done | `written` je počet a id bez karet. Done se nevykreslí. `failed` a `pending`, které v exportu zůstaly otevřené, zůstanou předvybrané. Třetí dávka se nevolá. U 409 se `expect_oid` vymění za `failures[].oid`. Další klik teprve zapíše. Dialog Q9 se neukáže. Náhled zůstane, dokud `failed` nebo `pending` není prázdné | R4, R6 | T8, T9 |
| B19 | Propose bez apply; tři limity focusu; `cas_conflict` | vlastní text; „Přesto uložit“ se neotevře | R5 | T8, T10 |
| B20 | Prázdný export | Radar nuly, HTTP 200 | R1 | T1, T8 |
| B21 | Export N=0 obsahuje jen otevřené. Vedle toho ve vaultu leží Done a Cancelled | v prohlížeči nejsou. Žádná obrazovka je neukáže. Kanban sloupec Done nemá. Do obsazenosti se nepočítají | R1 | T3, T8 |
| B22 | Typeahead, epic jiného aktivního projektu a epic pauzy | při vypnuté pauzně jen aktivní epic, text `ID — title` | R1 | T8 |
| B23 | Dvě stejná id; 81 položek; sucho | 400 `duplicate_id` a `batch_too_large` | R4 | T4 |
| B24 | Epic ve focusu; story s otevřeným taskem; recurring; Waiting; dítě jen v pauze | sloty počítají recurring a story s dítětem jen v pauze | R2 | T1, T8 |
| B25 | Drop mezi Doing a Next | patch má `status` a nemá `parent` | R1 | T8 |
| B26 | Dva projekty, jeden `paused` | přepínač je schová a po zapnutí ukáže. Focus se nezvedne | R1 | T8 |
| B27 | Hotovo na listu ve `02-PROJEKTY/<slug>/tasks` bez dětí; Doing s deadlinem; prázdné potvrzení bez deadlinu | Hotovo je PATCH jen `{status: Done}`. Prázdné potvrzení Brain nevolá. Sloupec Done se k tomu nepoužije | R1, R5 | T8 |
| B28 | Focus story s otevřeným taskem; 11. slot; 6. epic; špatný oid | 403 a 409 `cas_conflict` podle dnešních reasonů | R5 | T10 |
| B29 | Waiting bez `waitUntil` na create i na patch | 400 `waiting_no_waituntil` | R5 | T6 |
| B30 | Detail a kanban jeden task; úklid dva | PATCH a `POST /v1/tasks/bulk` | R3 | T9 |
| B31 | Suchý bulk: otevřené dítě; Waiting bez data; duplicita; 81; špatné oid | stejné 400 nebo 409 jako ostrý zápis. Dítě nevrátí 503 `vault_flock_busy` | R4, R6 | T4, T5, T6 |
| B32 | `2026-10-19T22:30:00Z`, deadline `2026-10-19` | den Prahy je `2026-10-20`, task je Overdue | R2 | T1 |
| B33 | Create s `detail`, deadline a review | soubor má `detail` a prázdné review | R1, R5 | T6 |
| B34 | Jeden task, 409 `oid_mismatch`, uživatel měnil title | dialog Q9. „Přesto uložit“ pošle title a oid z 409. „Upravit“ Brain nevolá | R4 | T8, T9 |
| B35 | Doing bez deadlinu; Waiting bez data; Next bez data | první dva request nesloží; Next se odešle | R5 | T8, T9 |
| B36 | Řetězec na pěti obrazovkách tasků | filtr je sdílený. Lišta projektů tasky nehledá | R2 | T8 |
| B37 | Nový task, pauza vypnutá | pauznutý projekt v selectu není | R1 | T8 |
| B38 | Max 1, Od `2026-11-09`, Do `2026-11-13`. `B-E` slug `proj-b`, epic, parent prázdný, updated `2026-01-01`, score prázdné, ve frontě není. Fronta `project_epic`: `A-X` `proj-a` epic updated `2026-01-01` score prázdné; `A-T0` až `A-T2` task parent `A-X`, updated `2026-02-01`, `2026-03-01`, `2026-04-01`; `B-T1` `proj-b` task parent `B-E` updated `2026-01-01`. `priority`: `S-OLD` a `S-NEW` score 10, updated `2026-01-01` a `2026-06-01`; `S-MISS` score 10, updated chybí; `S-LOW` score 0; `S-EMPTY` score prázdné. `age`: `Z-OLD` `2026-01-01`, `Z-NEW` `2026-06-01`, `Z-A` a `Z-B` updated chybí | dny `2026-11-09` až `2026-11-13` v pořadí A17. `B-E` pořadí nemění. Score 0 jde před prázdné | R6 | T3 |
| B39 | Fronta není prázdná, jeden den se nevejde, max 0, Od po Do | request neodejde | R6 | T3, T8 |
| B40 | Deadline dítěte po deadlinu epicu, otevřená story bez deadlinu mostí, stejný den a review | panel ukáže jen nerovnost. „Přesto uložit“ není | R4 | T8, T9 |
| B41 | Story na Done, otevřené dítě v pauze, oba otevřené v exportu prohlížeče | request se nesloží. Dítě se samo nezavře | R6 | T5, T8 |
| B42 | Zavřený řádek v náhledu uvolní den. Jeden task má deadline i review v jeden den | den se uvolní. V jednom dni přidá task nejvýš 1 | R6 | T3, T8 |
| B43 | Ponechat na dítěti ustoupí bližšímu Zrušit | status je vidět před potvrzením. Ponechat den nepotřebuje | R6 | T2, T8 |
| B44 | (1) Story Done pořád ve složce `tasks`, export N=7 ji vynechá. (2) Story v archivu v okně 7 dní, dávka zavírá jen epic, otevřené dítě T v dávce není | (1) 400 kvůli T není. (2) server vrátí 400, rodič je epic, `child_ids` obsahuje T, story ve `failures` není. Prohlížeč T do náhledu epicu sám nepřidá, protože archivní hop v jeho exportu není. T jako otevřený řádek v seznamu Úklidu je | R6 | T2, T5 |
| B45 | Předek a 80 zamčených potomků | nic neodejde, ani suchý běh | R6 | T8 |
| B46 | Doing bez deadlinu a Waiting bez `waitUntil` | Ponechat se nenabídne. Zrušit a Hotovo zůstanou | R5, R6 | T8 |
| B47 | Nový task proti deadlinu parenta | 409, soubor nevznikne, dialog Q9 se neotevře | R1, R4 | T6, T8 |
| B48 | OWN `2026-11-08`, pole pro výběr `2026-11-12`, FILL bez data, fronta po vyplnění prázdná, obsazenost `2026-11-08` je 2 | zápis odejít smí. V mapě je `2026-11-08` i `2026-11-12`. Prázdné Od při neprázdné frontě neodejde | R6 | T3, T8 |
| B49 | Zamčený potomek, uživatel přepne na Hotovo | patch je jen status. Staré review v patchi není | R6 | T2, T8 |
| B50 | Done story jen v archivu, dítě má pozdější deadline | server 409 `deadline_order` pro ten pár nevrátí | R4 | T6, T8 |
| B51 | Dva rodiče, děti `C-A` a `C-10`/`C-2` | HTTP 400, nic se nezapíše. `failures` jen, `C-10` před `C-2` | R6 | T5 |
| B52 | Done story pořád ve složce `tasks`, dítě má pozdější deadline | první požadavek odejde, 409, panel z `detail`. Automatický druhý request ne. Nové Uložit je nový požadavek | R4 | T6, T8, T9 |
| B53 | Review `2026-11-03`, `updated` `2026-10-01`. Přepis na `2026-11-15`. Smazání. Potvrzení beze změny | přepis je vlastní datum. Po smazání starý den v mapě není. Potvrzení nechá `updated` `2026-10-01` | R6 | T2, T3, T5, T8 |
| B54 | `E-1` a `S-1` se zavírají, `T-1` pod `S-1`. (3) `T-1` je Done a `dry_run=false` | (1)(2) 400, `failures` `E-1` pak `S-1`, `T-1` v každém `child_ids` jednou, bez 503. (3) soubory jsou Cancelled, Done a Done | R6 | T5 |
| B55 | Smazání, přepnutí, ruční datum, refresh, nové otevření | smazání a ruční datum přežijí refresh. Nové otevření předvyplní znovu | R6 | T8 |
| B56 | 400 otevřeného dítěte, jeden rodič a dva | obrazovka i výběr zůstanou. Text je `ID — title` z exportu prohlížeče. Dialog oid se neukáže | R6 | T8, T9 |
| B57 | Export pro prohlížeč je N=0 a ve vaultu je `07-ARCHIV/tasks-done/finance/X.md`. Někdo přesto pošle PATCH s tím `path`. Task `02-PROJEKTY/finance/tasks/Y.md` dostane Hotovo | X v žádné obrazovce není. PATCH i bulk i focus na ten path jsou 400 `archive_readonly` a Brain se nezavolá. Y odešle PATCH jen `{status: Done}` | R1, R4 | T8, T9 |

Checklist A: authn B17. RBAC netýká se. Validace B13, B14, B23, B29, B31, B44, B51, B54, B57. Prázdný výsledek B20. Idempotence suchých běhů B8, B11, B31, B54. Částečný zápis B9, B18, B39, B45. Tvar chyby: bulk `oid_mismatch` vždy `detail.failures` (B8, B9). Jeden rodič `parent_id` a `child_ids` (B11). Archiv `archive_readonly` (B57). Side effect: prohlížeč vault neotevírá, vnořený export zámek nebere podruhé (B11). Tiché ořezání: strop 80 je odmítnutí. Časová zóna Praha, B32. CAS B8, B9, B34. Kompatibilita: bulk bez oid (B10), `deadline_order` zůstává na `iter_active_tasks` (B50, B52).

## Výkonový rozpočet (P)

1. SQL: netýká se.
2. Indexy: netýká se.
3. N+1: prohlížeč jedno `GET /v1/tasks/export?include_closed_days=0` a znovu po úspěchu. Dialog Q9 přidá jeden item. Úklid je sekvence bulk, ne paralelně. Kontrola dětí je jedno `task_export.export_tasks(vault, include_closed_days=7)` uvnitř už otevřené session. Druhý `brain_vault` se nezaloží. `deadline_order` dál čte `iter_active_tasks` v téže session.
4. Payload: export otevřených tasků je menší než export s oknem 7 dní. Plán exportu uvádí ~600 otevřených a 250–400 kB pro N=0. `failures` jsou id, ne těla.
5. Ořez: strop exportu se nezavádí. Strop 80 je odmítnutí. Rozprostření, které se nevejde, nezapíše první N.
6. Cache: BFF export nekešuje. Lokální datum nezapsaného řádku refresh nepřepíše (B55).
7. Latence: strop pod 1000 ms platí pro N=0 a to je volání prohlížeče. Mutace k tomu v téže session přečte i archiv okna 7 dní, pořád pod jedním zámkem.
8. Archiv: prohlížeč ho nedostane. Server ho čte jen kvůli hopu otevřeného dítěte. Terminál ve složce `tasks` v exportu N=0 není hned, ještě než ho `archive_done_tasks` přesune. `updated` se kvůli zobrazení nedoplňuje.
9. Zámek: jeden flock session. Vnořený export ho nežádá znovu.
10. Paměť: jeden export otevřených tasků v prohlížeči a mapa lokálního data náhledu.
11. Externí volání: Google jen při loginu. Brain REST ze serveru. Allfred, Slack a Gmail se nevolají.

## Testy (T#)

| T# | Typ | Owner | Soubor | Co ověřuje |
|---|---|---|---|---|
| T1 | vitest | gate | `web/src/classify.test.js`, `focusSlots.test.js` | B1–B4, B20, B24, B32 |
| T2 | vitest | gate | `web/src/writes.test.js` | B5, B25, B41, B43, B44, B49, B53. Done potomek se do náhledu nepřidá |
| T3 | vitest | gate | `web/src/spread.test.js` | B6, B7, B21, B38, B39, B42, B48, B53. `B-E` má updated `2026-01-01` a prázdné score |
| T4 | pytest | gate | `vps/second-brain-brain/tests/test_bulk_oid.py` | B8, B9, B10, B15. B9 čeká 409 a `detail.failures`, ne 500 |
| T5 | pytest | gate | `vps/second-brain-brain/tests/test_hierarchy_contract.py` | B11, B12, B31, B44, B51, B53, B54. Vault v testu je ten, který nástroj už dostal. Druhé otevření se nevolá |
| T6 | pytest | gate | `vps/second-brain-brain/tests/test_create_and_bulk.py` | B13, B14, B29, B33, B47, B50, B52 |
| T7 | pytest | gate | `vps/second-brain-hub/tests/test_today_priority.py` | B16 |
| T8 | vitest + Testing Library | gate | `web/src/ui/*.test.jsx` | B4, B5, B18, B21, B27, B34, B40, B48, B52, B55–B57. Sloupec Done v DOM není. Archivní id na obrazovce není |
| T9 | pytest | gate | `bff/tests/test_bff.py` | B17, B18, B30, B52, B56, B57. Export z BFF jde s `include_closed_days=0`. Archivní PATCH Brain mock nezavolá |
| T10 | pytest | gate | `bff/tests/test_bff.py` | B19, B28 |
| T11 | ruční po deployi | gate (QA) | curl | `/healthz` 200. `/api/export` bez cookie 401. Kontejner nemá `/data/vault` |
| T12 | ruční suchý běh | gate (QA) | bulk `dry_run=true` se špatným oid | 409, hlava vaultu se nezmění |

Playwright-T6-full: netýká se. `TESTER: přeskočeno (profil SECOND_BRAIN)`.

Lokální gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`, pytest brainu a BFF, `npm test` a `npm run build` ve `web`. T11 a T12 až po deployi. T12 jen suchý běh.

## Pořadí implementace

Start až když je follow-up pipeline DONE.

F1 — T7 a `needs_decision`.

F2 — T4, T5, T6. Brain: exclusive deadline, Waiting, kontrola dětí přes `task_export.export_tasks(vault, …)` v otevřené session, `expect_oid` do `write_text`, 409 se `detail.failures`, všechny neshody oid, REST bulk. Množina `deadline_order` se nemění.

F3 — T1, T2, T3. Klasifikace a rozprostření nad exportem bez terminálu. Na F2 nezávisí.

F4 — BFF s exportem N=0, `archive_readonly` a zastavením dávek, T9, T10.

F5 — Obrazovky bez sloupce Done a bez archivních karet, T8.

F6 — Dockerfile, setup, README, redirect URI (A28).

F7 — T11 a suchý T12.

Žádný zápis Done nebo Cancelled do živého vaultu v gate.

## Rizika a zpětná kompatibilita

1. `needs_decision` přestane obsahovat prošlý deadline. Overdue v dashboardu ty tasky má dál.
2. `bulk_update` bez oid se chová jako dnes, kromě nových 400. Víc neshod oid vrací celý seznam (B8). Závod v `write_text` nově vrací 409 místo 500 (B9).
3. Čisté Done čte export N=7 na už otevřeném vaultu. `iter_active_tasks` se kvůli němu nevolá. `deadline_order` se u čistého Done nepočítá.
4. Otevřené dítě za archivním hopem server pořád ohlásí (B44). Prohlížeč ho do náhledu epicu sám nepřidá, protože hop v jeho datech není. V seznamu Úklidu ten otevřený task je.
5. Mezi dávkami po 40 už je commit. Další chyba ho nevrací (B18).
6. Service token umí totéž co cron. Archivní zápis BFF odmítne dřív (B57).
7. Git commit nese autora Brainu.
8. `set_focus` při `cas_conflict` nemá „Přesto uložit“.
9. `hierarchy: true` rozsvítí `story_no_epic` i tam, kde to dřív pětice přeskakovala.
10. Kontrola dětí v session přečte i archiv okna 7 dní. Zámek se kvůli tomu nebere podruhé.
11. Setup sahá do Coolify DB. Chybějící projekt je chyba a INSERT se neprovede.
12. Než BFF volá suchý create, musí být F2 na nasazeném Brainu. `deadline_order` soubor nezaloží, pád je před `mkdir`.
13. Prohlížeč Done jako most `deadline_order` nevidí. Server ho vidí jen když soubor pořád leží ve složce `tasks` (B52).
14. Story, jejíž otevřený task je jen v pauze, ve Focus slotu je (B24).
15. Waiting bez `waitUntil` vrací 400. Zrušit a Hotovo u něj v Úklidu projdou (B46).
16. „Přesto uložit“ u jednoho tasku přepíše jen poslaná pole. Bulk ho nepoužije (A29).
17. Pořadí bere `priority_score` z exportu. `0` je skóre (B38).
18. Zavření parenta vtáhne otevřené potomky, které seznam schoval (B5). Rodina nad 80 se nezapíše (B45).
19. Detail a kanban story s otevřeným dítětem nezavřou, pokud ho chod v datech prohlížeče vidí.
20. Obsazenost umí položit review na den, který zavřený řádek téhož náhledu uvolní (B42).
21. Dítě za Done, který export N=7 vynechal, protože soubor pořád leží ve složce `tasks`, server neohlásí (B44).
22. Dokud je rodina nad 80, neodejde ani nesouvisející Zrušit v tom samém náhledu.
23. Konkrétní datum smí obsadit víkend (B48). Smazané předvyplnění den hned pustí (B53).
24. Po 409 `deadline_order` automatický retry není (B52).
25. Potvrzení předvyplněného dne nemění frontmatter `updated` (B53).
26. Dvě zavírané větve s týmž dítětem shodí celou dávku, dokud ho patch Done nebo Cancelled nekryje (B54).
27. Lokální smazání a ruční datum přežijí refresh nezapsaného řádku (B55).
28. Task právě přepsaný na Done nebo Cancelled po refreshi v přehledu není, protože export N=0 terminál ve složce `tasks` nevrátí (`task_export.py` 87–89), ještě než ho `archive_done_tasks` přesune. Sloupec Done, do kterého by spadl, není. `updated` se kvůli tomu nedoplňuje.

## Otevřené otázky pro uživatele

Žádné.

## Q1–Q39 a C1–C8

| ID | Stav |
|---|---|
| Q1–Q33, Q35, Q36, Q38, Q39 | beze změny vůči předchozímu plánu, kromě míst, která Q40 bere z obrazovky |
| Q34, Q37 | zobrazení padá. Není archivní karta, ani jen ke čtení. BFF 400 `archive_readonly` zůstává (A26, B57) |
| C1–C8 | beze změny. C8 dál sedí: `B-E` má updated `2026-01-01` a prázdné score a ve frontě není |

## C9, C10 a co Q40 bere z obrazovky

| ID | Jak vyřešeno |
|---|---|
| C9 | Vyřešeno. Kontrola otevřeného dítěte volá `task_export.export_tasks(vault, include_closed_days=7)` na vaultu, který `bulk_update` a `update_task` už drží (`task_export.py` 55–63). Nástroj `app.tools.export_tasks.export_tasks` se z té session nevolá (`export_tasks.py` 76–84). Druhý `LOCK_EX` se nezakládá (`git_io.py` 289–303, `vault_deps.py` 138–151). B11, B12, B31, B44 a B54 proto nejsou 503 `vault_flock_busy`. Okno 7 dní na serveru zůstává, protože bez něj archivní story hop není (`task_export.py` 71–91). |
| C10 | Vyřešeno v B9 a A29. Smyčka předá `expect_oid` do `write_text`. `DriveConflictError` se mapuje na 409 `oid_mismatch` jako v `update_task.py` 179–192, ale tělo je `detail.failures` jednoho prvku `{id, path, oid}`, stejné jako B8. `oid` jen na vrcholu by A29 nevyměnilo. Session necommitne. MCP u téhle 409 vrací `CallToolResult`. `main.py` 126–133 tu výjimku pak vrátí jako 409, ne jako 500. |
| Q40 | Vyřešeno v R1, A2, A14, A18, A26, A30, B4, B21 a B57. Done, Cancelled a `path` pod `07-ARCHIV/` prohlížeč nedostane (`include_closed_days=0`). Sloupec Done není. Úklid dál přidá otevřeného potomka a Done nebo archivního potomka neukáže. |
| Co padá | Kanbanový sloupec Done. Read-only karta archivu, její drop, focus a „Otevřít celý task“ (Q34, Q37), protože řádek v prohlížeči není. Věta, že se čerstvé Done ukáže ve sloupci Done, když je `updated` v okně 7 dní. Prohlížečový export s N=7. Automatické přitažení otevřeného dítěte přes archivní hop v prohlížeči; serverový hop a 400 zůstávají (B44). |

## Q41–Q42 (grill g=10, neblokující předpoklady)

| ID | Jak vyřešeno |
|---|---|
| Q41 / A31 | Po zápisu se export načte znovu. Done a Cancelled se nevykreslí. `written` je souhrn bez karet. Označit jako uložený jde jen řádek, který zůstal otevřený. Náhled se zavře, až když `failed` i `pending` jsou prázdné. Detail právě zavřeného úkolu se zavře (A29, B18). |
| Q42 / A32 | Prohlížeč přeskočí `parent_closed` stejně jako `parent_not_found`. Červený důvod je jen `parent_missing_or_closed` (A4, B4). |
| g=10 needs_forest | Kontrola otevřeného dítěte běží i pro čisté Done nebo Cancelled. `needs_forest` pro samotný status Done vrací false (`parent_link.py` 117–123) a B12 se o něj neopře (B12). |
