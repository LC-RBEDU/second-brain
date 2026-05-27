# SECOND_BRAIN — repo (automatizace v2)

Git + tooling kolem Obsidian vaultu. **Vault (poznámky) není v kořeni repa.**

## Obsidian vault (SSOT)

```
/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN/
```

Mirror na Google Drive — verzování řeší Drive native versioning (proto `OBSIDIAN/` = git-ignored).

| Složka | Účel |
|--------|------|
| `Home.md`, `00-System/`, `01-INBOX/`, `02-PROJEKTY/`, `03-AREAS/`, `05-RESOURCES/`, `07-ARCHIV/` | Second Brain v Obsidianu |
| `vps/`, `scripts/`, `ŠABLONY/`, `.cursor/` | Jen v **kořeni repa** — neotevírat ve vaultu |

## Architektura v2 (po file-per-task migraci)

- **TASK** = single `.md` v `02-PROJEKTY/<slug>/tasks/<ID>-<slug>.md` se YAML frontmatterem (SSOT)
- **PROJECT HUB** = `02-PROJEKTY/<Hub>.md` s charterem + Bases embedy (`![[All-tasks.base#ProjectKanban]]`)
- **MATERIAL** = `02-PROJEKTY/<slug>/materials/` (project-specific) nebo `05-RESOURCES/<category>/` (cross-project), M:N přes `materials:` array v task frontmatteru
- **DASHBOARD** = `OBSIDIAN/Dashboard.md` + `Bases/*.base` plugins (live z frontmatteru, žádný HTML build)
- **AGENT CONTEXT** = `OBSIDIAN/00-System/agent-context.json` snapshot (every-write trigger / VPS cron 15 min)

Detaily: `OBSIDIAN/00-System/Templates/agenda-system.md`, `agent-bootstrap.md`.

## Příkazy

### Refresh agent context (lokální, every-write)

```bash
python3 scripts/build_agent_context.py
```

Píše `OBSIDIAN/00-System/agent-context.json` — Cursor agent ho čte přes always-applied rule `.cursor/rules/second-brain-bootstrap.mdc`.

### Sync skills (po editaci ŠABLONY/skills/<skill>/SKILL.md)

```bash
bash scripts/sync-agenda-skills.sh
```

### VPS cron (Coolify, supercronic) — viz `vps/second-brain-hub/deploy/crontab`

| Skript | Frekvence | Účel |
|--------|-----------|------|
| `lifecycle_done_from_checkboxes.py` | 03:00 | All checkboxes [x] → status: Done |
| `lifecycle_waiting_to_asap.py` | 03:10 | Waiting + waitUntil ≤ dnes → ASAP (waitUntil smaže) |
| `lifecycle_waituntil_hygiene.py` | 03:15 | waitUntil vyčistí u tasků mimo Waiting |
| `lifecycle_overdue_flag.py` | 03:20 | Append OVERDUE log do body |
| `archive_done_tasks.py` | 04:00 | Done > 90 dní → 07-ARCHIV/tasks-done/<slug>/ |
| `lifecycle_recurring.py` | 04:30 | Done + recurring → archive + nová instance |
| `triage_run.py` | Po-Pa 7/14/20, So-Ne 7 | INBOX → Triage-Pending/*.json (v2 schema) |
| `lifecycle_extra_edu_news.py` | denně 07:10 | OPS2 marker block refresh (top 5 témat) |
| `build_agent_context.py` (VPS) | každých 15 min v workhours | agent-context.json refresh |
| `weekly_summary_draft.py` + `retro_draft.py` | Ne 20:00 | týdenní + retro draft |

## Git

Viz `.gitignore` — `OBSIDIAN/` je celé excluded (Drive versioning).
Versioned: `vps/`, `scripts/`, `ŠABLONY/`, `.cursor/`.

## Související dokumentace

- `OBSIDIAN/00-System/agent-bootstrap.md` — uživatelská kopie agent kontextu
- `OBSIDIAN/00-System/Templates/agenda-system.md` — kompletní průvodce v2
- `OBSIDIAN/00-System/Templates/konvence-a-slovnik.md`
- `OBSIDIAN/00-System/Memory/vault-gdrive-migration.md` — historie Phase 1 migrace
- `vps/second-brain-hub/README.md` — VPS deployment
