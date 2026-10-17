# Plán: Hierarchie všude, křížový rodič, zábrana nového projektu

## Zadání a požadavky

R1 — Projekt zůstává domov souboru (složka, prefix ID, hub, pauza, area, materiály). Tagy se nezavádějí. Zdroj: rozhodnutí 1.

R2 — Soubor dítěte zůstává ve složce svého `slug`. `parent` je jen id. Epic nebo story může být v jiném projektu. Zdroj: rozhodnutí 2.

R3 — Epic nemá rodiče. Zdroj: rozhodnutí 3.

R4 — Story má povinně rodiče a ten rodič je epic (libovolný projekt). Story bez epicu nejde založit a parent jí nejde vymazat. Zdroj: rozhodnutí 4.

R5 — Task smí být bez rodiče. Když rodiče má, je to story, klidně v jiném projektu. Task přímo pod epicem nejde. Zdroj: rozhodnutí 5.

R6 — Nový task pod existující story, nová story pod existující epic a nový epic musí jít založit. Zdroj: rozhodnutí 6.

R7 — Existující ploché tasky se hromadně nepřepisují. Dodatečné zařazení je `update_task` s `parent`. Zdroj: rozhodnutí 7.

R8 — MCP nástroje se neslučují. Rozšířit `create_task` a `update_task`. `bulk_update` kontroluje `parent`, když je v patchi. Zdroj: rozhodnutí 8.

R9 — Mapování story bez epicu je hotové ve vaultu (2026-10-16). Tahle pipeline vault znovu nezapisuje a mapování nevymýšlí. Zdroj: rozhodnutí 9.

R10 — Nový task v hierarchii nemá ICE 5/5/5 ani zástupný checkbox `**ID-1**`. Story ICE má. Platí i v projektech, které byly ploché. Zdroj: rozhodnutí 10.

R11 — `get_tree` a `list_children` vrací u uzlu slug projektu, ve kterém soubor leží. Zdroj: rozhodnutí 11.

R12 — Kontrola deadline a rotace vidí předky a potomky i v jiném projektu. Pravidla termínu se nemění. Zdroj: rozhodnutí 12.

R13 — `project_uses_hierarchy` vrací true pro každý projekt. Zdroj: rozhodnutí 13.

R14 — `append_task_note` na story dál založí dítě ve složce té story. Dítě v jiném projektu je `create_task` s jiným slug a `parent`. Zdroj: rozhodnutí 14.

R15 — Zápis, který by založil složku projektu, odmítne slug bez existujícího hub charteru (`02-PROJEKTY/*.md`, frontmatter `slug:`). Nový hub vzniká jen přímým příkazem uživatele, ne přes `create_task`. Chování odmítnout neznámý slug platí; necommitnutý draft v `create_task.py` / `test_create_and_bulk.py` není schválená implementace. Zdroj: rozhodnutí 15.

R16 — `close_task` dál jen navrhuje zavření rodiče. Focus zůstává propose/apply. Neměnit, pokud na ně nové pravidlo nenarazí. Zdroj: rozhodnutí 16.

R17 — Schvalování plánu uživatelem: ne. Po schválení kritikem se implementuje rovnou. Zdroj: rozhodnutí 17.

R18 — Úzký kužel deadline. Dolů se jde jen z měněných id. Sourozenec a bratranec v kuželu nejsou a zápis neshodí. Konflikt mezi předkem a vlastním potomkem měněného uzlu ho shodí. Zdroj: Q1, 2026-10-16.

R19 — Složený les. Po všech patchích `parent` a `type` v jednom requestu overlay na les v paměti (všechny projekty). Kontrola měněného uzlu i jeho přímých aktivních dětí. Jakákoli chyba = 400 a nula zápisů. Děti se nepřepisují. Typové důvody: `parent_not_story`, `parent_not_epic`, `epic_has_no_parent`, `parent_required`. Lookup před tou kontrolou vrací i `parent_not_found`, `parent_ambiguous` a `parent_cycle` (C1): nečitelný neprázdný raw se nesmí složit na prázdné `parent_id`. Zdroj: Q2, doplněno C1.

R20 — Rodič, který leží v `tasks/`, smí být `Done` i `Cancelled`. Archiv vrací `parent_not_found`. Zdroj: Q3.

R21 — Jedno `items` v `create_task` nevidí sourozence z téže dávky. Dopředný odkaz je `parent_not_found` a nula souborů. Zdroj: Q4.

R22 — `projects[].hierarchy` zůstává flag hubu plus natvrdo `rb-universe-development`. `agent_context_build.py` se needituje. Zdroj: Q5.

R23 — Nový epic dál dostane ICE 5/5/5 a `**ID-1**`. Ve F9 se `task-convention.md` sjednotí s tím, co Brain do souboru píše. Zdroj: Q6.

Mimo rozsah: hromadný přepis vaultu a nové přiřazení rodičů; sloučení nebo mazání MCP nástrojů; založení nového project hubu; automatický přesun souboru mezi projekty (nové ID + Cancelled původního); posun checkboxové promoce a 90denního aliasu; změna snapshot pole `projects[].hierarchy` v `agent_context_build.py`; živý zápis do vaultu v testech.

## Předpoklady

A1 — Výsledný pár (`type`, `parent`) se kontroluje, když je v patchi `parent` nebo `type`. Když klíč v patchi není, stávající soubor se nechá být (R7), s jednou výjimkou C2: když je v patchi `status` a výsledný status je aktivní (`Doing|Next|Backlog|Waiting`), na tom uzlu se spustí `parent_type_error`. Parent se při tom nepřepisuje. U `update_task` a `bulk_update` se patche `parent` a `type` nejdřív složí na les (R19). Aktivní dítě = stejná množina. Dítě `Done` nebo `Cancelled` změnu typu rodiče neshodí (B44). `create_task` `items` se na les neskládá (R21). Les se nenačte jen u čistého statusu `Done` nebo `Cancelled` (patch, který má jen `status`). Jakmile je v patchi i `parent`, `type` nebo `deadline`, kontrola běží i při závěrečném `Done`/`Cancelled`: nečitelný parent se nesmaže (C1, B48), story nesmí přijít o povinný epic (R4) a deadline pořád projde kuželem (B49). Kontrola aktivního statusu čte stejný overlay jako složený les, po všech patchích `parent` a `type` v requestu. Request, který `parent` ani `type` nemá, má overlay rovný snímku z disku.

A2 — Rodič smí být `Done` i `Cancelled`, pokud leží v aktivních `tasks/`. Archiv (`07-ARCHIV/tasks-done/`) se jako rodič nebere a vrací `parent_not_found`.

A3 — Stejné `items` v jednom `create_task` nevidí sourozence z téže dávky. Rodič musí už být na disku (R6: „existující“). Epic a story v jednom volání, kde story ukazuje na epic z téže dávky, skončí `parent_not_found` a nezapíše nic.

A4 — Pauza projektu zábranu nemění. Charter se `slug:` stačí, i když je hub `paused`.

A5 — Shoda id je přesná, bez case-fold. `parse_parent_id` se nemění.

