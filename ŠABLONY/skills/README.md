# Agenda skills — zdroj a instalace

**Zdroj pravdy (edituj tady):** `ŠABLONY/skills/<skill>/SKILL.md` (verzováno gitem)

| Skill | Kdy |
|-------|-----|
| `agenda-capture` | Capture do `02-PROJEKTY` (file-per-task + materiály) |
| `agenda-cursor-inbox` | Ulož task/plán/popis z Cursor chatu → `01-INBOX/daily/` + odkaz na konverzaci |
| `agenda-triage` | INBOX batch/deep/pending |
| `agenda-co-ted` | Co teď (TOP priority / dashboard) |
| `agenda-work` | Práce na projektu + výstupy |
| `agenda-status-update` | Single-task status flip (hotovo / odlož / do fokusu / zruš) |
| `agenda-analyze` | Rozbor materiálů → strukturovaný material `.md` |
| `agenda-proces` | Firemní procesy pro RB Universe Procesní architekt |
| `agenda-weekly-review` | Neděle: schválení weekly draftu |
| `agenda-priority-review` | Ad-hoc revize priorit / ICE |
| `agenda-retro` | Neděle: meta retro systému |

## Instalace (agent dělá sám)

Distribuce = **symlinky** `~/.cursor/skills/<skill>/` → `ŠABLONY/skills/<skill>/`.
Díky symlinkům se editace v repu projeví okamžitě — install se spouští jen při **přidání/smazání** skillu:

```bash
bash scripts/install_agenda_skills.sh
```

Skript zároveň odstraní deprecated kopie v `~/.claude/skills/`.

**Nepoužívat:** `.cursor/skills/` v repu (zrušeno), `~/.claude/skills/` (Claude se nepoužívá), ruční kopírování.

## Test v Cursoru

- *"Co teď?"* → `agenda-co-ted`
- *"Projeď inbox"* → `agenda-triage`
- *"Hotovo S21"* → `agenda-status-update`
- *"Jdeme na strategy"* → `agenda-work`
- *"Analyzuj tento PDF"* → `agenda-analyze`
- *"Týdenní shrnutí"* → `agenda-weekly-review`
- *"Revize priorit"* → `agenda-priority-review`
- *"Retro"* → `agenda-retro`

Pravidlo v repu: `.cursor/rules/mrluc-agent-skills.mdc` — úpravy a sync skills vždy dělá agent.
