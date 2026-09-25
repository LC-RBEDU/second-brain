# Pulse stories vault — implementační plán (SECOND_BRAIN)

Architekt: [rbu-architect](cc1a4de1-5662-4bc3-aa2b-3448ded199cb) · otevření #1 · k=1 · **r=2** (po kritice C1–C5)

## Zadání a požadavky

| R# | Požadavek |
|---|---|
| **R1** | **RBU-S96-3** UI karty+mřížka; S96-1/2 beze změny |
| **R2** | Tile `rounded-lg border border-border bg-card p-3 sm:p-4`; header beze změny; card jen open; `border-t` |
| **R3** | Monthly: pnl/plan/streams/cost_structure/overhead · Weekly: cash/pipeline/issued_invoicing/expected_invoicing |
| **R4** | Story Quarterly pod **RBU-E90**, Backlog, assist, ID z next_task_id (cílově RBU-S108) |
| **R5** | DoD NEW-1…7 v Detail + kroky 1–6 (viz F2 doslovně) |
| **R6** | `build_agent_context.py` |
| **R7** | Bez Universe kódu |

## Předpoklady

A1 ID RBU-S108 (recheck skript) · A2 ICE 8/7/5 · A3 prázdné focus/deadline/review_deadline/waitUntil · A4 story `title` = Vytvořit Quarterly Strategy Pulse; display/hub „Kvartální Pulse“ jen v S108-6 · A5 sectionIds z FE · A6 E90 neupravovat · A7 vault git-ignored · A8 datum 2026-09-25 · A9 prázdná pole jako u S96 (bez `null`)

## Současný stav

- S96: Next, parent `[[RBU-E90 — Strategy]]`, kroky 1–2, updated 2026-09-22
- E90: `title: Strategy` (epic); děti přes parent wikilink
- Hub: „Kvartální Pulse“ + Brzy
- next_task_id → RBU-S108
- Backlog je v `agent-context-light.json` → `tasks[]`, ne v `top_priority`

## Návrh

### F1 — S96 (doslovně)

1. `updated: 2026-09-25` jen
2. Detail + věta: Scope zahrnuje i UI karty (**RBU-S96-3**); forecast v S96-1/2.
3. Přidat checkbox (S96-1/2 neměnit):

```markdown
- [ ] **RBU-S96-3** UI karty + mřížka: kolem těla otevřené sekce wrapper s třídami `rounded-lg border border-border bg-card p-3 sm:p-4` (vzor sticky Cash Tile v `PulseSemaphoreRow`); accordion header `SectionCard` beze změny; card **jen když open**; Monthly sectionId `pnl`, `plan`, `streams`, `cost_structure`, `overhead`; Weekly `cash`, `pipeline`, `issued_invoicing`, `expected_invoicing` (ne `team`/`delivery`/`actions`); mezi metric rows `border-t` → *DoD:* vizuál sedí se sticky Cash Tile
```

4. Log: `- 2026-09-25: Přidán **RBU-S96-3** — UI karty + mřížka (monthly 5 + weekly číselné); forecast S96-1/2 beze změny.`

### F2 — S108 (doslovně)

Před create: `python3 scripts/next_task_id.py rb-universe-development --type story`.

**Frontmatter checklist:**

```yaml
---
id: RBU-S108
type: story
title: Vytvořit Quarterly Strategy Pulse
project: '[[RB Universe development]]'
slug: rb-universe-development
aliases:
- RBU-S108
status: Backlog
parent: '[[RBU-E90 — Strategy]]'
focus:
agent: assist
ice_i: 8
ice_c: 7
ice_e: 5
deadline:
review_deadline:
waitUntil:
created: 2026-09-25
updated: 2026-09-25
materials: []
source: 'Pulse vault plán 2026-09-25 (Cursor + kritik R1; NEW-1…7)'
blocked_by: []
---
```

**Detail** musí obsahovat: cadence quarterly hub→API; RBAC strategy; NEW-4 bez e-mail/Celery; NEW-5 bez sticky; NEW-2 přepínač FY Q default vs 3 uzavřené M; FY Q1 bře–kvě … Q4 pro–úno; gate 1. Po po 15.; NEW-7 YTD do konce okna; NEW-3 % OE/% fakt okno+YTD; P&C as_of/prům okno/prům FY; NEW-6 mezery vynechat; NEW-1 prům FTE; title Kvartální Pulse.

