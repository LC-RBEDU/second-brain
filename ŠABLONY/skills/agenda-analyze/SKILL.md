---
name: agenda-analyze
description: "Analyzuje materiály (URL, vault) k tématu/úkolu. Výstup: strukturovaný .md ve 02-PROJEKTY/<slug>/ — podle typu dokumentu, bullet-heavy, diagramy/tabulky kde pomůžou. Triggers: analyzuj, rozbor materiálů, deep dive, projdi k úkolu. Zapisuje rovnou; chat = wikilink + 2–3 bullets."
---

# agenda-analyze

> Paralelní skill. Rozbor materiálů → **stručný, strukturovaný** `.md` ve výstupech — **ne** jedna fixní šablona, ale **tvar podle typu dokumentu**.

**Vault (v2):** `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`
**Referenční příručka tvarů výstupu:** `00-System/Templates/analyze-output-guide.md` (varianty, ne kopírovat 1:1)
**V2 změna:** analýza je **material soubor** se YAML frontmatter `type: material` v `02-PROJEKTY/<slug>/materials/` (project-specific) nebo `05-RESOURCES/<kategorie>/` (cross-project). M:N linkování přes `projects:` array. Konvence: `00-System/Templates/material-template.md`.

## Kdy spouštět

- „Analyzuj …“ / „Rozbor materiálů …“ / „Deep dive …“
- „Projdi k úkolu F17“ / „K PD4 zpracuj dokumenty“
- URL, soubor, nebo cesta ve vaultu u konkrétního tématu

## Principy výstupu (vždy)

1. **Ne zeď textu** — max ~1–2 obrazovky v Obsidianu; raději kratší než delší.
2. **TL;DR nahoře** — 3–5 bulletů: co to je, proč to řešíme, hlavní závěr.
3. **Struktura podle typu materiálu** — viz tabulka níže; sekce bez obsahu **vynechat**.
4. **Bullets jako default** — pod bulletem max 1–2 věty vysvětlení, ne odstavec.
5. **Vizuál kde pomůže** — mermaid (flow, timeline, mindmap), tabulka (srovnání, čísla), jednoduchý ASCII jen pokud mermaid nestačí.
6. **Akční závěr** — sekce **Co s tím** (konkrétní kroky / návrhy do hubu), pak **Otevřené otázky**.
7. **Žádná fixní šablona** — vždy zvol tvar podle toho, *co* analyzuješ.

**Filtr pro Action items:** Vault je single-user (Lukáš). Action items extrahuj **pouze pro Lukáše**. Cizí akce patří do "Kontext" / "Otevřené otázky" sekce výstupu, ne do tasků. (Hraniční: pokud Lukáš čeká na cizí výstup → status Waiting + waitUntil.)

## Workflow

### 1. Urči projekt + typ materiálu

- Projekt: slug / hub / ID úkolu → **Slug** z hubu = složka výstupů
- Typ materiálu (vyber jeden primární; u mixu uveď v YAML `typ: smlouva+url`):

| Typ | Signály |
|-----|---------|
| `clanek` | URL, blog, výzkum, newsletter |
| `smlouva` | PDF smlouva, VOP, Ninjabot docs |
| `schuzka` | Sembly, transkript, zápis z hovoru |
| `technicky` | API, architektura, bug report, spec |
| `data` | Tabulka, čísla, report, dashboard export |
| `slack` | Krátký capture, thread, odkazy v INBOX |
| `mix` | Víc souborů / heterogenní balík |

### 2. Načti materiály + kontext úkolu

- Zdroje: URL fetch, vault cesty, přílohy (parsuj `## Přílohy` z INBOX `.md` — Drive linky; sidecar `type: attachment` s `## Extrahovaný text`)
- Hub charter + **`sources:` / `notebooklm:` / `workspace:`** — aktivně použij deklarované zdroje
- **MCP routing (povinný):** `python3 scripts/build_sources_routing.py --check` → regeneruj pokud stale; načti `sources-routing.json`; pro každý hub `sources:` tag volej MCP/CLI dle routes
- Prohledej `05-RESOURCES/` podle `topics:` relevantních k projektu (`.cursor/rules/resources-para.mdc`)
- U procesních témat: RB Universe MCP — existující procesy v Architektovi
- `00-System/Memory/about-me.md` pokud ještě v session ne

### 3. Zapiš analýzu (v2)

**Soubor:**
- Project-specific: `02-PROJEKTY/<slug>/materials/YYYY-MM-DD-analyza-<tema>.md`
- Cross-project: `05-RESOURCES/<kategorie>/YYYY-MM-DD-analyza-<tema>.md`

**YAML hlavička (v2 material schema):**

