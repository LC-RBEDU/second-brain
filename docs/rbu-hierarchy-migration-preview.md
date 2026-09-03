# RBU hierarchy migration preview (2026-09-03)

Dry-run plán. Zápis jen po `--apply` a tvém `ano`.

## Strategie

- **RBU23, RBU7, RBU27** → `type: epic` (stejné ID)
- Ostatní otevřené RBU → `type: story` + `parent:` dle skupiny
- Hub → `hierarchy: true`
- Epic checkboxy se zatím nerozřezávají na nová story ID (další iterace)

## Diff

| ID | Title | type | parent | poznámka |
|----|-------|------|--------|----------|
| RBU16 | Tabulka alokací PM dle mentální zátěže | `task` → `story` | [[RBU7 — Project management feature (Pavel Kroupa MVP)]] | parent → RBU7 |
| RBU18 | Vytěžování kontaktů z e-mailů do Pipedrive — osoby, čísla, pozice | `task` → `story` | [[RBU23 — MVP karet externistů v RB Universe (kategorizace, NDA stav, brand kategorie)]] | parent → RBU23 |
| RBU21 | Enrichment profilu lidí: účast na akcích + LinkedIn data | `task` → `story` | [[RBU23 — MVP karet externistů v RB Universe (kategorizace, NDA stav, brand kategorie)]] | parent → RBU23 |
| RBU23 | MVP karet externistů v RB Universe (kategorizace, NDA stav, brand kategorie) | `task` → `epic` | — | Lidé a kontakty — karty externistů / NDA / brand |
| RBU27 | Vytěžování nahrávek → entity (firma / člověk / deal / úkol / zápis) | `task` → `epic` | — | Těžba entit z nahrávek a integrace |
| RBU44 | Zadávání nových dealů přímo do Universe (Pavel + Saša) | `task` → `story` | [[RBU7 — Project management feature (Pavel Kroupa MVP)]] | parent → RBU7 |
| RBU49 | Nahradit tabulku SW licencí funkcionalitou v Universe | `task` → `story` | [[RBU27 — Vytěžování nahrávek → entity (firma - člověk - deal - úkol - zápis)]] | parent → RBU27 |
| RBU57 | Zkontrolovat sledování LinkedIn followers (lidé i firemní profily) | `task` → `story` | [[RBU23 — MVP karet externistů v RB Universe (kategorizace, NDA stav, brand kategorie)]] | parent → RBU23 |
| RBU58 | Cashflow graf v Universe — dotáhnout část z planned expenses | `task` → `story` | — | standalone story |
| RBU6 | Signi integrace s RB Universe | `task` → `story` | [[RBU27 — Vytěžování nahrávek → entity (firma - člověk - deal - úkol - zápis)]] | parent → RBU27 |
| RBU60 | Upgrade Traefik proxy v Coolify | `task` → `story` | — | standalone story |
| RBU61 | Ownership kontaktů v Universe (ne jen Pipedrive) | `task` → `story` | [[RBU23 — MVP karet externistů v RB Universe (kategorizace, NDA stav, brand kategorie)]] | parent → RBU23 |
| RBU62 | MCP Procesní architekt + návod pro PM | `task` → `story` | — | standalone story |
| RBU63 | SignatureSatori — centrální e-mailové podpisy v RB Universe | `task` → `story` | — | standalone story |
| RBU7 | Project management feature (Pavel Kroupa MVP) | `task` → `epic` | — | Delivery / PM feature v Universe |

## Skupiny

1. **Lidé a kontakty** — epic RBU23 ← RBU61, RBU21, RBU18, RBU57
2. **Delivery / PM** — epic RBU7 ← RBU16, RBU44
3. **Těžba / integrace** — epic RBU27 ← RBU6, RBU49
4. **Finance pohled** — story RBU58 (standalone)
5. **Procesní architekt** — story RBU62 (standalone)
6. **Platforma** — story RBU60 (standalone)
