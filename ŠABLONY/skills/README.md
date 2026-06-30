# Agenda skills — zdroj a instalace

**Zdroj pravdy (edituj tady):** `ŠABLONY/skills/<skill>/SKILL.md`

| Skill | Kdy |
|-------|-----|
| `agenda-capture` | Capture do `02-PROJEKTY` |
| `agenda-cursor-inbox` | Ulož task/plán/popis z Cursor chatu → `01-INBOX/daily/` + odkaz na konverzaci |
| `agenda-triage` | INBOX batch/deep |
| `agenda-co-ted` | Co teď (ICE / dashboard) |
| `agenda-work` | Práce na projektu + výstupy |
| `agenda-weekly-review` | Neděle: schválení weekly draftu |
| `agenda-priority-review` | Ad-hoc revize priorit |
| `agenda-retro` | Neděle: meta retro systému |

## Instalace (agent dělá sám)

Po každé úpravě skillu agent synchronizuje do:

1. `~/.cursor/skills/<skill>/` — Cursor (všechny projekty)
2. `~/.claude/skills/<skill>/` — Claude / Cowork
3. `.cursor/skills/<skill>/` — tento repozitář (git)

Ručně (jednorázově nebo po editaci):

```bash
"/Users/lukascypra/My Drive - PRV/# WORK/SECOND_BRAIN/OBSIDIAN/scripts/sync-agenda-skills.sh"
```

## Test v Cursoru

- *"Co teď?"* → `agenda-co-ted`
- *"Projeď inbox"* → `agenda-triage`
- *"Týdenní shrnutí"* → `agenda-weekly-review`
- *"Revize priorit"* → `agenda-priority-review`
- *"Retro"* → `agenda-retro`

Pravidlo v repu: `.cursor/rules/mrluc-agent-skills.mdc` — vytváření a sync skills vždy na agentovi.
