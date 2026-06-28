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

### Refresh agent context + lidé (lokální, po zápisu v Cursoru)

```bash
python3 scripts/build_agent_context.py
python3 scripts/sync_lide_people.py --incremental --paths "02-PROJEKTY/.../tasks/foo.md,07-ARCHIV/..."
```

`build_agent_context` → `OBSIDIAN/00-System/agent-context.json`. `sync_lide_people` (incremental po triáži/capture) → wikilinky + tabulky `05-RESOURCES/lide/*.md`. Skills `agenda-triage` / `agenda-capture` to spouštějí automaticky po apply.

### Sync skills (po editaci ŠABLONY/skills/<skill>/SKILL.md)

```bash
bash scripts/install_agenda_skills.sh
```

Symlinky `~/.cursor/skills/agenda-*` → `ŠABLONY/skills/` (jediný SSOT).

### Hub stav + zdroje dat

```bash
python3 scripts/update_hub_state.py          # ## Stav (auto) ve všech hubech
python3 scripts/patch_hub_sources.py --strip-workspace   # legacy cleanup
python3 scripts/create_project_hub.py --help # nový projekt (scaffold)
```

Charter **`## Zdroje dat`** (konkrétní URL) + frontmatter `sources:` / `notebooklm:` — viz [[00-System/Templates/agenda-system]] §6. Nový projekt: [[00-System/Templates/new-project-workflow]].

### NotebookLM (vyžaduje jednorázový login)

```bash
pip3 install --user "notebooklm-py[browser]"
~/Library/Python/3.14/bin/notebooklm login   # browser OAuth — jednou
python3 scripts/notebooklm_query.py list
python3 scripts/notebooklm_query.py ask "Allfred" "…"
```

Po inventuře doplň `notebooklm:` v hub frontmatteru (např. Allfred).

### Cursor hooks (repo `.cursor/hooks.json`)

- `afterFileEdit` → debounced `build_agent_context.py`
- `sessionStart` → výtah z `agent-context.json`

### VPS cron (Coolify, supercronic) — viz `vps/second-brain-hub/deploy/crontab`

| Skript | Frekvence | Účel |
|--------|-----------|------|
| `lifecycle_done_from_checkboxes.py` | every 2h :00 | All checkboxes [x] → status: Done |
| `lifecycle_waiting_to_asap.py` | every 2h :01 | Waiting + waitUntil ≤ dnes → ASAP (waitUntil smaže) |
| `lifecycle_waiting_default_waituntil.py` | every 2h :02 | Waiting bez waitUntil → doplní dnes + 3 dny |
| `lifecycle_waituntil_hygiene.py` | every 2h :03 | waitUntil vyčistí u tasků mimo Waiting |
| `lifecycle_overdue_flag.py` | every 2h :04 | Append OVERDUE log do body |
| `archive_done_tasks.py` | every 2h :05 | Done > 90 dní → 07-ARCHIV/tasks-done/<slug>/ |
| `lifecycle_recurring.py` | every 2h :06 | Done + recurring → archive + nová instance |
| `lifecycle_hub_state.py` | every 2h :07 | `## Stav (auto)` v project hubech + staleness |
| `lifecycle_asap_backfill.py` | každou hodinu 10:00–02:00 | ASAP < 3 → promote top Next (today_score) |
| `triage_llm_run.py` | Po-Pa 7/14/20, So-Ne 7 | LLM triáž → Triage-Pending/*.json (`CURSOR_API_KEY` + `cursor-agent`) |
| `inbox_inventory.py` | Po 6:55 | Log nezpracovaného INBOXu (bez návrhů) |
| `lifecycle_extra_edu_news.py` | denně 07:10 | OPS2 marker block refresh (top 5 témat) |
| `build_agent_context.py` (VPS) | každých 15 min v workhours | agent-context.json refresh |
| `weekly_summary_draft.py` + `retro_draft.py` | Ne 20:00 | týdenní + retro draft |

**Deploy LLM triáže:** nastav Coolify secret `CURSOR_API_KEY` + nainstaluj `cursor-agent` CLI v cron kontejneru. Bez klíče cron jen zaloguje inbox a triáž běží manuálně (`projeď inbox`).

## Git

Viz `.gitignore` — `OBSIDIAN/` je celé excluded (Drive versioning).
Versioned: `vps/`, `scripts/`, `ŠABLONY/`, `.cursor/`.

## Související dokumentace

- `OBSIDIAN/00-System/agent-bootstrap.md` — uživatelská kopie agent kontextu
- `OBSIDIAN/00-System/Templates/agenda-system.md` — kompletní průvodce v2
- `OBSIDIAN/00-System/Templates/konvence-a-slovnik.md`
- `OBSIDIAN/00-System/Memory/vault-gdrive-migration.md` — historie Phase 1 migrace
- `vps/second-brain-hub/README.md` — VPS deployment
