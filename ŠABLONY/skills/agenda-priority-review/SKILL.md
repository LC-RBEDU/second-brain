---
name: agenda-priority-review
description: "Use when user asks revize priorit, přehodnotit ICE, srovnat ASAP/Next/Waiting in MrLUC Second Brain v2. Ad-hoc only. Scans all 02-PROJEKTY/<slug>/tasks/*.md frontmatters, proposes status/ICE/waitUntil changes. ALWAYS preview before write. Optional export to 00-System/Triage-Pending/priority-review-*.json."
---

# agenda-priority-review (v2)

> Ad-hoc srovnání priorit napříč vaultem. Ne cron — spouštíš, když cítíš chaos v prioritách. **V2:** čte task `.md` frontmattery (file-per-task), ne H3 v hubu.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Revize priorit" / "přehodnotit priority" / "srovnat ICE"
- Po velké změně v projektech (reorganizace, nové ASAP vlny)
- **Ne** místo týdenního shrnutí — to je `agenda-weekly-review`

## Načti data

1. Všechny `02-PROJEKTY/<slug>/tasks/*.md` aktivní (status != Done) — frontmatter
2. (Po F8) `OBSIDIAN/00-System/agent-context.json` → top_priority list, overdue, waiting
3. `00-System/Memory/procesy-mrluc.md` — pravidla Waiting / SSOT

## Scoring (sjednoceno s `today_priority.py` / agent-context)

- `priority_score = (ice_i * ice_c) / ice_e`
- `today_score = priority_score + urgency_bonus`:
  - +35 overdue (`deadline < today`)
  - +30 deadline dnes
  - +15 deadline zítra
- **TOP eligibility:** ASAP vždy; Next jen bez otevřeného ASAP; nikdy Waiting/Backlog
- **Waiting** — nepatří do TOP; zkontroluj `waitUntil` a smysl
- **Blocked** — pokud `blocked_by != []`, označ v preview

## Preview formát

Každá zmínka tasku v chatu: **`ID — title`** z frontmatter (ne jen ID). Viz `.cursor/rules/task-mention-convention.mdc`.

```
REVIZE PRIORIT — YYYY-MM-DD

Navrhované změny (N):
  [finance] F17 — Název úkolu: status Next → ASAP, ICE I7→I10 (důvod: cashflow)
  [strategy] S8 — Název úkolu: status ASAP → Waiting, waitUntil: 2026-05-31 (důvod: čeká na Lenku)
  ...

Beze změny (TOP 5 podle today_score):
  1. [strategy/S2] Hierarchie cílů — Next, today_score 8.3
  2. [rb-universe-development/RBU30] ... — ASAP, today_score 64
  ...

Watch — Waiting blízko expiraci (≤ 7 dnů):
  • [strategy/S5] waitUntil 2026-05-31 — připravit follow-up
```

## Zápis

- Jen po explicitním "schval" / "apply"
- Patch task `.md` frontmatter (CAS): status, ice_i/c/e, waitUntil, deadline, updated
- Append do body `## Poznámky / log`: `- <today>: priority-review — <change>`
- (Volitelně) ulož batch do `00-System/Triage-Pending/priority-review-YYYY-MM-DD.json` pro audit
- **Bases dashboard** se aktualizuje sám — žádný cron build potřeba
- **Po batchi spusť** `python3 scripts/build_agent_context.py` — refresh `agent-context.json` pro Cursor agenta

## Pravidla

- Nikdy neměň `id`, `slug`, `created`
- Duplicitní ID napříč projekty — flagni, nespojuj automaticky (ID je per-slug; AF1 ≠ S1, ale F1 v finance vs F1 v firemni-procesy je collision warning)
- Propojené tasky (F13 ↔ F19) — navrhni stejný wait/deadline jen pokud dává smysl
- Recurring tasky — review jen ICE/status; `recurring:` blok ne menit (řídí cron)