A6 — Neprázdný `parent`, který nejde přečíst jako id, není „prázdný rodič“. Platí pro `assign_parent` i pro overlay v `update_task` a `bulk_update` (C1). Lookup surového řetězce, jinak `parent_not_found`. Jinak by překlep u tasku rodiče tiše smazal, protože prázdné `parent_id` u tasku je úspěch. Duplicitní id se počítají na seznamu, dřív než by se id složilo do dictu.

A7 — Dva charter soubory se stejným `slug:` ve frontmatteru jsou `hub_ambiguous` (400), bez zápisu. Draft bere první shodu a mohl by do `project:` napsat špatný hub.

A8 — `project_uses_hierarchy` vrací `True` a argumenty `hub_frontmatter` / `slug_has_epic` ignoruje (signatura zůstává). Snapshot `hierarchy` v `agent_context_build.py` (řádky 228–232) se nemění: pořád hub frontmatter nebo natvrdo `rb-universe-development`.

A9 — Epic dál při založení dostane ICE 5/5/5 a zástupný `**ID-1**` (R23). F9 přepíše v `task-convention.md` buňku ICE u epicu a komentář, že se ICE nevyplňuje, tak, aby říkaly, že Brain při create zapíše `ice_i/c/e: 5` a zástupný checkbox.

A10 — Objem vaultu tenhle běh nespočítal (`OBSIDIAN/` je mimo vyhledávání). Plán počítá s méně než 2 000 soubory v `02-PROJEKTY/*/tasks/*.md` a méně než 80 hub markdowny. Ověření před implementací: `find` nad git vaultem `~/GitHub/second-brain-vault/02-PROJEKTY`. Když je tasků víc než 2 000, pořád jeden průchod `iter_active_tasks` (stejná třída jako dnešní `get_tree`), bez nové cache.

A11 — Úzký kužel (R18). Dolů se jde jen z měněných id, ne z jejich předků. Sourozenec a bratranec v množině `down` nejsou. Nahoru se jde po `parent_id` k předkům. Pár zůstane jen když dítě je v `down` a předek v `up`. Strop 32 kroků. Sourozenec v jiném projektu s deadline po společném předkovi zápis neshodí. Konflikt předka s měněným uzlem nebo s jeho vlastním potomkem ho shodí.

A12 — `append_task_note` bere slug ze složky souboru story, ne z frontmatter `slug`. Stem hubu do `project:` dítěte je návrat `require_project`. `_hub_filename` zůstane v `create_task.py` až do F7 a smaže se v tom samém kroku, ve kterém append přestane importovat (C5).

A13 — Vault kopie konvence (`OBSIDIAN/00-System/…`) se nezapisují (R9). Mění se jen git: rule, šablona, dvě věty ve skillech, a smaže se předčasný řádek výjimky.

## Současný stav (ověřeno v kódu)

- `vps/second-brain-hub/lib/hierarchy.py` 105–121: `project_uses_hierarchy` je true jen pro `rb-universe-development`, hub `hierarchy: true`, nebo `slug_has_epic`. `DEFAULT_HIERARCHY_SLUGS` je jen ten jeden slug (řádek 24).
- `vps/second-brain-brain/app/tools/create_task.py` 154–183: `_slug_is_hierarchy` kvůli tomu čte všechny task soubory slugu a hledá `type: epic`.
- Tamtéž 117–120 a 145–146: při `hierarchy and type==task` se ICE nepíše; checkbox `**ID-1**` se nepíše pro task ani story. Epic ICE i checkbox má. Když `hierarchy` není, píše se obojí.
- Tamtéž 186–206: `_parent_story` hledá rodiče jen v `02-PROJEKTY/{slug}/tasks` dítěte, vyžaduje `type: story`, a při jiném `slug` ve frontmatteru vrací `parent_slug`.
- Tamtéž 324–326: `parent_required` jen když hierarchie a `level==task` a parent je prázdný. Story bez parent projde. Epic s parent se nechá uložit, pokud řetězec náhodou trefí story.
- Tamtéž 37–55 a 310–315: necommitnutý draft `_known_project` vrací 400 `unknown_project`. Regex je přes celý soubor charteru, ne jen frontmatter. `except` při `list_dir` vrací false, tedy taky odmítnutí.
- Tamtéž 58–75: `_hub_filename` bere první soubor, kde je podřetězec `slug: {slug}` (tedy i `slug: finance-ops` pro `finance`).
- Tamtéž 228–260: `_reject_deadline_order` načte jen `02-PROJEKTY/{slug}/tasks`.
- `update_task.py` 61–79 a 121–142: `_deadline_nodes` je jen složka slugu z cesty. Kontrola běží jen když je v patchi `deadline`. `parent` se zapíše bez kontroly typu. Focus pořád 403 (`focus_requires_proposal`).
- `bulk_update.py` 45–68: deadline už jde přes `load_tasks` (celý vault) a při konfliktu nezapíše nic. `parent` v patchi se nekontroluje. `evaluate_deadline_order` ale padá na libovolný konflikt v dodaném seznamu, ne jen na měněném uzlu (`deadline_order.py` 202–224).
- `task_io.py` 86–102: `iter_active_tasks` už chodí přes všechny `02-PROJEKTY/<slug>/tasks/*.md`.
- `lifecycle_recurring.py` 259–273 a 298: rotace už předává všechny aktivní tasky. Cizí konflikt kdekoli ve vaultu tedy rotaci zablokuje už dnes. Pravidlo samo (předek vs. otevřený potomek, stejný den smí, prázdný deadline je mimo pravidlo, `review_deadline` se nepočítá) je v `deadline_order.py` 1–9.
- `task_query.py` 48–64: `card()["project"]` je frontmatter `slug`, ne složka. `children_of` (148–154) vrací jen `id`, `title`, `status`, `deadline`. `tree_for` (178–197) je jeden level dětí plus `open_descendants`, bez slugu. Párování parent id je přes celý seznam, takže křížové dítě už v seznamu je, jen bez slugu složky.
- `append_task_note.py` 204–252: dítě story se zakládá ve `02-PROJEKTY/{fm.slug}/tasks`, `hierarchy=True`, parent `[[id story]]`. Zábranu projektu nevolá. `mkdir_p` je na řádku 251.
- `close_task.py` 100–126: `load_tasks` je celý vault, otevřené dítě v jiném projektu už vidí, rodiče nezavírá, jen `suggest_close_parent`. Focus větev v `close_task` není.
- `today_priority.py` 339–350: `parents_with_open_task_children` bere parent id z celého předaného seznamu. `agent_context_build` ten seznam plní z `iter_active_tasks`. Křížové dítě už story z top fronty schová. Na R16 to nenaráží.
- `mcp_app.py` 198–204 a 288: popisy pořád říkají „Hierarchy level=task requires parent“ a děti bez projektu. REST `CreateTaskBody` (`main.py` 349–360) parent, deadline ani `dry_run` nepředává. MCP `create_task` parent má.
- `test_hierarchy.py` 48–52: `finance` bez flagu je false. `test_create_and_bulk.py` 111–128: neznámý slug a task bez parent v RBU čekají `unknown_project` / `parent_required`.
- `docs/plans/pipeline-exceptions.md` řádek 7: tahle zábrana je zapsaná jako výjimka z pipeline. Tahle pipeline ji přebírá, řádek tam nemá zůstat.
- `task-convention.md` 7–18 a 37: pořád opt-in hierarchie a „story bez parent = standalone“. `second-brain-bootstrap.mdc` v sekci hierarchie totéž (opt-in čtyři slugy, osamocený kus = story bez parent).

