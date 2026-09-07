---
name: agenda-lessons
description: "Capture atomická lessons learned (assist): návrh ze session → preview → schválení → zápis do 00-System/Lessons/. Triggers: ulož lessons, co jsme se naučili, lesson z téhle session, schval lessons. ALWAYS preview before write. Max 1–5 návrhů."
---

# agenda-lessons

> Atomická poučení pro budoucí agenta. Ty schvaluješ — agent jen připraví.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

| Cesta | Účel |
|-------|------|
| `00-System/Lessons/` | Active lessons (`LL-YYYY-MM-DD-<slug>.md`) |
| `00-System/Lessons-Pending/` | Batch návrhů ke schválení |
| Šablona | `00-System/Templates/lesson-template.md` |

## Kdy spouštět

- Explicitně: „ulož lessons“, „co jsme se naučili“, „lesson z téhle session“, „schval lessons“
- Po nabídce na konci relevantní práce (viz Adoption níže / `.cursor/rules/lessons-learned.mdc`)

## Domény

`process` | `project` | `tech` | `collaboration` | `other`

## Workflow — návrh (assist)

1. Z session vyber **1–5** kandidátů (ne 20). Prázdné = „Nic k uložení.“
2. Preview v chatu (povinný formát):

```
**Lessons? (assist)** — odpověz `ulož 1,3` / `uprav 2: …` / `drop`

1. `[tech]` krátký title → příště: …
2. `[process]` …
```

3. **Bez odpovědi nic nezapisuj.**
4. Po `ulož …` / `schval`:
   - Zapiš Active lesson(s) do `00-System/Lessons/LL-YYYY-MM-DD-<slugify-title>.md`
   - Frontmatter dle šablony (`status: Active`, `agent_recall: true`, …)
   - Tělo: Situace / Poučení / Důsledek pro agenta (max ~25 řádků)
   - Volitelně: krátký odkaz v `00-System/Agent-Log/YYYY-MM.md`
5. Pending batch (pokud user chce odložit): `00-System/Lessons-Pending/YYYY-MM-DD-HHMM-batch.md`

## Workflow — schval pending

1. Načti `00-System/Lessons-Pending/*.md`
2. Preview kandidátů
3. Po OK → Active soubory + smaž/archivuj pending batch

## Pravidla

- Jedno lesson = jedno zjištění
- Žádné přepisy celých chatů
- Stabilizované pravidlo → nabídni povýšení do Memory/bootstrap (zápis až po OK)
- Spam: max 1 nabídka na session, pokud user už dropnul

## Adoption (povinná nabídka)

Na konci turnu nabídni 1–3 kandidáty (formát výše), když nastalo:

- oprava bugu / incident / root cause
- korekce od uživatele („tohle ne, dělej X“)
- architektonické rozhodnutí s trvalým dopadem
- změna konvence / skillu / n8n / Bases / triage

## Kam poučení patří — Lessons vs. rules

**Nejdřív se zeptej, kdy má zjištění platit.** Podle toho se rozhoduje umístění, ne podle toho, jak
zajímavě znělo.

| Kdy platí | Kam | Proč |
|---|---|---|
| Vázané na projekt, nástroj, doménu | `00-System/Lessons/` | Recall je cílený — vytáhne se, až se na tom dělá |
| **Vždycky, napříč vším** (konvence, formát, styl) | `.cursor/rules/*.mdc` | Rules se načítají při každé session, lessons ne |
| Stabilní fakt o firmě / vaultu | `00-System/Memory/` nebo bootstrap rule | Není to poučení z chyby, ale kontext |

**U konvence je zápis do rules výchozí volba, ne bonus.** Konvence uložená jen jako lesson je
prakticky mrtvá — vytáhne ji leda `agenda-work` nad tím správným projektem, takže při běžné práci
podle ní nikdo nepojede. Když pravidlo v rules už existuje a chyba ukázala díru, **zpřísni ho**
(uprav sekci, přidej sebekontrolu) a lesson napiš jako záznam, proč to pravidlo tak vypadá.

Zápis do `.cursor/rules/` schvaluje uživatel stejně jako lesson — nabídni obojí naráz.

## Recall (pro jiné skills)

Active lessons s `agent_recall: true` se propisují do **`00-System/agent-context.json` → `lessons[]`**
(max 30, nejnovější první). Každá položka nese `title`, `domain`, `projects`, `topics`, `path`
a `takeaway` — první „Příště **udělej:**" větu. Snapshot je tedy index: podle `projects` / `topics`
poznáš, co je relevantní, a teprve pak otevřeš soubor.

Při `agenda-work`: po Work-Context vyber max **3** lessons ze `lessons[]`, kde `projects` obsahuje hub
projektu NEBO `topics` overlap s tématem práce. Stručně cituj v briefingu (`takeaway` stačí).
