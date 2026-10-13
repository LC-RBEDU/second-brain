# Red Button Design System — local SSOT (Cursor / Grok)

Lokální kopie **firemního brand / marketing design systemu** z Claude artifactu.

| Role | Co |
|---|---|
| **Claude** | Má to jako firemní skill (marketing manažerka). **Neduplikovat** jako Claude skill. |
| **Cursor / Grok Bot** | Tahle složka = SSOT. Před použitím **check-before-use** (`manifest.json` + refresh skript). |

## Soubory

| Cesta | Účel |
|---|---|
| [`SOURCE.url`](SOURCE.url) | Kanonická URL artifactu |
| [`manifest.json`](manifest.json) | `source_url`, `fetched_at`, `content_hash`, `bundle_hash`, refresh návod |
| [`snapshot/design-system.md`](snapshot/design-system.md) | Textový snapshot (manuál, tokeny, komponenty, ToV…) |
| [`snapshot/assets/project/`](snapshot/assets/project/) | Veřejně stažitelné `tokens.json` / `tokens.css` / `bundle.css` / `bundle.js` |
| [`snapshot/FETCH_NOTES.md`](snapshot/FETCH_NOTES.md) | Co chybí (403 assety) + ruční refresh |

## Check-before-use

1. `python3 scripts/refresh_rb_design_system.py --check`
2. Pokud skript hlásí **changed** → nech ho doběhnout bez `--check` (nebo `--force`), pak teprve čti snapshot.
3. Pokud **unchanged** → použij lokální `snapshot/`.

Agent s Firecrawl MCP: scrape `SOURCE.url` → `--from-firecrawl-json` / `--from-markdown` (viz `manifest.refresh`).

## Odliš od EDUteka UI

- **Tahle složka** = brand Red Button (Rubik, Wine `#a11834`, Red Button `#e4003a`, Permanent Marker, marketing/web/slidy).
- **`rb-edu-ui-patterns`** (RBU) = interní tool UI (Plus Jakarta, edu-red `#e9244a`, EDUteka/Universe).

Oba systémy žijí vedle sebe; neslučovat tokeny.
