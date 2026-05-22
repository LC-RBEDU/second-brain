# n8n workflows pro Agenda systém

5 workflows. Každý je samostatný JSON, importovatelný do n8n.

## Google Drive — vault INBOX (SECOND_BRAIN)

**Cesta na Drive (PRV):** `SECOND_BRAIN/OBSIDIAN/01-INBOX/`

| Podsložka | Účel |
|-----------|------|
| `slack/` | Slack capture workflow |
| `sembly/` | Sembly webhook |
| `email/` | Gmail forward |
| `email/sent/` | Workspace odeslané (`lukas@redbuttonedu.cz`) |
| `daily/` | Ruční / mobilní capture |

U každého workflow v n8n: node **Save to Drive** → `folderId` = ID **konkrétní** podsložky (z URL ve webu Drive po otevření složky).

Staré cíle (`SECOND_BRAIN_INBOX/INBOX/SLACK`, kořenové `INBOX/` na jiném účtu) **nepoužívat**.

Šablony JSON mají placeholdery `REPLACE_WITH_INBOX_*_FOLDER_ID`.

## Workflows

| Soubor | Co dělá | Čeká na |
|--------|---------|---------|
| `sembly-to-cowork.json` | **Webhook** z Sembly → `.md` do `01-INBOX/sembly/` | Veřejná n8n URL, Drive credential, folder ID sembly |
| `slack-reaction-capture.json` | Nová zpráva v capture kanálu → `.md` → `01-INBOX/slack/` | Slack + Drive; viz `slack-app-setup-checklist.md` |
| `email-to-cowork.json` | Gmail `to:lukas.cypra+cowork@gmail.com` → `01-INBOX/email/` | Gmail + Drive; přílohy do stejné nebo `email-attachments` podsložky |
| `workspace-sent-to-inbox.json` | Workspace `in:sent from:lukas@redbuttonedu.cz` → `01-INBOX/email/sent/` | Workspace Gmail OAuth + Drive; viz `workspace-sent-email-setup.md` |
| `mobile-capture-to-cowork.json` | Webhook iOS → `01-INBOX/manual/` | Drive folder ID pro `manual/` |

## Společné předpoklady

- n8n self-hosted
- **Google Drive credential** — cíl = `SECOND_BRAIN/OBSIDIAN/01-INBOX/<podsložka>/`
- Slack: jen inbound capture

## Postup importu

1. n8n → Workflows → Import from File
2. Nastav credentials na triggerech a Drive nodech
3. U každého „Save to Drive“ ověř `folderId` = konkrétní podsložka pod `SECOND_BRAIN/01-INBOX/`
4. Activate workflow

## VPS triage

Cron na **coolify-dev** čte `01-INBOX/{slack,sembly,email,email/sent,daily}/` — sync vaultu viz `vps/second-brain-hub/README.md`. Odeslané e-maily → commitment návrhy v Triage-Pending.
