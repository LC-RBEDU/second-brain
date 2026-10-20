# Pipeline: export_tasks
Stav: DONE
Plán: docs/plans/2026-10-19-export-tasks.md
Schvalování plánu uživatelem: ne
Architekt: agent ID afd56998-1bce-4c5c-966d-f33a1d1d16e0, otevření plánu #2 (PLAN nález Q3 z QA), generace v otevření k=1/3, kolo r=3/3 po C4 (otevření #1 skončilo SCHVÁLENO, k=2 byl afd56998, k=1 byl 09800b24)
Šťoural: agent ID f3ac21bc-7d2d-4e93-b979-f40a6d643732 · kolo grill g=4 (g=3 byl 396f4399)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 1/3 · kola REVIEW 1/5 (delta F6, čítač po předchozím SCHVÁLENO vynulován) · kola QA 2/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku): cd26eefe3674b9deaebaf864615af30433b79a9d · Kódový SHA: 9e0189e45994a6826708afd7606252936b880940 · Review SCHVÁLENO na: 9e0189e45994a6826708afd7606252936b880940 · QA PASS na: 9e0189e45994a6826708afd7606252936b880940 · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Plán schválen kritikem: otevření #2, 2026-10-19, 0 BLOCKER / 0 MAJOR (e3fec377). Otevření #1 bylo b3f721c4.
Goal: complete

## Zadání (doslovně) a rozhodnutí

Uživatel, 2026-10-19:

potřebuji aktualizovat funkčnost MCP dle tohoto zadání:

# Brief pro Cursor: Brain nástroj `export_tasks`

Stav: návrh k 19. 10. 2026 · Autor: Claude (chat, projekt Second Brain v2) · Schvaluje: Lukáš

## Cíl
Jedním voláním získat **kompletní snapshot tasků** ve vaultu (frontmatter, bez těla) pro přehledový dashboard Second Brainu (strom, Radar napříč projekty, pohled na projekt). Dashboard data drží v klientu a filtruje/hledá lokálně; zápisy dál jdou přes `update_task` / `create_task` s CAS.

## Proč stávající nástroje nestačí (ověřeno 19. 10. 2026)
- `find_tasks`: tvrdý strop **50 výsledků** (limit 1000 ignorován), bez offsetu/cursoru, řazení podle ID. Vrací jen otevřené. Chybí `oid`, `agent`, `waitUntil`, ICE, `created/updated`.
- `get_tree`: jen jedna úroveň pod epic/story, bez `type`, `review_deadline`, `focus`; tasky bez parenta nepokryje.
- `get_task`: plná data, ale po jednom (≈550 volání).
- `get_context`: ~170 kB, ale nemá všechny tasky.

## Rozhraní (MCP + REST)
MCP tool `export_tasks`, ideálně i REST `GET /v1/tasks/export` (human OAuth / service token, read-only scope).

### Parametry
| Parametr | Typ | Default | Popis |
|---|---|---|---|
| `include_closed_days` | int | 0 | Přidá Done/Cancelled z `07-ARCHIV/tasks-done/` aktualizované za posledních N dní (0 = jen otevřené). |
| `projects_csv` | string | "" | Volitelný filtr slugů; prázdné = vše. |
| `fields` | string | `"standard"` | `standard` = seznam polí níže; `full` = + `materials`, `blocked_by`, `company_priorities`, `source`. |
| `since` | ISO datetime | null | Volitelně jen tasky s `updated` / commitem po tomto čase (inkrementální refresh). |

