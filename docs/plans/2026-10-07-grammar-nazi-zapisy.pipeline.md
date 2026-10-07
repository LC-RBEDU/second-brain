# Pipeline: grammar-nazi zápisy
Stav: REVIEW
Plán: docs/plans/2026-10-07-grammar-nazi-zapisy.md
Schvalování plánu uživatelem: ne
Architekt: 3a1de96c-5cd2-4846-9c2b-294346f659a4, k=3/3, r=1/3
Šťoural: f44ab7f0… HOTOVÝ GRILL (post C9–C11)
Kritik: ffc57bb8… · **SCHVÁLENO** (0 BLOCKER, 0 MAJOR, 2 MINOR → C12/C13 do F4)
Počítadla: návraty 0/3 · REVIEW 0/5 · QA 0/5 · TESTER 0/5 · ENV 0/2
Base: f84c7081ac4d2e778dbf33abb4f377e4806aeb5e · Kódový SHA: 52e298e064b5fb24d416adba8fa690bf1050d1b4 · TESTER: přeskočeno (SECOND_BRAIN)

## Zadání uživatele (doslovně)
Přidej do skillu zápisu ze schůzky extra agenta grammar-nazi, který projde veškeré texty a opraví gramatiku (překlepy, skloňování, časování) a dohlédne na tone-of-voice — jen vybranou vrstvu (gramatika + thin anti-AI meeting language, ne full rbe offer voice); běží před preview; celý zápis; tichý rewrite; Cursor + Claude; CS/EN.

## Rozhodnutí z konverzace
Q1–Q7 + grill g=1–g=4 (viz plán R#/A#); kritik SCHVÁLENO včetně C12/C13 v F4; Schvalování plánu: ne.
Plán schválen uživatelem: nevyžadováno
Goal: aktivní (REVIEW)

## Projekt
SECOND_BRAIN — lokální ŠABLONY/ + scripts/ + dist ZIP + pytest fingerprint.

## Otevřené nálezy
| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|
| C1–C11 | … | PLAN | vyřešeno | 1 |
| C12 | MINOR | PLAN | zapracováno v F4 (baseline před editací) | 1 |
| C13 | MINOR | PLAN | zapracováno v F4 (Vault?=jen zápis default) | 1 |

## Implementace (F1–F6)
- F1: skill + meeting-language + md_fingerprint CLI + fixtures + struktura-vystupu Highlights
- F2: ŠABLONY/cursor-agents/grammar-nazi.md (readonly)
- F3: install_agenda_skills.sh (grammar-nazi + agents) — T1 OK (symlinky)
- T6/T7: `python3 -m pytest scripts/tests/test_md_fingerprint.py -q` → **10 passed**
- F4: agenda-zapis SKILL (DEEP#1, GN-1/2, A31/A32, meta A29, Krok 8 preview SSOT)
- F5: README, mrluc-agent-skills.mdc, claude-project-instructions; rbe exclusion beze změny
- F6: dist/grammar-nazi-claude.zip + INSTALL.md

## Průběh
| # | Čas | Stav | Agent | Verdikt |
|---|---|---|---|---|
| … | … | … | … | g=1–g=6, k=2→k=3, kritiky |
| 15 | 2026-10-08 | CRITIC | ffc57bb8… | SCHVÁLENO → IMPLEMENT |
| 16 | 2026-10-08 | IMPLEMENT | main | F1–F6 hotovo; pytest 10 passed → REVIEW |
