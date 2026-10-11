# Cowork — folder instructions

Working folder is this repo (`SECOND_BRAIN/`), not only `OBSIDIAN/`.

On every task, follow `ŠABLONY/skills/mrluc-loader/SKILL.md`: read `ŠABLONY/skills/*/SKILL.md` descriptions from disk and open the matching skill.

Po loaderu otevři `OBSIDIAN/00-System/agent-guide-mimo-cursor.md` a řiď se jím. Když ten soubor nejde otevřít, do existujícího `.md` nezapisuj; smíš jen nový soubor do `01-INBOX/daily/`. Když skill a návod nesedí u skriptů, archivu, focus, `## Stav (auto)` a nových tasků, platí návod.

## E-mail a Slack odpovědi

On-demand only — skill `agenda-reply`:

- Gmail: jen **draft**, nikdy send. Connector = Workspace (`lukas@redbuttonedu.cz`). Osobní Gmail konektor nenapojuje (jeden účet).
- Slack: nejdřív ukaž text; pošli až po „pošli“ / „ano“, jako Lukáš.
- Živé Slack vlákno: **ne** zapisuj do `01-INBOX/slack/` (F4 dump off). Pracuj z permalinku / live Slack; triage preview v chatu. Nový task nezakládej; co má vzniknout, dej do `01-INBOX/daily/`. Task založí Cursor na desktopu.

**F4:** Slack L1 = live (Brain / permalink), ne dump do `01-INBOX/slack/`. Cowork scheduled Slack archive 3.3 + 3.4 drž pauznuté (viz `vps/second-brain-hub/README.md`).

Žádné automatické drafty, karty v `_lukas_ai-comm`, ani pointery v `01-INBOX/drafts/`.

Hvězdičky do vaultu řeší n8n (viz `ŠABLONY/email-forward-setup.md`), ne Cowork schedule.

Do not send email or Slack unless a skill explicitly allows it (internal meeting note on a known channel, or confirmed Slack send from `agenda-reply`).

Drive Desktop: this folder must be Available offline.

Morning priority brief (scheduled): paste the prompt from `ŠABLONY/cowork-morning-brief.md` into `/schedule` (weekdays). It leads with lane Rozhodni (`needs_decision`).