### Výstup
```json
{
  "generated_at": "2026-10-19T01:10:00+02:00",
  "vault_head": "<git commit sha>",
  "focus_week": "2026-W43",
  "count": 539,
  "projects": [
    {"slug": "finance", "title": "Téma: Finance", "status": "active", "hierarchy": true}
  ],
  "tasks": [
    {
      "id": "F-S86",
      "title": "Zkonsolidovat mzdy, odvody, půjčky atd. Honzy a Luboše",
      "type": "story",
      "status": "Next",
      "parent": "F-E58",
      "project": "finance",
      "path": "02-PROJEKTY/finance/tasks/F-S86 — ….md",
      "oid": "43e3c633…",
      "deadline": "2026-10-18",
      "review_deadline": null,
      "waitUntil": null,
      "focus": "2026-W42",
      "agent": "none",
      "ice_i": 5, "ice_c": 5, "ice_e": 5,
      "priority_score": 5.0,
      "is_recurring": false,
      "promoted_from": null,
      "created": "2026-10-16",
      "updated": "2026-10-19",
      "steps_total": 3,
      "steps_done": 1,
      "filename_title_mismatch": false,
      "parse_errors": []
    }
  ]
}
```

### Poznámky k polím
- `parent` normalizovaný na **holé ID** (ve frontmatteru je wikilink `[[IAD-E4 — Security & Performance]]`).
- `oid` = stejný identifikátor, jaký přijímá `update_task(expect_oid=…)`.
- `steps_total` / `steps_done` = checkboxy v `## Operativní kroky` (pro progress bar bez čtení těla).
- `filename_title_mismatch` = `true`, když se název souboru neshoduje s `<ID> — <title>` (např. AF15, AF37). Brain při změně title soubor nepřejmenovává.
- `parse_errors` = seznam problémů při parsování (chybí frontmatter, neznámý status, rozbitý parent wikilink, parent neexistuje, …). Task se do výstupu dostane i s chybou, aby ho dashboard ukázal v kategorii „chybně zadané“, místo aby tiše zmizel.
- Výstup jako **objekt s polem**, ne JSON zabalený ve stringu `{"result": "…"}` (u MCP obsahu klidně `structuredContent`).

## Nefunkční požadavky
- Odpověď do ~1 s pro ~600 tasků (čte se jen frontmatter + odpočet checkboxů).
- Žádné tiché ořezání: buď celý výsledek, nebo chyba. `count` musí sedět s délkou `tasks`.
- Read-only, bez side-effectů (nesmí spouštět rebuild agent-context).

## Akceptační kritéria
1. `count` za otevřené tasky = `stats.total_open_tasks` z `get_context` (k 19. 10. 539).
2. Každý task z `find_tasks` (napříč projekty) je ve výstupu se shodným `status`, `parent`, `deadline`.
3. `oid` z exportu projde jako `expect_oid` v `update_task(dry_run=true)`.
4. Task s rozbitým frontmatterem se objeví s neprázdným `parse_errors`.
5. pytest pokrývá: prázdný vault, task bez parenta, parent jako wikilink i holé ID, archivované Done v okně `include_closed_days`.

## Navazující (mimo tento brief)
- Případně `find_tasks`: zvednout strop / přidat offset (pro našeptávač parenta stačí 50).
- Dashboard BFF bude volat `export_tasks` při startu a po každém zápisu (nebo `since` pro inkrement).

Uživatel potom: „jdeš na to přes /rbu-pipeline ?“ a v tom tahu je příkaz `/rbu-pipeline`.

### Rozhodnutí
- CLARIFY: nic blokujícího. Brief je specifikace. Schvalování plánu: ne.
- Profil: SECOND_BRAIN. Větev `main`, base `cd26eefe3674b9deaebaf864615af30433b79a9d`. Tester vždy přeskočen.
- Nasazení: push `main` až po schválení diff reviewera, pak Coolify brain, aby MCP na `https://brain.cyprovi.cz` nástroj opravdu měl. Hub jen pokud se mění sdílená lib, kterou hub importuje.
- Read-only. Žádný zápis do vaultu, žádný rebuild agent-context, žádný n8n deploy.
- `count` otevřených = `get_context` `stats.total_open_tasks` v okamžiku běhu. Literál 539 je stav k 19. 10., ne natvrdo navždy.
- Chybějící ICE brief nespecifikuje. Architekt zvolí předpoklad a zapíše ho. Tiché 0/0/1 se nezavádí, pokud to už není pravidlo snapshotu a plán ho explicitně nepřevezme.
- Mimo rozsah: zvednutí stropu `find_tasks`, dashboard BFF.
- Paralelní general agent `96fd3eaa` byl přerušen, aby nepsal kód vedle pipeline.

