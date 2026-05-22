# Workspace SENT → INBOX/email/sent

> Cíl: každý odeslaný e-mail z `lukas@redbuttonedu.cz` se uloží jako `.md` do `01-INBOX/email/sent/` a VPS triáž z něj vytáhne **Lukášovy závazky** (sliby, úkoly, „pošlu do pátku“).

## Proč n8n (ne Gmail API v cron)

| Varianta | Pro | Proti |
|----------|-----|-------|
| **n8n workflow** (doporučeno) | OAuth v n8n UI, žádné secret v repu; stejný stack jako forward capture | Nutný běžící n8n + Workspace Gmail credential |
| **Gmail API v `triage_run.py`** | Jedna pipeline na Coolify | Refresh token / OAuth JSON v env; složitější dedupe a polling |

Repozitář obsahuje šablonu `ŠABLONY/n8n/workspace-sent-to-inbox.json` — **bez credentials**.

## Jak to funguje

1. n8n pollne Gmail Workspace s filtrem `in:sent from:lukas@redbuttonedu.cz`
2. Dedupe podle `messageId` (workflow static data)
3. Markdown s YAML frontmatter (`source: sent`, `messageId`, `to`, `subject`, `date`)
4. Upload na Drive → `OBSIDIAN/01-INBOX/email/sent/`
5. Coolify cron `triage_run.py` → `triage_commitments.py` → návrhy v `00-System/Triage-Pending/*.json`

## Setup

### 1. Složka na Drive

V `OBSIDIAN/01-INBOX/email/` vytvoř podsložku **`sent/`** a z URL zkopíruj folder ID.

### 2. Gmail OAuth (Workspace)

- n8n → Credentials → **Gmail OAuth2 API**
- Přihlas se jako **`lukas@redbuttonedu.cz`** (Google Workspace)
- Scope: `gmail.readonly` (čtení odeslané pošty)

> Osobní `lukas.cypra@gmail.com` **nepoužívej** — ten je pro forward workflow `email-to-cowork.json`.

### 3. Import workflow

- n8n → Import → `ŠABLONY/n8n/workspace-sent-to-inbox.json`
- Gmail trigger: credential z bodu 2
- Drive node: stejný Drive credential jako ostatní INBOX workflowy
- `folderId` = ID složky `email/sent/`
- **Simplify = OFF** u Gmail triggeru (plné tělo e-mailu)
- Activate

### 4. Coolify (volitelné LLM)

Pro přesnější extrakci závazků nastav na `second-brain-hub`:

| Proměnná | Význam |
|----------|--------|
| `ANTHROPIC_API_KEY` | LLM extrakce závazků (bez klíče běží česká heuristika) |
| `ANTHROPIC_MODEL` | volitelné, default `claude-3-5-haiku-20241022` |

### 5. Test

1. Pošli testovací e-mail z workspace účtu (nebo počkej na další odeslaný)
2. Ověř `.md` v `01-INBOX/email/sent/` na Drive
3. Po cron triáži: `00-System/Triage-Pending/*-batch.json` — položky s `"`kind: commitment`

## Schválení v Cursoru

`schval pending triáž` → skill `agenda-triage` PENDING — u commitment návrhů zkontroluj `confidence` a citaci v `notes`.

## Dedupe a historie

- n8n drží zpracovaná `messageId` ve workflow static data (max ~5000)
- Po reinstall n8n může znovu zpracovat staré odeslané — mitigace: Gmail label `MrLUC-captured` + filtr `-label:MrLUC-captured` v query
- Triage přeskakuje soubory už v otevřeném pending batchi (existující fix)

## Související

- Forward příchozí pošty: `ŠABLONY/email-forward-setup.md`
- Přehled workflowů: `ŠABLONY/n8n/README.md`
- VPS cron: `vps/second-brain-hub/README.md`
