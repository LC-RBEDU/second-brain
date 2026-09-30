# Plán: SB3 — Podpora `paused` u projektů v lifecycle a agent-contextu

## Zadání a požadavky

| R# | Požadavek | Zdroj |
|---|---|---|
| **R1** | Projít skripty — kde se čte `status` projektu (hub). | SB3 |
| **R2** | Vyloučit tasky pauznutých z `top_priority_today` / `top_priority`. | SB3 |
| **R3** | `asap_backfill` — **N/A** (neexistuje). | SB3 + rozhodnutí |
| **R4** | Konvence: `second-brain-bootstrap.mdc` + `konvence-a-slovnik.md`. | SB3 |
| **R5** | Ověřit Krátký potlesk (paused) + Red Button Network (active). | SB3 |
| **R6** | Hub state nepřepisuje `## Stav (auto)` u paused. | Kontext |
| **R7** | Paused zůstává v `projects[]` / open counts; nesoupeří o TOP / Rozhodni / due_soon / focus suggestions. | Kontext |

**Mimo rozsah:** pauznutí dalších projektů; Bases UI; Waiting/overdue/recurring pro paused; push bez pokynu.

**Profil:** SECOND_BRAIN. Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q` (**T1+T6**). Tester: přeskočeno.

## Předpoklady

A1 WT = cíl + delty D2/D5/D5a. A2 asap N/A. A3 active = `active`/`""`/None; `PAUSED` = non-active. A4 due lanes přes `queue_tasks`. A5 open_epics/projects včetně paused. A6 slug `rb-network`. A7 live TOP slabý → T1/T6. A8 twin scripts↔VPS. A9 hub se **čte**, early-continue bez write.

## Návrh (stav)

Helpers v `today_priority.py`; `queue_tasks` v obou `build_agent_context.py`; `should_refresh_hub_state` v `hub_state.py` používaný `update_hub_state.py` + `lifecycle_hub_state.py`; konvence R4; D1 bootstrap due_soon; D2 mrtvý import smazán; T6 `tests/test_paused_projects.py`.

### Delta

| D# | Stav |
|---|---|
| D1 bootstrap due_soon | hotovo |
| D2 smazat today_score import | hotovo |
| D5 T6 pytest | hotovo |
| D5a should_refresh_hub_state | hotovo |
| D4 commit/push | po SCHVÁLENO reviewera; push jen na pokyn |

## B#

| B# | Očekávání | T# |
|---|---|---|
| B1 prázdný paused | queue == open | T1 |
| B2 missing/"" status | active | T1, T6 |
| B3 paused/PAUSED | mimo TOP/lanes; skip Stav; mimo stale_hubs | T6 (+ T1 TOP část) |
| B4 focused paused task | mimo TOP | T1 |
| B5 active task | smí TOP | T1, T3 |
| B6 projects[] + counts | paused zůstává; active_projects ne | T3 |
| B7 stale_hubs | paused ∉ | T6, T3 |
| B8 kratky-potlesk | skip hub state | T2, T3 |
| B9 idempotent skip | no write paused | T6, T2 |
| B10 | **read ano, write/CAS ne** u paused; CAS beze změny u active | T4, T6 |
| B11 VPS twin | stejná sémantika | T5 po push |
| B12 JSON klíče | beze změny | T1, T3 |
| B13 asap | N/A | — |

## P

Filtr O(n); hub read všech, write jen active. Lokál build ≪ 2 s.

## T#

| T# | Příkaz / soubor | B# |
|---|---|---|
| T1 | `test_today_priority.py::test_paused_project_helpers_exclude_from_queue` | B1,B2,B4,B5 |
| T6 | `tests/test_paused_projects.py` (casefold, should_refresh, stale loop, tmp vault no-write) | B3,B7,B9,B10 |
| T2 | `update_hub_state.py --dry-run` — potlesk není would-update | B8,B9 |
| T3 | build_agent_context smoke checklist | B5–B8,B12 |
| T4 | twin + B10 review | B10 |
| T5 | po push coolify-dev | B11 |

## Pořadí

F1–F5 hotovo (včetně D2/D5/D5a). F6: critic → review → commit → QA; TESTER přeskočeno.

## Rizika

Twin drift; slabý live TOP; neznámý status = paused; ostatní lifecycle mutuje paused tasky; push = ostrý vault.

## Otevřené otázky (výchozí ne)

1 open_epics filtrovat? 2 Waiting/crony vypnout? 3 Push? 4 agent-bootstrap?

## Vyřešení C#

| C# | Stav |
|---|---|
| C1 MAJOR test coverage | vyřešeno — T1 zúžen; T6 + D5a |
| C2 MINOR dead import | vyřešeno — D2 |
| C3 MINOR B10 wording | vyřešeno — A9 + B10 text |
