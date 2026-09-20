# Task convention (v2) — Epic / Story / Task

SSOT pro work-item frontmatter. Verzováno v gitu (`ŠABLONY/obsidian-templates/`).
Vault kopie: `OBSIDIAN/00-System/Templates/task-convention.md` (Drive).

## Tři vrstvy (opt-in)

Zapnuto u **`rb-universe-development`**, **`it-ai-data`**, **`firemni-procesy`**, **`finance`**. (`vibe-coding` paused → merge do `it-ai-data`, SB10.)
Jinde: hub `hierarchy: true` nebo presence alespoň jednoho `type: epic` v `tasks/`.

> **Past (opraveno 20. 9. 2026):** flat `All-tasks.base` má root filtr `type != "epic"`
> (dřív `type == "task"`, což schovávalo všechny stories). V hierarchickém projektu
> stále platí: osamocený kus = `story` bez `parent`, ne `type: task` — hub views
> filtrují `story` / `epic`.

| Vrstva | `type` | Soubor | ICE | focus | Auto-Done |
|--------|--------|--------|-----|-------|-----------|
| Epic | `epic` | `.md` v `tasks/` | ne | ano (téma týdne; fronta se nerozbaluje v etapě 1) | **nikdy** (jen člověk) |
| User story | `story` | `.md` v `tasks/` | ano | ano | checkboxy všechny `[x]` **nebo** GitHub `Closes ID` (bez otevřených kroků) |
| Task (list) | — | checkbox `- [ ] **ID-N**` v `## Operativní kroky` story | — | — | GitHub `Closes ID-N` / ruční odškrtnutí |

Mimo hierarchii zůstává `type: task` (legacy flat).

## Frontmatter

### Epic

```yaml
type: epic
parent:   # vždy prázdné / null
# ice_*: nevyplňovat (nesoutěží o fokus skóre)
focus:    # volitelné — téma týdne (ISO); etapa 3 rozbalí děti
deadline: # jen externí závazek
review_deadline:  # kdy se k epicu vrátím
```

### Story

```yaml
type: story
parent: "[[RBU-E23 — MVP karet externistů]]"  # wikilink na epic; null = standalone
focus:   # jen člověk, ISO týden
agent: none | assist | solo
ice_i: …
ice_c: …
ice_e: …
deadline:         # jen reálný externí závazek
review_deadline:  # kdy se k tomu vracím (vlastní měkké datum)
```

### Flat task (legacy / non-hierarchy slug)

```yaml
type: task
deadline:         # jen reálný externí závazek
review_deadline:  # kdy se k tomu vracím
```

## Osy priority (v2.1)

| Otázka | Pole |
|---|---|
| Udělám to vůbec? | `status` |
| Externí závazek? | `deadline` |
| Kdy se k tomu vrátím? | `review_deadline` |
| Na co teď? | `focus` (ISO týden, max 5; člověk) |

`due = min(deadline, review_deadline)`. Lane **Rozhodni** = `due < today` (mimo Waiting).
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

- Prefix projektu (`RBU`, …) + `python3 scripts/next_task_id.py <slug> --type epic|story|task`.
- **Úroveň je součástí ID:** `RBU-E69` epic, `RBU-S70` story, `RBU-T12` task.
- **Jeden čítač na projekt, ne per úroveň** — povýšení story na epic mění písmeno, číslo zůstává, takže se žádné neuvolní k recyklaci.
- Listové kroky: `**RBU-S70-1**`, `**RBU-S70-2**` v body story — číslo kroku je vždy za poslední pomlčkou.
- Ploché projekty a archiv mají dál `<PREFIX><N>` (`S12`, `AF14`); parsery zvládají obojí.

## GitHub → vault (jen RBU)

Commity / merged PR do větve **`dev`** v `RedButtonEDU/RB-Universe`:

- `Closes RBU-S70-1` — odškrtne checkbox
- `Closes RBU-S70` — story `Done` jen když nezůstane otevřený krok

Cron: `lifecycle_github_rbu_closes.py`. Agent v Universe musí ID zapsat — viz `.cursor/rules/rbu-commit-closes.mdc` v repu RB-Universe (zdroj: `ŠABLONY/cursor-rules/`).

## Chat

Vždy **`ID — title`**. U kroku: parent story + text checkboxu (`RBU-S70-1` pod **RBU-S70 — …**).
