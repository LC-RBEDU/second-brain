# Plán: Brain set_focus — fokus po potvrzení (MCP/REST)

> Generace PLAN k=1 r=2 (patch po kritice). Zamčená rozhodnutí uživatele 2026-10-12: Q1a (eligible+exclude paused), Q2a (Europe/Prague), Q3a (sjednotit focus_count ve stejném PR).

## Zadání a požadavky

| R# | Požadavek | Zdroj |
|---|---|---|
| **R1** | Saturnin / Claude přes Brain MCP mohou po potvrzení v chatu nastavit nebo zrušit `focus` (vratná změna). Dnes vždy 403. | brief zadání |
| **R2** | Cursor lokální patch přes `agenda-status-update` **nechat** — mimo Brain. | brief |
| **R3** | Cron **nikdy** nepíše / nenastavuje aktuální `focus` přes `set_focus`; `## Stav (auto)` mimo scope. Recurring clear focus (už dnes) OK. | brief + bootstrap + grill A13 |
| **R4** | Jen autentizovaný interaktivní caller (ne cron); potvrzení **není** API flag — skill/guide: náhled → „ano“ → tool. | CLARIFY 1, 4 |
| **R5** | Server enforce `FOCUS_LIMIT=5` na aktuální ISO týden; 403 **jen** když target **nově** vstoupí do eligible∩¬paused a ostatní v množině ≥5. Re-set / clear / mimo množinu → allow. | CLARIFY 2 + NEW-1 |
| **R6** | Prázdný `focus_week` = clear `focus:`. | CLARIFY 3 |
| **R7** | Kontrakt `set_focus(task_path, focus_week)`: validace ISO week, CAS pokud `expect_oid`, `focus_count` **po** zápisu, `already_in_focus` = stav **před** setem. | brief + NEW-9 |
| **R8** | Aktualizovat testy, MCP popis, docs/skills/boti-prehled / agent-guide dle potřeby. | brief |
| **R9** | Jedna SSOT funkce `count_focus_slots` v hub `lib/today_priority.py`; Brain `set_focus` i `agent_context_build` (a consumers) ji volají; `count_focused` sjednotit/deprecate. | NEW-4 + Q3a |
| **R10** | Deploy: Brain **i** hub image na stejný SHA; smoke oba. | NEW-5 |

**Mimo rozsah:** lokální Cursor `agenda-status-update` / `agent_write_guard`; hub cron zápis aktuálního focus; `## Stav (auto)`; Universe/Alembic/RBAC/FE; Playwright-T6 / `rbu-tester`; confirm flag v API; **ghost overflow po unpause** (NEBLOKUJÍCÍ default — neřešit v tomto PR).

---

## Předpoklady

| A# | Předpoklad | Proč |
|---|---|---|
| **A1** | Allow focus write pro `oauth:*` i `ServicePrincipal` (Bearer MCP). Deny jen bez autentizace. | MCP klienti = Bearer. OAuth-only by rozbilo R1. |
| **A2** | `update_task` + `focus` → dál 403 (jediný zápis = `set_focus`). | Choke-point. |
| **A3** | `focus_week` jen `""` (clear) nebo **aktuální** ISO week (Prague). Jinak 400. | Q2a |
| **A4** | Slot = `is_focus_eligible` ∩ `exclude_paused_project_tasks`. Epic / Waiting / Backlog / Done / Cancelled / paused-project smí dostat `focus` **bez** spotřeby slotu (allow i při count≥5). | Q1a + NEW-1 |
| **A5** / **A9** | Tombstone `delete_context_tombstone` **na začátku** mutate session (i při pozdějším 409) — jako `create_task`. | grill A18 |
| **A18** | (alias A5 sjednocení) | grill kolo 2 |
| **A19** | `paused_slugs` před limitem ze stejného zdroje jako `agent_context_build`; `exclude_path` = rel path tasku. | grill kolo 2 |
| **A20** | `hub_state` focused list: preferovat eligible∩¬paused; jinak zmínit v rizicích. | grill kolo 2 NEBLOKUJÍCÍ |
| **A21** | Brain Dockerfile už COPY hub lib + TZ Prague; krok 0 ZoneInfo zůstává kvůli testům. | grill kolo 2 |
| **A6** | Potvrzení = klient (docs/skills). | CLARIFY 4 |
| **A7** | `dev` principal = allow (local / testy). | Pattern ostatních tools. |
| **A8** | MCP principal přes ContextVar z `mcp_auth` (povinné; T12). | grill + NEW-2 |
| **A9** | Tombstone na začátku mutate session (i při pozdějším 409) — jako `create_task`. | grill |
| **A10** | Race stropu = `brain_vault` flock. | grill |
| **A11** | MCP i REST: volitelné `expect_oid`. | grill |
| **A12** | Neexistující path → 404 `not_found`; clear idempotent (už prázdný focus → 200, bump `updated`). | grill + NEW-8 |
| **A13** | B11: cron nenastavuje aktuální focus / nevolá `set_focus`. `lifecycle_recurring` smí clear. | grill |
| **A14** | `today` / current ISO week = **Europe/Prague** (`TZ` env default), **před** week check i limitem (krok 0). | Q2a + NEW-6 |
| **A15** | Ve stejném PR: `stats.focus_count` + suggestions count přes `count_focus_slots` (A4). | Q3a + NEW-4 |
| **A16** | Ghost overflow (>5 eligible po unpause) **neřešit** v tomto PR — jen dokumentovat riziko. | NEBLOKUJÍCÍ default |
| **A17** | Coolify: změna `hub/lib/` je v Brain image (`COPY second-brain-hub/lib/`) **i** hub image — oba redeploy na stejný git SHA. | NEW-5 |

