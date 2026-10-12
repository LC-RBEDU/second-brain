# Pipeline: focus-limits-10-tasks-5-epics

Stav: QA
Plán: docs/plans/2026-10-13-focus-limits-10-tasks-5-epics.md
Architekt: hlavní (limit change, CLARIFY zamčeno uživatelem)
Šťoural: přeskočen (jasné limity)
Kritik: přeskočen (jasné limity; diff review po implementaci)
Diff review: PASS po opravě NEW-1/NEW-2 (pool independence + runbook)
testerGate: ne · TESTER: přeskočeno (profil SECOND_BRAIN)
Base (origin/main): dd3e25bc98d989b568e345f362212c0e4cb90ca3
Kódový SHA: be3d3a308ca715051b7c63b40d5e25e82b68e91f
Goal: aktivní

## Rozhodnutí
- Max 10 focus-eligible tasků/stories; max 5 focused epiců (Doing/Next ekv. filter)
- TOP dnes max 10 tasků; epicy mimo TOP
- Guard reason: deny_focus_task_limit / deny_focus_epic_limit
- Brain error_reason task limitu zůstává `focus_limit_exceeded` (kompatibilita); epic = `focus_epic_limit_exceeded`

## Průběh
| # | Čas | Stav | Verdikt | Poznámka |
|---|---|---|---|---|
| 1 | 2026-10-13 | IMPLEMENT | — | user: max 5 epic / 10 task |
| 2 | 2026-10-13 | IMPLEMENT | — | set_focus + guard + context + docs + tests |
| 3 | 2026-10-13 | REVIEW | FAIL→fix | pool tests + brain-api-runbook; gate 54 passed |
