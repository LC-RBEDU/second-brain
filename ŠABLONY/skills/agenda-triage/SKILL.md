---
name: agenda-triage
description: "INBOX triage in MrLUC vault, pending batch approval from cron, or re-priority. Triggers: projeď inbox, schval pending triáž, apply batch, udělejme triage. Modes: BATCH, DEEP, PENDING (read 00-System/Triage-Pending/*.json). Updates 02-PROJEKTY/<slug>.md, 00-System/Index.md, archives to 07-ARCHIV/inbox-processed/. ALWAYS preview before write."
---

# agenda-triage

> Pravidelný průchod nasbíraného. Capture ukládá rychle, triage pročistí.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive - PRV/# WORK/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- „Projeď inbox“ / „udělejme triage“ / „co tam mám nasbíráno“
- V `01-INBOX/*` je >5 nezpracovaných položek
- „Schval pending triáž“ / „apply batch“ → mód **PENDING**

## Módy

```
Mám N položek v INBOXu.
  [B]atch — rychlý souhrn, potvrzení najednou
  [D]eep — položka po položce
  [P]ending — schválení 00-System/Triage-Pending/*.json (cron návrh)
  [R]e-priority — delegace na agenda-priority-review

Default: B (nebo P pokud uživatel žádá pending).
```

## Batch

1. Načti `01-INBOX/*/`
2. Extrahuj, navrhni téma + ICE + kvadrant
3. Preview jako v `agenda-capture`
4. Po OK: zápis do `02-PROJEKTY/`, archiv, Index

### Odeslané e-maily (`01-INBOX/email/sent/`)

- Capture: n8n `workspace-sent-to-inbox.json` (Workspace `lukas@redbuttonedu.cz`, frontmatter `source: sent`)
- Cron `triage_run.py` + `triage_commitments.py` navrhne jen **Lukášovy závazky** z odeslané pošty (ne generický úkol na celý mail)
- Batch JSON může mít `kind: "commitment"`, `confidence` (0–1), `action`: `add_task` | `add_note_to_task` | `commitment_watch`
- Odeslaný mail bez závazku → cron ho přeskočí (žádný návrh v batchi)
- PENDING: u commitmentů zkontroluj `notes` (citace z e-mailu) a `confidence` před schválením

## Deep

Pro každou položku: shrnutí, návrh tématu/metadata, OK/uprav/přeskoč/drop.

## PENDING (cron)

1. Načti nejnovější `00-System/Triage-Pending/*-batch.json` + summary
2. Ukaž změny (nové úkoly, commitment z sent mail, …). U `kind: commitment` zobraz `confidence` a citaci v `notes`. Vypršené **Waiting** řeší `build_dashboard.py` automaticky (hub → **ASAP**); staré `waiting_expired` pending batch jen archivuj, neptej se znovu.
3. **Nikdy neaplikuj bez explicitního „ano“ / „apply“**
4. Po schválení: aplikuj na hub `.md`, přesuň batch do `Triage-Applied/`, rebuild dashboard pokud požádáno

## Refresh Index

Po triage: pro každý `02-PROJEKTY/<slug>.md` aktivní úkoly, top Score, last update → tabulka v `00-System/Index.md`.

## Re-prioritizace

„Eisenhower přepočítej“ → skill `agenda-priority-review` nebo projdi aktivní úkoly (po termínu, Q1 dnes, Q2 top 3).

## Kontext před startem

- `00-System/Memory/about-me.md`
- `00-System/Index.md`
