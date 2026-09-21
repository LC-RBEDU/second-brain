# Workspace SENT → INBOX/email/sent

> Cíl: **nové** odeslané e-maily z `lukas@redbuttonedu.cz` (ne odpověď ve vlákně) se uloží do `01-INBOX/email/sent/` a dostanou label **SB Saved**. Odpovědi v cizím vlákně bez hvězdičky se neukládají.

## Proč n8n

OAuth v n8n UI, stejný stack jako hvězdičky. Šablona: `ŠABLONY/n8n/workspace-sent-to-inbox.json`.

## Jak to funguje

1. Poll `in:sent from:lukas@redbuttonedu.cz`
2. Dedupe `messageId`
3. Přeskočí `In-Reply-To` / Re:/Fwd: a drop list (OOO, kalendář, šablony)
4. Markdown → `01-INBOX/email/sent/` + label SB Saved
5. Závazky: chat `agenda-triage` (cron triáže vypnutý)

## Setup

1. Folder ID `email/sent/` do Drive nodu
2. Gmail OAuth = **`lukas@redbuttonedu.cz`**
3. Simplify = OFF, Activate

Osobní Gmail: `ŠABLONY/email-forward-setup.md` (starred personal workflow).

Drop list SSOT: `workspace-sent-format-markdown.js` + `triage_commitments._SENT_INBOX_DROP_RULES`.

## Související

- Hvězdičky: `ŠABLONY/email-forward-setup.md`
- Přehled: `ŠABLONY/n8n/README.md`
