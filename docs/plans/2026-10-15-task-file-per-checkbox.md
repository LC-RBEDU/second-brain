# Každý úkol jako soubor

## Obsidian pryč

Uživatel (grill g=1, Q1): Obsidian se nepoužívá, vše je v Gitu. Cokoliv, co počítá s Obsidianem jako s místem, kde se úkol edituje, se má smazat, ať to nemate. Ruční edit v Obsidianu není výjimka z kontroly termínů.

Fakt z runbooku, ať se nesmaže vault: SSOT je git repo `second-brain-vault`. Složka `OBSIDIAN/` na Drive je legacy mirror, ne místo zápisu. Obsidian jako aplikace je v runbooku volitelný pull-only klient. Mazání znamená klienta, dual-writer a texty, které ho berou jako editor. Markdown úkolů v gitu zůstává.

## Závislosti termínů (uzavřeno, grill g=1)

- **Q1 = A + varování.** Zápis, který by dal rodiči deadline dřív než nejpozdější deadline otevřeného potomka, neprojde. Stejný den projde. Rodič se sám neposune. Varování dá na výběr: posunout deadline dítěte na dřív, nebo člověk výslovně dovolí posunout deadline rodiče. Až to dovolí, smí se rodič posunout.
- **Q2 = A.** Hlídá se jen `deadline`. `review_deadline` do nerovnosti nepatří. Rodič bez deadline je mimo pravidlo. Smazat deadline rodiče jde.
- **Q3 = B.** Každý předek proti všem otevřeným potomkům, kteří deadline mají. Story bez data task před epicem neschová.
- **Q4 = B.** Story s právě jedním otevřeným checkboxem: `deadline` i `review_deadline` přejdou na ten task a ze story zmizí. Víc otevřených checkboxů: datum zůstane na story, dry-run to vypíše, na tasky se nekopíruje.
- **Q5 předpoklad.** Do maxima jdou Doing, Next, Backlog i Waiting, pokud mají deadline. Done a Cancelled vypadnou a rodiče se kvůli tomu neposouvají. Bez deadline se uzel nepočítá. Checkbox `[x]` ve story do maxima nejde.

Rozhodnutí z chatu: tři vrstvy souborů (epic → story jako kontejner → task). Status, focus a další práce žijí na tasku. Převést jen otevřené checkboxy. Hotové `[x]` zůstanou ve story jako historie.

Dnešek: v hierarchii je práce checkbox `**ID-N**` v těle story (`vps/second-brain-hub/lib/hierarchy.py`). Hubové pohledy berou `type == story` (`ŠABLONY/obsidian-templates/All-tasks-hierarchy.base`). `type: task` se v hierarchii záměrně nezakládá, protože na hubu není řádek práce. Otevřených checkboxů s id je teď **346** ve čtyřech projektech (finance 98, rb-universe-development 92, firemni-procesy 85, it-ai-data 71). Odškrtnutých, které zůstanou, je 48.

Realizace až příkazem `/rbu-pipeline` (profil SECOND_BRAIN), po grillu. Vault se při testech a při deployi nezapisuje. Zápis 346 souborů je až dry-run a samostatné „apply“.

## Identita

- Nový soubor dostane další `PREFIX-T<N>` ze společného čítače (`next_task_id.py --type task`). Id checkboxu (`RBU-S7-1`) jako `id` souboru nejde: parsery ho berou jako podkrok story, ne jako id souboru.
- Ve frontmatteru tasku `promoted_from: RBU-S7-1`. `Closes RBU-S7-1` i `Closes RBU-T123` označí ten soubor Done.
- Název souboru `RBU-T123 — <text checkboxu>.md`. `type: task`, `parent` = wikilink na story.
- Nové úkoly po migraci mají taky `PREFIX-T<N>`. Plochý projekt se nemění (pořád soubor `type: task` bez parenta, checkboxy v něm zůstávají).

## Co se do souboru zkopíruje

