# Pipeline: grammar-nazi zápisy
Stav: QA
Plán: docs/plans/2026-10-07-grammar-nazi-zapisy.md
Schvalování plánu uživatelem: ne
Architekt: 3a1de96c-5cd2-4846-9c2b-294346f659a4, k=3/3, r=1/3
Šťoural: f44ab7f0… HOTOVÝ GRILL (post C9–C11)
Kritik: ffc57bb8… · **SCHVÁLENO**
Diff reviewer: abeb0f34… · **SCHVÁLENO** (0 BLOCKER, 0 MAJOR; MINOR NEW-5/6/7 neblokují)
Počítadla: návraty 0/3 · REVIEW 2/5 · QA 0/5 · TESTER 0/5 · ENV 0/2
Base: f84c7081ac4d2e778dbf33abb4f377e4806aeb5e · Kódový SHA: 26d3527109236578166ba3053894aac779c17501 · TESTER: přeskočeno (SECOND_BRAIN)
Push: origin/main = 26d3527 (2026-10-08)
Lokální gate před push: `python3 -m pytest scripts/tests -q` → **50 passed**
ZIP T8: grammar-nazi-claude.zip obsahuje SKILL, meeting-language, md_fingerprint, fixtures, INSTALL

## Zadání uživatele (doslovně)
Přidej do skillu zápisu ze schůzky extra agenta grammar-nazi, který projde veškeré texty a opraví gramatiku (překlepy, skloňování, časování) a dohlédne na tone-of-voice — jen vybranou vrstvu (gramatika + thin anti-AI meeting language, ne full rbe offer voice); běží před preview; celý zápis; tichý rewrite; Cursor + Claude; CS/EN.

## Rozhodnutí z konverzace
Q1–Q7 + grill g=1–g=4 (viz plán R#/A#); kritik SCHVÁLENO včetně C12/C13 v F4; Schvalování plánu: ne.

## Projekt
SECOND_BRAIN — lokální ŠABLONY/ + scripts/; Coolify hub se netýká (žádná změna vps/).

## Otevřené nálezy
| ID | Závažnost | Typ | Stav |
|---|---|---|---|
| NEW-5/6/7 | MINOR | IMPL/PLAN | akceptováno po SCHVÁLENO review (neblokuje) |

## Průběh
| # | Čas | Stav | Agent | Verdikt |
|---|---|---|---|---|
| 15 | 2026-10-08 | CRITIC | ffc57bb8… | SCHVÁLENO → IMPLEMENT |
| 16 | 2026-10-08 | IMPLEMENT | main | F1–F6; commit 52e298e |
| 17 | 2026-10-08 | REVIEW | 45651620… | K OPRAVĚ NEW-1…5 |
| 18 | 2026-10-08 | IMPLEMENT | main | fix → 26d3527; pytest 13 + scripts/tests 50 |
| 19 | 2026-10-08 | REVIEW | abeb0f34… | SCHVÁLENO → push → QA |
