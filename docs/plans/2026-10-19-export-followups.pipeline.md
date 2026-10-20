# Pipeline: export follow-upy
Stav: DONE
Plán: docs/plans/2026-10-19-export-followups.md
Schvalování plánu uživatelem: ne
Architekt: agent ID d82a8556-6db2-4c4d-bdb9-96d9b2e6a0ee, otevření plánu #2 (PLAN nález z IMPLEMENT), generace v otevření k=1/3, kolo r=1/3
Šťoural: agent ID 59f21b8e-09c3-4d4a-b9f5-19b80aa4277b · kolo grill g=3 (g=2 byl 31ab096e, g=1 byl 790258f6)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 1/3 (první je z IMPLEMENT, ne z review) · kola REVIEW 1/5 · kola QA 1/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku): 9e0189e45994a6826708afd7606252936b880940 · Kódový SHA: 0736e9d750a3b9376f935971dba978f11d804a46 · Review SCHVÁLENO na: 0736e9d750a3b9376f935971dba978f11d804a46 · QA PASS na: 0736e9d750a3b9376f935971dba978f11d804a46 · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Plán schválen kritikem: otevření #2, 2026-10-19, 0 BLOCKER / 0 MAJOR (04c69673). Otevření #1 bylo f7744362.
Goal: bez goalu (uživatel neřekl /rbu-pipeline ani /goal)

## Zadání (doslovně) a rozhodnutí

Uživatel, 2026-10-19:

Mám tu několik objevů Claude s doporučením, kterých se ujmi:

Chyby k opravě (Cursor)
hierarchy je u všech 17 projektů true. get_context ho přitom má jen u 5 (Finance, Firemní procesy, IT AI Data, RB Universe, Vibe coding). Pravidlo „story musí mít epic“ by pak hlásilo chyby i v Allfredu, Osobním a dalších.
Odmítnutý CAS vrací obecné „Error executing tool“ bez důvodu. Dashboard potřebuje strukturovanou chybu (error_reason: oid_mismatch + aktuální oid), aby uměl ukázat dialog „task se mezitím změnil“.
filename_title_mismatch je téměř samý šum: 262 hitů, z toho 258 jen kosmetických (lomítko vs pomlčka, pomlčky místo mezer, zkrácení). Skutečně jiný název mají jen 4:
AF15 — Nový formát Allfred budgetu — jedna struktura šablony
AF37 — přehodit planned expenses Our Work→Production
F-S63 — Sledovat: Honza × Luboš — potvrzení net odměny 120k
RBU-S99 — Delivery karta projektu — Lucie skill vs Universe
Porovnávat by se mělo po normalizaci (jen písmena a čísla).

Rozbitý soubor: RBU-S117 — Bug-fixing-RBU-tlačítko-pro-generování-příkazů.md má chybu v YAML, takže chybí id, title i status. Export ho správně ukáže, ale chce opravit.
Sirotci pod uzavřeným parentem: F-T161, F-T176, FP-T136, IAD-T129, RBU-T142 visí pod Done stories. Brain to hlásí jako parent_not_found. Inference: přesnější by bylo parent_closed, protože parent existuje v archivu.
updated chybí u 337 tasků a since filtruje podle něj. Tyto tasky inkrementální refresh nikdy nezachytí. Návrh: since počítat z git commitů (od daného vault_head), ne z frontmatteru.
ICE chybí u 374 tasků (null). Pro dashboard v pořádku, jen ICE nemůže být povinné pole v kategorii „chybně zadané“.
ID neodpovídá typu: S-S33 — Inspirace: review pripravmese.cz má ID story, ale type: task. Kandidát na novou kontrolu.

### Rozhodnutí (zatím)

