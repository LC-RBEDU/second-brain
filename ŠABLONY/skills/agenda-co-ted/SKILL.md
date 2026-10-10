---
name: agenda-co-ted
description: "Use when user asks 'co teď', 'co dnes', 'na co se mám zaměřit', 'co je urgentní', 'ukaž mi dashboard', 'co mám rozdělaného' v MrLUC Second Brain v2. Reads 00-System/agent-context.json (primary) or 02-PROJEKTY/<slug>/tasks/*.md frontmatter (fallback). ICE scoring (I*C)/E sjednocený s Bases formula. Optional 'ukliď' archivuje Done tasky do 07-ARCHIV/tasks-done/. Never modifies files unless user says ukliď/clean/urgent/odlož."
---

**F1 (git vault):** pokud vault je git klon (`SECOND_BRAIN_VAULT` / `~/GitHub/second-brain-vault`), skill = **pull + read only** — žádný FS zápis do klonu. Snapshot = VPS; lidský zápis = GitHub web UI PR. Až F2.


# agenda-co-ted (v2)

> "Sednu si, jednou se podívám, vím co dělat." Ad-hoc prioritní kapka — bez týdenního review.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Co teď?" / "Co dnes?" / "Na co se mám zaměřit?"
- "Co je v agendě?" / "Ukaž mi dashboard"
- Začátek pracovního dne

## Načti data

V2 priority pořadí:

1. **`OBSIDIAN/00-System/agent-context.json`** (PRIMARY) — `needs_decision`, `top_priority_today` (TOP dnes, max 5), `top_priority` (max 15), `due_soon`, `no_review_deadline`, `recently_done`, `upcoming_deadlines`, `recurring_pending`, `blocked_by_graph`, `priority_rules`. Pokud `generated_at` je starší než 24 h, spusť `python3 scripts/build_agent_context.py` před analýzou.
2. Fallback: parsuj všechny `OBSIDIAN/02-PROJEKTY/<slug>/tasks/*.md` frontmattery + aplikuj stejná pravidla jako `vps/second-brain-hub/lib/today_priority.py`
3. Backup: `OBSIDIAN/Dashboard.md` Bases embedy (aproximace — SSOT je agent-context)
4. **Lessons pending:** pokud `00-System/Lessons-Pending/*.md` (ne `.gitkeep`) není prázdný → v dashboardu řádek `Lessons ke schválení: N` (+ **stale** pokud mtime > 7 dní). Příkaz: „schval lessons“ → skill `agenda-lessons`.

## Lane Rozhodni (SSOT: `needs_decision`)

**Nejdřív tahle lane**, pak fokus.

- `due = deadline` (pokud je), jinak `review_deadline` — `due < dnes` a status není Waiting / Done / Cancelled
- **Pořadí TOP / suggestions:** ber pořadí polí ze snapshotu — **nesortuj** podle `today_score`. Hard deadline ≤7d je nahoře.
- U každé položky nabídni: hotovo / nové `review_deadline` (jen bez `deadline`) nebo posun `deadline` (externí) / Waiting + blocker / Cancelled
- Když je `needs_decision` neprázdné, **nesmíš mlčet** — vypiš ji i když fokus je plný

## TOP priority dnes (SSOT: `top_priority_today`)

**Eligibility** (nikdy porušit):
- **Jen `focus` = aktuální ISO týden** (např. `2026-W32`). Nic jiného do TOP dnes nepatří.
- **Nikdy:** `Waiting`, `Backlog`, `Done`, `Cancelled`
- **Max 5.** Fokus vybírá **výhradně člověk** — nikdy ho nenastavuj sám.

**Když je fokus prázdný nebo pod pěti:**
- `agent-context.json` → `focus_suggestions[]` = kandidáti v pořadí ze snapshotu (už `rank_key`; neresortuj).
- **Nabídni je, nepovyšuj.** Formulace: „Fokus týdne má X z 5. Kandidáti: … Chceš některý přidat?"

**Scoring / řazení:**
- `priority_score = (ice_i * ice_c) / ice_e`
- `rank_score` / `today_score` = ICE + 5 pokud `company_priorities` neprázdné
- řazení v snapshotu: hard `deadline` ≤7d (vč. overdue) nahoře (ASC), pak `rank_score`; `review_deadline` bez vlivu
- **nesortuj** pole podle `today_score` — pořadí = pořadí v JSON

**Pole `agent`** — u každé položky zmiň, kdo ji udělá: `solo` (zvládnu sám a můžu se do toho pustit hned), `assist` (připravím podklad, rozhodneš ty), `none` (jen ty).

## Ostatní klasifikace

- **ROZHODNI**: `needs_decision` — viz výše
- **BEZ DATA**: `no_review_deadline` — otevřené **bez** `deadline` i bez `review_deadline` (doplň review)
- **Firemní priority**: volitelné `company_priorities` → viz `00-System/Memory/firemni-priority-2hy-2026.md`
- **DUE SOON**: `due_soon` — `due` v příštích 7 dnech
- **PO TERMÍNU (externí)**: `deadline` < dnes && `status != Done`
- **WAITING**: `status = Waiting` && `waitUntil >= dnes` — zobraz zvlášť, **nikdy v TOP**
- **BLOKOVANÉ**: `blocked_by != []` — kromě "nic"

## Zmínka tasků v chatu

Vždy **`ID — title`** (z frontmatter / `agent-context.json`), ne jen zkratka ID. Příklad: **SBD4 — Česká spořitelna — rozšíření rámcovky (dodatek)**. Viz `.cursor/rules/task-mention-convention.mdc`.

## Vrať dashboard

```
═══════════════════════════════════════════════
CO TEĎ — DD/MM/YYYY
═══════════════════════════════════════════════

⚠️ ROZHODNI (N) — due po termínu
  • [slug] ID — title — due=… deadline=… review=… status=…
  → nabídni: hotovo / nové datum / Waiting / Cancelled

🔥 TOP (z `top_priority_today`, pořadí ze snapshotu)
  • [slug] ID — title — focus=2026-W32 agent=solo today_score=… due=…
  ...

📅 DUE ≤ 7 dní (N)
  • …

⏸ WAITING (N)
  • [slug] ID — title — do YYYY-MM-DD

📭 BEZ review_deadline (top ICE, max 5)
  • …

🚧 BLOKOVANÉ (N)
  ...

═══════════════════════════════════════════════
📝 Lessons ke schválení: N (nebo vynech řádek) — „schval lessons“
═══════════════════════════════════════════════
Příkazy: ukliď | detail <slug> | revize priorit | schval lessons
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
