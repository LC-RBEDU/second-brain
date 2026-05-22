---
name: agenda-capture
description: "Capture into MrLUC vault: paste, files, or new files in OBSIDIAN/01-INBOX/. Proposes 02-PROJEKTY/<topic>.md, metadata ICE/Eisenhower, archives to 07-ARCHIV/inbox-processed/. Triggers: capture, zapiš si, INBOX. ALWAYS preview before write. Preserve Poznámky k úkolu / Poznámka u subtasků."
---

# agenda-capture

> Bere libovolný střípek a integruje ho do živého systému v `02-PROJEKTY/`.

**Vault (SSOT):** `OBSIDIAN/` v repo `SECOND_BRAIN` (Google Drive). Absolutní cesta:  
`/Users/lukascypra/My Drive - PRV/# WORK/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- Uživatel paste-ne text do chatu
- V chatu se objeví soubor (PDF, .docx, .xlsx, .png, audio)
- Nové soubory v `01-INBOX/{slack,sembly,email,email/sent,daily}/` (n8n → Drive)
- „zapiš si“, „hoď to k tématu X“, „rozhoď to“, „máš tam něco v inboxu?“

## Workflow

### 1. Načti kontext

1. Přečti `OBSIDIAN/00-System/Memory/about-me.md` (pokud ještě v session ne)
2. Přečti `OBSIDIAN/00-System/Index.md` (existující témata)
3. Při čtení z INBOXu: projdi `01-INBOX/*/` a soubory novější než archiv v `07-ARCHIV/inbox-processed/`

### 2. Vytěž obsah podle zdroje

- **Text v chatu** → ber jak je
- **PDF / .docx / .xlsx** → extrakce textu
- **Obrázek** → vision + OCR text
- **Audio** → transkripce pokud k dispozici; jinak požádej o text
- **INBOX/sembly/** → markdown ze Sembly
- **INBOX/slack/** → markdown z n8n
- **INBOX/email/** → markdown z n8n (forward); přílohy vedle .md otevři zvlášť
- **INBOX/email/sent/** → odeslané z Workspace (`source: sent`); hledej Lukášovy sliby/úkoly; cron je zpracuje jako commitment návrhy v Triage-Pending

### 3. Rozsekej na položky

- Akční bod → jedna položka
- Nápad bez akce → Backlog tématu
- Otázka / čeká na odpověď → Otevřené otázky
- Kontext bez akce → Materiály a poznámky

### 4. Navrhni téma

- Projdi `02-PROJEKTY/*.md` (slug, Kontext)
- Sembly `Suggested topic:` jako default, lze překlopit

### 5. Metadata (akční úkoly)

- Eisenhower Q1–Q4
- ICE (I, C, E 1–10), Score = (I×C)/E
- Vrátit se, Blokováno

### 6. Preview PŘED zápisem

```
## Návrh capture (X položek z [zdroj])

### → 02-PROJEKTY/rb-universe.md
- [Aktivní] [Q2, ICE 8/7/4, S=14] …

### → 02-PROJEKTY/ceo-reporting.md (NOVÉ TÉMA)
- …

OK? (ano / uprav / vyhoď)
```

### 7. Zapiš a archivuj

- Uprav `02-PROJEKTY/<slug>.md` (sekce dle typu položky)
- Nové téma: zkopíruj `00-System/Templates/topic-template.md`
- Update `00-System/Index.md`
- Originál z INBOX → `07-ARCHIV/inbox-processed/YYYY/MM/<den>-<filename>`
- V hubu odkaz na archiv v Materiálech

### 8. Hláška

Krátká, akční: kolik položek, kam, top Q1 pokud je.

## Speciální případy

- Nejasný obsah → jedna cílená otázka
- Q1 → explicitně v hlášce
- Smalltalk → neukládat
- Citlivá data → potvrzení před zápisem

## Tone

`OBSIDIAN/00-System/Memory/anti-ai-writing-tools.md`
