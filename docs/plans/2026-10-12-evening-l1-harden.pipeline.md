# Pipeline: evening-l1-harden

Stav: DONE
Plán: docs/plans/2026-10-12-evening-l1-harden.md
Architekt: c5522f32… · otevření #1 · k=1 · r=3
Šťoural: d64ce46a… HOTOVÝ (1b 2a)
Kritik: 19e59be9… **SCHVÁLENO**
Diff reviewer: 4fef7a7a… **SCHVÁLENO** (kolo 2)
QA: PASS (smoke) na image 95fc60a8
testerGate: ne · TESTER: přeskočeno (profil SECOND_BRAIN)
Schvalování plánu uživatelem: ne → po SCHVÁLENO kritika rovnou IMPLEMENT
Počítadla: návraty 0/3 · REVIEW 2/5 · QA 1/5 · TESTER 0/5 · ENV 1/2
Base (origin/main): e45bc8db0868f9cfa1aa293189fe616f41e9044e
Kódový SHA: 5aa48cb82dd4fd94e5e3b13a76f084bd27962ab3
Review SCHVÁLENO na: 4fef7a7a…
QA PASS na: 95fc60a8 (Coolify; sembly_match_body OK)
Goal: complete

## Projekt
SECOND_BRAIN — kořen `~/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN`, větev `main`,
base = origin/main `e45bc8db…`. Nasazení: push `main` → Coolify `second-brain-hub`.
Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`.
Tester: vždy přeskočeno. Brain app se pro match NEMĚNÍ (jen hub evening).

## Zadání (doslovně)
1. match proti Sembly přepisům — max kvalita, nebourat brain/workflow
2. retry 1–2× při 503 před total degrade
3. slack_token_missing — ENV hotovo; mimo PR

## Rozhodnutí
- Sembly match **varianta A** (haystack bez full transcript / Plný přepis|transkript)
- Pool jen open tasky/stories bez epic; ne 03-AREAS (**volba 1**)
- Retry 1–2× na HTTP 503; backoff 1s/2s
- Brain API / webhook / vault layout neměnit
- Grill Q1=**b**: po cutu cap HEAD_CAP 8192
- Grill Q2=**a**: T15 = Coolify smoke; čísla = pytest T1–T6

## Průběh
| # | Čas | Stav | Agent | Verdikt | Poznámka |
|---|---|---|---|---|---|
| 1 | 2026-10-12T18:25 | PLAN | c5522f32… | plán v1 | A + 1 zamčeno uživatelem |
| 2 | 2026-10-12T18:30 | GRILL | d64ce46a… | POTŘEBUJE ODPOVĚDI | Q1 cap, Q2 T15 | → AWAITING_USER |
| 3 | 2026-10-12T23:35 | AWAITING_USER | uživatel | 1b 2a | → PLAN r=2 → CRITIC |
| 4 | 2026-10-12T23:40 | CRITIC | 9da10542… | K PŘEPRACOVÁNÍ | NEW-1..4 MAJOR | → PLAN r=3 |
| 5 | 2026-10-12T23:42 | CRITIC | 19e59be9… | **SCHVÁLENO** | NEW uzavřeno | → IMPLEMENT |
| 6 | 2026-10-12T23:45 | IMPLEMENT | hlavní | haystack A + 503 retry; 404 passed | → REVIEW |
| 7 | 2026-10-12T23:46 | REVIEW | 8ee42c81… | K OPRAVĚ | NEW-1 keep-only + tests | → IMPLEMENT |
| 8 | 2026-10-12T23:48 | REVIEW | 4fef7a7a… | **SCHVÁLENO** | — | → push |
| 9 | 2026-10-12T21:47 | ENV | Coolify | b502e67 failed Docker Hub TLS | empty retry 95fc60a |
| 10 | 2026-10-12T21:52 | QA | hlavní | T15 smoke PASS; sembly cut OK na image | → DONE |

## Otevřené nálezy
(žádné — NEW z review uzavřené)
