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
| `daily/` | Ruční / mobilní capture (iOS Shortcut) |
| `Clippings/` | Web Clipper / ruční — **bez n8n**, jen Obsidian |

U každého workflow v n8n: node **Save to Drive** → `folderId` = ID **konkrétní** podsložky (z URL ve webu Drive po otevření složky).

Staré cíle (`SECOND_BRAIN_INBOX/INBOX/SLACK`, kořenové `INBOX/` na jiném účtu) **nepoužívat**.

Šablony JSON mají placeholdery `REPLACE_WITH_INBOX_*_FOLDER_ID`.

## Workflows (produkční ID na n8n.redbuttonedu.cz)

| Soubor | n8n workflow ID | Co dělá |
|--------|-----------------|---------|
| `slack-cowork-inbox-with-attachments.json` | `rCOoXlfbD1XcVmtn` | Slack capture + přílohy + vlákna |
| `email-to-cowork.json` | `omQRpDBa48ePiKnT` | Gmail +cowork → INBOX/email/ |
| `workspace-sent-to-inbox.json` | `7fhDXThOaxl1yNtE` | Workspace sent → INBOX/email/sent/ |
| `mobile-capture-to-cowork.json` | `k5p32VUAgaPL0KPe` | Webhook `mobile-cowork-capture` → daily/ |
| `sembly-to-cowork.json` | `hKL04ATDDRSt0FOG` | Sembly webhook → sembly/ |

Deploy z repa: `python3 scripts/deploy_n8n_cowork_workflows.py` (REST API, zachová credentials).

## Workflows

| Soubor | Co dělá | Čeká na |
|--------|---------|---------|
| `sembly-to-cowork.json` | **Webhook** z Sembly → `.md` do `01-INBOX/sembly/` | Veřejná n8n URL, Drive credential, folder ID sembly |
| `slack-cowork-inbox-with-attachments.json` | Nová zpráva v capture kanálu → `.md` + přílohy → `01-INBOX/slack/` | Slack + Drive; vlákno API jen v capture kanálu (forward = unfurl); `onError` na thread fetch + ✅; SSOT `slack-build-threads.js` |
| `slack-reaction-capture.json` | **Deprecated** — stará šablona bez příloh; použij `slack-cowork-inbox-with-attachments.json` |
| `email-to-cowork.json` | Gmail `to:lukas.cypra+cowork@gmail.com` → `01-INBOX/email/` | Gmail + Drive; přílohy → Drive linky v `## Přílohy` |
| `workspace-sent-to-inbox.json` | Workspace `in:sent from:lukas@redbuttonedu.cz` → `01-INBOX/email/sent/` | Workspace Gmail OAuth + Drive; přílohy v `## Přílohy`; **drop list** (to+subject) neukládá do INBOX — SSOT `workspace-sent-format-markdown.js` + `triage_commitments._SENT_INBOX_DROP_RULES` |
| `mobile-capture-to-cowork.json` | Webhook iOS → `01-INBOX/daily/` | Drive folder ID pro `daily/`; optional multipart přílohy |

## Kanonický formát `## Přílohy`

Všechny capture workflow (Slack, email, sent, mobile) používají stejný blok:

```markdown
## Přílohy

- [soubor.pdf](https://drive.google.com/.../view) — application/pdf, 1.2 MB
```

Helper pro n8n Code uzly: `ŠABLONY/n8n/lib/attachments-markdown.js`. Cron triage flaguje položky s `## Přílohy` jako DEEP.

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

Cron na **coolify-dev** čte `01-INBOX/{slack,sembly,email,daily,Clippings}/` (+ rekurzivně `email/sent/`) — viz `vps/second-brain-hub/README.md`. Odeslané e-maily → commitment / archiv návrhy v `Triage-Pending`.