- Title = text checkboxu. Odsazené pokračování řádku jde do těla tasku.
- `agent` se kopíruje ze story. `project` / `slug` taky.
- Status: story `Backlog` → task `Backlog`; story `Waiting` → task `Waiting` a stejné `waitUntil`; jinak task `Next`. Žádný task nedostane `Doing` jen proto, že story je Doing.
- ICE se nekopíruje a nesází se 5/5/5. Skóre tasku bez ICE je 0, do TOP jde jen přes focus.
- **Focus:** story má focus a právě jeden otevřený checkbox → focus se přesune na ten task a ze story se smaže. Víc otevřených checkboxů → focus se ze story smaže a na tasky se nezapíše (strop 10). Dry-run vypíše každý takový přesun i každé smazání.
- Migrace data: jedno otevřené dítě dostane `deadline` i `review_deadline` a story o ně přijde, pokud to není později než deadline epicu. Když později je, děti se převedou, obě data zůstanou na story a dry-run vypíše story i epic. Víc dětí datum nedostane.
- Status story se při migraci nemění. Materiály story se na task nekopírují.

## Závislosti termínů

Uzavřeno v sekci nahoře (Q1–Q5). Tady se neopakuje otevřený seznam.

## Tělo story

- Otevřený checkbox i jeho odsazené pokračování se smaže.
- Do `## Poznámky / log` přibude řádek `RBU-S7-1 → [[RBU-T123 — title]]`.
- `[x]` zůstane.
- Embed Bases se nepřidává. Existující `![[*.base#…]]` se při apply vyjmou. Soubory `.base` se smažou.
- Epic se nerozřezává. Checkbox bez `**ID-N**` zůstane. Plochý projekt se nesahá.

## Pohledy a automatika

- Pohledy Bases se nezakládají. Fronta: story s otevřeným child taskem není v `top_priority` ani ve `focus_suggestions`. Status story se nemění. `top_priority_today` dál řídí jen focus.
- GitHub `Closes`: nejdřív soubor (id nebo `promoted_from`). Checkbox se odškrtne jen když soubor neexistuje. Story se nesmí označit Done jen proto, že zbylé checkboxy jsou `[x]`, dokud má otevřený child task. Epic se auto-Done nedotkne.
- `append_task_note` s `target=step` na story založí child soubor, nepřidá checkbox. Na souboru `type: task` smí `target=step` dál přidat drobný checkbox `**RBU-T123-1**` (to už není samostatný úkol). `target=log` se nemění.
- `create_task` dostane `parent`. V hierarchii je u `level=task` parent povinný (story). Nový task soubor nedostane placeholder `- [ ] **ID-1**`.

## Co se přepíše

- Migrace: nový skript s defaultem dry-run a `--apply` až po náhledu. Fixture testy, ne živý vault.
- `vps/second-brain-hub/lib/hierarchy.py`, `vps/second-brain-hub/lib/github_rbu_closes.py`, `vps/second-brain-brain/app/tools/create_task.py`, `vps/second-brain-brain/app/tools/append_task_note.py`.
- Šablony a pravidla, která dnes říkají „v hierarchii `type: task` nepoužívej“ a „práce = checkbox ve story“: `ŠABLONY/obsidian-templates/task-convention.md`, bootstrap, task-mention, task-operational-steps, skill `agenda-capture` / `agenda-triage` / `agenda-work` / `agenda-status-update`.
- Po apply jednou `build_agent_context.py`.

## Mimo rozsah

- MCP konektor a „Grok nevidí nástroj“ — samostatně, až po téhle změně.
- Převod hotových `[x]` a plochých projektů.

## Architekt k=1 (98ebe203) — kontrakt k grillu g=2

Q1–Q5 z grillu g=1 jsou uzavřené. Architekt je rozepsal. Druhé kolo Šťourala se na ně neptá znovu. Otevřené jsou jen body, které architekt nechal na člověka.

Zápis, který poruší nerovnost, se neuloží. Varování nabídne dřívější datum dítěte, nebo výslovný posun rodiče na den, který nerovnost splní. Neplatný stav se neukládá. Hlídá se jen `deadline`. Předek se srovnává se všemi otevřenými potomky s datem, i přes story bez data. Do maxima patří Doing, Next, Backlog a Waiting. Done, Cancelled a `[x]` ne.

