# Pipeline: rbedu-grammar-nazi (rename + scope)

Stav: AWAITING_USER (z: grill) — pauza: uživatel přerušil (chtěl /daily capture, ne pipeline)
Plán: docs/plans/2026-10-08-rbedu-grammar-nazi-rename.md
Schvalování plánu uživatelem: ne
Architekt: 0b071ad7… · otevření #1 · k=1 · r=1
Šťoural: 864fff89… · kolo g=1 · POTŘEBUJE ODPOVĚDI (4 BLOKUJÍCÍ)
Kritik: —
Diff reviewer: —
QA: —
testerGate: ne · TESTER: přeskočeno (profil SECOND_BRAIN)
Počítadla: návraty 0/3 · REVIEW 0/5 · QA 0/5 · TESTER 0/5 · ENV 0/2
Base: 674a82a9373cc02a790e24a2ecf48222ccd61719 (= origin/main / HEAD před touto deltov)
Kódový SHA: (zatím uncommitted WIP)
Goal: bez goalu (pipeline_gate auto-resume, ne /rbu-pipeline s goal)

## Zadání uživatele (doslovně)

(Implicitní ze stavu working tree + pipeline_gate po DONE parent pipeline `2026-10-07-grammar-nazi-zapisy`:)

Přejmenuj skill `grammar-nazi` na `rbedu-grammar-nazi`, rozšiř jazykový průchod na obecné texty týmu RB EDU (e-maily, Slack, dokumenty, wiki, prezentace, artefakty) při zachování přísného režimu zápisu s fingerprint; vždy in-process (bez Cursor agenta `grammar-nazi`); aktualizuj `install_agenda_skills.sh`, pytest cestu, napojení `agenda-zapis-ze-schuzky`, Claude dist/ZIP; odstraň starý skill a cursor-agent.

## Rozhodnutí z konverzace

| # | Rozhodnutí |
|---|---|
| D1 | Parent pipeline grammar-nazi zápisy = DONE (QA PASS s výhradami T3; ledger `2026-10-07-grammar-nazi-zapisy.pipeline.md` obnoven z git). |
| D2 | Tato pipeline = delta: rename + scope + zrušení Cursor agenta. |
| D3 | Schvalování plánu uživatelem: ne (default SECOND_BRAIN / gate resume). |
| D4 | TESTER vždy přeskočen (profil SECOND_BRAIN). |
| D5 | WIP už existuje ve working tree — architekt ověří proti kódu; IMPLEMENT = dovést/opravovat dle schváleného plánu, ne začínat od nuly. |

## Projekt

SECOND_BRAIN — `ŠABLONY/skills/`, `scripts/`; Coolify hub nedotčen. Lokální gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`.

## Průběh

| # | Čas | Stav | Agent | Verdikt | Poznámka |
|---|---|---|---|---|---|
| 1 | 2026-10-08 ~18:08 | PLAN | — | — | pipeline_gate: 372 řádků bez ledgeru → založen ledger, parent plány obnoveny z HEAD |
| 2 | 2026-10-08 ~18:12 | PLAN | 0b071ad7… | plán k=1 r=1 | F0 fingerprint = jen docstring (ověřeno); G1–G5 mezery WIP |
| 3 | 2026-10-08 ~18:13 | GRILL | 864fff89… | POTŘEBUJE ODPOVĚDI | Q1–Q6 (BLOKUJÍCÍ Q1,Q2,Q4,Q5); NEBLOKUJÍCÍ Q3→1, Q6→1 |
| 4 | 2026-10-08 ~18:15 | AWAITING_USER (z: grill) | — | — | čeká na Q1,Q2,Q4,Q5 |

## Grill g=1 — čeká na odpovědi

| Q# | BLOKUJÍCÍ | Doporučení Šťourala | Odpověď |
|---|---|---|---|
| Q1 auto-trigger obecného režimu | ano | 1 skill-description auto | |
| Q2 detekce režimu zápis | ano | 1 OR (Meta ∨ doc_type) | |
| Q3 HANDOFF tělo | ne | 1 truncate + DONE hlavička | (default) |
| Q4 T3 v této deltě | ano | 1 Ne (T9 stačí) | |
| Q5 B34 grep allowlist | ano | 1 aktivní runtime paths | |
| Q6 F5 globál rule | ne | 1 one-shot sync | (default) |

## Otevřené nálezy

(zatím žádné)

## Související

- Parent DONE: [2026-10-07-grammar-nazi-zapisy.pipeline.md](./2026-10-07-grammar-nazi-zapisy.pipeline.md)
- WIP: `ŠABLONY/skills/rbedu-grammar-nazi/` (untracked), delete `grammar-nazi/`, delete `cursor-agents/grammar-nazi.md`