---

## Současný stav (ověřeno v kódu)

| Soubor | Fakt |
|---|---|
| `vps/second-brain-brain/app/policy.py` | `deny_focus_write()` vždy deny |
| `…/tools/set_focus.py` | Stub vždy 403 |
| `…/tools/update_task.py` | `focus` v patch → deny |
| `…/mcp_app.py` | `set_focus` stub; MCP has no principal |
| `…/mcp_auth.py` | Auth gate; neukládá principal |
| `…/main.py` | `POST /v1/set_focus` bez body |
| `…/tests/test_policy_tools.py` | Očekává deny |
| `vps/second-brain-hub/lib/focus.py` | `FOCUS_LIMIT`, `parse_focus`, `current_focus_week` |
| `…/today_priority.py` | `exclude_paused_project_tasks`, `is_focus_eligible` |
| `…/lifecycle_promotion.py` | `count_focused` = jen `is_focus_current` (≠ A4) |
| `…/agent_context_build.py` | `stats.focus_count` = `is_focus_current` (bez eligible) |
| Brain Dockerfile | kopíruje `second-brain-hub/lib/` |

**Nezměnit:** cron zápis aktuálního focus; `deny_stav_auto_write`; lokální `agenda-status-update`.

---

## Návrh

### Architektonické rozhodnutí

- Funkční **`set_focus`**.
- **`update_task` + `focus` → 403** (A2).
- Limit SSOT = **`count_focus_slots`** (R9).

### 0. Hub SSOT — `count_focus_slots` (R9, NEW-4)

**Soubor:** `vps/second-brain-hub/lib/today_priority.py`

```python
def count_focus_slots(
    tasks: list[Any],
    today: date,
    *,
    paused_slugs: set[str] | None = None,
    exclude_path: str | None = None,
) -> int:
    """Počet slotů = is_focus_eligible ∩ ¬paused (± exclude_path)."""
```

- Filtr: `exclude_paused_project_tasks`, pak `is_focus_eligible`.
- `lifecycle_promotion.count_focused`: thin wrapper → `count_focus_slots` (nebo deprecate + update tests).
- `agent_context_build.py`: `focus_count = count_focus_slots(queue_tasks, today)`; suggestions se stejným count.
- Preferovat `is_focus_eligible` i v `hub_state` focused list pokud počítá.

Brain import: `/app/lib` (Dockerfile COPY).

### 1. Policy — `app/policy.py`

`allow_focus_write(principal)` — oauth / ServicePrincipal / "dev" → allow.  
`update_task`: deny „use set_focus“. `deny_stav_auto_write` beze změny.

### 2. Principal MCP — ContextVar + `mcp_auth.py` (A8, NEW-2)

- `app/request_principal.py`: ContextVar + get/set/reset.
- Middleware nastaví principal; finally reset.
- REST: `principal=_auth`.
- **T12:** middleware → ContextVar → set_focus allow.

### 3. Tool `set_focus`

Signature: `task_path`, `focus_week=""`, `expect_oid=None`, `principal=None`, `env=None`.

**Algoritmus (jedna mutate session; flock = A10):**

