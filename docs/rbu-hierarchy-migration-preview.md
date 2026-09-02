# RBU hierarchy migration preview (2026-09-02)

Dry-run plán. Zápis jen po `--apply` a tvém `ano`.

## Strategie

- **RBU23, RBU7, RBU27** → `type: epic` (stejné ID)
- Ostatní otevřené RBU → `type: story` + `parent:` dle skupiny
- Hub → `hierarchy: true`
- Epic checkboxy se zatím nerozřezávají na nová story ID (další iterace)

## Diff

| ID | Title | type | parent | poznámka |
|----|-------|------|--------|----------|
| RBU16 | (file not in this environment) | `task` → `story` | [[RBU7]] | parent → RBU7 |
| RBU18 | (file not in this environment) | `task` → `story` | [[RBU23]] | parent → RBU23 |
| RBU21 | (file not in this environment) | `task` → `story` | [[RBU23]] | parent → RBU23 |
| RBU23 | Lidé a kontakty — karty externistů / NDA / brand | `task` → `epic` | — | Lidé a kontakty — karty externistů / NDA / brand |
| RBU27 | Těžba entit z nahrávek a integrace | `task` → `epic` | — | Těžba entit z nahrávek a integrace |
| RBU44 | (file not in this environment) | `task` → `story` | [[RBU7]] | parent → RBU7 |
| RBU49 | (file not in this environment) | `task` → `story` | [[RBU27]] | parent → RBU27 |
| RBU57 | (file not in this environment) | `task` → `story` | [[RBU23]] | parent → RBU23 |
| RBU58 | (file not in this environment) | `task` → `story` | — | standalone story |
| RBU6 | (file not in this environment) | `task` → `story` | [[RBU27]] | parent → RBU27 |
| RBU60 | (file not in this environment) | `task` → `story` | — | standalone story |
| RBU61 | (file not in this environment) | `task` → `story` | [[RBU23]] | parent → RBU23 |
| RBU62 | (file not in this environment) | `task` → `story` | — | standalone story |
| RBU7 | Delivery / PM feature v Universe | `task` → `epic` | — | Delivery / PM feature v Universe |

## Skupiny

1. **Lidé a kontakty** — epic RBU23 ← RBU61, RBU21, RBU18, RBU57
2. **Delivery / PM** — epic RBU7 ← RBU16, RBU44
3. **Těžba / integrace** — epic RBU27 ← RBU6, RBU49
4. **Finance pohled** — story RBU58 (standalone)
5. **Procesní architekt** — story RBU62 (standalone)
6. **Platforma** — story RBU60 (standalone)
