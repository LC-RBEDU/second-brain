# Pipeline: SB3 — Podpora statusu paused u projektů

Stav: CRITIC  
Plán: docs/plans/2026-09-30-sb3-paused-projects.md  
Schvalování plánu uživatelem: ne  
Architekt: agent ID 33629e01-f89c-4ea2-b7d7-8001945888ab, otevření plánu #1, generace k=1/3, kolo r=2/3  
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2  
Base (origin/main před pipeline): cdc28559444b41f0a9ac7c6cae049aab4024a326 · Kódový SHA: (po IMPLEMENT) · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)  
Plán schválen uživatelem: nevyžadováno  
Goal: bez goalu (pipeline_gate recovery)

## Zadání (doslovně)

Z úkolu **SB3 — Podpora statusu paused u projektů v lifecycle a agent-contextu** (batch Rozhodni 30. 9. 2026, uživatel: „toto chci vyřešit — je to solo?“):

- Projít skripty v `scripts/` a `vps/` — kde se čte `status` projektu.
- Vyloučit tasky pauznutých projektů z `top_priority_today` a `top_priority`.
- Vyloučit je z `asap_backfill` (pokud ještě existuje; jinak N/A).
- Doplnit `paused` do konvencí — `second-brain-bootstrap.mdc` + `konvence-a-slovnik.md`.
- Ověřit chování na Krátký potlesk (paused) a Red Button Network (active).

## Rozhodnutí z konverzace

- Solo; asap_backfill N/A; Network nepauzovat.
- Výchozí: nefiltrovat open_epics; nesahej na Waiting/overdue/recurring; push ne; agent-bootstrap ne.
- Po C1: implementována D5/D5a (`should_refresh_hub_state` + `test_paused_projects.py`) a D2 (smazán mrtvý import); pytest 30 passed.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 21:17 | PLAN | — | — | — | Ledger po pipeline_gate |
| 2 | 21:20 | PLAN | 33629e01… | plán | — | → CRITIC r1 |
| 3 | 21:22 | CRITIC | 428d6458… | K PŘEPRACOVÁNÍ | C1 MAJOR, C2/C3 MINOR | → architekt r2 |
| 4 | 21:25 | PLAN | 33629e01… | plán r2 | C1–C3 vyřešeno | D2/D5/D5a implementováno v WT → CRITIC r2 |

## Otevřené nálezy

| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|
| C1 | MAJOR | PLAN→IMPL | vyřešen v #4 (T6+D5a) | 1 |
| C2 | MINOR | IMPL | vyřešen (D2) | 1 |
| C3 | MINOR | PLAN | vyřešen (B10 wording) | 1 |
