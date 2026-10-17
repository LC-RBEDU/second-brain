# Task convention (v2) — Epic / Story / Task

SSOT pro work-item frontmatter. Verzováno v gitu (`ŠABLONY/obsidian-templates/`).
Vault kopie: `OBSIDIAN/00-System/Templates/task-convention.md` (Drive).

## Tři vrstvy

Pravidla parentu platí v každém projektu. Soubor zůstává ve své složce, parent id smí být z jiného projektu. Existující story bez parent se hromadně nepřepisují; navázání jde přes `update_task`.

> **Od 16. 10. 2026:** otevřená práce je soubor `type: task`. Checkbox `**ID-N**` se jako nová práce nezakládá. Osamocený kus bez story je `type: task` bez parent.

| Vrstva | `type` | Soubor | ICE | focus | Auto-Done |
|--------|--------|--------|-----|-------|-----------|
| Epic | `epic` | `.md` v `tasks/` | Brain při create zapíše 5/5/5 a `**ID-1**` | ano (téma týdne; fronta se nerozbaluje v etapě 1) | **nikdy** (jen člověk) |
| User story | `story` | `.md` v `tasks/` | ano | ano | checkboxy všechny `[x]` **nebo** GitHub `Closes ID` (bez otevřených kroků) |
| Task (list) | `task` | `.md` v `tasks/`, `parent` na story | ne (skóre 0) | ano | `Closes` souboru / `close_task` |

Plochý `type: task` bez parent je povolený v každém projektu.

## Frontmatter

### Epic

```yaml
type: epic
parent:   # vždy prázdné
# Brain při create zapíše ice_i/c/e: 5 a zástupný **ID-1**
focus:    # volitelné — téma týdne (ISO); etapa 3 rozbalí děti
deadline: # jen externí závazek
review_deadline:  # kdy se k epicu vrátím
```

### Story

```yaml
type: story
parent: "[[RBU-E23 — MVP karet externistů]]"  # povinný epic, id smí být z jiného projektu
focus:   # jen člověk, ISO týden
agent: none | assist | solo
ice_i: …
ice_c: …
ice_e: …
deadline:         # jen reálný externí závazek
review_deadline:  # kdy se k tomu vracím (vlastní měkké datum)
```

### Task (v každém projektu smí být bez parent)

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
| Kdy se k tomu vrátím? | `review_deadline` (jen když není `deadline`) |
| Na co teď? | `focus` (ISO týden, max 10 tasků nebo stories a max 5 epiců; člověk) |

`due = deadline` pokud existuje, jinak `review_deadline`. Při nastavení `deadline` se `review_deadline` vymaže. Lane **Rozhodni** = `due < today` (mimo Waiting).

**Ranking (co teď / top_priority):** hard `deadline` ≤ 7 dní (vč. overdue) striktně nahoře (uvnitř ASC); pak `rank_score` = ICE + 5 pokud `company_priorities` neprázdné. `review_deadline` neovlivní pořadí. Snapshot pole jsou pre-sorted — **nesortuj** podle `today_score`.
Volitelné `company_priorities: ["[[CP8 — …]]"]` (prázdné OK). Index: `00-System/Memory/firemni-priority-2hy-2026.md`.
## Hub page

Sekce `## Aktivní práce (Epic → Story → Task)` je text charteru. Embed `![[*.base]]` se nepřidává. Soubory `All-tasks.base` a `All-tasks-hierarchy.base` jsou smazané.

`project:` v tasku míří na **název hub souboru**, ne na alias.

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
