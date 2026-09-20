---
name: mrluc-loader
description: >-
  MrLUC Second Brain loader. Use whenever the working folder is SECOND_BRAIN,
  or the user mentions vault, INBOX, triage, zápis, task, agenda, Cowork, draft
  odpovědi. First action: read description lines in ŠABLONY/skills/*/SKILL.md
  from disk and follow the matching skill, including its scripts.
---

# MrLUC loader

Working folder must be the repo root `SECOND_BRAIN/` (ŠABLONY + OBSIDIAN), not only `OBSIDIAN/`. Files need to be **Available offline** in Drive Desktop. Streaming placeholders are not a filesystem.

## Start of a task

1. List `ŠABLONY/skills/*/SKILL.md`.
2. Read each YAML `description`.
3. Open the one skill that matches the request and follow it. Do not re-implement it from memory.
4. Vault writes go through that skill. Do not invent a second task tracker.

Cursor installs the same skills via `scripts/install_agenda_skills.sh` → `~/.cursor/skills`. This loader is the Cowork side: the ZIP is uploaded once; the SKILL.md files stay live on disk.

## What this loader does not do

- n8n, Coolify, git push of the hub
- Gmail send or Slack send except where a skill already says so (internal meeting notes)
- Phone-only session when Claude Desktop is closed: disk skills and the vault are not reachable. Gmail drafts still show in the Gmail app.

## Folder instruction

If Cowork asks for folder instructions, use the text in `cowork-instructions.md` at the repo root.
