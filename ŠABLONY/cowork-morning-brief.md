# Cowork — ranní brief (priorita v2.1)

Lokální scheduled task (Claude Desktop otevřený). Interval: **každý pracovní den ráno** (např. 8:00). Složka: `SECOND_BRAIN`.

## Prompt (vlož do `/schedule`)

```
Follow ŠABLONY/skills/agenda-co-ted/SKILL.md and read OBSIDIAN/00-System/agent-context.json (refresh with `python3 scripts/build_agent_context.py` if generated_at is older than 24h).

Write the morning priority brief in this chat only. Do not write the vault or Slack.

Order (never skip Rozhodni when non-empty):
1. needs_decision — due (deadline if set, else review_deadline) is past. Use array order from snapshot; do not re-sort by today_score. For each item offer: Done / new review_deadline (only if no deadline) or move deadline / Waiting + blocker / Cancelled. Always show ID — title.
2. Focus week count (X of 5) + top_priority_today. If under 5, list focus_suggestions — do not set focus yourself.
3. due_soon (next 7 days).
4. Waiting with waitUntil within 3 days.
5. no_review_deadline — open tasks without deadline and without review_deadline; top 5 by ICE; ask to set review_deadline.

If needs_decision is empty and focus is full, still show due_soon and Waiting briefly.
If needs_decision is non-empty, you must not reply with nothing.
Czech, short, Lukáš style (registr A).
```

## Poznámka

`deadline` = externí závazek (když je, `review_deadline` se maže a ignoruje). `review_deadline` = vlastní měkké datum jen bez deadline. Lane Rozhodni bere `due`.