## Návrh

### Hub lib — hierarchie (R3, R4, R5, R13)

`vps/second-brain-hub/lib/hierarchy.py`

- Docstring: pravidla platí v každém projektu. Epic nemá parent. Story má parent a je to epic. Task parent nemá, nebo je to story. Id rodiče smí ležet v jiném slugu. Soubor se mezi projekty nestěhuje.
- `project_uses_hierarchy` vrací `True` pro každý neprázdný slug. Argumenty `hub_frontmatter` a `slug_has_epic` zůstanou v signatuře a nic neudělají. Prázdný slug pořád `True` (žádný „flat“ režim). `DEFAULT_HIERARCHY_SLUGS` nechat exportovaný, ale funkce ho nečte.
- Nová čistá funkce `parent_type_error(child_type, child_id, parent_id, parent_type) -> str | None`:
  - `parent_id` prázdné: story → `parent_required`; epic a task → `None`.
  - `parent_id == child_id` → `parent_cycle`.
  - `parent_id` je a `parent_type` je `None` → `parent_not_found` (volající to použije, až lookup nic nenajde).
  - epic a `parent_id` → `epic_has_no_parent`.
  - story a `parent_type != epic` → `parent_not_epic`.
  - task a `parent_type != story` → `parent_not_story`.
  - jinak `None`.
- Nová `parent_chain_cycle(child_id, parent_id, parent_of: dict[str, str | None], limit=32) -> bool`. Jde z `parent_id` po `parent_of`. Když uvidí `child_id` nebo překročí limit (rozbitá data ve vaultu), true. Volající pak `parent_cycle`.

`create_task` po téhle změně `_slug_is_hierarchy` nevolá. Render vždy s `hierarchy=True` (R10 i pro dřív ploché slugy).

### Brain — zábrana projektu (R15, A7, A12)

Nový `vps/second-brain-brain/app/tools/project_guard.py`. F3 smaže jen `_known_project` a přepne create na `require_project`. `_hub_filename` se ve F3 nesmaže, ať `append_task_note.py` dál importuje (C5). Smaže se až ve F7 spolu s přepojením appendu.

- `require_project(vault, slug) -> str` (stem hub souboru):
  - `list_dir("02-PROJEKTY", pattern="*.md", recursive=False)`.
  - Jen soubory bez `/` v `name`.
  - Z textu jen frontmatter mezi prvním a druhým `---`. Když frontmatter není, soubor se nepočítá (slug v těle charteru nestačí).
  - Regex s multiline, protože skutečný charter má `slug:` až pod jinými klíči (`Finance.md`: `---`, `type: project`, `slug: finance`). Vzor: `(?m)^slug:\s*(?:\"<slug>\"|'<slug>'|<slug>)\s*$` se `re.escape` na hodnotě. Tvary `slug: finance` a `slug: "finance"` platí. `slug: finance-ops` pro `finance` ne. Bez `(?m)` by `^` trefil jen začátek řetězce.
  - 0 shod → `BrainClientError` 400 `unknown_project`. 2+ → 400 `hub_ambiguous`. 1 → stem názvu souboru.
  - `list_dir` vyhodí výjimku → stejné `unknown_project` (fail closed, složka nevznikne).
- `folder_slug_from_path(path) -> str`: `02-PROJEKTY/{slug}/tasks/…` → `slug`, jinak `""`.

`create_task` volá `require_project` hned po vstupu do vault session, před `peek_ids`, před `mkdir_p`, i při `dry_run`. `mkdir_p("02-PROJEKTY/{slug}/tasks")` zůstane až po úspěchu, jako dnes na řádku 339.

`append_task_note._spawn_child` před `mkdir_p` zavolá `require_project` na slug ze cesty story. Když cesta slug nemá, 400 `invalid_task_path` (cesta už `_TASK_PATH_RE` pustila, tohle je pojistka). Nová složka jiného slugu z frontmatteru nevznikne.

`scripts/create_project_hub.py` a ruční hub se nemění. To je přímý příkaz, ne Brain.

### Brain — přiřazení rodiče (R2–R8)

Nový `vps/second-brain-brain/app/tools/parent_link.py`:

- `assign_parent(*, child_id, child_type, parent_raw, tasks) -> str`.
  - Prázdný / `parse_parent_id` je `None` a raw je prázdný → `parent_type_error` s `parent_id=None`. Úspěch u tasku a epicu vrací `""`.
  - Neprázdný raw, který parser nesebere → lookup raw řetězce (A6).
  - Lookup: všechny aktivní tasky, jejichž frontmatter `id` se rovná hledanému id. 0 → `parent_not_found`. 2+ → `parent_ambiguous`. 1 → typ z `work_type_of` (chybějící type = task, dnešní `normalise_work_type`).
  - Pak `parent_type_error`. Pak `parent_chain_cycle` nad mapou id → `parent_id_of`.
  - Úspěch vrací `[[<id>]]` bez titulku (stejný tvar jako dnešní create na řádku 204). Slug rodiče se neporovnává. `parent_slug` se přestane vracet.
- Chyby jsou 400, `error_reason` jak v tabulce B#. Nic se nezapisuje.

`create_task` (jeden spec i `items`):

- Jednou `iter_active_tasks` na validaci všech speců.
- `level` epic / story / task jako dnes, jinak 400 `bad_level`.
- Smazat větev `parent_required` pro task (řádky 324–326) a `_parent_story`.
- `child_id` při validaci ještě není. Pro `parent_cycle` proti vlastnímu id použít prázdné child id (nový soubor sebe nemůže trefit). Cyklus přes existující řetěz se řeší, až je parent id znám: story → epic (epic parent prázdný) a task → story cyklus neudělají, pokud typy sedí. Kontrola řetězu u create stejně poběží s `child_id=""`, takže trefí jen smyčku v existujících datech nad zvoleným rodičem (`parent_chain_cycle` s prázdným child id hlídá limit 32). Když řetěz rodiče cyklí sám v sobě, 400 `parent_cycle` a zápis nevznikne.
- `promoted_from` zůstane v jednom slugu (mimo rozsah aliasu).
- Po validaci `peek_ids` a deadline (níže). Až pak zápis. Chyba uprostřed `items` nezapíše ani předchozí položky (dnešní pořadí: nejdřív prepared, pak jeden write cyklus).

`update_task` a `bulk_update` skládají les (R19):

