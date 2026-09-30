# Pipeline: SB3 — Podpora statusu paused u projektů

Stav: REVIEW  
Plán: docs/plans/2026-09-30-sb3-paused-projects.md  
Schvalování plánu uživatelem: ne  
Architekt: agent ID 33629e01-f89c-4ea2-b7d7-8001945888ab, otevření plánu #1, generace k=1/3, kolo r=2/3  
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 1/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2  
Base (origin/main před pipeline): cdc28559444b41f0a9ac7c6cae049aab4024a326 · Kódový SHA: 06328a486f37e352f4e6b278ebab58c9a5ce5aa4 · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)  
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

- Solo; asap_backfill N/A; Network nepauzovat; open_epics nefiltrovat; push ne; agent-bootstrap ne.
- Critic r2 SCHVÁLENO (3 MINOR): NEW-1 active positive control v T6 **opraveno**; NEW-2 untracked přidáno do commitu; NEW-3 mirror stale — T3 smoke.
- `.cursor/rules/second-brain-bootstrap.mdc` je gitignored — R4 v commitu přes ŠABLONY konvence + lokální bootstrap (due_soon wording).

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | Poznámka |
|---|---|---|---|---|---|
| 1–4 | 21:17–25 | PLAN/CRITIC | 33629e01 / 428d6458 | C1→oprava | |
| 5 | 21:28 | CRITIC | 2bdd51a9… | SCHVÁLENO | 3 MINOR |
| 6 | 21:30 | IMPLEMENT | hlavní | commit 06328a4 | T6+D5a+D2; NEW-1 fix |
| 7 | 21:30 | REVIEW | (běží) | — | diff 06328a4^..06328a4 |

## Otevřené nálezy

| ID | Závažnost | Stav |
|---|---|---|
| C1–C3 | — | vyřešeno |
| NEW-1 (critic r2) | MINOR | opraveno v T6 |
| NEW-2 | MINOR | commit obsahuje test + ŠABLONY konvence |
| NEW-3 | MINOR | T3 smoke (accepted) |
