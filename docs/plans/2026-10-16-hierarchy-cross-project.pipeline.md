# Pipeline: Hierarchie všude, křížový rodič, zábrana nového projektu
Stav: REVIEW
Plán: docs/plans/2026-10-16-hierarchy-cross-project.md
Schvalování plánu uživatelem: ne
Architekt: 70f91dc7-ff87-425b-ab71-1cb603af5ccf, otevření plánu #4, generace v otevření 1/3, kolo 2/3
Šťoural: e43969a5-b9b5-4d6b-8a30-90cd94383057 · kolo grill 2 otevření #4 · HOTOVÝ GRILL
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 2/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): 83877808710d74a1a6a20719d8af7f322eefac59 · Kódový SHA: c95b780646667ee9cf86ad21d4e8b13f4ffd1a9b · Review SCHVÁLENO na: — · QA PASS na: — · TESTER: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Goal: aktivní

## Projekt
SECOND_BRAIN. Kořen `~/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN`. Větev `main`, base = origin/main `83877808710d74a1a6a20719d8af7f322eefac59`. Nasazení: push `main` → Coolify `second-brain-hub` a `second-brain-brain` na coolify-dev. Ostrý zápis do vaultu tato pipeline nedělá. Gate: `python3 -m pytest vps/second-brain-hub/tests vps/second-brain-brain/tests scripts/tests -q` (brain testy, které importují FastAPI, mohou lokálně chybět modul — to není důvod je přeskočit v plánu). Tester: vždy přeskočeno.

## Zadání (doslovně) a rozhodnutí

### Zadání uživatele (doslovně)
ok, přidej i poslední zábranu do pipeline a spusť na to celé /rbu-pipeline

„To celé“ je rozsah potvrzený v předchozí větě uživatele („ok, každopádně tímto máme domapované tasky epicy atd. takže co je další krok?“) a odpovědi na ni: kód hierarchie (čtyři kusy) plus zábrana, ať Brain nezaloží projekt bez přímého příkazu.

### Rozhodnutí
1. Projekt zůstává domov souboru (složka, prefix ID, hub, pauza, area, materiály). Tagy se nezavádějí.
2. Soubor dítěte zůstává ve složce svého `slug`. `parent` je jen id. Epic nebo story může být v jiném projektu.
3. Epic nemá rodiče.
4. Story má povinně rodiče a ten rodič je epic (libovolný projekt). Story bez epicu nejde založit a parent jí nejde vymazat.
5. Task smí být bez rodiče. Když rodiče má, je to story, klidně v jiném projektu. Task přímo pod epicem nejde.
6. Nový task pod existující story, nová story pod existující epic a nový epic musí jít založit.
7. Existující ploché tasky se hromadně nepřepisují. Dodatečné zařazení je `update_task` s `parent`.
8. MCP nástroje se neslučují. Rozšířit `create_task` a `update_task`. `bulk_update` kontroluje `parent`, když je v patchi.
9. Mapování story bez epicu uživatel už rozhodl a je zapsané ve vaultu (2026-10-16). Tahle pipeline vault znovu nezapisuje a mapování nevymýšlí.
10. Nový task v hierarchii nemá ICE 5/5/5 ani zástupný checkbox `**ID-1**`. Story ICE má. Platí i v projektech, které byly ploché.
11. `get_tree` a `list_children` vrací u uzlu slug projektu, ve kterém soubor leží.
12. Kontrola deadline a rotace vidí předky a potomky i v jiném projektu. Pravidla termínu se nemění.
13. `project_uses_hierarchy` vrací true pro každý projekt.
14. `append_task_note` na story dál založí dítě ve složce té story. Dítě v jiném projektu je `create_task` s jiným slug a `parent`.
15. Zábrana nového projektu: zápis, který by založil složku projektu, odmítne slug bez existujícího hub charteru (`02-PROJEKTY/*.md`, frontmatter `slug:`). Nový hub vzniká jen přímým příkazem uživatele, ne přes `create_task`. Lokální necommitnutý draft je `_known_project` v `vps/second-brain-brain/app/tools/create_task.py` (`error_reason=unknown_project`) a test v `vps/second-brain-brain/tests/test_create_and_bulk.py`. Na serveru to není. Draft není schválený plán — architekt ho smí upravit, chování (odmítnout neznámý slug) platí.
16. `close_task` dál jen navrhuje zavření rodiče. Focus zůstává propose/apply. Tahle pipeline je nemění, pokud na ně nové pravidlo nenarazí.
17. Schvalování plánu uživatelem: ne.
18. Q1 (2026-10-16): úzký kužel deadline. Shodí jen konflikt s předkem nebo potomkem měněného uzlu. Sourozenec a bratranec zápis neshodí.
19. Q2 (2026-10-16): po všech patchích `parent` a `type` v jednom requestu overlay na les. Kontrola měněného uzlu i jeho přímých aktivních dětí. Chyba = 400 a nula zápisů. Děti se nepřepisují.
20. Q3–Q6 bez otázky uživateli, předpoklady Šťourala: rodič ve `tasks/` smí být Done i Cancelled; dávka `items` nevidí sourozence; snapshot `hierarchy` zůstává flag hubu; nový epic dál dostane ICE 5/5/5 a zástupný checkbox, konvence se sjednotí s renderem.
21. Grill kolo 3, Q1 (2026-10-16): les se nenačte jen u čistého statusu `Done` nebo `Cancelled`. Jakmile je v patchi i `parent`, `type` nebo `deadline`, kontrola běží i při závěrečném `Done`/`Cancelled`.
22. Grill kolo 3, Q2 (2026-10-16): kontrola aktivního statusu čte stejný overlay jako složený les, po všech patchích `parent` a `type` v requestu. Disk jen když request `parent` ani `type` nemá.
23. 2026-10-17, uživatel: když se story mění na epic, parent v overlay zůstane a story má přímý otevřený task, 400 vrátí obě porušení a nic se nezapíše. Tvar navazuje na `BrainClientError.as_dict()`: `error_reason` je první důvod (vlastní pravidlo uzlu, `epic_has_no_parent`), `detail.errors` je seznam v pořadí vlastní pravidlo, pak dítě (`parent_not_story`), `message` jmenuje oba. Jedno porušení: seznam má jednu položku a `error_reason` se jí rovná. Děti se procházejí i když vlastní kontrola selže. Dítě `Done`/`Cancelled` druhé porušení není. Když patch parent vyprázdní, vlastní kontrola projde a otevřený task dá jen `parent_not_story`.
24. 2026-10-17: spojený bulk, který mění story na epic bez vyprázdnění parentu a zároveň budí její Done task na `Next`, vrací obě hlášky jako rozhodnutí 23. `error_reason` je `epic_has_no_parent`, `detail.errors` je `["epic_has_no_parent", "parent_not_story"]`, důvod dítěte je v seznamu jednou. Samostatný pozdější request jen se `status: Next` vrací jen `parent_not_story`.
25. 2026-10-17: `detail.errors` skládá všechny porušené uzly v pořadí položek requestu. Uvnitř uzlu nejdřív vlastní důvod, pak přímé otevřené děti seřazené podle id. Stejný důvod téhož dítěte jednou. `error_reason` je první položka. `message` u víc důvodů obsahuje kódy ve stejném pořadí. 403, 404 a 409 seznam nemají. Věta „každé 400 má jednu položku“ platí jen pro jedno porušení.