Migrace: jedno otevřené dítě dostane obě datová pole, story o ně přijde, ale jen když to sedí vůči epicu. Jinak datum zůstane na story a dry-run to vypíše. Víc dětí datum nedostane. Focus u jednoho dítěte přejde na task, u víc dětí se ze story smaže a na tasky se nezapíše.

Obsidian jako editor mizí z textů a z runbooku (zákaz, ne „volitelný pull-only“). Markdown v git vaultu, wikilink `parent`, složka `ŠABLONY/obsidian-templates/` a rollback `VAULT_BACKEND=drive` zůstávají. Embed Bases do vaultu se nepřidává.

Předpoklady, které architekt zvolil a které grill může označit za sporné:

- A2: datum, které by po přesunu na jediné dítě bylo později než epic, zůstane na story. Apply se kvůli tomu nezastaví.
- A3: převádějí se jen checkboxy v `## Operativní kroky`. Mimo sekci jen výpis.
- A6: kontrola je v Brain `update_task` a ve skillech přes `scripts/check_deadline_order.py`. Samotný zápis souboru mimo ně kontrolu mine. Mac klon je pull-only.
- A8: story, která zůstane Next nebo Doing, zůstane ve širší frontě `top_priority`, i když práci nesou tasky. V TOP dneška rozhoduje focus.
- A10: nová hierarchy story ani task nedostanou placeholder checkbox. Plochý task ho má dál.

Grill g=2 (uzavřeno):

- **Q6:** Smazat `.base` v šablonách i ve vaultu `00-System/Bases/`. Při apply vyjmout existující `![[*.base#…]]` z hubů, epiců a stories. Nový embed nepřidávat. Markdown šablony nechat.
- **Q7 předpoklad:** Cesty `ŠABLONY/obsidian-templates/` a Drive `OBSIDIAN/` zůstávají. Rollback `VAULT_BACKEND=drive` zůstává. Texty, které berou Obsidian jako editor, se přepíšou na zákaz.
- **Q8:** Story s otevřeným child taskem do širší fronty `top_priority` nepatří. Status story se nemění. Story bez otevřeného child tasku ve frontě zůstává.
- **Q9 předpoklad:** Migrace bere každý otevřený `**ID-N**` v celém těle story, ne jen v `## Operativní kroky`. Checkbox bez id zůstává. Dry-run oddělí řádky mimo sekci.
- **Q10:** Celé apply se nezastaví. U story, jejíž jediné dítě by bylo později než epic, se děti převedou na soubory, ale obě datová pole zůstanou na story. Na task se nekopírují. Epic se neposouvá. Dry-run vypíše obě strany. Další zápis data jde přes varování z Q1.
- **Q11 předpoklad:** Kontrola sedí ve všech hub zápisech `deadline`, včetně recurring. Skill není druhá autorita. PR merge se v tomhle zásahu neblokuje. Neplatný stav se při čtení jen zaloguje a další zápis `deadline` ho odmítne.

## Provozní vrstva MCP (2026-10-16)