### Grill kolo 1 (756c77e6) — čeká na uživatele
- Q1 BLOKUJÍCÍ, odpověď Lukáše 2026-10-19: **varianta 2, jen otevřené.** Výchozí `tasks` = ne-terminální (prázdný status jako Next, bez Done/Cancelled). `count` = `len(tasks)` = otevřený počet = `total_open_tasks`. Aktivní Done/Cancelled ve výstupu nejsou a žádný parametr je z aktivní složky nevrátí. `include_closed_days` dál přidává jen archiv `07-ARCHIV/tasks-done/`. AC2 pro aktivní terminály neplatí. Pole `open_count` se nezavádí.
- Q2 NEBLOKUJÍCÍ, zapsáno: A5 celý pražský den pro date-only `updated`. Slučovací klíč inkrementu je `path`, ne `oid`.
- Zapsané předpoklady, znovu se neptat: A1 ICE `null` (ne snapshot 0/0/1), A3 `project` = složkový slug, A4 `hierarchy` = vlajka charteru, A6 žádný nový scope, A7 `parent_not_found` proti indexu tohoto volání, A8 oid na Drive je `null`, A9 číslo 539 se nefixuje.
- Do plánu po odpovědi na Q1, bez ohledu na variantu: `yaml_error` z raw textu jednoho `read_text` (parser YAML polyká), checkboxy přes `is_operational_header`, prázdný status není `missing_status`, F5 musí počítat s tím, že push `lib/` nasadí Brain (watch `vps/second-brain-hub/lib/**`) a typicky i hub.

### Grill otevření #2 (9f2621b3) — čeká na uživatele
- Q4 BLOKUJÍCÍ (Šťoural ji značil Q1 tohoto kola). `end_session` na úspěšné session, která není `skipped` a není `dry_run`, volá `commit_if_dirty` (`git add -A`, při diffu commit). Brain má `GIT_VAULT_PUSH=1`, takže commit se i pushne. F6 vypíná dirty check jen u exportu, špinavý strom by se tím zapsal. Na čistém stromu `git add -A` běží v každém exportu a v rozpočtu A10 není.
- Odpověď Lukáše 2026-10-19: **varianta A.** Každý `mode="read"` nevolá `commit_if_dirty`. Žádný `git add`, commit ani push. Export smí dirty check vynechat a vrátí bajty z disku (B30), `vault_head` zůstane lokální HEAD. Ostatní read na špinavém stromu dál 503. Mutate a rebuild nechají fetch, dirty check i commit. Do stropu návratů do PLAN se tahle odpověď nepočítá.