### Mimo rozsah
- Hromadný přepis vaultu a nové přiřazení rodičů.
- Sloučení nebo mazání MCP nástrojů.
- Založení nového project hubu.
- Přesun souboru úkolu mezi projekty (nové ID + Cancelled původního). To už umí člověk ručně; tahle pipeline to neautomatizuje.
- Posun checkboxové promoce a 90denního aliasu.

## Průběh
| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
| 1 | 2026-10-16 | PLAN | — | — | — | Ledger založen. CLARIFY bez blokující otázky. |
| 2 | 2026-10-16 | PLAN | 70f91dc7-ff87-425b-ab71-1cb603af5ccf | plán | — | Plán od architekta. Předpoklady A1–A13. |
| 3 | 2026-10-16 | GRILL | 89298928-f195-4e86-ab32-3cd95af32bc7 | neproběhl | — | Soubor plánu ještě nebyl na disku. Verdikt z paměti nedal. |
| 4 | 2026-10-16 | GRILL | 84b486b7-a7ab-41a6-8d5c-6a5a7c0e46c6 | POTŘEBUJE ODPOVĚDI | Q1 Q2 blokující | Q3–Q6 neblokující, předpoklady A2/A3/A8/A9. Přechod AWAITING_USER (z: grill). |
| 5 | 2026-10-16 | AWAITING_USER | — | — | — | Čeká na Q1 a Q2. |
| 6 | 2026-10-16 | PLAN | 70f91dc7-ff87-425b-ab71-1cb603af5ccf | odpovědi | — | Q1 úzký kužel, Q2 složený les. Q3–Q6 předpoklady. Resume architekta, kolo 2. |
| 7 | 2026-10-16 | GRILL | 37e788b2-2158-4336-a1ee-1b84705af82d | HOTOVÝ GRILL | 0 | Q1/Q2 jednoznačné v R18/R19. Přechod CRITIC. |
| 8 | 2026-10-16 | CRITIC | a6397baf-b5c1-4f07-b692-dfb636cb1132 | K PŘEPRACOVÁNÍ | 1 BLOCKER, 3 MAJOR, 1 MINOR | C1–C5. Resume architekta, kolo 3. |
| 9 | 2026-10-16 | PLAN | 70f91dc7-ff87-425b-ab71-1cb603af5ccf | plán r=3 | — | C1–C5 zapsané. Přechod GRILL. |
| 10 | 2026-10-16 | GRILL | 9b07d722-6155-467b-a270-ce5f14580fa0 | POTŘEBUJE ODPOVĚDI | Q1 Q2 blokující | Čistý Done vs. Done+parent. Overlay vs. disk u status checku. Přechod AWAITING_USER (z: grill). |
| 11 | 2026-10-16 | PLAN | — | odpovědi | — | Q1 čistý status. Q2 overlay. Nové otevření #2, resume architekta, r=1. |
| 12 | 2026-10-16 | GRILL | cb5d9cc0-e870-4f1c-97ab-1cd8eeac45aa | HOTOVÝ GRILL | 0 | Rozhodnutí 21 a 22 jednoznačné. Přechod CRITIC. |
| 13 | 2026-10-16 | CRITIC | 273a27a2-67ac-48b3-8dc4-756571098429 | K PŘEPRACOVÁNÍ | 1 BLOCKER, 1 MAJOR | C6, C7. C1–C5 vyřešeny. Resume architekta, kolo 2. |
| 14 | 2026-10-16 | GRILL | 2c8c10fe-8656-4284-ac98-3fcb02738cb4 | POTŘEBUJE ODPOVĚDI | Q1 blokující | Holé type epic na story s otevřeným taskem: který error_reason. Přechod AWAITING_USER (z: grill). |
| 15 | 2026-10-17 | PLAN | — | obě hlášky | — | Uživatel: vrať obě porušení. Rozhodnutí 23. Otevření #3, resume architekta, r=1. |
| 16 | 2026-10-17 | GRILL | 90a9c9ba-7a50-4a34-b1df-091a31953c64 | POTŘEBUJE ODPOVĚDI | Q1 Q2 blokující | B47 versus obě hlášky. Pořadí detail.errors mezi uzly. AWAITING_USER (z: grill). |
| 17 | 2026-10-17 | PLAN | — | odpovědi | — | Q1 obě hlášky i u spojeného bulku. Q2 pořadí podle requestu. Rozhodnutí 24 a 25. Otevření #4, r=1. |
| 18 | 2026-10-17 | GRILL | 0a208410-108b-4dc4-948d-f29b58141e3a | HOTOVÝ GRILL | 0 | B47 a pořadí detail.errors jednoznačné. Přechod CRITIC. |
| 19 | 2026-10-17 | CRITIC | 67619766-b05d-4219-8d74-dfc2ce5c3994 | K PŘEPRACOVÁNÍ | 0 BLOCKER, 1 MAJOR, 1 MINOR | C8 T7 versus B22. C9 bulk dry_run. C6 C7 vyřešeny. Resume architekta, kolo 2. |
| 20 | 2026-10-17 | GRILL | e43969a5-b9b5-4d6b-8a30-90cd94383057 | HOTOVÝ GRILL | 0 | B22 a B51 disjunktní. Bulk dry_run hází 400. Přechod CRITIC. |
| 21 | 2026-10-17 | CRITIC | 355d1608-cbd6-4a36-b280-4f1f8c86e821 | SCHVÁLENO | 0 | C8 a C9 sedí. Schvalování plánu: ne. Přechod IMPLEMENT. |
| 22 | 2026-10-17 | IMPLEMENT | — | commit | — | Lokální commit `e952541` na main, bez push. Gate 623 passed. Přechod REVIEW. |
| 23 | 2026-10-17 | REVIEW | ccc1daff-6dfd-476d-bf7c-d6114aadcfff | K OPRAVĚ | 0 BLOCKER, 1 MAJOR, 2 MINOR | D1–D3, vše IMPL. Přechod IMPLEMENT. |
| 24 | 2026-10-17 | IMPLEMENT | — | commit | — | Oprava D1–D3 v `343cdbe`. Gate 627 passed. Přechod REVIEW. |
| 25 | 2026-10-17 | REVIEW | 1a895aec-1d9b-4fe1-98dd-8de566459759 | K OPRAVĚ | 0 BLOCKER, 1 MAJOR, 1 MINOR | D1–D3 potvrzeny. D4 major, D5 minor. Přechod IMPLEMENT. |
| 26 | 2026-10-17 | IMPLEMENT | — | commit | — | Oprava D4 a D5 v `c95b780`. Gate 630 passed. Přechod REVIEW. |

## Otevřené nálezy
| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
| C1 | BLOCKER | PLAN | vyřešen v #12 | 1 |
| C2 | MAJOR | PLAN | vyřešen v #12 | 1 |
| C3 | MAJOR | PLAN | vyřešen v #12 | 1 |
| C4 | MAJOR | PLAN | vyřešen v #12 | 1 |
| C5 | MINOR | PLAN | vyřešen v #12 | 1 |
| C6 | BLOCKER | PLAN | vyřešen v #18 | 1 |
| C7 | MAJOR | PLAN | vyřešen v #18 | 1 |
| C8 | MAJOR | PLAN | vyřešen v #20 | 1 |
| C9 | MINOR | PLAN | vyřešen v #20 | 1 |
| D1 | MAJOR | IMPL | vyřešen v #25 | 1 |
| D2 | MINOR | IMPL | vyřešen v #25 | 1 |
| D3 | MINOR | IMPL | vyřešen v #25 | 1 |
| D4 | MAJOR | IMPL | opraveno v c95b780, čeká review | 1 |
| D5 | MINOR | IMPL | opraveno v c95b780, čeká review | 1 |
