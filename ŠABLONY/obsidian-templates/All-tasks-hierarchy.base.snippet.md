# Bases — hierarchy views (RBU)

`OBSIDIAN/00-System/Bases/All-tasks.base` je v Drive (git-ignored). Po migraci přidej view / filtr:

## Doporučené view „RBU hierarchy“

- Filter: `slug == "rb-universe-development"` AND `status` not in Done/Cancelled
- Group by: `type` (epic / story / task) **nebo** `parent`
- Columns: `id`, `title`, `status`, `type`, `parent`, `focus`, `priority_score`, `deadline`

## Hub embed

V `RB Universe development.md` (vedle stávajícího All-tasks embedu):

```markdown
![[All-tasks.base#RBU hierarchy]]
```

Epicy se v TOP / fokus frontách neobjevují — jen v tomto groupBy pohledu a v `agent-context.json` → `open_epics[]`.
