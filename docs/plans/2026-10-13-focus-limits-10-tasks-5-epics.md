# Plán: Focus limity — 10 tasků + 5 epiců

## Zadání
Focus na týden: max **5 epiců**, max **10 tasků** (stories / legacy task). Důvod: víc tasků může mířit stejným směrem.

## Model
| Sloty | Co počítá | Limit |
|---|---|---|
| Task | `is_focus_eligible` (story/task, Doing/Next, focus=aktuální týden, ¬paused) | **10** |
| Epic | `is_epic` ∧ focus=aktuální týden ∧ status ∉ Waiting/Backlog/Done/Cancelled ∧ ¬paused | **5** |

- `top_priority_today` = focused **tasky**, max **10** (epicy dál mimo TOP).
- `set_focus`: nový vstup do task slotu deny při ≥10; nový epic deny při ≥5.
- Re-set / clear / ne-eligible beze změny (allow).
- `stats.focus_count` = task slots; `stats.focus_epic_count` = epic slots; `focus_limit=10`, `focus_epic_limit=5`.
- Guard: `deny_focus_task_limit` / `deny_focus_epic_limit` (nahrazuje `deny_focus_over_5`).

## Soubory
`focus.py`, `today_priority.py`, `set_focus.py`, `agent_context_build.py`, `scripts/build_agent_context.py`, `agent_write_guard.py`, testy, bootstrap/skills/README.

## Mimo rozsah
Scorované match, změna Waiting/Backlog eligibility, UI.
