---
name: agenda-weekly-review
description: "Use when user asks for týdenní shrnutí, weekly review, schvál weekly draft, or after Sunday cron created 00-System/weekly/*-draft.md. Reads draft, enriches narrative, writes final YYYY-Www.md. Optionally updates ## Progress in 02-PROJEKTY hubs. ALWAYS preview before write."
---

# agenda-weekly-review

> Nedělní rytmus: cron vytvoří faktický draft → ty schválíš a doplníš smysl v chatu.

## Kdy spouštět

- "Týdenní shrnutí" / "weekly review" / "schval weekly draft"
- Po cronu: soubor `OBSIDIAN/00-System/weekly/YYYY-Www-draft.md` existuje
- Neděle večer — hned po otevření draftu (před nebo po `agenda-retro`)

## Cesty (vault, v2)

- Vault: `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`
- Draft: `00-System/weekly/YYYY-Www-draft.md`
- Finální: `00-System/weekly/YYYY-Www.md`
- Procesy: `00-System/Memory/procesy-mrluc.md`

## Workflow

### 1. Načti draft

- Najdi nejnovější `*-draft.md` v `00-System/weekly/` (nebo konkrétní týden z dotazu)
- (Po F8) Přečti `00-System/agent-context.json` pro kontext priorit
- Jinak: scan `02-PROJEKTY/<slug>/tasks/*.md` frontmatterů (file-per-task) a `07-ARCHIV/tasks-done/<slug>/*.md` pro Done tasky tohoto týdne

### 2. Obohať (LLM) — struktura po **Areas** (F6)

Projdi 7 oblastí z `03-AREAS/_index.md`. U každé area krátce:
- **Je standard ohrožen?** (otevřené tasky, blokéry, stale flag z `agent-context.json`)
- **Má area pohyb?** (nové logy, dokončené tasky v projektech area)

Pak doplň ke skeletonu draftu:

- **Co se povedlo** — 3–7 bulletů s dopadem (ne jen seznam task ID)
- **Kam se posunulo** — per projekt max 1 věta u aktivních témat
- **Blokéry / Waiting** — co čeká a do kdy
- **Priorita příští týden** — max 5 konkrétních bodů (odkaz na task ID)

### 3. Preview

Ukaž finální markdown celý. Zeptej se: schválit / upravit sekci X.

### 4. Zápis (po „schval“)

- Ulož `YYYY-Www.md` (bez `-draft` suffix)
- Volitelně: do `## Progress` u 2–3 hubů přidej 1 odrážku s datem (nesmaž staré bez potvrzení)
- Draft ponech nebo přejmenuj na `_archived` — dle preference uživatele

## Pravidla

- Markdown hubů je SSOT pro úkoly — weekly soubor je SSOT pro týdenní narrative
- Nikdy neměň ICE/priority v úkolech v tomto skillu (k tomu `agenda-priority-review`)
- Česky, stručně, akční tón
