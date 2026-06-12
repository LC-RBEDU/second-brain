---
name: agenda-proces
description: "Tvorba a úprava firemních procesů pro RB Universe Procesní architekt: Markdown ve 02-PROJEKTY/firemni-procesy/procesy/, konvence odrážek + Mermaid kontrola. Triggers: proces, procesní mapa, architekt, připrav proces, import do universe, přeformátuj proces. ALWAYS preview before write."
---

# agenda-proces

> Draft procesu v Obsidianu → vizuální kontrola (Mermaid) → import do **RB Universe Procesní architekt** (`body_md` + *Vygenerovat kroky z Markdown těla*).

**Vault (v2):** `OBSIDIAN/` v SECOND_BRAIN — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`
**Šablona:** `00-System/Templates/proces-architect-vstup.md`
**Referenční pilot:** `02-PROJEKTY/firemni-procesy/procesy/04-prijem-uctovani-dokladu.md`
**RB Universe konvence:** repozitář `Red Button Universe` — `docs/procesy/obchodni-proces-architect-vstup.md`, `docs/architect_pilot.md`

## Kdy spouštět

- „Připrav proces …“ / „Přeformátuj proces 04 …“ / „Procesní mapa pro …“
- „Import do architekta“ / „Vstup pro Procesní architekt“
- „Uprav Mermaid u procesu …“ / „Srovnej diagram a kroky“
- Práce na hubu [[02-PROJEKTY/Firemní procesy]] s výstupem `.md` procesu

**Nespouštět** pro obecnou analýzu smluv/schůzek → `agenda-analyze`. Pro otevření tématu bez procesu → `agenda-work`.

## Principy

1. **SSOT = sekce Kroky pro Architekta** — odrážky `- **Název:**`, řádky `*Role:*`, `*Nástroj:*`.
2. **Mermaid = kontrolní vrstva** — sekce `## Diagram (kontrola — neimportuje se)`; max ~12 uzlů; swimlanes přes `subgraph`.
3. **Jeden soubor = jeden proces** — složka `02-PROJEKTY/firemni-procesy/procesy/`.
4. **Inventář** — `Procesní inventář.md` je katalog; nový soubor na něj wikilinkem, inventář při schválení pilotu doplň o odkaz (preview).
5. **Žádné pipe tabulky** v importovatelném těle.
6. **Role** — slug z katalogu Architekta (`finance`, `pm`, `hod`, `kam`, `presales`, `system`, `cfo`), ne dlouhé věty.

## Workflow

### 1. Získej zadání

- Číslo / název z inventáře, nebo nový proces (slug + název)
- Zdroje: inventář, `a02-a-propojene-procesy.md`, schůzky, Miro, existující `.md`
- Cíl: nový soubor vs. úprava existujícího v `procesy/`

### 2. Načti kontext

- `02-PROJEKTY/Firemní procesy.md` — hranice tématu
- `02-PROJEKTY/firemni-procesy/Procesní inventář.md` — příslušná sekce
- Šablona `00-System/Templates/proces-architect-vstup.md`
- Pokud existuje soubor v `procesy/` → přečti celý

### 3. Navrhni strukturu (preview)

Ukaž uživateli před zápisem:

```
═══════════════════════════════════════════════
PROCES: <název> [<slug>]
═══════════════════════════════════════════════

📍 Soubor: 02-PROJEKTY/firemni-procesy/procesy/<název-souboru>.md

📋 Kroky (N):
  1. <název> — role: finance
  2. …

🔀 Mermaid: <počet uzlů> uzlů, subgraphy: Finance, PM, …

🔗 Související: 05, 06A, …

⚠️ Otevřené: …
═══════════════════════════════════════════════
Schválit zápis? (uprav / ano)
```

### 4. Zapiš soubor (až po schválení)

- Nový: podle šablony + YAML frontmatter
- Úprava: zachovej slug; bump `verze` / `datum` v YAML
- Po zápisu: wikilink v hubu **Výstupy** nebo v inventáři u příslušné položky (navrhni diff, preview)

### 5. Sync diagram ↔ kroky

Při každé větší změně kroků **přepiš Mermaid** tak, aby odpovídal pořadí a rolím (subgraph = role). Pokud uživatel změnil jen diagram, navrhni úpravu odrážek.

### 6. Chat po zápisu

- Wikilink na soubor
- 2–3 bullets: co je hotové, co zbývá před importem do Universe
- Tabulka **Import do RB Universe**: slug, název, co zkopírovat (sekce Kroky + úvod, bez Diagram a bez YAML)

## Formát souboru (povinné sekce)

| Sekce | Povinné |
|--------|---------|
| YAML frontmatter | ano |
| `# Název` + úvod | ano |
| `## Diagram (kontrola — neimportuje se)` | ano (mermaid flowchart) |
| `## Kroky pro Architekta` | ano |
| `## Související procesy` | doporučeno |
| `## Otevřené otázky` | pokud jsou nejasnosti |
| `## Import do RB Universe` | ano (krátká tabulka slug/název/kroky) |

## Pojmenování souboru

`NN-<slug>.md` nebo `<slug>.md` — např. `04-prijem-uctovani-dokladu.md`. Slug v YAML = slug v Architektovi (bez diakritiky, pomlčky).

## Role — rychlá mapa (Architekt)

| Slug | Kdy použít |
|------|------------|
| `finance` | Dominik / Martina — doklady, faktury, banka |
| `pm` | Project manager — zařazení k projektu, schválení |
| `hod` | Head of Delivery — handover |
| `kam` | Obchod / KAM |
| `presales` | Nabídky, rozpočty |
| `system` | Automatizace, integrace |
| `cfo` | Strategický reporting, agregace |

Neznámá role → nech text v `*Role:*`, upozorni že v Architektovi může spadnout do „nerozpoznaná“.

## RB Universe Procesní architekt (oboustranně)

**Před zápisem nového/upraveného procesu:**
1. Přes RB Universe MCP (`rb-universe` / `mcp.redbuttonedu.cz`) ověř **aktuální import formát** Architekta — nepoužívej zastaralou šablonu slepě.
2. Zkontroluj, zda podobný proces v Architektovi už neexistuje (kolize názvů/slug).

**Po schválení draftu:**
- Nabídn import do Universe (Procesní architekt UI).
- Odkaz na task **RBU9 — Procesní architect** pro stav platformy.

**Čtení (pro ostatní skills):** `agenda-work` / `agenda-analyze` při procesním tématu kontrolují Architekta přes MCP — nenavrhuj postup kolidující s existujícím procesem.

## Anti-patterns

- BPMN / Excalidraw jako zdroj pravdy (jen export do MD, ne paralelní SSOT)
- Duplicitní kroky v Mermaid i v odrážkách s různým pořadím
- Import celého souboru včetně YAML a Diagram do `body_md`
- Tabulky `|` v sekci kroků
