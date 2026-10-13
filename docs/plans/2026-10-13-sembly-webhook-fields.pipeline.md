# Pipeline: Sembly webhook field mapping + dedupe

**Projekt:** SECOND_BRAIN  
**Base:** `origin/main` @ `98f3aebc56e5c8326e46f5a9369eec4292ac9a68`  
Stav: DONE  
Plán: docs/plans/2026-10-13-sembly-webhook-fields.md  
Schvalování plánu uživatelem: ne  
Architekt: 45c741cf… (k=2 takeover) · kritik d365f09d… SCHVÁLENO  
Šťoural: HOTOVÝ (kola 1–3 + k=2)  
Počítadla: návraty 0/3 · REVIEW 2/5 · QA 1/5 · TESTER 0/5 · ENV 0/2  
Base: `98f3aebc56e5c8326e46f5a9369eec4292ac9a68` · Kódový SHA: `ea1eca04e17c35433667450c725fa300a3bfe3e6` · Review SCHVÁLENO na: `ea1eca04e17c35433667450c725fa300a3bfe3e6` · QA PASS na: `ea1eca04e17c35433667450c725fa300a3bfe3e6` · TESTER: přeskočeno (profil SECOND_BRAIN)  
Goal: bez goalu

## Zadání (doslovně)
Bug: sembly_template mapuje title/start_time/transcript místo meeting_title/meeting_started_at/meeting_transcription → unknown-time-meeting.md → false dedupe. Duration sekundy. Dedupe .keys. Oprav + testy + push main + Coolify smoke.

## Rozhodnutí
A1–A16; R11 hard gate exact path; schválení plánu ne; C19 F6 exists-guard; TESTER skip.

## Průběh
| # | Stav | Verdikt | Poznámka |
|---|---|---|---|
| … | PLAN/GRILL/CRITIC | k=1 → k=2 | C1–C18 |
| … | CRITIC | SCHVÁLENO | MINOR C19 |
| … | IMPLEMENT | 88 pytest | commits 19389ea + ea1eca0 |
| … | REVIEW | SCHVÁLENO | D1/D2 fixed |
| … | push main | ea1eca0 | Coolify deploy 6002 finished |
| … | QA | PASS | B1–B18; B8 smoke; B12 cleanup |
| … | TESTER | přeskočeno | profil SECOND_BRAIN |
| … | DONE | | |

## Otevřené nálezy
| ID | Stav |
|---|---|
| C1–C19, D1–D2 | vyřešeno |

## Důkazy
- Push: `ea1eca04e17c35433667450c725fa300a3bfe3e6` → `origin/main`
- Image: `…:ea1eca04e17c35433667450c725fa300a3bfe3e6`
- Smoke: `path=01-INBOX/sembly/2026-10-13-1200-Brain-Smoke.md`, `deduped=false`
- R11: deleted `unknown-time-meeting.md` + `15166792.path` + smoke artefakty; B12_OK
