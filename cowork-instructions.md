# Cowork — folder instructions

Working folder is this repo (`SECOND_BRAIN/`), not only `OBSIDIAN/`.

On every task, follow `ŠABLONY/skills/mrluc-loader/SKILL.md`: read `ŠABLONY/skills/*/SKILL.md` descriptions from disk and open the matching skill.

## E-mail a Slack odpovědi

On-demand only — skill `agenda-reply`:

- Gmail: jen **draft**, nikdy send. Connector = Workspace (`lukas@redbuttonedu.cz`). Osobní Gmail konektor nenapojuje (jeden účet).
- Slack: nejdřív ukaž text; pošli až po „pošli“ / „ano“, jako Lukáš.
- Živé Slack vlákno: zapiš do `01-INBOX/slack/` (dedup channel+thread_ts) a spusť triage preview; task/hub až po schválení.

Continuous reply-watch (nové odpovědi v DM/GDM a sledovaných vláknech) = **VPS `slack_poll`**, ne Cowork `on:date` sweep. Scheduled Slack archive tasky 3.3 + 3.4 mají být pauznuté (viz `vps/second-brain-hub/README.md`).

Žádné automatické drafty, karty v `_lukas_ai-comm`, ani pointery v `01-INBOX/drafts/`.

Hvězdičky do vaultu řeší n8n (viz `ŠABLONY/email-forward-setup.md`), ne Cowork schedule.

Do not send email or Slack unless a skill explicitly allows it (internal meeting note on a known channel, or confirmed Slack send from `agenda-reply`).

Drive Desktop: this folder must be Available offline.

Morning priority brief (scheduled): paste the prompt from `ŠABLONY/cowork-morning-brief.md` into `/schedule` (weekdays). It leads with lane Rozhodni (`needs_decision`).
