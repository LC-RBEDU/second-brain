# Pipeline: Deadline bucket + firemní priority → ranking

Stav: DONE  
Plán: docs/plans/2026-10-03-deadline-company-priorities.md  
Schvalování plánu uživatelem: ne  
Profil: SECOND_BRAIN  
Architekt: přeskočen (plán vznikl v chatu + critic r1–r4)  
Kritik: agent ID b452f441-d808-4cdd-bfa9-9b506ee2b9e4 (r4 SCHVÁLENO); předchozí 8c617c7d, c2b03b3d, 30fec483  
Počítadla: návraty PLAN 0/3 · REVIEW 1/5 · QA 1/5 · TESTER 0/5 · ENV 0/2  
Base (origin/main před pipeline): 9c6abd68c406856f246337938852be0bc266005e · Kódový SHA: 6f88837e034586c6ca653a33ae951a5d03b7d776 · Review SCHVÁLENO na: 37d1981 (95d22a13) + docs 6f88837 · QA PASS na: 6f88837 (bde0da3c) · Deploy: coolify-dev image `…:6f88837e` (2026-10-02 23:51 finished) · TESTER: přeskočeno (profil SECOND_BRAIN)  
Goal: complete  
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
| 3 | 2026-10-03 | REVIEW | 1730e520 | K OPRAVĚ | MAJOR NEW-1 co-ted truncate |
| 4 | 2026-10-03 | IMPLEMENT | hlavní | OK | fix 37d1981 |
| 5 | 2026-10-03 | REVIEW | 95d22a13 | SCHVÁLENO | 0 MAJOR |
| 6 | 2026-10-03 | PUSH | hlavní | OK | e62796a..6f88837 → main |
| 7 | 2026-10-03 | QA | bde0da3c | PASS | Coolify 6f88837; pytest 254; B1–B9 |
| 8 | 2026-10-03 | testerGate | — | TESTER: přeskočeno (SECOND_BRAIN) | |
| 9 | 2026-10-03 | DONE | hlavní | gate 254 passed | |

## Otevřené nálezy

(žádné)
