---
name: agenda-remind
description: "Schedule chat reminders (Grok → Claude → Slack) via Brain MCP tools schedule_reminder / cancel_reminder / list_reminders. Triggers: připomeň mi, remind me, Slack připomínka, reminder v .... ALWAYS preview before write."
---

# agenda-remind

> Naplánuj připomínku na konkrétní čas. Doručení = **zpráva do chatu** (Grok Bot → Claude → Slack). OS push = nastavení appky u tebe.

**F2:** zakládej jen přes **Brain MCP** (`schedule_reminder` / `cancel_reminder` / `list_reminders`).  
Lokální `scripts/schedule_reminder.py schedule|cancel` na Mac git klonu **nepoužívej** (readonly).  
Hub cron `reminders_dispatch.py` (*/2) volá chat řetězec; kontrakt Grok webhook: [`docs/brain-api-runbook.md`](../../../docs/brain-api-runbook.md).

## Kdy spouštět

- „Připomeň mi … ve středu v 8“
- „Reminder v pondělí 14:00: …“
- Zrušení: „zruš připomínku …“ / „co mám naplánované?“

**Nepoužívat** pro task `waitUntil` / lifecycle.

## Workflow

### 1. Preview (povinné)

```
Navrhuju připomínku (chat Grok→Claude→Slack):

  Kdy: 2026-09-02 08:00 (Europe/Prague)
  Zpráva: …
  Task ref (volitelně): S12-16 — H2 rozpočty a forecast — …

OK? (ano / uprav / cancel)
```

### 2. Zápis (po ano)

Brain MCP tool `schedule_reminder`:

- `message` — text
- `deliver_at` — ISO nebo `YYYY-MM-DD HH:MM` (Europe/Prague)
- `task_ref` — vždy `ID — title` když jde o task

REST ekvivalent (machine): `POST /v1/reminders` + service token.

### 3. Seznam / zrušení

- `list_reminders`
- `cancel_reminder` s `reminder_id`

## Formát zprávy

- Stručně, registr A.
- U tasku vždy **`ID — title`** v `task_ref`.

## Setup

1. Coolify Brain: `BRAIN_PUBLIC_URL`, OAuth, MCP `/mcp`.
2. Coolify Hub: `GROK_BOT_REMINDER_WEBHOOK_URL` + `KEY` (runbook); `SLACK_BOT_TOKEN` jen jako fallback po Grok/Claude.
3. Plugin: [`ŠABLONY/plugins/`](../../plugins/README.md).
