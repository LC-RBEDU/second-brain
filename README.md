# SECOND_BRAIN (repo)

Tenké repo pro **automatizaci** kolem MrLUC vaultu — **ne** pro živé poznámky a úkoly.

## SSOT (jediný zdroj pravdy)

**Obsidian vault MrLUC** (iCloud):

`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC`

Struktura: `01-INBOX`, `02-PROJEKTY`, `03-AREAS`, `05-RESOURCES`, `07-ARCHIV`, `00-System`.

Návod: v vaultu `00-System/Memory/jak-ctu-mrluc.md`.

## Deprecated v tomto repu (needitovat jako agendu)

| Složka | Stav |
|--------|------|
| `AGENDA/` | Zastaralý Cowork mirror — projekty jsou v MrLUC `02-PROJEKTY/` |
| `VÝSTUPY/` | Zastaralý mirror — výstupy jsou v `02-PROJEKTY/<slug>/` |
| `INBOX/` | Zastaralý mirror — capture je v MrLUC `01-INBOX/` |

## Co v repu používat

- `vps/second-brain-hub/` — cron, dashboard build, deploy na Coolify
- `scripts/` — lokální watch + serve dashboardu
- `ŠABLONY/` — n8n workflow JSON, skills kopie

## Dashboard lokálně

Viz [vps/second-brain-hub/README.md](vps/second-brain-hub/README.md).