- Jednou načíst všechny aktivní tasky jako seznam. `parent` v patchi projde stejným pořadím jako `assign_parent` (A6): prázdný raw je legitimní prázdný parent; neprázdný raw, který parser nevezme, se hledá jako surový řetězec a nikdy se nesloží na prázdné `parent_id`; shody se počítají na seznamu před dictem (0 → `parent_not_found`, 2+ → `parent_ambiguous`). Teprve potom `parent_type_error`. Na kopii v paměti se všechny patche `parent` a `type` aplikují dřív, než se kontroluje. Disk se při kontrole znovu nečte.
- Pro každé id, kterému se změnil type nebo parent: `parent_type_error` proti typu rodiče v overlay.
- Pro každé id, kterému se změnil type: každé přímé aktivní dítě (i v jiném projektu). Dítě v patchi se bere z overlay. Dítě mimo patch se nezapíše, ale když je po overlay nelegální, request je 400 a nula zápisů.
- Story, která se mění na epic a v patchi má i `parent: ""`: vlastní kontrola projde. Otevřený task dá jen `parent_not_story`, `detail.errors` má jednu položku a `error_reason` se jí rovná, nula zápisů (B43). Done task: story se zapíše jako epic, dítě se nezapíše (B44). Holé `{type: epic}` na story, která rodiče pořád má: děti se projdou i když vlastní kontrola selže. Jsou-li jen Done nebo Cancelled, odpověď má jen `epic_has_no_parent` a seznam jednu položku. Má-li přímý otevřený task, nic se nezapíše a odpověď ukáže obě porušení (B50). `detail.errors` skládá všechny porušené uzly v pořadí položek requestu; uvnitř uzlu nejdřív vlastní důvod, pak přímé otevřené děti seřazené podle id, stejný důvod téhož dítěte jednou, `error_reason` je první položka a `message` u víc důvodů obsahuje kódy ve stejném pořadí. 403, 404 a 409 seznam nemají. Jedno porušení na create, update a bulk, včetně `parent_not_found` a `unknown_project`, nese `detail.errors` s jednou položkou rovnou `error_reason`. Víc porušení skládá seznam stejně a neodporuje B50.
- Když je v patchi `status` a výsledný status je v `Doing|Next|Backlog|Waiting`: `parent_type_error` na tom uzlu proti rodiči v overlay po všech patchích `parent` a `type` v requestu. Request, který `parent` ani `type` nemá, má overlay rovný snímku z disku. Cizí změna typu rodiče v téže dávce se do kontroly počítá (B47). Klíč `parent` se do zápisu nepřidá. Task, jehož rodič je v overlay epic, dostane 400 `parent_not_story` a nula zápisů (C2). Les se nenačte jen když patch má jen `status` a hodnota je `Done` nebo `Cancelled` (B22). Jakmile je v patchi i `parent`, `type` nebo `deadline`, kontrola běží i při závěrečném `Done`/`Cancelled`: nečitelný parent je 400 a v souboru zůstane (B48), story bez epicu je `parent_required` (R4), deadline pořád projde úzkým kuželem (B49).
- Bulk, kde se task P mění na epic a task C (dítě P) na story v jedné dávce: složený les je story pod epicem, zapíšou se oba. Kontrola nesmí číst starý disk.
- `create_task` `items` se neskládá (R21).

`update_task` dál:

- Do patche dát normalizované `[[id]]` nebo prázdné `parent`.
- Zkratka „výsledný parent id je stejné a type se nemění, overlay parent kontrolu nespouští“ platí jen pro větev, kde se změnil parent nebo type. Aktivní status jí nepodléhá. Čistý `status: Next` u Done tasku pod epicem kontrolu spustí a vrátí `parent_not_story` (rozhodnutí 22, B47).
- Focus a `stav*` beze změny (R16).
- CAS `expect_oid` beze změny, kontrola parentu je před `write_text`. `dry_run` při chybě vyhodí, při úspěchu vrátí klíče patche a nezapíše.

`bulk_update`:

- Focus pořád 403 dřív, než se sahá na vault.
- Jednou `load_tasks`. Neznámé id → 404 `not_found`, nula zápisů (dnes).
- Všechny patche `parent` a `type` nejdřív na overlay (R19), pak jedna kontrola. Chyba 400 → nula zápisů. Chyba parent, type nebo status při `dry_run` vyhodí 400 a `write_text` se nevolá, stejně jako u `update_task`. Náhled po deadline a před zápisem se u špatného parentu nevrátí.
- Deadline až po normalizaci parentu (níže). 409 → nula zápisů.
- Když je parent špatně a deadline taky, vrátí se 400 (parent se kontroluje dřív).

### Deadline kužel (R12, A11)

`vps/second-brain-hub/lib/deadline_order.py`

- Beze změny významu: stejný kalendářní den smí, uzel bez deadline je mimo pravidlo a neschová datovaného potomka, smazání deadline smí, `review_deadline` není vstup, `allow_parent_shift` nerelaxuje nerovnost.
- Nový volitelný argument `touched_ids: set[str] | None = None` na `evaluate_deadline_order`. `None` = dnešní chování (jakýkoli konflikt v dodaném seznamu). To drží stávající testy v `test_deadline_order.py`.
- Když je `touched_ids` dané: úzký kužel (R18, A11). Pro každé měněné id `t` dej `t` do `down` i do `up`. Dolů jdi jen z `t` (děti, vnuci), ne z předků. Nahoru jdi po `parent_id` a předky dej do `up`, jejich ostatní děti nepřidávej. Pár zůstane jen když `child_id` je v `down` a `parent_id` v `up`. Strop 32, `seen` proti smyčce. Sourozenec v `down` není.

Volající, kteří načtou celý vault, vždy předají `touched_ids`:

- `create_task._reject_deadline_order`: uzly = všechny aktivní + čerstvé specy s deadline. `touched_ids` = id těch čerstvých, které mají deadline. Rodič v jiném projektu je v seznamu aktivních, takže kužel ho vidí. Bez deadline v dávce se funkce nevolá (dnes řádky 244–245).
- `update_task`: sken všech aktivních místo `_deadline_nodes(vault, slug)`. Když patch mění deadline, nebo se mění parent id, zavolat evaluate. Předtím na kopii uzlu nasadit nový `parent_id` (dataclass je frozen, nová instance). `touched_ids` = `{id souboru}`. Soubor, který v `iter_active_tasks` chybí, se do seznamu přidá jako dnes (řádky 127–128).
- `bulk_update`: uzly ze všech tasků, parent overlay u položek, kde se parent id mění, deadline patches jako dnes. `touched_ids` = id, kde se mění deadline nebo parent id. Prázdná množina → evaluate se nevolá.
- `lifecycle_recurring.rotation_blocked`: seznam pořád všechny aktivní tasky (už je). Přidat `touched_ids={task.task_id}`. `main()` smyčku nepřepisovat: opakované `iter_active_tasks` uvnitř cyklu zůstane, protože po rotaci se změní termín sourozence a další rituál ho musí vidět. Žádný nový průchod vaultu.

### Strom (R11)

`task_query.py`: pomocná `file_project(task) -> str` z `rel_path` (`02-PROJEKTY/{slug}/…`). `children_of` přidá do každého řádku `"project": file_project(...)`. `tree_for` totéž na kořen. Děti to zdědí z `children_of`. Tvar stromu (jeden level + `open_descendants`) se nemění.

`card()["project"]` nechat jako frontmatter slug. `find_tasks(project=…)` by jinak začal filtrovat podle složky a to R11 nechce.

`task_tree.py` bez nové logiky, jen vrací, co vrátí `task_query`. `mcp_app.py` popisy: `list_children` a `get_tree` zmíní `project` jako slug složky souboru. `create_task` popis přepsat: story vyžaduje epic parent kdekoli, task parent volitelný a musí být story, epic parent nemá, neznámý slug je `unknown_project`. `update_task` a `bulk_update` jedna věta, že `parent` / `type` v patchi prochází stejnými pravidly.

