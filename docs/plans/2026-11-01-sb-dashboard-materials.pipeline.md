# Pipeline: sb-dashboard-materials

Stav: DONE
Plán: docs/plans/2026-11-01-sb-dashboard-materials.md
Schvalování plánu uživatelem: ne
Architekt: e7dc58bd→465e2959→hlavní r=3…6; Šťoural 4eb5646c; Kritik 8fc150ad SCHVÁLENO
Implementace: F1–F5 hotovo (normalize, FE A12–A16, testy); lokální gate pytest+vitest PASS
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): ff46df06016e90f065201f77625ae8794d7d0ac2 · Kódový SHA: 0f20d546b1a494d14d2ab21a80c1624c14fd94d6 · Review SCHVÁLENO na: 0f20d546b1a494d14d2ab21a80c1624c14fd94d6 · QA PASS na: 033ed58da671752c1bdfdff60735280b8fa8722d (PASS s výhradami: T14 live OAuth DATA-NELZE; přijato orchestrátorem) · TESTER PASS na: 033ed58 (T6 PASS, 93905f4a)
Plán schválen uživatelem: nevyžadováno
Vizuální gate člověka: ne (A4)
Goal: aktivní
Projekt: SECOND_BRAIN
UI produkt: ano (vps/second-brain-dashboard) — Tester povinný (subagent-ui-gate); vizuální B# + layout probe
Vizuální gate člověka: ne (A4)

## Zadání (doslovně)

> potřebuji, aby se při ukládání tasků uložily taky související materiály a odkazy na ně.
>
> Příklad: u tasku IAD-T168 by měl být odkaz na Slack nebo samotný web, kde se dá na akci registrovat
>
> (později) ok, push
> prostě tenhle task řeš přes /rbu-pipeline

## Rozhodnutí z konverzace

- Pole `materials` ve frontmatter (URL i `[[wikilink]]`); při Uložit Detail i Založit Nový.
- URL z textu Detailu se při save/create sloučí do `materials` (harvest).
- Brain `update_task` musí umět YAML list bez orphan řádků (incident IAD-T168).
- **IAD-T168** už opraven ve vaultu (`second-brain-vault` `36a6a7b4`): Gmail + Circle event tracking URL + https://no-work.circle.so; Detail s RSVP poznámkou. Pipeline se na vault data nezaměřuje jako T# ostrý zápis (už hotové).
- Lokálně existuje WIP (necommitnutý) v Brain + dashboard — architekt plánuje proti zadání a kódu; IMPLEMENT sjednotí s WIP nebo přepíše.
- Dřívější řádek v `pipeline-exceptions.md` pro materials se touto pipeline ruší jako způsob dodání (plná pipeline).

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-11-01 | CLARIFY→PLAN | hlavní | — | — | Bez blokující otázky; start architekt |
| 2 | 2026-11-01 | PLAN | e7dc58bd | plán v1 | — | WIP OK směr; F1–F8; vizuální B#; Tester povinný → GRILL |
| 3 | 2026-11-01 | GRILL | 4eb5646c | VRÁTIT_ARCHITEKTOVI | — | B11/baselineOf/A8–A11 chybí |
| 4 | 2026-11-01 | PLAN | 465e2959 | plán r=2 | — | B11 A8–A11 baselineOf uzavřené Q → CRITIC |
| 5 | 2026-11-01 | CRITIC | d39aad87 | K PŘEPRACOVÁNÍ | 1 BLOCKER 2 MAJOR | NEW-1 wikilink/toHref; NEW-2 materialsKey; NEW-3 original |
| 6 | 2026-11-01 | PLAN | hlavní | plán r=3 | — | A12–A14 T18 → CRITIC #2 |
| 7 | 2026-11-01 | CRITIC | 0baff94d | K PŘEPRACOVÁNÍ | NEW-5 BLOCKER NEW-6 MAJOR | baseline z list exportu; materialsKey string |
| 8 | 2026-11-01 | PLAN | hlavní | plán r=4 | — | A15 + A13 dual → CRITIC #3 |
| 9 | 2026-11-01 | CRITIC | a643f95c | K PŘEPRACOVÁNÍ | NEW-7 | dirty≠effective |
| 10 | 2026-11-01 | CRITIC | 409eb9b3 | K PŘEPRACOVÁNÍ | NEW-9 | T4 vs A16 |
| 11 | 2026-11-01 | CRITIC | 8fc150ad | SCHVÁLENO | 0B 0M | MINOR NEW-11 T10(d) → IMPLEMENT |
| 12 | 2026-11-01 | IMPLEMENT | hlavní | gate PASS | — | → REVIEW |
| 13 | 2026-11-01 | REVIEW | 2c997311 | SCHVÁLENO | 0B 0M | T7/T10/T16 OK → push + QA |
| 14 | 2026-11-01 | QA | f320c65a | PASS s výhradami | DATA-NELZE T14 | → testerGate T6 |
| 15 | 2026-11-01 | TESTER | 93905f4a | PASS | T6 9/9 | → DONE audit |
| 16 | 2026-11-01 | DONE | hlavní | gate exit 0 | — | pytest+vitest+T6 |

## Otevřené nálezy

| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|

- 2026-11-01: QA PASS s výhradami (OAuth DATA-NELZE) přijato → Tester T6.

## DONE audit
- Kritik SCHVÁLENO (8fc150ad) na plán r=6
- Review SCHVÁLENO (2c997311) na 0f20d54
- QA PASS s výhradami přijato (f320c65a) na 033ed58
- Tester PASS (93905f4a) T6 na 033ed58
- Vizuální gate člověka: ne (A4)
- Vlastní gate: pytest materials 7+1, BFF 1, vitest 42 — exit 0