Zadání: [2026-10-16-brain-mcp-pozadavky.md](file:///Users/lukascypra/Downloads/2026-10-16-brain-mcp-pozadavky.md). Patří do stejné pipeline jako soubor na každý úkol.

- `close_task` rodiče jen navrhne. Story se sama nezavře.
- Focus: `propose_focus` + `apply_focus` až po ano. Strop 10. Story s otevřeným child taskem focus nedostane.
- Alias `promoted_from` pro čtení a `Closes` platí 90 dní od apply migrace, pak vyhledání starým id checkboxu skončí. Pole v souboru zůstane.
- Dodat P1, P2 i P3, pokud to nerozbije migraci ani nerovnost termínů. Jinak oddělit a napsat proč.

## Delta architekta r=2

R1–R11 a R13–R17 beze změny. R12 navíc maže soubory `.base`. A3, A6 a A8 padají a nahrazují je Q9, Q11 a Q8. A2 se přepisuje na Q10: sporné jediné dítě se na soubor převede, obě data zůstanou na story, apply pokračuje, dry-run vypíše story, její deadline, epic a deadline epicu.

Nové B26: neplatný strom se při čtení jen zaloguje. B27: otevřený `**ID-N**` mimo sekci se stane souborem. B28: po F6 nejsou `*.base` v toolingu, po F8 apply nejsou ve vaultu a v hubechnení embed `![[*.base`.

F6 už nepřidává pohled StoryTasks. Maže `.base` a vytáhne embedy ze šablon a skillů. F8 při apply maže `00-System/Bases/*.base` a embedy ve vaultu, pak teprve promote.

## Delta MCP, architekt d3b2bc77, otevření #2, kolo r=1

P1, P2 i P3 jdou do stejné změny. Nic se neodděluje. Q1–Q11, R1–R17, B1–B28 a F1–F8 se nepřepisují. Hromadný převod týdne focusu `bulk_update` neudělá: klíč `focus` odmítne stejně jako dnešní `update_task`.

### Požadavky

- R18 `find_tasks`. R19 `get_task` včetně starého id checkboxu a `resolved_from`; po okně A11 staré id nic nenajde. R20 `edit_task_body` jen s `confirm: true`, frontmatter nemění, stopu migrace jen s `allow_migration_trace`.
- R21 `toggle_step` jen na task souboru a v plochém projektu. Story vrátí chybu.
- R22 `close_task` zavře jen zadané id, focus smaže, rodiče nezapíše. Výstup: `parent_story`, `open_siblings`, `suggest_close_parent`. Story ani epic se sami nezavřou.
- R23 porušení Q1 vrátí `deadline_order` se dvěma volbami. `allow_parent_shift` nerovnost nevypne.
- R24 `propose_focus` nezapíše. `apply_focus` zapíše až jako druhý krok. Strop 10. Story s otevřeným child taskem focus nedostane.
- R25 `list_children` a `get_tree`. R26 log `YYYY-MM-DD HH:MM · source · reason`, když jsou oba. R27 dry-run u zápisů; u starých nástrojů default `dry_run: false`.
- R28 `append_task_note` na story založí child soubor a vrátí `{created, path, parent}`. Na tasku vrátí `{appended_step_id}`.
- R29 `bulk_update` jedna session, validace po všech patchích, chyba = žádný zápis, `focus` v patchi je 403. R30 `create_task` v hierarchii vyžaduje parent u tasku, umí dávku, bez placeholderu a bez ICE 5/5/5.
- R31 kotva okna je soubor z A11, zapisuje ho F8 při `--apply`, druhé apply čas nepřepíše.
- R32 `Closes` stejné okno jako `get_task`. Napřed id souboru, pak `promoted_from`. Child story ani epic na Done nepřepne.
- R33 přímé `set_focus` nezapíše a vrátí `focus_requires_proposal`. Jediný zápis focusu je `apply_focus`, plus smazání focusu v `close_task`.

Mimo rozsah: TECH-010, `index.md` smluv, jednorázové ruční opravy v Gitu.

### Předpoklady

- A11 — 90 dní od kalendářního data `applied_at` v `00-System/task-promotion-applied.json` (Europe/Prague), zapsaného poprvé při úspěšném `--apply`. Platí `today <= applied_at + 90 dní` včetně posledního dne. Den 91 staré id skončí. Suchý běh čas nenastaví. Chybí-li soubor, alias se nepoužije. Pole `promoted_from` se nemaže.
- A12 — U `update_task`, `append_task_note` a `create_task` jsou `source` i `reason` volitelné. `close_task`, `edit_task_body` a `toggle_step` bez obou vrátí 400 `missing_provenance`.
- A13 — `apply_focus` nevolá `gate_brain_apply` (ta zápis vždy odmítne). „Ano“ je volání `apply_focus` s `proposal_id`. Návrh je v paměti procesu, TTL 2 h. Po apply se batch smaže. Druhé apply je 404.
- A14 — nové testy od T30.
- A15 — volba `move_child_earlier` nese `child_id` a datum. `move_parent_later` nese `parent_id`, datum = nejpozdější deadline otevřeného potomka, `requires: allow_parent_shift`.
- A16 — přímý zápis focusu končí pro service, OAuth i `dev`.
- A17 — `expected_hash` je SHA-256 celého souboru. Vedle něj platí `expect_oid`. Jsou-li oba, musí sedět oba.
- A18 — `promoted_from` na `create_task` je unikátní a nesmí patřit otevřenému checkboxu. Migrace 346 souborů jde skriptem, ne přes `create_task`.

### Chování (výběr, zbytek v odpovědi architekta)

- B29 staré id v okně vrátí task a `resolved_from`. B30 po okně 404 `alias_expired`. B31 bez kotvy 404 `alias_inactive`.
- B33 edit bez `confirm` jen diff. B36 close posledního tasku story nechá story otevřenou a `suggest_close_parent: true`. B38 close story/epicu s otevřeným potomkem je 409.
- B40 deadline rodiče dřív než potomek: 409 `deadline_order`, zápis 0×. B41 stejný den projde. B43 `allow_parent_shift` a datum = max potomka posune rodiče.
- B45 append na story v dry-run nezaloží soubor. B46 bez dry-run založí `PREFIX-T<N>`.
- B47 propose nic nezapíše. B49 11. focus je 403. B50 story s otevřeným dítětem je 403. B51 přímé `set_focus` je 403.
- B52 bulk, který rozbije nerovnost, nezapíše nic. B54 hierarchy task bez parent je 400. B57 toggle na story je chyba.

`suggest_close_parent` je true jen když zavřený uzel je task, rodič je story a po zavření má nula otevřených dětí. Výslovné `close_task` na id story zapíše Done jen když story nemá otevřené dítě ani otevřený checkbox.

### Pořadí

F1–F7 beze změny. F8 na konci úspěšného `--apply` zapíše kotvu A11, pokud už není. Suchý běh kotvu nezakládá.

F9 alias. F10 čtení. F11 payload nerovnosti nad existující funkcí. F12 edit a toggle. F13 close. F14 propose/apply a vypnutí přímého `set_focus`. F15 provenience a návrat appendu. F16 bulk a create. F17 `Closes` a okno aliasu. Kód F9–F17 smí být v repu dřív než ostré F8. Bez kotvy alias na živém vaultu nic nenajde.

Testy fixture, živý vault se nezapisuje. Čísla T30–T42 už má `test_append_task_note.py`. Nové testy od T43.

## Grill g=1 otevření #2 (HOTOVÝ)

Šťoural [eb9a4192](eb9a4192-966e-4a0b-a624-6f1baceb2c62). Bez otázek. Předpoklady, které platí:

- A19 — Než existuje `00-System/task-promotion-applied.json`, `append_task_note` na story dál přidává checkbox a `toggle_step` se chová jako dnes. Po kotvě platí R21 a R28. Kontrola termínů (Q11) může jet hned.
- A20 — `apply_focus` s prázdným týdnem focus smaže. Zákaz story s otevřeným dítětem platí jen při nastavení týdne. Nastavit jde jen aktuální ISO týden. Strop 10 je task/story, strop 5 epiců zůstává. Waiting, Backlog a pauznutý projekt se do stropu nepočítají.
- A21 — Append a create focus na story samy nemažou ani nepřesouvají. Sundání je prázdné `apply_focus`. Přesun focusu při migraci dělá jen skript F8.
- A22 — `Closes` task souboru parent story ani epic na Done neoznačí. `Closes` id story smí story Done, jen když nemá otevřený child task ani otevřený checkbox. Epic nikdy. Alias v closeru jen u prefixu RBU. `get_task` alias platí pro všechny prefixy.
- A23 — `toggle_step` staré id checkboxu nepřekládá. `find_tasks(id=…)` používá stejné okno jako `get_task`. Textové `query` je název a tělo, ne frontmatter.
- A24 — S `allow_parent_shift` projde deadline rodiče ≥ maximum všech otevřených potomků s `deadline`, i přes uzel bez data. Datum v nabídce je to maximum. Stejný den projde. `move_child_earlier` je jedna volba na každý konfliktní uzel. Druhé volání, které rozbije hlubší nerovnost, znovu vrátí `deadline_order` a nezapíše.
- A25 — `suggest_close_parent` je true jen když by hned potom výslovné `close_task` na tu story prošlo: nula otevřených child tasků a nula otevřených checkboxů.
- A26 — `create_task` `level=task` v hierarchii: parent je existující story stejného slugu, bez placeholderu, bez ICE 5/5/5, skóre 0. Story a epic dál dostanou 5/5/5. Plochý task si placeholder nechá. Dávka se validuje nad celou sadou.
- A27 — `confirm: true` vyžaduje `expected_hash`. Když je i `expect_oid`, musí sedět oba. `match` musí trefit právě jeden výskyt, jinak 409. `dry_run` nezapisuje.
- A28 — Stejné `resolution` u terminálního úkolu je noop. Jiné resolution, nebo `toggle_step` na Done/Cancelled, je 409.
- A29 — Návrh focusu je ve stejném store jako `external_propose`. `apply_focus` nejde přes `gate_brain_apply`, jde přes `brain_vault(mode=mutate)`.
- A30 — `bulk_update` je jedna session, validace dřív než první zápis. Výjimka necommituje a vrátí pracovní strom.
- A31 — Nové nástroje i vypnutí přímého `set_focus` jsou na MCP i na REST. `/v1/set_focus` volá stejnou funkci.

Opravy vůči deltě: B43 je „libovolné datum od maxima potomků výš“, ne jen přesné maximum. B50 platí jen při nastavení týdne, smazání focusu jde. R21 a R28 na živém vaultu až po kotvě. R32 je zákaz kaskády, ne zákaz `Closes` story bez otevřených dětí.

## Delta r=2, nálezy kritika

Čísla T30–T45 z delty r=1 se nepoužijí. T1–T42 zůstávají v `test_append_task_note.py`.

- **A32.** T43–T47 patří jen NEW-1 až NEW-5. Ostatní testy MCP (alias, hledání, edit, close, strom, provenience a zbylá tvrzení R18–R32) jdou od T48 výš, v pořadí požadavků.
- **A33.** T43 ověří špatný backend na fixtuře. Session, discard a kotvu jede dočasný git. Živý `/data/vault` se v testu nezapisuje.

- **NEW-1 zavřeno.** F8 `--apply` jen když `VAULT_BACKEND=git` a `GIT_VAULT_ROOT=/data/vault`. Jinak chyba a nula zápisů. Jedna session s `discard_dirty_on_error=True`. Dirty start se neresetuje a apply neproběhne. Kotva je poslední zápis ve stejné session, commit až na konci. Výjimka necommituje a vrátí strom na HEAD. Opakovaný apply přeskočí checkbox, který už má soubor s tím `promoted_from`, a `applied_at` nepřepíše. R34, B63, T43.
- **NEW-2 zavřeno.** Recurring spočítá nový deadline v paměti a zkontroluje nerovnost před archivací. Při porušení soubor zůstane v `tasks/`, rotace neproběhne, do logu přibude jeden důvod. Cron rodiče neposouvá. R35, B64, B65, T44.
- **NEW-3 zavřeno.** `update_task`, `bulk_update` i `set_focus` při pokusu zapsat focus vrátí 403 `focus_requires_proposal` a text s `propose_focus` a `apply_focus`. Skill `agenda-status-update` přestane volat `set_focus` a přestane psát strop 5. Strop je 10 task/story a 5 epiců. R33, B66, T45.
- **NEW-4 zavřeno.** Testy, které od `set_focus` čekají zápis, čekají 403. Zápis focusu kryjí testy návrhu a apply. B67, T46.
- **NEW-5 zavřeno.** Jedna dávka `create_task` drží čítač v paměti. Suchý běh N úkolů vrátí N různých id a nic nezapíše. R30, B68, T47.
