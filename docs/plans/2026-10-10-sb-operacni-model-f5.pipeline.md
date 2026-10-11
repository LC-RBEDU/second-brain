# Pipeline: SB operační model F5

Stav: AWAITING_USER (z: F5-c Grok UI — T2–T4 / New Bot)
Plán: docs/plans/2026-10-10-sb-operacni-model-f5.md
Schvalování plánu uživatelem: ne
Architekt: parent delta · otevření #1 · k=2/3 · r=1/3
Šťoural: 714fee03… · g=1 HOTOVÝ
Kritik: 00396014… · kolo 3 → SCHVÁLENO
Reviewer: dd148c74… · SCHVÁLENO (0B/0M/1m → fix `3df393e`)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 1/5 · kola QA 1/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): 80403c65803d20971f35aee00abf766fe39e5230 · Kódový SHA: 3df393e · Review SCHVÁLENO na: 3df393e · QA PASS na: 3df393e (lokální pytest 429; Coolify redeploy netřeba — docs) · TESTER: přeskočeno (profil SECOND_BRAIN)
Goal: paused-awaiting-user
Plán schválen uživatelem: nevyžadováno
Goal: —
Profil: SECOND_BRAIN

## Zadání (doslovně)

ok, pusť se do F5 a pak co znamená ten Claude artifact? ten ještě nevznikl ne?

## Rozhodnutí / důkazy IMPLEMENT

- F5-a: vault `materials/2026-10-11 — boti-prehled.md` + paste blocky
- F5-b: guide Brain-first, cowork, morning override, claude-project, mrluc-loader, runbook F5, superseded note
- T12: Coolify hub `GROK_BOT_REMINDER_*` ≡ brain `GROK_BOT_MEETING_PREP_*` (ciphertext md5 match; runtime sha12 `f23353b728ef`; deploy queue id 5899 finished)
- Pytest: `test_f5_docs_brain_first.py` + plný suite před commit
- **F5-c zbývá (ruční Grok):** smazat New Bot; paste z boti-prehled; plugin; smoke T2–T4 → teprve **SB15-6** `[x]`

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | Poznámka |
|---|---|---|---|---|---|
| 1–8 | 2026-10-11 | PLAN→CRITIC | … | SCHVÁLENO kolo 3 | 00396014 |
| 9 | 2026-10-11 | IMPLEMENT | parent | F5-a/b + T12 | F5-c open |
