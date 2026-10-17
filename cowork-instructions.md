# Cowork — folder instructions

Working folder is this tooling repo (`SECOND_BRAIN/`). Vault je git `~/GitHub/second-brain-vault`.

On every task, follow `ŠABLONY/skills/mrluc-loader/SKILL.md`: read `ŠABLONY/skills/*/SKILL.md` descriptions from disk and open the matching skill.

Po loaderu otevři `~/GitHub/second-brain-vault/00-System/agent-guide-mimo-cursor.md` a řiď se jím (Brain-first). Inventář botů: `~/GitHub/second-brain-vault/02-PROJEKTY/second-brain/materials/2026-10-11 — boti-prehled.md`. Když návod nejde otevřít a Brain MCP taky ne, do existujícího `.md` nezapisuj; smíš jen nový soubor do `01-INBOX/daily/`. Když skill a návod nesedí u skriptů, archivu, focus, `## Stav (auto)` a write path, platí návod.

**Vault write:** Brain MCP (`capture_daily`, `create_task`, `update_task`, …). FS overwrite jen legacy fail-path po explicitním dovolení.

## E-mail a Slack odpovědi

On-demand only — skill `agenda-reply`:

- Gmail: jen **draft**, nikdy send. Connector = Workspace (`lukas@redbuttonedu.cz`). Osobní Gmail konektor nenapojuje (jeden účet).
- Slack: nejdřív ukaž text; pošli až po „pošli“ / „ano“, jako Lukáš.
- Živé Slack vlákno: **ne** zapisuj do `01-INBOX/slack/` (F4 dump off). Pracuj z permalinku / live Slack; triage preview v chatu.

**F4:** Slack L1 = live (Brain / permalink), ne dump do `01-INBOX/slack/`. Cowork scheduled Slack archive 3.3 + 3.4 drž pauznuté (viz `vps/second-brain-hub/README.md`).

Žádné automatické drafty, karty v `_lukas_ai-comm`, ani pointery v `01-INBOX/drafts/`.

Hvězdičky do vaultu řeší n8n (viz `ŠABLONY/email-forward-setup.md`), ne Cowork schedule — writers jsou off.

Do not send email or Slack unless a skill explicitly allows it (internal meeting note on a known channel, or confirmed Slack send from `agenda-reply`).

Drive Desktop: this folder must be Available offline (read / legacy).

Morning priority brief (scheduled): paste the prompt from `ŠABLONY/cowork-morning-brief.md` into `/schedule` (weekdays). It leads with lane Rozhodni (`needs_decision`).