### REST (R6)

`main.py` `CreateTaskBody`: přidat `parent: str = ""` a předat ho do `create_task`. Deadline, `items` a `dry_run` na REST nepřidávat (MCP je má, REST je neměl, R6 přes REST potřebuje jen parent). Existující REST klient, který zakládá story bez parent, dostane 400 `parent_required`. To je R4, ne tichá kompatibilita.

### Render (R10)

`_render_task` nechat. Vždy `hierarchy=True`:

- task: bez `ice_*`, bez `- [ ] **ID-1**`.
- story: `ice_i/c/e` 5, bez zástupného checkboxu.
- epic: ICE i `**ID-1**` jako dnes (A9).

### Rotace, close, focus (R12, R16)

- `rotation_blocked` jen `touched_ids`. Pravidlo a marker `deadline_order — rotace přeskočena` (jednou, když už v body je) beze změny.
- `close_task.py` a focus propose/apply se needitují. Křížové dítě už `load_tasks` vidí. Test to zamkne, ať tam někdo později nepřidá filtr slugu.

### Dokumentace konvence (jinak rule odporuje R4/R5/R13)

- `.cursor/rules/second-brain-bootstrap.mdc` sekce hierarchie: opt-in seznam pryč. Pravidla parentu jako R3–R5. Křížový parent. Nový hub ne přes `create_task`. Osamocený kus je `type: task` bez parent, ne story. Existující soubory se hromadně nepřepisují.
- `ŠABLONY/obsidian-templates/task-convention.md` úvod a story parent: story parent je povinný epic, id smí být z jiného projektu; existující story bez parent zůstávají, dokud je někdo neupraví přes `update_task`. Flat task bez parent je povolený v každém projektu. Věta „null = standalone“ pryč. Buňka ICE u epicu a komentář `# ice_*` říkají, že Brain při create zapíše `ice_i/c/e: 5` a `**ID-1**`.
- `ŠABLONY/obsidian-templates/task-template.md` řádek 9: prázdný parent jen u epicu a u `type: task` bez story. Nová story má `[[<epic id>]]`. Řádek 42: totéž, věta „Mimo hierarchy projekty… parent smaž“ pryč.
- `ŠABLONY/skills/agenda-capture/SKILL.md` řádky u `type`, „epic/standalone prázdné“ a „parent jen pokud patří pod epic“: epic má parent prázdný; nová story má vždy epic parent; kus bez story je `type: task` a parent prázdný. Návod nesmí dál radit story bez parentu.
- `ŠABLONY/skills/agenda-work/SKILL.md`: jedna věta, že Brain parent pravidla platí v každém projektu a snapshot `hierarchy` je pořád flag hubu, ne vypínač pravidel.
- `docs/plans/pipeline-exceptions.md`: smazat řádek 2026-10-16 pro `create_task.py` / `test_create_and_bulk.py`. Zábrana už není výjimka, je v tomhle plánu.

Vault, `agent_context_build.py`, promoce, alias, `close_task`, focus: bez editu.

### RB Universe checklisty, které se SECOND_BRAIN netýkají

