# Bases — hierarchy views

SSOT: `ŠABLONY/obsidian-templates/All-tasks-hierarchy.base`  
Vault: `OBSIDIAN/00-System/Bases/All-tasks-hierarchy.base` (Drive)

## Proč ne `All-tasks.base`

Flat base má root filtr `type == "task"` — **stories a epicy se neukážou**. Hierarchy projekty (`hierarchy: true`) embedují views z tohoto souboru.

## Views

| View | Účel |
|------|------|
| `ProjectEpics` | Tabulka otevřených epiců |
| `ProjectStoriesKanban` | Kanban stories (Doing / Next / Waiting / Backlog) |
| `ProjectStoriesByParent` | Stories seskupené podle `parent` (epic) |
| `ProjectStandaloneStories` | Stories bez `parent` |
| `ProjectStoriesFocus` | Max 5 stories ve fokusu týdne |
| `ProjectRecentDone` | Nedávno hotové stories |

## Hub embed (RB Universe)

```markdown
![[All-tasks-hierarchy.base#ProjectStoriesKanban]]
![[All-tasks-hierarchy.base#ProjectEpics]]
![[All-tasks-hierarchy.base#ProjectStoriesByParent]]
```

Viz `RB Universe development.md` — sekce **Aktivní práce (Epic → Story → Task)**.

## Nový hierarchy projekt

1. Hub frontmatter: `hierarchy: true`
2. Zkopíruj `All-tasks-hierarchy.base` do `00-System/Bases/` (nebo symlink — stejný globální soubor pro všechny hierarchy projekty)
3. Embed views s `project == this.file.asLink()` fungují z libovolného hub charteru

Epicy **ne** do fokusu / TOP — jen v `ProjectEpics` a `agent-context.json` → `open_epics[]`.
