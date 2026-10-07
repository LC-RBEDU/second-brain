# Pipeline: grammar-nazi zápisy
Stav: DONE
Plán: docs/plans/2026-10-07-grammar-nazi-zapisy.md
Schvalování plánu uživatelem: ne
Architekt: 3a1de96c… k=3 · Šťoural: f44ab7f0… · Kritik: ffc57bb8… SCHVÁLENO
Diff reviewer: abeb0f34… SCHVÁLENO (0 BLOCKER/MAJOR)
QA: f741e898… **PASS s výhradami** — výhrady = T3 živý GN rewrite (B2/B3/B7/B8) DATA-NELZE; dle plánu T3=ruční/gate. Akceptováno (neproduktová regrese).
testerGate: ne · TESTER: přeskočeno (profil SECOND_BRAIN)
Počítadla: návraty 0/3 · REVIEW 2/5 · QA 1/5 · TESTER 0/5 · ENV 0/2
Base: f84c7081ac4d2e778dbf33abb4f377e4806aeb5e
Kódový SHA (funkční): 26d3527109236578166ba3053894aac779c17501
Ledger docs SHA: de422f720e9b44cf6237582f461b8d4c87985fcb (origin/main)
Vlastní gate: `python3 -m pytest scripts/tests -q` → **50 passed**; fingerprint **13 passed**
Goal: complete

## Zadání uživatele (doslovně)
Přidej do skillu zápisu ze schůzky extra agenta grammar-nazi, který projde veškeré texty a opraví gramatiku (překlepy, skloňování, časování) a dohlédne na tone-of-voice — jen vybranou vrstvu (gramatika + thin anti-AI meeting language, ne full rbe offer voice); běží před preview; celý zápis; tichý rewrite; Cursor + Claude; CS/EN.

## Projekt
SECOND_BRAIN — ŠABLONY + scripts; Coolify hub nedotčen.

## Dodáno
- Skill `grammar-nazi` + `meeting-language` + CLI `md_fingerprint.py` + fixtures
- Cursor agent + install symlinky
- Napojení `agenda-zapis-ze-schuzky` (DEEP#1, GN-1/2, A31/A32, meta A29)
- Claude ZIP `ŠABLONY/skills/grammar-nazi/dist/grammar-nazi-claude.zip`
- pytest T6/T7

## Průběh (zkráceně)
IMPLEMENT → REVIEW (oprava NEW-1…4) → REVIEW SCHVÁLENO → push 26d3527 → QA PASS s výhradami T3 → testerGate skip → DONE