Alembic, RBAC, Celery, subnav, hub dlaždice, `qa_gate.mjs`, měny a DPH, Pipedrive sync, `data_consistency.py`: netýká se. Důvod u B# níže.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | `project_uses_hierarchy("finance")` i s `hierarchy: false` a `slug_has_epic=False` | `True` | R13 | T1 |
| B2 | `create_task` slug bez charteru (`auto-superb`), i `dry_run` | 400 `unknown_project`, `write_text` ani `mkdir_p` | R15 | T2 |
| B3 | Charter má `slug:` jen v těle, ne ve frontmatteru | 400 `unknown_project` | R15 | T2 |
| B4 | Frontmatter `slug: "finance"` nebo `slug: 'finance'` | projekt známý, stem hubu do `project:` | R15 | T2 |
| B5 | Dva charter soubory se stejným `slug:` | 400 `hub_ambiguous`, bez zápisu | R15, A7 | T2 |
| B6 | `list_dir` hubů vyhodí výjimku | 400 `unknown_project`, bez mkdir | R15 | T2 |
| B7 | Nový epic bez parent, známý slug | soubor ve složce toho slugu, `type: epic`, prázdný parent, ICE 5/5/5 a `**ID-1**` | R3, R6, A9 | T3 |
| B8 | Epic s parent (i když parent je epic) | 400 `epic_has_no_parent`, bez zápisu | R3 | T3 |
| B9 | Story bez parent, libovolný slug včetně dřív plochého | 400 `parent_required`, bez zápisu | R4, R10 | T4 |
| B10 | Story, parent je epic v jiném slugu | zápis ve složce dítěte, `parent: "[[<id epic>]]"`, ICE 5/5/5, bez `**ID-1**` | R2, R4, R6, R10 | T4 |
| B11 | Story, parent je story nebo task | 400 `parent_not_epic` | R4 | T4 |
| B12 | Task bez parent, i slug `rb-universe-development` | zápis, bez `ice_*`, bez `**ID-1**` | R5, R10 | T5 |
| B13 | Task, parent je story v jiném projektu | zápis ve složce tasku, `parent: "[[<id>]]"`, ne `parent_slug` | R2, R5, R6 | T5 |
| B14 | Task, parent je epic | 400 `parent_not_story` | R5 | T5 |
| B15 | Parent id nikde v aktivních `tasks/` (ani v archivu) | 400 `parent_not_found` | R4, R6, A2 | T6 |
| B16 | Dva aktivní soubory se stejným id rodiče, create i update i bulk | 400 `parent_ambiguous`, nula zápisů. Počet shod je na seznamu, ne po složení do dictu | A6, C1 | T6, T7 |
| B17 | `parent` neprázdný a parser ho nevezme a raw id neexistuje. Create, `update_task` i `bulk_update` | 400 `parent_not_found`. U tasku se parent nesmaže | A6, C1 | T6, T7 |
| B18 | `items`: druhá položka ukazuje na epic z první položky téže dávky | 400 `parent_not_found`, nula souborů | A3 | T6 |
| B19 | `update_task` na plochém tasku, `parent` = story v jiném projektu | CAS zápis `parent: "[[id]]"`, soubor zůstane ve své složce | R2, R7 | T7 |
| B20 | `update_task` na story, `parent` prázdné | 400 `parent_required`, soubor beze změny | R4 | T7 |
| B21 | `update_task` jen `{"type":"story"}` a současný parent není epic | 400 `parent_not_epic` nebo `parent_required`, bez zápisu | R4, A1 | T7 |
| B22 | Patch má jen `status` a hodnota je `Done` nebo `Cancelled` | les se nenačte, parent se nekontroluje a nepřepíše | R7, rozhodnutí 21 | T7 |
| B23 | `update_task` / `bulk_update` s `focus` | 403 `focus_requires_proposal`, bez zápisu | R16 | T8 |
| B24 | `bulk_update` dvě položky, u jedné parent špatně | 400, `write_text` nula | R8 | T8 |
| B25 | `bulk_update` parent v pořádku a deadline mimo kužel v pořádku, jinde ve vaultu je starý konflikt | zapíše obě položky | R12, A11 | T9 |
| B26 | Create/update/bulk: dítě s deadline po deadline předka v jiném projektu | 409 `deadline_order`, nula zápisů; stejný den projde; prázdný deadline dítěte projde | R12 | T9 |
| B27 | Posun deadline, který netrefí kužel měněného id, ale jiný pár ve vaultu je rozbitý | zápis projde | R12, A11 | T9 |
| B28 | Rotace: další deadline je po deadline epicu v jiném slugu | `rotation_blocked` true, soubor zůstane v `tasks/`, rodič se neposouvá | R12 | T10 |
| B29 | Rotace: cizí konflikt mimo kužel rituálu | rotace není blokovaná tímto párem | R12, A11 | T10 |
| B30 | `get_tree` / `list_children`: dítě v jiném slugu, frontmatter `slug` lže | uzel má `project` ze složky cesty; dítě v seznamu je | R11 | T11 |
| B31 | `get_tree` neznámé id | 404 `not_found` | R11 | T11 |
| B32 | `list_children` bez dětí | `children: []`, ne 500 | R11 | T11 |
| B33 | `append_task_note` target step na story | dítě ve složce té story, parent id story, bez nové složky | R14 | T12 |
| B34 | Story path ve známém projektu, frontmatter `slug` je neznámý | dítě pořád ve složce path, `mkdir` jiného slugu se nevolá | R14, A12 | T12 |
| B35 | `append` by měl mkdir slugu bez charteru | 400 `unknown_project`, bez zápisu | R15 | T12 |
| B36 | `close_task` story, otevřený task dítě v jiném projektu | 409 `parent_has_open_children`, rodič se nezavře | R16 | T13 |
| B37 | `close_task` poslední task, rodič story v jiném projektu, bez otevřených sourozenců a bez otevřených checkboxů | `suggest_close_parent` true, soubor rodiče se nezmění | R16 | T13 |
| B38 | REST `POST /v1/tasks` s `parent` | tělo pole přijme a `create_task` ho dostane | R6 | T14 |
| B39 | Suchý běh create/update při B2–B21 | stejná chyba nebo náhled, `write_text` se nevolá | R8, R15 | T2, T4, T7 |
| B40 | Existující soubory bez parent | pipeline je nepřepisuje; žádný migrační skript | R7, R9 | T15 |
| B41 | Měním deadline tasku T. Sourozenec S v jiném projektu už má deadline po společném předkovi E. Deadline T po E není | zápis projde. Když deadline potomka T je po E, 409 a nula zápisů | R18 | T9 |
| B42 | `_spawn_child`, charter `Finance.md` / `slug: finance`, vedle `Finance-ops.md` | v těle `project: "[[Finance]]"`, ne prázdné a ne `[[Finance-ops]]` | R14, R15 | T12 |
| B43 | Story se mění na epic a patch má i `parent: ""`. Má otevřený task v jiném projektu | vlastní kontrola projde, 400 `parent_not_story`, nula zápisů, task se nezapíše. Samotné `{type: epic}` bez vyprázdnění parentu je `epic_has_no_parent` i když jsou děti Done | R19, C6 | T8 |
| B44 | Stejná story, patch má `type: epic` a `parent: ""`, task je Done | vlastní kontrola projde, story se zapíše jako epic, Done task se nezapíše | R19, C6 | T8 |
| B45 | Bulk: P je task bez rodiče a mění se na epic, C (dítě P) se v téže dávce mění z tasku na story | zapíšou se oba, kontrola čte overlay, ne starý disk. Když P rodiče má, 400 `epic_has_no_parent` a nula zápisů | R19, C6 | T8 |
| B46 | Rodič v `tasks/` je Done nebo Cancelled | `assign_parent` ho přijme. Stejné id jen v archivu je `parent_not_found` | R20 | T6 |
| B47 | Spojený bulk: první položka mění story na epic bez vyprázdnění parentu, druhá budí její Done task na `status: Next`. Kontrola čte overlay. Samostatný pozdější request jen se `status: Next`, když už je rodič epic | Spojený bulk: 400, nula zápisů, `error_reason` je `epic_has_no_parent`, `detail.errors` je `["epic_has_no_parent", "parent_not_story"]`, `message` jmenuje oba, důvod dítěte je v seznamu jednou. Pozdější request: jen `parent_not_story`, `detail.errors` má jednu položku, parent v souboru tasku se nezmění | R5, rozhodnutí 22 a 24 | T8 |
| B48 | Patch má `status: Done` a nečitelný neprázdný `parent` (`update_task` i `bulk_update`) | 400 `parent_not_found`, nula zápisů, parent v souboru zůstane. Les se načte | C1, rozhodnutí 21 | T7 |
| B49 | Patch má `status: Done` a `deadline` | deadline pořád projde úzkým kuželem. Po předkovi je 409 a nula zápisů. Den, který kužel neporuší, se zapíše | R12, R18, rozhodnutí 21 | T7, T8 |
| B50 | Story se mění na epic, parent v overlay zůstane, přímý otevřený task | 400, nula zápisů. `error_reason` je `epic_has_no_parent`. `detail.errors` je `["epic_has_no_parent", "parent_not_story"]`. `message` jmenuje oba důvody. Dítě Done nebo Cancelled druhou položku nepřidá | rozhodnutí 23 | T8 |
| B51 | Patch `{status: Done, parent: ""}` na story | 400 `parent_required`, nula zápisů | R4, rozhodnutí 21, C8 | T7 |

**Checklist A**

1. Prázdná data — B15, B31, B32. Prázdný seznam dětí není chyba.
2. Chybějící / `None` — prázdný parent (B9, B12, B20), prázdný deadline je povolený a pravidlo ho nebere (B26), chybějící `type` se čte jako task (`normalise_work_type`). `review_deadline` deadline kontrola nečte.
3. Hranice období — fiskální rok se netýká. Deadline je kalendářní den bez času; stejný den smí (B26). Europe/Prague se v `deadline_order` nepoužívá.
4. Měny a DPH — netýká se, žádná částka.
5. Oprávnění — netýká se RBAC. Mutate session a focus 403 zůstávají (B23). Neznámý projekt je 400, ne 403.
6. Stav syncu — netýká se Allfred/Pipedrive. Zdroj je vault v tom samém requestu.
7. Smazané / archivované — archivovaný rodič je `parent_not_found` (B15, A2). `Done` rodič založit smí. Otevřenost potomka pro deadline i close pořád `Doing|Next|Backlog|Waiting`.
8. Duplicity a opakování — `parent_ambiguous` (B16), `hub_ambiguous` (B5), bulk a create all-or-nothing (B18, B24), CAS `expect_oid` beze změny, rotace marker jednou (stávající `if marker not in body`), append `already_present` beze změny.
9. Chyba externí služby — Allfred/Fio/Pipedrive se netýká. Selhání `list_dir` hubů je fail closed (B6), ne tiché založení složky.
10. Zpětná kompatibilita — B40. `parent_required` už neznamená „task bez parent v hierarchickém slugu“, ale „story bez epicu“. `parent_slug` se přestane vracet; křížový parent je úspěch (B13). Do stromu přibude pole `project`. REST story bez parent začne padat na 400. Existující URL a filtry `find_tasks` se nemění, protože `card()["project"]` zůstává frontmatter slug.
11. Konzistence Pipedrive ↔ Allfred — netýká se.