```yaml
---
type: material
material_kind: clanek          # clanek | smlouva | schuzka | technicky | data | slack | mix | gdoc
url: ""                        # pokud je externí URL primární
projects:
  - "[[<slug>]]"               # bare alias, M:N
areas:
  - "[[03-AREAS/<oblast>]]"    # path-style, area mimo PROJEKTY
title: "Analýza — <téma>"
created: YYYY-MM-DD
zdroje:
  - "[popisek](https://...)"
  - "[[07-ARCHIV/...]]"
---
```

V task `.md` frontmatteru je material referencován v `materials:` array (bare alias).

**Tělo — podle `typ` (vyber odpovídající blok; ostatní vynech):**

#### `clanek` / výzkum

- `## TL;DR`
- `## Klíčové body` (bullets, každý = tvrzení + 1 věta proč záleží)
- `## Relevance pro [[02-PROJEKTY/...]]` (bullets: dopad na projekt / úkol)
- Volitelně `## Srovnání / kontext` — **tabulka** nebo mermaid mindmap
- `## Co s tím` → `## Otevřené otázky`

#### `smlouva` / PDF

- `## TL;DR`
- `## Předmět a strany` (bullets)
- `## Co platíme / co dostáváme` — tabulka sloupce: Položka | Hodnota | Poznámka
- `## Rizika a výhrady` (bullets, závažnost: vysoká/střední/nízká)
- `## Termíny a výpověď` (bullets nebo timeline mermaid)
- `## Co s tím` → `## Otevřené otázky`

#### `schuzka` / transkript

- `## TL;DR`
- `## Kontext` (2–3 bullets)
- `## Rozhodnutí` (bullets)
- `## Akční body` — tabulka: Kdo | Co | Do kdy (pokud známo). Slouží jen pro záznam meetingu — **task soubory v `02-PROJEKTY/.../tasks/` se vytváří jen pro řádky, kde "Kdo" = Lukáš** (případně `Waiting` pokud Lukáš čeká na cizí dodání).
- `## Co patří do hubu` (návrhy úkolů / materiálů — bullets, ne automatický zápis; pouze Lukášovy akce, viz Filtr pro Action items výše)
- Volitelně mermaid `flowchart` pro proces, o kterém se mluvilo
- `## Co s tím` → `## Otevřené otázky`

#### `technicky`

- `## TL;DR`
- `## Problém / cíl` (bullets)
- `## Zjištění` (bullets + pod-bullets pro důkazy)
- `## Možnosti` — tabulka: Varianta | Pro | Proti | Effort
- `## Doporučený postup` (číslované krátké kroky nebo mermaid flowchart)
- `## Co s tím` → `## Otevřené otázky`

#### `data` / čísla

- `## TL;DR`
- `## Čísla na první pohled` — tabulka nebo bullets s jednotkami
- `## Trendy / vzory` (bullets)
- Volitelně jednoduchý mermaid nebo popis grafu („line chart: …“ — data v tabulce pod tím)
- `## Co to znamená pro projekt` (bullets)
- `## Co s tím` → `## Otevřené otázky`

#### `slack` / krátký vstup

- `## TL;DR`
- `## Co přišlo` (bullets)
- `## Návrh zařazení` (téma, úkol, backlog — bullets)
- `## Co s tím` → `## Otevřené otázky`

#### `mix` (víc zdrojů)

- `## TL;DR`
- `## Po zdrojích` — podnadpis per zdroj, u každého max 5 bullets
- `## Společný obraz` (bullets nebo mermaid)
- `## Co s tím` → `## Otevřené otázky`

### Vizuály — kdy použít

| Situace | Použij |
|---------|--------|
| Proces / workflow | mermaid `flowchart TD` |
| Časová osa | mermaid `timeline` nebo tabulka Datum \| Událost |
| Srovnání 3+ variant | tabulka |
| Vztahy témat | mermaid `mindmap` |
| Podíly / struktura | tabulka čísel; pie jen pokud máš konkrétní % |

Mermaid vždy v fenced bloku ` ```mermaid `. Udržuj diagramy **malé** (≤ 12 uzlů).

### 4. Propoj hub a tasky

- Hub `02-PROJEKTY/<HubName>.md` → `## Materiály` Bases embed (`![[All-materials.base#ProjectMaterials]]`) automaticky zachytí material soubor s `projects: [[<slug>]]`
- U dotčeného tasku: patch frontmatter `materials:` array — přidat `[[<material-filename-bez-pripony>]]`
- **updated** v hubu (frontmatter) nebo task = dnes

### 5. Chat (max 5 řádků)

```
Uloženo: [[2026-05-21-analyza-nrb-zaruka|NRB záruka — rozbor]] (material → finance)

• material_kind: smlouva — hlavní riziko: …
• doporučení: …
• otevřeno: …
```

**Celou analýzu do chatu nedávej.**

## Wikilinks & tone

- Projekty / úkoly: viz `00-System/Templates/wikilink-convention.md`
- Externí URL: `[text](https://…)`
- Tone: `00-System/Memory/anti-ai-writing-tools.md`
