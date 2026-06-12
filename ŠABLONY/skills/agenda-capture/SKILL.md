---
name: agenda-capture
description: "Capture into MrLUC Second Brain v2 vault: paste, files, or new files in OBSIDIAN/01-INBOX/. Creates task files in 02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md (file-per-task + frontmatter, em-dash U+2014, human-readable filename), archives source to 07-ARCHIV/inbox-processed/. Triggers: capture, zapiš si, INBOX. ALWAYS preview before write. Preserve subtask checklisty (číslované **<ID>-N**) + source links."
---

# agenda-capture (v2)

> Bere libovolný střípek a integruje ho do živého systému jako **soubor-per-task** v `02-PROJEKTY/<slug>/tasks/`.

**Vault (SSOT):** `OBSIDIAN/` v repo `SECOND_BRAIN` (Google Drive).
Cesta: `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Architektura v2 (povinný kontext)

- **TASK** = vlastní `.md` v `02-PROJEKTY/<slug>/tasks/<ID> — <sanitize(title)>.md` se YAML frontmatterem (SSOT) a body s checkboxy. Filename = ID + em-dash U+2014 (` — `) + sanitizovaný titulek (diakritika, emoji zachovány).
- **PROJECT HUB** = `02-PROJEKTY/<HubName>.md` s charter sekcemi a embedy `![[All-tasks.base#ProjectKanban]]` (Bases plugin).
- **MATERIAL** = `02-PROJEKTY/<slug>/materials/<title>.md` (project-specific) nebo `05-RESOURCES/<kategorie>/<title>.md` (cross-project), s frontmatter `projects:` array (M:N).
- Konvence: `OBSIDIAN/00-System/Templates/konvence-a-slovnik.md`, `task-convention.md`, `task-template.md`, `material-template.md`, `id-generation-spec.md`, `filename-normalization.md`.

## Kdy spouštět

- Uživatel paste-ne text do chatu
- V chatu se objeví soubor (PDF, .docx, .xlsx, .png, audio)
- Nové soubory v `01-INBOX/{slack,sembly,email,email/sent,daily,Clippings}/` (n8n → Drive; Clippings = Web Clipper / ručně)
- "zapiš si", "hoď to k tématu X", "rozhoď to", "máš tam něco v inboxu?"

## Workflow

### 1. Načti kontext

1. Přečti `OBSIDIAN/00-System/Memory/about-me.md` (1× per session)
2. Přečti `OBSIDIAN/00-System/Index.md` (existující projekty)
3. Při čtení INBOXu: `01-INBOX/*/` soubory novější než archiv v `07-ARCHIV/inbox-processed/`

### 2. Vytěž obsah podle zdroje

- **Text v chatu** → ber jak je
- **PDF / .docx / .xlsx** → extrakce textu
- **Obrázek** → vision + OCR
- **Audio** → transkripce; jinak požádej o text
- **INBOX/sembly/** → markdown ze Sembly
- **INBOX/slack/** → markdown z n8n
- **INBOX/email/** → markdown z n8n (forward); přílohy vedle .md otevři zvlášť
- **INBOX/email/sent/** → odeslané z Workspace (`source: sent`); hledej Lukášovy sliby/úkoly
- **INBOX/Clippings/** → Web Clipper / uložené stránky (články, docs)
- **INBOX/daily/** → ruční / mobilní zápisky

### 3. Rozsekej na položky

- Akční bod → **task soubor** v `02-PROJEKTY/<slug>/tasks/`
- Nápad bez akce → task se status `Backlog`
- Otázka / čeká na odpověď → projektový hub `## Otevřené otázky`
- Kontext bez akce → **material soubor** v `02-PROJEKTY/<slug>/materials/` nebo `05-RESOURCES/` (viz `.cursor/rules/resources-para.mdc`)
- **Osoby ve zdroji** — porovnej s `05-RESOURCES/lide/*.md` (aliases v frontmatteru):
  - neznámá osoba → preview `add_person` (soubor ze `_ŠABLONA-person.md`, vytěž role/org/email)
  - nová info u známé → preview `update_person` (patch Kontakty/Významná data/Témata)
  - ve všech task/materiálech používej `[[Jméno]]` wikilinks

**Single-user filter:** Capture vždy z Lukášovy perspektivy. Pokud zachycujeme cizí commitment ("Pavel udělá X"), patří jako kontext do související materiálky / `## Poznámky` u tasku, ne jako samostatný task. Lukášova reakce ("zkontrolovat, že Pavel dodá") = task ve statusu `Waiting`.

### 4. Navrhni projekt (slug)

- Projdi `02-PROJEKTY/*.md` (frontmatter `slug` + `aliases`)
- Sembly `Suggested topic:` jako default

### 5. Generuj ID a filename

- **ID:** scanuj `02-PROJEKTY/<slug>/tasks/*` + `07-ARCHIV/tasks-done/<slug>/*`, najdi max ID s prefixem (S, AF, F, RBU, …), použij `+1`. Algoritmus: `00-System/Templates/id-generation-spec.md`.
- **Filename:** `<ID> — <sanitize(title)>.md` (em-dash U+2014 obklopený mezerou; diakritika + emoji zachovány; FS-hostile chars sanitizovány — viz `filename-normalization.md`). Příklady: `S2 — Hierarchie cílů obrat vs. ziskovost vs. dopad.md`, `OPS2 — Nahrát EDU news ♻️ weekly (čtvrtek).md`.

### 6. Frontmatter (povinný)

```yaml
---
id: <ID>
type: task
title: "<lidsky čitelný titulek bez ID prefixu>"
project: "[[<HubFilename>]]"
slug: <slug>
aliases: [<ID>]
status: Next | ASAP | Backlog | Waiting | Done
ice_i: <1-10>
ice_c: <1-10>
ice_e: <1-10>
deadline: <YYYY-MM-DD or empty>
waitUntil: <YYYY-MM-DD or empty>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
materials:
  - "[[<material-slug-or-filename>]]"
source: "<zdroj — Slack/Sembly/email/manual>"
blocked_by: []
---
```

`aliases: [<ID>]` zajišťuje, že `[[<ID>]]` z body resolvuje na soubor i po případné změně titulu.

### 7. Body šablony

```markdown
# <ID> — <Title>

**Z:** <zdroj s link>
**Detail:** <kontext z capture>

## Operativní kroky
- [ ] **<ID>-1** <subtask 1>
- [ ] **<ID>-2** <subtask 2>

## Poznámky / log
- <YYYY-MM-DD>: <poznámka>
```

Subtasky musí mít prefix `**<ID>-N**` (1-indexed). Lze je referencovat z chatu / jiných tasků jako `<ID>-N` (např. „viz PD4-3").

### 8. Preview PŘED zápisem

```
## Návrh capture (X položek z [zdroj])

### → 02-PROJEKTY/rb-universe-development/tasks/RBU30-...md (NEW)
- Status: Next | ICE I8 C7 E4 (Score 14.0)
- Detail: ...

### → 02-PROJEKTY/<slug>/materials/<title>.md (NEW material)
- ...

OK? (ano / uprav / vyhoď)
```

### 9. Zapiš a archivuj

- Vytvoř task soubor v `02-PROJEKTY/<slug>/tasks/`
- Vytvoř material soubor v `02-PROJEKTY/<slug>/materials/` nebo `05-RESOURCES/<kategorie>/`
- U Resources: progressive summarization (3–5 bullet výtah nahoře) + `topics:` tagy (PARA: `.cursor/rules/resources-para.mdc`)
- Po vytvoření **inkrementuj** `open_tasks_count` v hub `.md` frontmatteru
- Originál z INBOX → `07-ARCHIV/inbox-processed/YYYY/MM/<den>-<filename>`
- V hubu odkaz na archiv v Materiálech (nebo nech projít přes triage)
- **Bases dashboard** se sám zaktualizuje při dalším otevření `Dashboard.md` — žádný cron build potřeba.

### 10. Sync lidí + agent context (povinné)

Po každém zápisu spusť (repo root `SECOND_BRAIN/`):

```bash
python3 scripts/sync_lide_people.py --incremental --paths "<cesty vault-relative oddělené středníkem ;>"
python3 scripts/build_agent_context.py
```

`sync_lide_people` doplní wikilinky k lidem v dotčených souborech a přegeneruje tabulky v `05-RESOURCES/lide/*.md`. `build_agent_context` aktualizuje `00-System/agent-context.json`.

### 11. Hláška

Krátká, akční: kolik task souborů, do kterých projektů, top ASAP/Q1 pokud je; `lide_sync: linkified=L profiles_rebuilt=P`.

## Speciální případy

- Nejasný obsah → jedna cílená otázka
- ASAP s deadline today → explicitně v hlášce
- Smalltalk → neukládat
- Citlivá data → potvrzení před zápisem

## Tone

`OBSIDIAN/00-System/Memory/anti-ai-writing-tools.md`