## Výkonový rozpočet (P)

Cron nový průchod vaultu nedostane. `lifecycle_recurring` už na každý hotový rituál volá `iter_active_tasks` (`lifecycle_recurring.py` 298). Tahle změna přidá jen filtr kužele v paměti. Smyčku nehoistovat: po rotaci se musí další rituál podívat na nový deadline.

Les se přeskočí jen u čistého statusu `Done` nebo `Cancelled`, tedy u patche, který má jen `status`. Jakmile je v patchi i `parent`, `type` nebo `deadline`, les se načte i při závěrečném `Done`/`Cancelled`. `require_project` čte jen top-level `02-PROJEKTY/*.md`. `require_project` čte jen top-level `02-PROJEKTY/*.md` (huby, ne tasky).

Create, update a bulk, které parent nebo deadline řeší, zavolají `iter_active_tasks` jednou na request, ne jednou na položku `items`. To je stejný průchod, jaký už dělají `get_tree`, `list_children` a `bulk_update` (`task_catalog.load_tasks` → `iter_active_tasks`).

| Bod checklistu B | create / update / bulk při parent nebo deadline | rotace | get_tree / list_children |
|---|---|---|---|
| 1. Objem | A10: předpoklad < 2 000 task md, < 80 hubů. Ověřit findem výše. Za dva roky pořád jeden průchod, ne N+1. | Beze změny objemu. | Beze změny, už celý vault. |
| 2. Počet dotazů | SQL 0. Vault: 1× list hubů + 1× všechny task soubory. | SQL 0. Žádný nový list. | SQL 0, beze změny. |
| 3. Co se načítá | Celý markdown tasku, protože `parse_task_text` bere i body. Stejně jako dnešní `load_tasks`. Žádný nový sloupec navíc. | Stejný seznam jako dnes. | Beze změny. |
| 4. Externí volání | Žádné. | Žádné. | Žádné. |
| 5. Stránkování | Není seznam pro UI. Strop 2 000 je předpoklad, ne limit v kódu. Nad ním pořád jeden průchod. | netýká se | `list_children` vrací všechny děti jednoho id. To už dnes. Nové pole je jeden slug. |
| 6. Payload | Jeden nový md, řádově kilobajty. Strom: k dnešnímu uzlu přibude řetězec slugu. | Beze změny. | + `project` na uzel. |
| 7. Cache | Žádná. Čte se vault v session, invalidace není potřeba. | Žádná. | Žádná. |
| 8. Násobení | Jeden sken na request. `items` neskenuje znovu. | Stávající sken na rituál zůstává. | Jeden sken, jako dnes. |
| 9. Frontend | netýká se | netýká se | netýká se |
| 10. Worker | netýká se Celery. Cron zápis jen když rotace fakticky běží nebo přidává jeden marker, jako dnes. | netýká se | netýká se |
| 11. Cíl | Stejná třída jako dnešní `get_tree` (jeden `iter_active_tasks` nad git vaultem v kontejneru). Gate je pytest, ne měření `api_ms`. Žádný nový cron scan, takže práh „cron čte celý vault nově“ nenastává. | Beze změny času průchodu. | Beze změny. |

Když find ukáže víc než 2 000 tasků, implementace se nemění. Do plánu se jen doplní naměřený počet. Cache se nezavádí.

## Testy (T#)

Všechno pytest proti fake vaultu / čistým funkcím. Žádný zápis do živého vaultu. Owner = gate. Playwright a Tester se netýkají.

