# Pipeline: Sembly webhook field mapping + dedupe

**Projekt:** SECOND_BRAIN  
**Base:** `origin/main` @ `98f3aebc56e5c8326e46f5a9369eec4292ac9a68`  
Stav: REVIEW  
Plán: docs/plans/2026-10-13-sembly-webhook-fields.md  
Schvalování plánu uživatelem: ne  
Architekt: agent ID 45c741cf-d837-48a6-88da-bf83f4b9809e (k=2), otevření #1, r=1/3 po takeover  
Šťoural: 87493410… HOTOVÝ · kritik d365f09d… SCHVÁLENO (1 MINOR C19 zapracován)  
Počítadla: návraty 0/3 · REVIEW 1/5 · QA 0/5 · TESTER 0/5 · ENV 0/2  
Base: `98f3aebc56e5c8326e46f5a9369eec4292ac9a68` · Kódový SHA: (pending commit) · Review: — · QA: — · TESTER: přeskočeno (profil SECOND_BRAIN)  
Goal: bez goalu

## Zadání (doslovně)
Bug: sembly_template mapuje title/start_time/transcript místo meeting_title/meeting_started_at/meeting_transcription → unknown-time-meeting.md → false dedupe. Duration možná sekundy. Dedupe .keys. Oprav + testy + push main + Coolify smoke. Recovery mimo scope. Secrets ne.

## Rozhodnutí
A1–A16; R11 hard gate exact path; schválení plánu ne; C19 F6 exists před list_dir; TESTER skip.

## Průběh
| # | Čas | Stav | Agent | Verdikt | Poznámka |
|---|---|---|---|---|---|
| 1–10 | … | PLAN/GRILL/CRITIC | … | k=1 r=1–3 MAJOR | → fresh architekt k=2 |
| 11 | … | PLAN | 45c741cf | plán k=2 | A1–A16 embed |
| 12 | … | GRILL | 87493410 | HOTOVÝ | |
| 13 | … | CRITIC | d365f09d | SCHVÁLENO | MINOR C19 |
| 14 | … | IMPLEMENT | main | pytest 87 passed | commit pending |
| 15 | … | REVIEW | pending | | |

## Otevřené nálezy
| ID | Závažnost | Stav |
|---|---|---|
| C19 | MINOR | vyřešen v plánu F6 exists-guard |
