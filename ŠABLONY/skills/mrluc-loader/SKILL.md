---
name: mrluc-loader
description: >-
  MrLUC Second Brain loader. Use whenever the working folder is SECOND_BRAIN,
  or the user mentions vault, INBOX, triage, zápis, task, agenda, Cowork, draft
  odpovědi. First action: read description lines in ŠABLONY/skills/*/SKILL.md
  from disk and follow the matching skill, including its scripts. When the task
  is n8n workflow work, also load official n8n-io skills from ~/.cursor/skills
  (using-n8n-skills-official and related) — not agenda skills alone.
---

**F1 (git vault):** pokud vault je git klon (`SECOND_BRAIN_VAULT` / `~/GitHub/second-brain-vault`), skill = **pull + read only** — žádný FS zápis do klonu. Snapshot = VPS; lidský zápis = GitHub web UI PR. Až F2.


# MrLUC loader

Working folder must be the repo root `SECOND_BRAIN/` (ŠABLONY + OBSIDIAN), not only `OBSIDIAN/`. Files need to be **Available offline** in Drive Desktop. Streaming placeholders are not a filesystem.

## Start of a task

1. List `ŠABLONY/skills/*/SKILL.md`.
2. Read each YAML `description`.
3. Open the one skill that matches the request and follow it. Do not re-implement it from memory.
4. Vault writes go through that skill. Do not invent a second task tracker.

### n8n workflows (go-to)

Když zadání obsahuje n8n (workflow, credentials, debugging, error handling, publish):

1. Načti `~/.cursor/skills/using-n8n-skills-official/SKILL.md` (router).
2. Podle situace přidej `n8n-debugging-official`, `n8n-credentials-and-security-official`, `n8n-error-handling-official`, `n8n-workflow-lifecycle-official`.
3. REST přístup: always-on rule `n8n-rest-api-access` + MCP `user-n8n`.
4. Tyto skilly **nejsou** ve `ŠABLONY/` (vendor z [n8n-io/skills](https://github.com/n8n-io/skills)) — leží v `~/.agents/skills/` se symlinkem do `~/.cursor/skills/`. Reinstalace: viz `scripts/install_external_skills.sh`.

Cursor installs agenda skills via `scripts/install_agenda_skills.sh` → `~/.cursor/skills`. This loader is the Cowork side: the ZIP is uploaded once; the SKILL.md files stay live on disk.

## What this loader does not do

- Coolify, git push of the hub
- Gmail send or Slack send except where a skill already says so (internal meeting notes)
- Phone-only session when Claude Desktop is closed: disk skills and the vault are not reachable. Gmail drafts still show in the Gmail app.

## Folder instruction

If Cowork asks for folder instructions, use the text in `cowork-instructions.md` at the repo root.
