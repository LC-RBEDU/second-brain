# Slack připomínky (agent → DM)

> Agent zapisuje JSON do vaultu; **VPS cron** posílá Slack DM v `deliver_at`.

## Architektura

```
Cursor (agenda-remind)
  → 00-System/Reminders-Pending/*.json  (Google Drive)
  → coolify-dev: reminders_dispatch.py (*/2 * * * *)
  → Slack DM (chat.postMessage)
  → 00-System/Reminders-Sent/*.json
```

## Coolify (second-brain-hub)

**Ověřeno 2026-08-29** (SSH `coolify-dev`, kontejner `second-brain-hub`):

| Env | Stav |
|-----|------|
| `CALENDAR_USER_EMAIL` | ✅ nastaveno (kalendář; cron ho použije i pro DM lookup) |
| `SLACK_BOT_TOKEN` | ❌ **chybí** — token není v tomto kontejneru |
| `reminders_dispatch.py` | ❌ **není deploynuté** (kód jen lokálně v repu) |

Slack pro capture běží v **n8n** (credential „Slack - Lukáš - RB EDU“) — **jiná služba**, token se do second-brain-hub **nepředává sám**.

| Env | Akce |
|-----|------|
| `SLACK_BOT_TOKEN` | **doplnit** — stejný `xoxb-...` jako v n8n credential |
| `SLACK_REMINDER_USER_EMAIL` | volitelné; bez něj se použije `CALENDAR_USER_EMAIL` |

## Scopes — co už běží vs. co připomínky potřebují

**n8n Cowork Capture dnes:** čtení kanálů, `reactions:write` (✅), `files:read`, `conversations.replies`. **Neposílá** `chat.postMessage`.

**Připomínky navíc potřebují:** `chat:write`, `im:write`, `users:read.email` — ověř v Slack app → OAuth & Permissions. Pokud chybí → Reinstall to Workspace.

## Slack app — scopes (checklist)

K existující appce **Cowork Capture** (viz `ŠABLONY/slack-app-setup-checklist.md`):

| Scope | Proč |
|-------|------|
| `chat:write` | poslat zprávu |
| `im:write` | otevřít DM |
| `users:read.email` | lookup email → user ID |

→ **Install App → Reinstall to Workspace**

## Ruční test

```bash
# Mac — naplánovat za 2 min
python3 scripts/schedule_reminder.py schedule \
  --at "$(date -v+2M '+%Y-%m-%d %H:%M')" \
  --message "Test Slack reminder"

# VPS log (po deployi)
tail -f /var/log/second-brain/reminders.log
```

## Složky ve vaultu

| Složka | Obsah |
|--------|--------|
| `Reminders-Pending/` | čeká na odeslání |
| `Reminders-Sent/` | odeslané (+ `sent_at`, `slack_ts`) |
| `Reminders-Cancelled/` | zrušené agentem |

Skill: `agenda-remind`.
