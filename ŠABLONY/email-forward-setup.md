# Gmail hvězdička → Second Brain INBOX

> Označ e-mail hvězdičkou → do ~2 min celé vlákno v `01-INBOX/email/` jako `sb-<mailbox>-<threadId>.md`, label **SB Saved**, hvězdička pryč.

## Co běží

| Účet | n8n workflow | Stav |
|------|--------------|------|
| `lukas@redbuttonedu.cz` | `xtnI0PYaTp8Ou2la` — Gmail starred → INBOX (workspace) | aktivní |
| `lukas.cypra@gmail.com` | `yuFyLHlioxuE2Jhj` — Gmail starred → INBOX (personal) | aktivní |

Query každých 2 min: `(is:starred -label:"SB Saved") OR (newer_than:2h label:"SB Saved")`.

- Nová hvězdička → stáhne celé vlákno, upsert souboru, label SB Saved, unstar.
- Vlákno už ve vaultu (`SB Saved`) → při nové zprávě do 2 h soubor přepíše.

Forward `lukas.cypra+cowork@gmail.com` je zrušený.

## Setup osobního účtu

Hotovo (2026-09-22): credential `Gmail - lukas.cypra@gmail.com`, workflow Active, stejný Drive upsert jako workspace (staticData).

## Přílohy + osobní doklady → Drive

Personal starred (`yuFyLHlioxuE2Jhj`) stahuje MIME přílohy (B0 filtr) jako co-located `{sb-personal-{threadId}}__{name}` + sekce `## Přílohy` (→ DEEP triáž). Odkaz „stáhnout fakturu/doklad/PDF“ (B4) best-effort před HTML stripem; session-gated → ručně `~/Downloads`.

Platební doklad po schválení v `agenda-triage` (`upload_personal_receipt`) → Drive složka [`1CpvJdkIgtzNqz33Bf61tseyyWXWySqDK`](https://drive.google.com/drive/folders/1CpvJdkIgtzNqz33Bf61tseyyWXWySqDK) / `MM-YYYY` dle DUZP. Config: `OBSIDIAN/00-System/personal-payment-docs.json`. Manifest: `00-System/Personal-Docs-Uploaded/manifest.json`.

## Odeslané (nové maily, ne odpovědi)

- Workspace: `7fhDXThOaxl1yNtE` — jen nové odeslané bez `In-Reply-To`, bez OOO/kalendáře/šablon; po zápisu label SB Saved.
- Osobní sent: zatím ne — jen Workspace.

Drop list SSOT: `ŠABLONY/n8n/workspace-sent-format-markdown.js` + `triage_commitments._SENT_INBOX_DROP_RULES`.

## On-demand draft

- Cursor / Cowork: skill `agenda-reply` → Gmail draft (Workspace). Nikdy send.
- Osobní draft v Cursoru: až druhý MCP `google-workspace-personal` (viz plán). Cowork druhý Gmail účet neumí.