## Průběh
| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
| 1 | 2026-10-19 | PLAN | 09800b24-f2ef-4c8a-9a0f-79860a2186b4 | plán odevzdán | — | Plán zapsán do docs/plans/2026-10-19-export-tasks.md. Předpoklady A1–A9. Přechod GRILL. |
| 2 | 2026-10-19 | GRILL | 756c77e6-c291-456c-9733-0c388e15ba08 | POTŘEBUJE ODPOVĚDI | Q1 BLOKUJÍCÍ, Q2 NEBLOKUJÍCÍ | Přechod AWAITING_USER (z: grill). Goal paused-awaiting-user. |
| 3 | 2026-10-19 | PLAN | 09800b24-f2ef-4c8a-9a0f-79860a2186b4 | plán r=2 odevzdán | — | Jen otevřené. Plán přepsán. Přechod GRILL g=2. |
| 4 | 2026-10-19 | GRILL | af7498ef-b190-423f-a3f3-051480a601e5 | HOTOVÝ GRILL | 0 | Frontier prázdný. Přechod CRITIC. |
| 5 | 2026-10-19 | CRITIC | fc782550-f64d-4a0c-ae6d-1651243c4454 | K PŘEPRACOVÁNÍ | C1 BLOCKER, C2 MAJOR, C3 MAJOR | NEW-1→C1, NEW-2→C2, NEW-3→C3. Resume architekta r=3. |
| 6 | 2026-10-19 | PLAN | 09800b24-f2ef-4c8a-9a0f-79860a2186b4 | plán r=3 odevzdán | C1–C3 vyřešeno v plánu | Přechod GRILL g=3. |
| 7 | 2026-10-19 | GRILL | 396f4399-505c-44b9-8fd4-889810019f92 | HOTOVÝ GRILL | 0 otázek | C1 a C3 drží. C2: git log -z --name-only nedělí cesty po NUL. Přechod CRITIC. |
| 8 | 2026-10-19 | CRITIC | cb0eaa9f-b2d7-40de-a9ae-601c4932050b | K PŘEPRACOVÁNÍ | C2 MAJOR | C1 a C3 vyřešeny. r=3 a k=1 → nový architekt k=2 r=1. |
| 9 | 2026-10-19 | PLAN | afd56998-1bce-4c5c-966d-f33a1d1d16e0 | plán k=2 r=1 odevzdán | C2 parser LF | Přechod GRILL g=4. |
| 10 | 2026-10-19 | GRILL | f3ac21bc-7d2d-4e93-b979-f40a6d643732 | HOTOVÝ GRILL | 0 | Parser C2 trefí rel_path. Přechod CRITIC kolo 3. |
| 11 | 2026-10-19 | CRITIC | b3f721c4-5a0d-42a6-a35d-8186e3768bb8 | SCHVÁLENO | 0/0 | C1–C3 vyřešeny. Přechod IMPLEMENT. Schvalování uživatelem nevyžadováno. |
| 12 | 2026-10-19 | IMPLEMENT | cd51c5ee-7323-466b-b015-2f95aa1e6fcf | commit 82c5afd | — | Pytest 39 passed. Bez push. Přechod REVIEW. |
| 13 | 2026-10-19 | REVIEW | 857358a5-b096-4af2-82ad-377ac57ea841 | SCHVÁLENO | 0 BLOCKER, 0 MAJOR, D1 MINOR | NEW-1→D1: archivní okno u quoted ISO nepočítá pražský den. Neblokuje. |
| 14 | 2026-10-19 | QA | 33086caf-853e-4f74-8fb0-2e1a4f9689e1 | — | — | Push ff. origin/main = 82c5afd. Pytest 39, exit 0. Brain deploy 6049 finished, healthz 200. Hub deploy 6050 finished. |
| 15 | 2026-10-19 | QA | e9d848e9-4bc9-4925-83dc-b3a6dd7d0e11 | FAIL | Q3 MAJOR | T24/B# drží (count 538, auth, MCP objekt, warm). Latence 2,1–2,2 s. NEW-1→Q3 PLAN. Návrat do PLAN, otevření #2. |
| 16 | 2026-10-19 | PLAN | afd56998-1bce-4c5c-966d-f33a1d1d16e0 | plán odevzdán | Q3 v plánu | A10: read bez fetch, export bez status a bez collect_projects, jedno čtení. Strop 1 s zůstává. Soubor zapsal hlavní agent. Přechod GRILL g=5. |
| 17 | 2026-10-19 | GRILL | 9f2621b3-fcd1-4b67-bf7a-f1d0d7660c79 | POTŘEBUJE ODPOVĚDI | Q4 BLOKUJÍCÍ | Read `end_session` volá `commit_if_dirty`. Lukáš zvolil A. Přechod PLAN r=2. |
| 18 | 2026-10-19 | PLAN | afd56998-1bce-4c5c-966d-f33a1d1d16e0 | plán odevzdán | Q4=A v plánu | `commit_on_end=False` pro každý read. Soubor zapsal hlavní agent. Přechod GRILL. |
| 19 | 2026-10-19 | GRILL | 87771cb5-32ee-410c-870e-d58f3eb29c86 | HOTOVÝ GRILL | 0 | Q4=A v plánu sedí. Frontier prázdný. Přechod CRITIC. |
| 20 | 2026-10-19 | CRITIC | 46b7a684-b17a-464d-927b-d41d53716912 | K PŘEPRACOVÁNÍ | C4 MAJOR | B30/T26 hlídají jen export 200. Neplatný `since` (400) při `discard_dirty_on_error=True` udělá `reset --hard` a vrátí tracked soubor na HEAD. T26 to nechytí. |
| 21 | 2026-10-19 | PLAN | afd56998-1bce-4c5c-966d-f33a1d1d16e0 | plán odevzdán | C4 v plánu | B30(b)/T26(b): tracked soubor, `since=not-a-date` → 400, bajty beze změny, bez `reset --hard`. Soubor zapsal hlavní agent. Přechod GRILL. |
| 22 | 2026-10-19 | GRILL | bd1bbcd7-f8d1-4d4a-afd8-e464361cd187 | HOTOVÝ GRILL | 0 | C4 sedí. Frontier prázdný. Přechod CRITIC. |
| 23 | 2026-10-19 | CRITIC | e3fec377-e8ee-4be6-b827-e008269fac26 | SCHVÁLENO | 0/0 | C4 drží. Q3 a Q4 nepadají. Schvalování uživatelem nevyžadováno. Přechod IMPLEMENT. |
| 24 | 2026-10-19 | IMPLEMENT | c7517613-3ec0-4fa7-8c2c-d0d88ba96a31 | commit 9e0189e | — | Pytest 43 passed, exit 0. Bez push. Přechod REVIEW. |
| 25 | 2026-10-19 | REVIEW | 639a3327-1d5f-48f5-b45e-c4fa9e021854 | SCHVÁLENO | 0 BLOCKER, 0 MAJOR | F6 drží. D1 se neotevírá. Diff z HEAD, git diff v reviewerovi nešel. |
| 26 | 2026-10-19 | QA | 618a02e1-eece-46ee-912c-70faaa13645b | push ff | — | origin/main = 9e0189e. Pytest 43, exit 0. Brain deploy 6053 finished, healthz 200. Hub deploy 6054 finished. |
| 27 | 2026-10-19 | QA | 67511032-fb5b-4db8-abf1-207e5d921da6 | PASS | 0 | T27: 916 / 919 / 908 / 863 ms. count 538. vault_head beze změny. Bez fetch/status/add/commit/push. mode=warm, total_open_tasks 538. |
| 28 | 2026-10-19 | TESTER | — | přeskočeno | — | TESTER: přeskočeno (profil SECOND_BRAIN). |
| 29 | 2026-10-19 | DONE | — | gate exit 0 | — | Vlastní pytest 43 passed, 12,11 s. QA PASS na 9e0189e. D1 MINOR zůstává otevřený, neblokuje. |

## Otevřené nálezy
| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
| C1 | BLOCKER | PLAN | vyřešen (kritika kolo 3) | 1 |
| C2 | MAJOR | PLAN | vyřešen (kritika kolo 3) | 2 |
| C3 | MAJOR | PLAN | vyřešen (kritika kolo 3) | 1 |
| D1 | MINOR | IMPL | otevřený, neblokuje | 1 |
| Q3 | MAJOR | PLAN | vyřešen (QA kolo 2, T27 pod 1000 ms) | 1 |
| Q4 | BLOKUJÍCÍ | PLAN | odpověď A v plánu; zbytková díra testu je C4 | 1 |
| C4 | MAJOR | PLAN | vyřešen (kritik e3fec377) | 1 |
