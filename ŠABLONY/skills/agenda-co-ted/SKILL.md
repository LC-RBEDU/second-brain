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

1. **`OBSIDIAN/00-System/agent-context.json`** (PRIMARY) — `needs_decision`, `top_priority_today` (TOP dnes, max 5), `top_priority` (max 15), `due_soon`, `no_review_deadline`, `recently_done`, `upcoming_deadlines`, `recurring_pending`, `blocked_by_graph`, `priority_rules`. Pokud `generated_at` je starší než 24 h, spusť `python3 scripts/build_agent_context.py` před analýzou.
2. Fallback: parsuj všechny `OBSIDIAN/02-PROJEKTY/<slug>/tasks/*.md` frontmattery + aplikuj stejná pravidla jako `vps/second-brain-hub/lib/today_priority.py`
3. Backup: `OBSIDIAN/Dashboard.md` Bases embedy (aproximace — SSOT je agent-context)
4. **Lessons pending:** pokud `00-System/Lessons-Pending/*.md` (ne `.gitkeep`) není prázdný → v dashboardu řádek `Lessons ke schválení: N` (+ **stale** pokud mtime > 7 dní). Příkaz: „schval lessons“ → skill `agenda-lessons`.

## Lane Rozhodni (SSOT: `needs_decision`)

**Nejdřív tahle lane**, pak fokus.

- `due = deadline` (pokud je), jinak `review_deadline` — `due < dnes` a status není Waiting / Done / Cancelled
- **Pořadí TOP / suggestions:** ber pořadí polí ze snapshotu (`top_priority_today`, `top_priority`, `focus_suggestions`) — **nesortuj** podle `today_score`. Hard deadline ≤7d je nahoře.
- U každé položky nabídni: hotovo / nové `review_deadline` (jen bez `deadline`) nebo posun `deadline` (externí) / Waiting + blocker / Cancelled
- Když je `needs_decision` neprázdné, **nesmíš mlčet** — vypiš ji i když fokus je plný

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
- `rank_score` / `today_score` = ICE + 5 pokud `company_priorities` neprázdné
  - řazení: deadline bucket (≤7d) → deadline ASC → rank_score DESC; review bez vlivu
