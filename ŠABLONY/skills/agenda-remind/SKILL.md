---
name: agenda-remind
description: "Schedule Slack DM reminders at a specific date/time independent of Cursor chat. Writes JSON to 00-System/Reminders-Pending/; VPS cron reminders_dispatch.py sends via Slack bot. Triggers: připomeň mi, remind me, Slack připomínka, reminder v ..., v pondělí v 8. Prefer over Google Calendar for agent-scheduled pings. ALWAYS preview before write."
---

# agenda-remind

> Naplánuj **Slack DM** na konkrétní čas. Doručení běží na **VPS cron** — nezávisle na tom, jestli jsi v Cursoru.

**Vault:** `OBSIDIAN/00-System/Reminders-Pending/*.json`  
**Cron (VPS):** `reminders_dispatch.py` každé **2 min** → `chat.postMessage` DM Lukášovi

## Kdy spouštět

- „Připomeň mi … ve středu v 8“
- „Reminder v pondělí 14:00: …“
- „Za 2 hodiny mi pošli Slack …“
- Zrušení: „zruš připomínku …“ / „co mám naplánované?“

**Nepoužívat** pro task `waitUntil` / lifecycle — to je probuzení úkolu ve vaultu, ne Slack ping.

## Jak to funguje

1. Agent parsuje **Europe/Prague** (`deliver_at` musí být v budoucnosti).
2. Zápis JSON do `00-System/Reminders-Pending/{id}.json` (Drive sync → VPS).
3. Cron na coolify-dev pošle Slack DM a přesune soubor do `Reminders-Sent/`.

## Workflow agenta

### 1. Preview (povinné)

```
Navrhuju Slack připomínku:

  Kdy: 2026-09-02 08:00 (Europe/Prague)
  Zpráva: …
  Task ref (volitelně): S12-16 — H2 rozpočty a forecast — urgovat u Domči tabulky fakturace Honzy a Luboše za 06–07/2026

OK? (ano / uprav / cancel)
```

### 2. Zápis

```bash
python3 scripts/schedule_reminder.py schedule \
  --at "2026-09-02 08:00" \
  --message "Urgovat u Domči tabulky fakturace Honzy a Luboše (06–07/2026)." \
  --task-ref "S12-16 — H2 rozpočty a forecast — urgovat u Domči tabulky fakturace Honzy a Luboše za 06–07/2026"
```

Výstup: `id`, `deliver_at`, cesta k JSON.

### 3. Potvrzení uživateli

- **ID připomínky** + přesný čas + že doručení jde **Slack DM** (ne Cursor chat).
- Pokud cron ještě není nasazený / chybí token → říct explicitně (viz Setup).

### Seznam / zrušení

```bash
python3 scripts/schedule_reminder.py list
python3 scripts/schedule_reminder.py cancel 2026-09-02-0800-rem-abc123
```

## Formát zprávy

- Stručně, registr A (kolega sám sobě).
- U tasku vždy **`ID — title`** v `--task-ref` (ne samotné ID).
- Slack text = `message` + volitelný řádek `↳ {task_ref}`.

## Setup (jednorázově na VPS)

1. **Slack app** (stejná jako Cowork Capture) — přidat bot scopes:
   - `chat:write`
   - `im:write`
   - `users:read.email` (lookup DM přes email)
   - → Reinstall to Workspace
2. **Coolify env** na second-brain-hub:
   - `SLACK_BOT_TOKEN=xoxb-...` (Bot User OAuth Token)
   - `SLACK_REMINDER_USER_EMAIL=lukas@redbuttonedu.cz` (default)
   - volitelně `SLACK_REMINDER_DM_USER_ID=U...` (přeskočí lookup)
3. **Deploy** repo + crontab řádek `reminders_dispatch.py` (už v repu).
4. Ověření: test JSON s `deliver_at` za 1 min → log `/var/log/second-brain/reminders.log`.

Detail: `vps/second-brain-hub/docs/slack-reminders-setup.md`

## Fallback

- Google Calendar = OK pro osobní blok v kalendáři, ale **agent default = tento skill** (Slack + audit trail ve vaultu).
- Cursor chat **nedokáže** sám poslat zprávu bez běžící session.

## Pravidla

- **Preview před zápisem** — stejně jako u capture/triage.
- **Nepiš secrets** do vault JSON.
- Max délka zprávy ~3000 znaků (Slack limit).
- Duplicitní `--at` + stejná zpráva → zeptej se, jestli nejde o update (cancel + nový).
