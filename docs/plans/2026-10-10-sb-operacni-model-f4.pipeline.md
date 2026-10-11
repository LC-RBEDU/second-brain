# Pipeline: SB operační model F4

Stav: PUSH/QA
Plán: docs/plans/2026-10-10-sb-operacni-model-f4.md
Schvalování plánu uživatelem: ne
Architekt: parent · otevření #1 · k=1/3 · r=6
Šťoural: 19f63106… · g=1 HOTOVÝ
Kritik: 08fa7f49… · SCHVÁLENO
Review: 4dae76cc… · SCHVÁLENO
Kódový SHA: tip main (po MINOR README)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): 7e63304962eba5bb1f769d9d90ed40b6c71696f9 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: —
Plán schválen uživatelem: nevyžadováno
Goal: —
Profil: SECOND_BRAIN

## Zadání (doslovně)

ok a můžeme teď tedy dál na F4?

(kontext: F3 DONE s výhradami 2026-10-11 tip `7e63304`; **SB15-4** `[x]`; další **SB15-5**)

## Rozhodnutí z konverzace

- F0 F4 scope: stop `slack_poll` dump; Drive jen R9; Obsidian nepovinný pull-only; Claude artifact dashboard; sync-architecture docs. R# R7, R9, R15, R24.
- F3 DONE s výhradami (B18 / T8 / B21 / Grok prep webhook) — akceptováno přechodem na F4.
- Schvalování plánu: ne (jako F2/F3).
- TESTER: přeskočeno (profil SECOND_BRAIN).

### Grill g=1 HOTOVÝ — defaulty (2026-10-11)

- **Q1/A4** — one-shot archiv residual `01-INBOX/slack/*` → `07-ARCHIV/…` (CAS + dry-run).
- **Q2/A7** — bez cron unreact; volitelně skill.
- **Q3/A9** — `/v1/context/light` OAuth human; FAIL → DONE s výhradou + fail-path.
- **Q4/A11** — Obsidian Sync mobil neobnovovat.
- **Q5/A16** — proactivity copy bez provozní závislosti na `slack_dump_count` (live triáž).
- **A5** (bez otázky) — poll kód ≤14 dní + `SLACK_POLL_DUMP=0` + crontab off.

### Kritik NEW-1 / reply (2026-10-11)

- **CAS archiv = 1** — rozšířit `GitVault.move(..., expect_oid=)` + B6/T4.
- **agenda-reply = ano** — F4 upraví skill: žádný nový dump zápis do `01-INBOX/slack/`; live/permalink.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-11 | PLAN | 9881f75d… | draft plán | — | f4.md na disk |
| 2 | 2026-10-11 | GRILL | 19f63106… | HOTOVÝ GRILL | 0 BLOKUJÍCÍ | A4–A16 defaulty → CRITIC |
| 3 | 2026-10-11 | CRITIC | 4ac70381… | K PŘEPRACOVÁNÍ | 3 MAJOR | NEW-1…3 |
| 4 | 2026-10-11 | PLAN | ac7540d0… (r=2) | draft | — | CAS move + reply + B26–28 |
| 5 | 2026-10-11 | CRITIC | 98f935d8… | K PŘEPRACOVÁNÍ | 1 BLOCKER + 2 MAJOR | list_dir oid; attachments; T18/T19 |
| 6 | 2026-10-11 | PLAN | parent r=3 | draft | — | stat oid + attach + T18/T19 |
| 7 | 2026-10-11 | CRITIC | 8dd57969… | K PŘEPRACOVÁNÍ | 2 MAJOR | P1 trio; archive dest |
| 8 | 2026-10-11 | PLAN | parent r=4 | draft | — | P1+dest+T20 |
| 9 | 2026-10-11 | CRITIC | b54af915… | K PŘEPRACOVÁNÍ | 1 MAJOR | co-ted podmíněný / mimo F4-e |
| 10 | 2026-10-11 | PLAN | parent r=5 | draft | — | co-ted B29/T21; no archive_inbox_capture; L66 |
| 11 | 2026-10-11 | CRITIC | 682c127a… | K PŘEPRACOVÁNÍ | 1 BLOCKER | orphan Path.rename / dry-run |
| 12 | 2026-10-11 | PLAN | parent r=6 | draft | — | orphan CAS+dry-run; F4-e risk |
| 13 | 2026-10-11 | CRITIC | 08fa7f49… | SCHVÁLENO | 0 | IMPLEMENT smí |
| 14 | 2026-10-11 | IMPLEMENT | parent | in progress | — | F4-a…i kód+docs; pytest hub 311 / brain 58 |
| 15 | 2026-10-11 | NOTE | — | F4-a | — | backup slack-poll-state.backup-2026-10-11.json; dump md=89 other=101 |
| 16 | 2026-10-11 | IMPLEMENT | parent | commit da00106 | — | pytest hub 311 brain 58 scripts 57 |
| 17 | 2026-10-11 | REVIEW | — | start | — | base 7e63304..da00106 |
