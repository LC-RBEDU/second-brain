# Task convention (v2) — Epic / Story / Task

SSOT pro work-item frontmatter. Verzováno v gitu (`ŠABLONY/obsidian-templates/`).
Vault kopie: `OBSIDIAN/00-System/Templates/task-convention.md` (Drive).

## Tři vrstvy (opt-in)

Zapnuto vždy u **`rb-universe-development`**. Jinde: hub `hierarchy: true` nebo presence alespoň jednoho `type: epic` v `tasks/`.

| Vrstva | `type` | Soubor | ICE / focus | Auto-Done |
|--------|--------|--------|-------------|-----------|
| Epic | `epic` | `.md` v `tasks/` | ne | **nikdy** (jen člověk) |
| User story | `story` | `.md` v `tasks/` | ano | checkboxy všechny `[x]` **nebo** GitHub `Closes ID` (bez otevřených kroků) |
| Task (list) | — | checkbox `- [ ] **ID-N**` v `## Operativní kroky` story | — | GitHub `Closes ID-N` / ruční odškrtnutí |

Mimo hierarchii zůstává `type: task` (legacy flat).

## Frontmatter

### Epic

```yaml
type: epic
parent:   # vždy prázdné / null
# ice_*: nevyplňovat (nesoutěží o fokus)
# focus: nevyplňovat
```

### Story

```yaml
type: story
parent: "[[RBU23 — MVP karet externistů]]"  # wikilink na epic; null = standalone
focus:   # jen člověk, ISO týden
agent: none | assist | solo
ice_i: …
ice_c: …
ice_e: …
```

### Flat task (legacy / non-hierarchy slug)

```yaml
type: task
```

## ID

- Prefix projektu (`RBU`, …) + `python3 scripts/next_task_id.py <slug>`.
- Epic i story berou další volné `RBU<N>` — **žádné** `RBU-E`.
- Listové kroky: `**RBU62-1**`, `**RBU62-2**` v body story.

## GitHub → vault (jen RBU)

Commity / merged PR do větve **`dev`** v `RedButtonEDU/RB-Universe`:

- `Closes RBU62-1` — odškrtne checkbox
- `Closes RBU62` — story `Done` jen když nezůstane otevřený krok

Cron: `lifecycle_github_rbu_closes.py`. Agent v Universe musí ID zapsat — viz `.cursor/rules/rbu-commit-closes.mdc` v repu RB-Universe (zdroj: `ŠABLONY/cursor-rules/`).

## Chat

Vždy **`ID — title`**. U kroku: parent story + text checkboxu (`RBU62-1` pod **RBU62 — …**).
