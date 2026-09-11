---
name: agenda-lessons
description: "Capture lessons = guardy proti třídám chyb (assist): návrh ze session → preview → schválení → zápis do 00-System/Lessons/. Triggers: ulož lessons, co jsme se naučili, lesson z téhle session, schval lessons. ALWAYS preview before write. Max 1–5 návrhů. Jen při škodě nebo opakování."
---

# agenda-lessons

> Guard proti třídě chyby — ne záznam incidentu. Ty schvaluješ — agent jen připraví.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

| Cesta | Účel |
|-------|------|
| `00-System/Lessons/` | Active guardy (`LL-YYYY-MM-DD-<slug>.md`) |
| `00-System/Lessons-Pending/` | Batch návrhů ke schválení |
| Šablona | `00-System/Templates/lesson-template.md` |

## Kdy spouštět

- Explicitně: „ulož lessons“, „co jsme se naučili“, „lesson z téhle session“, „schval lessons“
- Po nabídce na konci relevantní práce (viz Adoption / `.cursor/rules/lessons-learned.mdc`)

## Domény a severity

Domény: `process` | `project` | `tech` | `collaboration` | `other`

`severity`: `data` (poškození/ztráta dat) · `decision` (špatné rozhodnutí) · `trust` (chyba směrem ven) · `efficiency` (jen ztráta času — **jen při opakování**)

## Workflow — návrh (assist)

1. Z session vyber **1–5** kandidátů, které projdou **sítem škody** (níže). Prázdné = „Nic k uložení.“
2. **Tři destinace (první krok u každého kandidáta):**

| Kdy platí | Kam | Lesson? |
|---|---|---|
| Vždycky, napříč vším (konvence) | `.cursor/rules/*.mdc` | **Nevzniká** — při povýšení existující → `Superseded` ve stejném tahu |
| Fakt o nástroji / API | projektový materiál / design doc | **Nevzniká** (nebo `Superseded` po přesunu) |
| Třída chyby s reálnou škodou | `00-System/Lessons/` | Ano — guard |

3. **Existuje Active guard se stejným triggerem/škodou?** (povinné, před preview)
   Projdi `lessons[]` v `agent-context.json`.
   - **Ano** → nabídni `uprav LL-…` = přidat řádek do `## Incidenty`, ne nový soubor.
   - **Zpřesňuje starou** → nový guard + stará na `Superseded` s `superseded_by`.
   - **Jen jinými slovy totéž** → nezakládej.
   - **Nová třída** (trigger ani škoda se nepřekrývají) → nový guard + **rozhodnutí o placement** (situační řádek do always-on / scoped rule / skill).

4. Preview v chatu:

```
**Lessons? (assist)** — odpověz `ulož 1,3` / `uprav 2: …` / `drop`

1. `[tech|data]` krátký title → guard: …
2. `[process|decision]` …

Do incidentů: LL-2026-09-11-… (bod 2)
Nahrazuje: LL-… → Superseded
Placement: always-on řádek / slack-inbox-triage / …
```

5. **Bez odpovědi nic nezapisuj.**
6. Po `ulož …` / `schval`:
   - Active soubor dle šablony (Trigger / Škoda / Guard / Incidenty)
   - Frontmatter: `status: Active`, `agent_recall: true`, `severity`, …
   - Při povýšení do rules: uprav rule **a** lesson → `Superseded` ve stejném tahu
   - Pending batch: `00-System/Lessons-Pending/YYYY-MM-DD-HHMM-batch.md`

## Workflow — schval pending

1. Načti `00-System/Lessons-Pending/*.md`
2. Preview kandidátů
3. Po OK → Active soubory + smaž/archivuj pending batch

## Síto škody (Adoption)

Nabídni kandidáty **jen** když:

- zapsaná špatná data / ztracená práce / rozhodnutí na špatném podkladu / trapas ven, **nebo**
- stejná chyba podruhé

**Neprochází:** „zjistil jsem jak funguje X", drobná editace, první výskyt čisté `efficiency`.

Spam: max 1 nabídka na session po `drop`.

## Vyřazení

| Situace | Status | `superseded_by` |
|---|---|---|
| Novější guard | `Superseded` | `[[LL-…]]` |
| Povýšeno do rules | `Superseded` | `.cursor/rules/<soubor>.mdc` |
| Riziko zmizelo | `Archived` | — |

Soubor **nemaž**. Vyřazení navrhni při práci, ne plošně.

## Sada je otevřená

~počet Active = historie tříd chyb, ne uzavřený číselník. Nová třída OK, když síto projde a nepřekrývá se. Nepřecpávej nesouvisející rizika do jednoho guardu.

## Index (pro jiné skills)

`agent-context.json` → `lessons[]` (Active + `agent_recall`, bez limitu). Index pro „co jsme se naučili" / `agenda-work` (max 3 matching). Auto-výpis do session hlavičky **ne**.
