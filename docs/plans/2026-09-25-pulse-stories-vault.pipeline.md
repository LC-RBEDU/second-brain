# Pipeline: Pulse stories vault

Stav: IMPLEMENT
Plán: docs/plans/2026-09-25-pulse-stories-vault.md
Schvalování plánu uživatelem: ne
Architekt: agent ID cc1a4de1-5662-4bc3-aa2b-3448ded199cb, otevření plánu #1, generace v otevření k=1/3, kolo r=2/3
Kritik SCHVÁLENO: agent ID 290d0cda-fe42-4e23-8827-900dc5dc4976 (r=2, 0 BLOCKER/MAJOR)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): cdc28559444b41f0a9ac7c6cae049aab4024a326 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER: přeskočeno (profil SECOND_BRAIN — až po QA)
Plán schválen uživatelem: nevyžadováno
Goal: aktivní
Profil: SECOND_BRAIN
Stav: PLAN

## Zadání (doslovně)

`/rbu-pipeline` na schválený vault plán Pulse:

1. Doplnit k **RBU-S96 — Update Monthly a Weekly Strategy Pulse** UI fix (karty + mřížka).
2. Založit další story **Vytvořit Quarterly Strategy Pulse** pod Strategy epic se schváleným DoD.
3. Bez implementace Universe kódu v této pipeline; Universe `/rbu-pipeline` později.

## Rozhodnutí z konverzace

### RBU-S96 UI
- Karta Tile pattern kolem těla sekce; accordion header beze změny; card jen když open.
- Monthly: 5 finančních sekcí (P&L, Plán vs. realita, streamy, struktura nákladů, režie).
- Weekly: `cash`, `pipeline`, `issued_invoicing`, `expected_invoicing`.
- Mřížka = `border-t` mezi metric rows.
- Kroky S96-1/2 forecast zůstávají; nový krok S96-3.

### Quarterly story (parent RBU-E90)
- Status Backlog, agent assist; ID z `next_task_id` (před startem: RBU-S108).
- Cadence quarterly: hub→route+API, RBAC strategy; **bez** e-mail/Celery v1; **bez** sticky semaforů v1.
- Přepínač: poslední uzavřený FY kvartál (default) vs poslední 3 uzavřené měsíce.
- FY Q: Q1 bře–kvě, Q2 čer–srp, Q3 zář–lis, Q4 pro–úno; gate = monthly (1. Po po 15.).
- P&L/streamy/náklady/režie: FY YTD (do konce okna) + okno.
- Plán vs. realita: % OE a % fakturace za okno + YTD zvlášť.
- P&C: headcount+FTE as_of / prům okno / prům FY (mezery vynechat); fakturace/FTE/měsíc = okno + FY YTD; FTE jmenovatel = **průměr FTE období**; výnosy÷prům FTE÷počet uzavřených měsíců.
- Display title sjednotit s hubem Kvartální Pulse.

### Mimo rozsah
- Universe FE/BE, e-mail, Celery, deploy Coolify Universe.
- Forecast implementace (S96-1/2).

## Průběh
| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-09-25 ~22:55 | PLAN | — | — | — | Ledger založen; start architekt |
| 2 | 2026-09-25 ~23:00 | PLAN | cc1a4de1… | plán R1–R7 B1–B10 | — | Plán zapsán do docs/plans |
| 3 | 2026-09-25 | CRITIC | f2a590b9… | FAIL | C1–C3 MAJOR | DoD text / S96-3 / B5 frontmatter |
| 4 | 2026-09-25 | PLAN | cc1a4de1… resume r=2 | — | — | Oprava C1–C5 |

## Otevřené nálezy
| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|
| C1 (NEW-1) | MAJOR | PLAN | otevřený | 1 |
| C2 (NEW-2) | MAJOR | PLAN | otevřený | 1 |
| C3 (NEW-3) | MAJOR | PLAN | otevřený | 1 |
| C4 (NEW-4) | MINOR | PLAN | otevřený | 1 |
| C5 (NEW-5) | MINOR | PLAN | otevřený | 1 |
