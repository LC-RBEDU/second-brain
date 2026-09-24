# Pipeline: Inbound e-mail actionable → add_task

Stav: REVIEW (čeká kolo 3 / SCHVÁLENO po opravě NEW-1)  
Plán: docs/plans/2026-09-24-inbound-email-actionable.md  
Base: ee17b3da · Kódový SHA: (necommitnuto)

## Rozhodnutí uživatele

1. add_task solo + platební příkaz (ne DEEP)
2. triage_llm_run vysvětlen + hard post-filter

## Průběh

| # | Agent | Verdikt |
|---|-------|---------|
| 1 | main IMPLEMENT | bez PLAN/CRITIC |
| 2 | [Review R1](ab68212d-c028-4395-a51f-6db881bb5cc8) | K OPRAVĚ 2 MAJOR |
| 3 | main IMPL | D1–D6 |
| 4 | [Review R2](b4fc542f-cc8b-44db-a196-f39244bf1991) | K OPRAVĚ 1 MAJOR (skill pořadí) |
| 5 | main IMPL | NEW-1–4 opraveny; pytest 8/8 |

Další: krátké REVIEW kolo 3 → commit/push → QA (hub deploy + pytest na VPS).