0. `today = datetime.now(ZoneInfo(TZ or Europe/Prague)).date()` — **před** week check i limitem.
1. `allow_focus_write` → jinak 403.
2. Validace `task_path` pod `02-PROJEKTY/…/tasks/`.
3. `focus_week`: empty → clear; else parse; must == `current_focus_week(today)` else 400.
4. Tombstone delete (A9).
5. Read; missing → 404; CAS mismatch → 409.
6. `already_in_focus = is_focus_current(fm.focus, today)` (**před** zápisem).
7. Limit: jen pokud ne clear a target by **nově** vstoupil do eligible∩¬paused:
   - `paused_slugs` z hubů (A19, stejný zdroj jako agent_context_build)
   - `others = count_focus_slots(..., paused_slugs=…, exclude_path=task_path)`
   - pokud target po setu eligible a slug ∉ paused a others ≥ FOCUS_LIMIT → 403
   - Waiting/Backlog/epic/paused → allow (B16/B17)
   - Re-set (`already_in_focus`) → allow
8. Patch FM `focus` + `updated`. Clear idempotent (B20).
9. Write; `focus_count = count_focus_slots` **po** zápisu.
10. Response:

```json
{
  "path": "<task_path>",
  "focus": "2026-W42" | null,
  "focus_week": "2026-W42" | "",
  "cleared": false,
  "oid": "<blob>",
  "focus_count": 4,
  "focus_limit": 5,
  "already_in_focus": false
}
```

Úzký FM scan pod flockem (ne archiv); flock-hold typicky &lt;1 s (NEW-7).

### 4–6. REST + MCP + update_task

`SetFocusBody(task_path, focus_week="", expect_oid=None)`.  
MCP: set/clear; max 5 eligible; confirm first; expect_oid optional.  
`update_task`: 403 use set_focus.

### 7. Docs / skills

claude-project-instructions, brain-api-runbook, agent-guide, boti-prehled, agenda-status-update poznámka Brain remote.

---

## Kontrakt chování (B#)

| B# | Vstup | Očekávání | T# |
|---|---|---|---|
| B1 | oauth + current + others&lt;5 + eligible | 200 set | T1 |
| B2 | ServicePrincipal | stejně | T1 |
| B3 | bez auth | 401 | T2 |
| B4 | focus_week="" | clear | T3 |
| B5 | už `is_focus_current` (re-set) → allow i při plné pětici (target v `others` přes exclude_path nepočítá) | allow | T4 |
| B6 | others≥5; target **nově** do eligible∩¬paused | 403 | T4 |
| B7 | neplatný / neaktuální week | 400 | T5 |
| B8 | expect_oid mismatch | 409 | T6 |
| B9 | update_task focus | 403 | T7 |
| B10 | stav_auto | deny | T7 |
| B11 | cron | nenastavuje current focus / nevolá set_focus; recurring clear OK | T8 |
| B12 | Cursor local | beze změny | — |
| B13 | race 4→5 / 4→6 | max 5 | T9 |
| B14 | epic | allow, bez slotu | T4 |
| B15 | MCP/docs | allow + confirm | T10 |
| B16 | Waiting/Backlog + others≥5 | allow | T4 |
| B17 | paused project + others≥5 | allow | T4 |
| B18 | Prague week boundary | today z kroku 0 | T13 |
| B19 | unknown path | 404 | T3 |
| B20 | clear už prázdný | 200 idempotent | T3 |

---

## Výkon (P)

1 mutate: read + úzký FM scan + write + tombstone; flock-hold &lt;1 s typicky; ≤5 s + push.

---

## Testy (T#)

| T# | Soubor | B# |
|---|---|---|
| T1–T7, T9, T13 | brain tests | B1–B10, B13–B14, B18 |
| T3 | clear + 404 + idempotent | B4, B19, B20 |
| T4 | limit + epic + Waiting + Backlog + paused | B5, B6, B14, B16, B17 |
| T8 | grep cron | B11 |
| T10 | smoke Brain + hub | B1, B2, B15 |
| T11 | hub count_focus_slots + stats | R9, A15 |
| T12 | ContextVar middleware → set_focus | A8 |

Gate: pytest brain + hub + scripts (dotčené). TESTER přeskočeno.

---

## Pořadí

1. `count_focus_slots` + agent_context + T11  
2. ContextVar + middleware + T12  
3. set_focus + REST  
4. MCP + update_task message  
5. pytest T1–T7, T9, T13  
6. docs  
7. push → Coolify **Brain + hub** stejný SHA → T10  

---

## Rizika

1. Race → flock  
2. Service Bearer síla = create_task; confirm ve skillu  
3. Breaking always-403 — záměr  
4. Ghost overflow po unpause (A16)  
5. Dvojí image — R10  
6. `stats.focus_count` po A15 může klesnout (Waiting/epic ven) — očekávané  

---

## Kritika → vyřešeno (r=2)

| C# | Stav |
|---|---|
| NEW-1…NEW-9 | zapracováno (viz A/B/R/T výše) |
| Ghost overflow | A16 default neřešit |
