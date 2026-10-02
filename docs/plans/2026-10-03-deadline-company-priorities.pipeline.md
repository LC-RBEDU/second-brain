# Pipeline: Deadline bucket + firemní priority → ranking

Stav: REVIEW  
Plán: docs/plans/2026-10-03-deadline-company-priorities.md  
Schvalování plánu uživatelem: ne  
Profil: SECOND_BRAIN  
Architekt: přeskočen (plán vznikl v chatu + critic r1–r4)  
Kritik: agent ID b452f441-d808-4cdd-bfa9-9b506ee2b9e4 (r4 SCHVÁLENO); předchozí 8c617c7d, c2b03b3d, 30fec483  
Počítadla: návraty PLAN 0/3 · REVIEW 0/5 · QA 0/5 · TESTER 0/5 · ENV 0/2  
Base (origin/main před pipeline): 9c6abd68c406856f246337938852be0bc266005e · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER: —  
Goal: aktivní  
Schvalování plánu: ne

## Zadání (doslovně)

chtěl bych ještě jednou lehce upravit způsob používání "deadline" a "review deadline"

Představa je taková, že "deadline" budou mít pouze úkoly s hard deadline. Ostatní úkoly budou mít review deadline.

Pokud se ale zeptám "co teď" a podobně, tak by se měly prioritizovat úkoly s deadline v nejbližší době (týden do budoucna) a poté úkoly dle ICE.

A pak bych chtěl vytvořit někam do vaultu popis firemních priorit a ICE by měl zohledňovat to, zda úkol či story/epic má vazbu na nějakou z těchto priorit nebo ne. Pokud ano, musí to být prioritizováno zvýšením ICE.

… (sheet 2HY 2026) … ok, jdi do toho teď přes /rbu-pipeline

## Rozhodnutí

- deadline bucket ≤7d včetně overdue striktně nad ICE
- review_deadline bez vlivu na pořadí; exclusive s deadline beze změny Rozhodni
- company_bonus +5 (ne mutace I/C); strip neprázdný string
- snapshot model B: pre-sorted + in_deadline_bucket/rank_score; skills neresortují
- B8 ASC overdue first uvnitř bucketu
- 9 aktivních CP z sheetu; jednorázový export
- TESTER: přeskočeno (SECOND_BRAIN)

## Průběh

| # | Čas | Stav | Agent | Verdikt | Poznámka |
|---|---|---|---|---|---|
| 1 | 2026-10-03 | CRITIC r4 | b452f441 | SCHVÁLENO | před /rbu-pipeline |
| 2 | 2026-10-03 | IMPLEMENT | hlavní | OK | rank_key + vault CP + Bases/skills; pytest 253 |
| 3 | 2026-10-03 | REVIEW | — | — | pending |

## Otevřené nálezy

(žádné)
