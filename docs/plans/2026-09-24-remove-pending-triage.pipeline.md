# Pipeline: Odstranit mrtvou cron/PENDING triáž

Stav: DONE  
Plán: docs/plans/2026-09-24-remove-pending-triage.md  
Commit: cdc2855 · Diff review PASS · QA T4 PASS (coolify-dev image cdc2855)

## Průběh

| # | Stav | Verdikt |
|---|------|---------|
| PLAN kolo 4 | SCHVÁLENO | NEW-1…7 |
| IMPLEMENT | F1–F10 | done |
| REVIEW | PASS | 0 BLOCKER/MAJOR |
| QA T4 | PASS | image bez triage_*_run; inbox_scan OK |

## Výsledek

Triáž = chat `agenda-triage` BATCH/DEEP. Cron pending/LLM writers pryč. `inbox_inventory` + heuristiky + `:gear:` + email-actionable zůstaly.