- **RBU-S117 — Bug fixing RBU: tlačítko pro generování příkazů:** YAML opraven lokálně (smazaný řádek `- - RBU-E67 — Bug fixing`). Není v kódu tohoto plánu. Commit/push vaultu uživatel neřekl.
- Hierarchy: architekt ověřil, že charter i snapshot mají `hierarchy: true` u všech 17. Boolean se nemění (A1). Pět slugů se nehardcoduje.
- ICE null není chyba (R6).
- **S-S33 — Inspirace: review pripravmese.cz:** nová kontrola `id_type_mismatch`, soubor se nepřepisuje.
- Sirotci se nepřesouvají. Čtyři filename se nepřejmenovávají.
- D1 ze schváleného export plánu se neopravuje.
- Schvalování plánu: ne (uživatel neřekl „se schválením“).
- Grill g=1 (790258f6): Q2 NEBLOKUJÍCÍ → A7: `oid_mismatch` + `oid` jen u `update_task`. `edit_task_body`, `append_task_note`, `set_focus` zůstávají `cas_conflict`.
- Grill g=1: Q3 NEBLOKUJÍCÍ → A8: `id_type_mismatch` jen když raw `type` je `epic` / `story` / `task` a písmeno levelu v ID říká něco jiného. Chybějící type se nehlásí. Neznámý type zůstává `unknown_type`.
- Q1 (uživatel, 2026-10-19): varianta 2. `parent_closed`, když rodič není v aktivní složce `tasks/`. Platí i když ho tohle volání načte z archivu (`include_closed_days` > 0). Aktivní Done/Cancelled ve `tasks/` signál nedostane. Mění A2, větev 2, B38, T32.
- Poznámka Šťourala k plánu (ne otázka): A4 „množina“ = řetězec písmen a číslic v pořadí, ne matematická množina. `get_context` nebere epic post-pass z `build_agent_context.py` 528–529; R1 se nemění.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-19 16:00 | PLAN | d82a8556-6db2-4c4d-bdb9-96d9b2e6a0ee | plán v odpovědi, soubor nezapsal (readonly) | — | hlavní agent zapsal docs/plans/2026-10-19-export-followups.md |
| 2 | 2026-10-19 16:10 | GRILL | 790258f6-bf55-41ec-afe3-44cc0bdbeee9 | POTŘEBUJE ODPOVĚDI (3, z toho 1 BLOKUJÍCÍ) | Q1 BLOKUJÍCÍ | g=1. Q2 a Q3 zapsány jako A7 a A8. Přechod AWAITING_USER (z: grill) |
| 3 | 2026-10-19 16:25 | PLAN | d82a8556-6db2-4c4d-bdb9-96d9b2e6a0ee | plán r=2 v odpovědi | — | Q1 varianta 2 zapracována. Hlavní agent přepsal docs/plans/2026-10-19-export-followups.md |
| 4 | 2026-10-19 16:35 | GRILL | 31ab096e-e4d1-43b5-adce-f2bd1bde9565 | HOTOVÝ GRILL (0 otevřených) | — | g=2. Plán Q1–Q3 neporušuje. Přechod CRITIC |
| 5 | 2026-10-19 16:52 | CRITIC | f7744362-2298-48be-85e9-6cc41afaf89a | SCHVÁLENO | 0/0/0 | kolo 1. Přechod IMPLEMENT (schvalování uživatelem: ne) |
| 6 | 2026-10-19 17:05 | IMPLEMENT | 5b7300ab-7805-4d5e-b5ed-ceb47c9cf20e | gate exit 1, commit není | — | 33 passed, 1 failed (T34 MCP). Kód R1–R4 a R7 v pracovním stromě. REST oid_mismatch prošel |
| 7 | 2026-10-19 17:25 | PLAN | d82a8556-6db2-4c4d-bdb9-96d9b2e6a0ee | plán otevření #2 | Q4 | MCP oid_mismatch vrací CallToolResult, ne RuntimeError. Hlavní agent zapsal plán |
| 8 | 2026-10-19 17:30 | GRILL | 59f21b8e-09c3-4d4a-b9f5-19b80aa4277b | HOTOVÝ GRILL (0 otevřených) | — | g=3. Q4 CallToolResult knihovna potvrzuje. Přechod CRITIC |
| 9 | 2026-10-19 17:38 | CRITIC | 04c69673-e3d5-4ecf-b412-01d08234f032 | SCHVÁLENO | 0/0/0 | otevření #2. Přechod IMPLEMENT delty F4b |
| 10 | 2026-10-19 17:46 | IMPLEMENT | 5b7300ab-7805-4d5e-b5ed-ceb47c9cf20e | commit 0736e9d, gate exit 0, 34 passed | — | lokálně, bez push. Přechod REVIEW |
| 11 | 2026-10-19 17:52 | REVIEW | 8ef5d1ec-ad8d-4c1f-86ad-3fc08d71ae4f | SCHVÁLENO | 0/0/0 | git diff v reviewerovi nešel; review z kódu na disku. Dvě odchylky bez nálezu (úspěch update_task mimo _call; T29 navíc k T28) |
| 12 | 2026-10-19 18:02 | push | 2fc1f1e1-3458-4416-a8da-dc11799083ef | ff 9e0189e..0736e9d | — | Brain deploy 6060 healthy, image 0736e9d, healthz 200. Hub 6061 ještě in_progress |
| 13 | 2026-10-19 18:06 | QA | 0f13530f-126a-4e84-8614-4f69bda22c33 | PASS | B43 NEOVĚŘENO (živý zápis zakázán; T33 lokálně) | export 868/872/856/852 ms, count 533, parent_closed u pěti dětí, MCP i REST oid_mismatch, vault HEAD beze změny. TESTER přeskočeno. Přechod DONE |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| Q4 | MAJOR | PLAN | vyřešen v kódu 0736e9d (F4b, gate 34 passed) | 1 |
