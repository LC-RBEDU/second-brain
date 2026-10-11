# Claude artifact dashboard (F4)

Read-only UI nad Brain light contextem. Hosting = Claude Desktop artifact (ne VPS web).

## Data

- **URL:** `GET https://brain.cyprovi.cz/v1/context/light`
- **Auth:** human OAuth session (cookie po `/oauth/login`). Service Bearer → 403.
- **Payload:** `{"mode":"warm","context":{…light…}}` — cíl ≤256 KB.
- **Join:** položky v `top_priority_today` / `needs_decision` / `due_soon` nesou `id` — zobraz title z `context.tasks[]` (nebo ekvivalentní pole v light projection) podle `id`.

## UI (minimum)

1. TOP dnes (`top_priority_today`)
2. Rozhodni (`needs_decision`)
3. Due soon (`due_soon`)
4. Krátké stats (open counts pokud light obsahuje)

## Fail-path (když artifact/OAuth FAIL)

1. MCP `get_context` v chatu → stručný brief
2. Slack proactivity nudge („jdi do live triáže“)
3. Ne VPS `web/` dashboard

## Zdroj HTML

Volitelně [`ŠABLONY/claude-artifacts/dashboard.html`](../ŠABLONY/claude-artifacts/dashboard.html) — vložit do Claude artifact.