`TESTER: přeskočeno (profil SECOND_BRAIN)`.

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-hub/tests/test_hierarchy.py` | B1. Přepsat `test_project_uses_hierarchy`: každý slug `True`, kwargs ignorovány. `parent_type_error` a `parent_chain_cycle` (self, limit smyčky). |
| T2 | pytest | gate | `vps/second-brain-brain/tests/test_create_and_bulk.py` | B2–B6. Charter jako `Finance.md`: první řádek frontmatteru `type: project`, `slug: finance` až na dalším řádku, a totéž se `slug: "finance"`. U obou tvarů se soubor zapíše. Dva huby. Výjimka `list_dir`. |
| T3 | pytest | gate | `test_create_and_bulk.py` | B7, B8. Epic bez parent se zapíše (zachytit `write_text`). Epic s parent nezapíše. |
| T4 | pytest | gate | `test_create_and_bulk.py` | B9–B11. Smazat očekávání, že task bez parent v RBU je `parent_required`. Story bez parent je `parent_required`. Story pod epicem jiného slugu: cesta dítěte, `[[id]]`, ICE, žádný `**ID-1**`. |
| T5 | pytest | gate | `test_create_and_bulk.py` | B12–B14. Task bez parent ve `finance` i v `rb-universe-development`: bez `ice_`, bez `**ID-1**`. Task pod story jiného projektu. Task pod epicem `parent_not_story`. |
| T6 | pytest | gate | `test_create_and_bulk.py` | B15–B18. Archiv se do fake aktivních tasků nedává. Duplicitní id. Nepopsatelný parent. Dávka epic+story v jednom `items`. |
| T7 | pytest | gate | `vps/second-brain-brain/tests/test_parent_update.py` | B16, B17, B19–B22, B48, B49. Duplicitní id a nečitelný raw na `update_task` i `bulk_update`: `parent_ambiguous` / `parent_not_found`, u tasku parent v souboru zůstane. Čistý `status: Done` les nenačte (B22). `status: Done` plus nečitelný parent je 400 a parent v souboru zůstane (B48). `status: Done` plus deadline po předkovi je 409, den v kuželu se zapíše (B49). Čisté `{status: Done}` na story, která epic už nemá, les nenačte a status se zapíše (B22). Patch `{status: Done, parent: ""}` na story je `parent_required` a nula zápisů (B51). |
| T8 | pytest | gate | `test_create_and_bulk.py` | B23, B24, B43–B45, B47, B49, B50. Focus. Bulk s jedním špatným parentem nezapíše druhou položku. Story → epic v patchi i s `parent: ""` a otevřeným taskem: jen `parent_not_story`, `detail.errors` má jednu položku rovnou `error_reason`, nula zápisů (B43). Stejný patch a Done task: story se zapíše jako epic, task se nezapíše (B44). Holé `{type: epic}` a děti jen Done: jen `epic_has_no_parent`, seznam má jednu položku. Holé `{type: epic}` a otevřený task: `error_reason` je `epic_has_no_parent`, `detail.errors` je `["epic_has_no_parent", "parent_not_story"]`, `message` jmenuje oba, nula zápisů (B50). P v B45 rodiče nemá. Spojený bulk, první položka mění story na epic bez vyprázdnění parentu a druhá budí Done dítě na Next: 400, `error_reason` je `epic_has_no_parent`, `detail.errors` je `["epic_has_no_parent", "parent_not_story"]`, důvod dítěte jednou, nula zápisů (B47). Samostatný pozdější `status: Next` volá `update_task` a je jen `parent_not_story`, `detail.errors` má jednu položku. `status: Done` plus deadline v bulk pořád projde kuželem (B49). `bulk_update` se špatným parentem a `dry_run: true` vyhodí 400, ne úspěšný náhled, a `write_text` se nevolá. |
| T9 | pytest | gate | `vps/second-brain-hub/tests/test_deadline_order.py` + brain create/update/bulk | B25–B27. `touched_ids=None` pořád shodí jakýkoli konflikt v seznamu (staré testy). S `touched_ids` cizí pár ne. Křížový předek s dřívějším dnem shodí create i update i bulk, `write_text` nula. Stejný den projde. |
| T10 | pytest | gate | `vps/second-brain-hub/tests/test_rotation_and_autodone.py` | B28, B29. Epic v jiném `rel_path` slugu. Cizí pár mimo kužel neblokuje. |
| T11 | pytest | gate | `vps/second-brain-hub/tests/test_task_query.py` | B30–B32. `tree_for` / `children_of`: `project` ze `rel_path`, ne z fm `slug`. Dítě jiného slugu je v dětech. `tree_for` neznámého id je `None` (nástroj z toho dělá 404; brain test jen když už obal existuje, jinak stačí `task_query`). |
| T12 | pytest | gate | `vps/second-brain-brain/tests/test_append_task_note.py` nebo `test_create_and_bulk.py` | B33–B35. Cesta dítěte. Lživý fm slug nezaloží složku. Slug bez charteru 400. |
| T13 | pytest | gate | `vps/second-brain-brain/tests/test_edit_and_close.py` | B36, B37. Bez editu `close_task.py`. |
| T14 | pytest | gate | `test_create_and_bulk.py` nebo vedle `test_f3_routes.py` | B38. `CreateTaskBody` má `parent` a default `""`. |
| T15 | pytest | gate | žádný nový skript | B40. Diff nesmí obsahovat skript, který přepisuje `02-PROJEKTY/**/tasks`. |
| T16 | ruční při F9 | gate | capture, task-template, task-convention | C4, R23. V capture nejsou věty „standalone prázdné“ a „parent pokud patří pod epic“. V šabloně řádek 9 ani 42 neradí prázdný parent u nové story. Buňka ICE epicu říká 5/5/5 a `**ID-1**`. |

Lokální gate po implementaci: `python3 -m pytest vps/second-brain-hub/tests vps/second-brain-brain/tests scripts/tests -q`.

QA po nasazení: obraz podle `vps/second-brain-hub/README.md` (Git → Coolify) pro `second-brain-hub` a `second-brain-brain`, brain healthz a seznam tools. Chování z T# se znovu nespouští proti živému vaultu.

## Pořadí implementace

F1 — `hierarchy.py`: `project_uses_hierarchy` vždy true, `parent_type_error`, `parent_chain_cycle`. T1. Na tom stojí zbytek.

F2 — `deadline_order.py`: `touched_ids` a kužel. T9 část v hub testu. Stávající testy bez argumentu musí projít beze změny chování.

F3 — `project_guard.py` a create na `require_project`. Smazat jen `_known_project`. `_hub_filename` nechat (C5). T2 včetně charteru se slugem až pod `type:`.

F4 — `parent_link.py` + `create_task`: smazat `_slug_is_hierarchy` a `_parent_story`, vždy `hierarchy=True`, jeden `iter_active_tasks`, deadline kužel. T3–T6, T9 create. Závisí na F1–F3.

F5 — `update_task` a `bulk_update`. T7–T9. Závisí na F1 a F2. Může běžet vedle F4 až po F1 a F2.

F6 — `task_query` `file_project`, popisy v `mcp_app.py`, `CreateTaskBody.parent`. T11, T14. Nezávislé na F4, až na to, že popis create musí sedět na F4.

F7 — `append_task_note` na slug z cesty a `require_project`. V tom samém kroku smazat `_hub_filename` a import. T12. Mezi F3 a F7 pytest appendu nesmí spadnout na importu.

F8 — `rotation_blocked(..., touched_ids)`. T10. Závisí na F2.

F9 — rule, `task-convention.md` (ICE epicu), `task-template.md` řádky 9 a 42, `agenda-capture` řádky u type / standalone / parent, věta v `agenda-work`, smazat řádek výjimky. T16.

F10 — celý pytest gate z briefu.

`close_task.py` a focus se needitují. T13 jen test.

## Rizika a zpětná kompatibilita

1. `parent_required` mění význam. Klient, který v hierarchickém projektu zakládal task bez parent, dostával 400 a nově uspěje. Klient, který zakládal story bez parent (výchozí `level=story` na MCP i REST), nově dostane 400. REST pole `parent` to odblokuje.

2. `parent_slug` zmizí. Křížový parent, který dnes padá, projde. To je R2.

3. `evaluate_deadline_order` bez `touched_ids` se nemění. Volající nad celým vaultem (`bulk` už dnes, rotace už dnes, create/update nově) musí `touched_ids` předat. Když ho zapomenou, starý konflikt kdekoli ve vaultu shodí zápis. Testy T9 a T10 to hlídají.

4. Kužel naopak přestane blokovat rotaci a bulk kvůli konfliktu, který se měněného uzlu netýká. Dřív rotace s celým vaultem takový pár viděla. Pravidlo předek/potomek se nemění. Mění se dosah odmítnutí.

5. Normalizace parentu na `[[id]]` při patchi zahodí titulek ve wikilinku. `parse_parent_id` titulek nepotřebuje. Soubory, kterých se patch netýká, si titulek nechají.

6. Dva soubory se stejným id: parent lookup spadne na `parent_ambiguous`, deadline index v `_index` pořád nechá poslední (beze změny). Vznikne situace, kdy deadline kontrola a parent lookup vidí data jinak, dokud se duplicita nespraví. Zápis parentu na duplicitní id neprojde, takže se dál nerozšiřuje.

7. Snapshot `hierarchy` a skill, který čte jen ten flag, pořád ukáže „ne“ u projektu bez flagu v hubu. Pravidla Brain ale platí. F9 přidává větu do `agenda-work`, flag v `agent_context_build.py` se nemění (A8).

8. `parents_with_open_task_children` už křížové dítě vidí. Story s otevřeným taskem v jiném projektu vypadne z top fronty už dnes. Plán to neoslabuje ani neposiluje.

9. `_hub_filename` dnes může přilepit špatný hub přes prefix `slug:`. `require_project` to nahradí přesnou shodou a při dvou charterech spadne. Existující soubory se samy neopraví.

10. `append_task_note` přestane poslouchat fm `slug`, když se liší od složky. Dítě zůstane u souboru story. Kdo spoléhal na fm slug jako cílovou složku, dostane jinou cestu. R14 chce složku souboru.

11. Git diff nesmí obsahovat cizí špinavé soubory mimo tenhle seznam. Řádek v `pipeline-exceptions.md` se maže, protože výjimka končí.

12. MCP konzumenti dostanou navíc `project` ve stromu. Staré pole zůstávají. Popis nástroje `create_task` se mění, nástroj se nemaže a neslučuje.

## Otevřené otázky pro uživatele

Žádné. Q1–Q6 z prvního grillu jsou R18–R23. Grill kolo 3 je rozhodnutí 21 (čistý status) a 22 (overlay). C1–C5 zůstávají.
