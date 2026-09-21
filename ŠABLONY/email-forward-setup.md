# Gmail hvězdička → Second Brain INBOX

> Označ e-mail hvězdičkou → do ~2 min celé vlákno v `01-INBOX/email/` jako `sb-<mailbox>-<threadId>.md`, label **SB Saved**, hvězdička pryč.

## Co běží

| Účet | n8n workflow | Stav |
|------|--------------|------|
| `lukas@redbuttonedu.cz` | `xtnI0PYaTp8Ou2la` — Gmail starred → INBOX (workspace) | aktivní |
| `lukas.cypra@gmail.com` | `yuFyLHlioxuE2Jhj` — Gmail starred → INBOX (personal) | **neaktivní** — potřebuje Gmail OAuth osobního účtu |

Query každých 2 min: `(is:starred -label:"SB Saved") OR (newer_than:2h label:"SB Saved")`.

- Nová hvězdička → stáhne celé vlákno, upsert souboru, label SB Saved, unstar.
- Vlákno už ve vaultu (`SB Saved`) → při nové zprávě do 2 h soubor přepíše.

Forward `lukas.cypra+cowork@gmail.com` je zrušený.

## Setup osobního účtu

1. n8n → Credentials → Gmail OAuth2 → Sign in as **`lukas.cypra@gmail.com`**.
2. Do všech Gmail nodů ve workflow `yuFyLHlioxuE2Jhj` vlož ten credential (Drive nech stávající).
3. Activate.

## Odeslané (nové maily, ne odpovědi)

- Workspace: `7fhDXThOaxl1yNtE` — jen nové odeslané bez `In-Reply-To`, bez OOO/kalendáře/šablon; po zápisu label SB Saved.
- Osobní sent: až po OAuth výše — zatím jen Workspace.

Drop list SSOT: `ŠABLONY/n8n/workspace-sent-format-markdown.js` + `triage_commitments._SENT_INBOX_DROP_RULES`.

## On-demand draft

- Cursor / Cowork: skill `agenda-reply` → Gmail draft (Workspace). Nikdy send.
- Osobní draft v Cursoru: až druhý MCP `google-workspace-personal` (viz plán). Cowork druhý Gmail účet neumí.
