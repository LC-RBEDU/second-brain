# Task convention (v2) — Epic / Story / Task

SSOT pro work-item frontmatter. Verzováno v gitu (`ŠABLONY/obsidian-templates/`).
Vault kopie: `OBSIDIAN/00-System/Templates/task-convention.md` (Drive).

## Tři vrstvy (opt-in)

Zapnuto u **`rb-universe-development`**, **`vibe-coding`**, **`firemni-procesy`**, **`finance`**.
Jinde: hub `hierarchy: true` nebo presence alespoň jednoho `type: epic` v `tasks/`.

> **Past:** v hierarchickém projektu se `type: task` neukáže **nikde** na hub page — flat `All-tasks.base`
> má root filtr `type == "task"`, hierarchy views filtrují `story` / `epic`. Osamocený kus = `story` bez `parent`.

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

## Hub page

Hierarchický hub embeduje `All-tasks-hierarchy.base` (**ne** flat `All-tasks.base`, a to i u `ProjectRecentDone`):

```markdown
## Aktivní práce (Epic → Story → Task)

![[All-tasks-hierarchy.base#ProjectStoriesFocus]]
![[All-tasks-hierarchy.base#ProjectEpics]]
![[All-tasks-hierarchy.base#ProjectStoriesKanban]]
![[All-tasks-hierarchy.base#ProjectStoriesByParent]]
![[All-tasks-hierarchy.base#ProjectStandaloneStories]]
```

Views filtrují `project == this.file.asLink()` — `project:` v tasku proto musí mířit na **název hub souboru**,
ne na alias. `[[Vibe coding]]` místo `[[AI & Vibe coding]]` znamená prázdný view.

Sekce je ve whitelistu validátoru (`ALLOWED_EXTRA_HUB_SECTIONS` v `scripts/vault_reference.py`).

## Přesun tasku mezi projekty

Nové ID v cílovém projektu, původní soubor `status: Cancelled` s ukazatelem na nový.
Smazané ID by `next_task_id.py` přes `max+1` přidělil znovu někomu jinému.

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