**Operativní kroky:**

```markdown
- [ ] **RBU-S108-1** Cadence quarterly: hub „Kvartální Pulse“ → route + GET report API; RBAC strategy; v1 UI+API **bez** e-mail/Celery (**NEW-4**) a **bez** sticky semaforů (**NEW-5**) → *DoD:* dlaždice naviguje, report načte oprávněnému uživateli strategy
- [ ] **RBU-S108-2** Přepínač okna: default poslední uzavřený FY Q (Q1 bře–kvě … Q4 pro–úno) vs poslední 3 uzavřené reporting měsíce (**NEW-2**); uzavření = monthly gate (1. Po po 15. v M+1) → *DoD:* default i rolling 3M sedí na uzavřená období
- [ ] **RBU-S108-3** P&L / streamy / struktura nákladů / režie: sloupce FY YTD (do posledního dne okna, **NEW-7**) + zvolené okno → *DoD:* obě období ve 4 sekcích
- [ ] **RBU-S108-4** Plán vs. realita: % OE a % fakturace **za okno** + zvlášť YTD (**NEW-3**) → *DoD:* čtyři % hodnoty (okno OE, okno fakt., YTD OE, YTD fakt.)
- [ ] **RBU-S108-5** P&C: headcount+FTE as_of · prům. okna · prům. FY (mezery vynechat, **NEW-6**); fakturace/FTE/měsíc okno + FY YTD = výnosy ÷ prům. FTE období (**NEW-1**) ÷ počet uzavřených měsíců → *DoD:* sekce P&C s čísly dle vzorce
- [ ] **RBU-S108-6** Display title / hub copy = **„Kvartální Pulse“** (bez Brzy) → *DoD:* hub + stránka reportu stejný název
```

Log: založeno pod RBU-E90; DoD NEW-1…7; Universe = samostatný pipeline.

### F3 — build_agent_context.py
### F4 — REVIEW výpis vault; QA T1–T3; TESTER přeskočeno

## B#

| B# | Očekávaný výsledek | T# |
|---|---|---|
| **B1** | S96-3 řádek = F1 bod 3 (CSS, open, 5+4 IDs, border-t); S96-1/2 byte-identical | T1 |
| **B2** | updated 2026-09-25; parent E90; status Next | T1 |
| **B3** | Log 2026-09-25 + S96-3 | T1 |
| **B4** | Soubor S108 (nebo aktuální ID) existuje | T2 |
| **B5** | Frontmatter = F2 YAML checklist včetně `type: story`, přesný parent, prázdná focus/deadline/review_deadline/waitUntil | T2 |
| **B6** | Šest checkboxů 1–6 s NEW-* dle F2 | T2 |
| **B7** | Detail substringy NEW-1…7 + FY Q + gate + RBAC + title | T2 |
| **B8** | context exit 0; light `tasks[]` by id Backlog story (ne top_priority) | T3 |
| **B9** | ID race → aktuální next_task_id | T2 |
| **B10** | Žádný Universe diff | T4 |

## P

N/A API. build_agent_context exit 0.

## T#

T1 read S96 · T2 read S108 · T3 build_agent_context + light jq · T4 no Universe · T5 pytest skip · **TESTER přeskočeno**

## Pořadí

F0 docs → F1 → F2 → F3 → F4 DONE

## Rizika

ID race; duplicitní story; vault mimo git; S96 review_deadline dnes (neměnit); Backlog ≠ TOP.

## Otevřené otázky (neblokující)

ICE 8/7/5; review_deadline prázdné; bez logu E90; Detail věta S96 ano.

## C# → vyřešeno

| C# | Stav |
|---|---|
| C1 | vyřešeno — doslovný Detail + B6/B7 |
| C2 | vyřešeno — doslovný S96-3 + B1 |
| C3 | vyřešeno — B5 frontmatter checklist |
| C4 | vyřešeno — title Strategy |
| C5 | vyřešeno — B8 light tasks[] by id |
