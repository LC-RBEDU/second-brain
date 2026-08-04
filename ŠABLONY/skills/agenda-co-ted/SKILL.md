---
name: agenda-co-ted
description: "Use when user asks 'co teď', 'co dnes', 'na co se mám zaměřit', 'co je urgentní', 'ukaž mi dashboard', 'co mám rozdělaného' v MrLUC Second Brain v2. Reads 00-System/agent-context.json (primary) or 02-PROJEKTY/<slug>/tasks/*.md frontmatter (fallback). ICE scoring (I*C)/E sjednocený s Bases formula. Optional 'ukliď' archivuje Done tasky do 07-ARCHIV/tasks-done/. Never modifies files unless user says ukliď/clean/urgent/odlož."
---

# agenda-co-ted (v2)

> "Sednu si, jednou se podívám, vím co dělat." Ad-hoc prioritní kapka — bez týdenního review.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Co teď?" / "Co dnes?" / "Na co se mám zaměřit?"
- "Co je v agendě?" / "Ukaž mi dashboard"
- Začátek pracovního dne

## Načti data

V2 priority pořadí:

1. **`OBSIDIAN/00-System/agent-context.json`** (PRIMARY) — `top_priority_today` (TOP dnes, max 5), `top_priority` (max 15), `recently_done`, `upcoming_deadlines`, `recurring_pending`, `blocked_by_graph`, `priority_rules`. Pokud `generated_at` je starší než 24 h, spusť `python3 scripts/build_agent_context.py` před analýzou.
2. Fallback: parsuj všechny `OBSIDIAN/02-PROJEKTY/<slug>/tasks/*.md` frontmattery + aplikuj stejná pravidla jako `vps/second-brain-hub/lib/today_priority.py`
3. Backup: `OBSIDIAN/Dashboard.md` Bases embedy (aproximace — SSOT je agent-context)

## TOP priority dnes (SSOT: `top_priority_today`)

**Eligibility** (nikdy porušit):
- **Jen `focus` = aktuální ISO týden** (např. `2026-W32`). Nic jiného do TOP dnes nepatří.
- **Nikdy:** `Waiting`, `Backlog`, `Done`, `Cancelled`
- **Max 5.** Fokus vybírá **výhradně člověk** — nikdy ho nenastavuj sám.

**Když je fokus prázdný nebo pod pěti:**
- `agent-context.json` → `focus_suggestions[]` = kandidáti seřazení podle `today_score`.
- **Nabídni je, nepovyšuj.** Formulace: „Fokus týdne má X z 5. Kandidáti: … Chceš některý přidat?"

**Scoring:**
- `priority_score = (ice_i * ice_c) / ice_e`
- `today_score = priority_score + urgency_bonus`:
  - **+30** deadline dnes
  - **+15** deadline zítra
  - **+5** overdue (`deadline < dnes`) — jen rozřazovač, ne odměna za hnilobu
- Sort: `today_score DESC`

**Pole `agent`** — u každé položky zmiň, kdo ji udělá: `solo` (zvládnu sám a můžu se do toho pustit hned), `assist` (připravím podklad, rozhodneš ty), `none` (jen ty).

## Ostatní klasifikace

- **PO TERMÍNU**: `deadline` < dnes && `status != Done`
- **DNES**: `deadline` = dnes
- **WAITING**: `status = Waiting` && `waitUntil >= dnes` — zobraz zvlášť, **nikdy v TOP**
- **BLOKOVANÉ**: `blocked_by != []` — kromě "nic"

## Zmínka tasků v chatu

Vždy **`ID — title`** (z frontmatter / `agent-context.json`), ne jen zkratka ID. Příklad: **SBD4 — Česká spořitelna — rozšíření rámcovky (dodatek)**. Viz `.cursor/rules/task-mention-convention.mdc`.

## Vrať dashboard

```
═══════════════════════════════════════════════
CO TEĎ — DD/MM/YYYY
═══════════════════════════════════════════════

🔥 TOP 3 (z `top_priority_today`, sort today_score)
  • [slug] ID — title (z frontmatter) — focus=2026-W32 agent=solo today_score=… deadline=…
  ...

⏸ WAITING (N)
  • [slug] ID — title — do YYYY-MM-DD

⚠️ PO TERMÍNU (N)
  ...

🚧 BLOKOVANÉ (N)
  ...

═══════════════════════════════════════════════
Příkazy: ukliď | detail <slug> | revize priorit
```

## Subcommands

- **`ukliď` / `clean`**:
  - Najdi task soubory v `02-PROJEKTY/<slug>/tasks/` se `status: Done`
  - Preview seznam → potvrzení
  - Přesuň do `07-ARCHIV/tasks-done/<slug>/<filename>` (cron `archive_done_tasks.py` to dělá automaticky, ale tady manuální verze)
  - Update `open_tasks_count` v hub `.md` frontmatteru
  - Po batchi spusť `python3 scripts/build_agent_context.py`
- **`detail <slug>`** → otevři `02-PROJEKTY/<HubName>.md` + briefing (Cíl, Scope, Kontext, Otevřené otázky, Aktivní úkoly)
- **`revize priorit`** → deleguj na skill `agenda-priority-review`

## Pravidla

- Nikdy neukládej bez explicitního příkazu
- Waiting / Backlog **nikdy** v TOP (ani v `top_priority_today`, ani v `top_priority`)
- Cesty: `02-PROJEKTY/<slug>/tasks/` (ne `AGENDA/`, ne H3 v hubu)
- Bases dashboard (`Dashboard.md`) je pro user oko, agent ho čte přes frontmatter parser
- **Vault je single-user (Lukáš).** Co teď zobrazuje **Lukášovy priority** — všechny tasky v `02-PROJEKTY/<slug>/tasks/` jsou Lukášovy operativní akce (žádný explicit `owner` field, jeden majitel vault). Pokud task "Sledovat: <kdo> dodá <co>" má status `Waiting`, patří do sekce WAITING, ne do TOP 3.
