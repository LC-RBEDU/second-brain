---
name: agenda-cursor-inbox
description: "Uloží task, popis nebo plán z Cursor konverzace do MrLUC Second Brain: .md soubor v OBSIDIAN/01-INBOX/daily/ s odkazem na chat. Triggers: ulož do Second Brain, ulož do SB, zapiš do inboxu, ulož task/plán/popis do Obsidianu, capture konverzace, second brain inbox. ALWAYS preview before write."
---

# agenda-cursor-inbox

> Rychlý capture **z Cursor chatu** do INBOX — bez rovnou zakládat task v `02-PROJEKTY/`. Triáž později přes `agenda-triage`.

**Vault (SSOT):** `OBSIDIAN/` v repo `SECOND_BRAIN` (Google Drive).

```
/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN
```

**Cílová složka:** `01-INBOX/daily/` (viz `01-INBOX/daily/README.md`)

## Kdy spouštět

Uživatel výslovně chce uložit do Second Brain / Obsidian / INBOX:

- task, úkol, TODO z konverzace
- popis problému / kontext
- plán, návrh, rozhodnutí k pozdějšímu zpracování
- shrnutí vlákna „ať to mám v SB“

**Nespouštět** místo `agenda-capture`, pokud uživatel chce rovnou **soubor-per-task** v `02-PROJEKTY/<slug>/tasks/` — tam použij `agenda-capture`.

## Workflow

### 1. Identifikuj konverzaci

- **UUID chatu** vezmi z aktuální session (`agent-transcripts/<uuid>.jsonl` nebo `transcript_location` v kontextu).
- **Krátký název konverzace** (3–8 slov, česky) — např. `RB Universe — Celofiremní Edit a priority`.
- **Odkaz (kanonický formát v Obsidianu):**

  ```markdown
  [Krátký název konverzace](<uuid-bez-.jsonl>)
  ```

  Příklad: `[RB Universe — finance KPI](a8017558-a4aa-4864-84f4-7ea755e87fbf)`

### 2. Název souboru

```
YYYY-MM-DD-daily-<kratky-slug>.md
```

- `YYYY-MM-DD` = dnešní datum (Europe/Prague)
- slug: lowercase, ASCII, pomlčky, max ~40 znaků (viz existující soubory ve `daily/`)

### 3. Obsah souboru (šablona)

```markdown
---
created: YYYY-MM-DD
type: daily-capture
status: open
tags: [<volitelné — projekt, produkt>]
source: cursor
source_chat: "[Krátký název konverzace](<uuid>)"
---

# <Titulek — co se ukládá>

> Odkaz na konverzaci: [Krátký název konverzace](<uuid>)

## <Sekce dle typu obsahu>

<stručný, strukturovaný obsah z konverzace — task / popis / plán>

## Další krok (volitelné)

- …
```

**Pravidla obsahu:**

- Piš **stručně a věcně** — enough pro triáž za týden; ne celý chat verbatim.
- U **plánu** použij číslované kroky nebo checklist.
- U **tasku** jasně „co / proč / blokery“.
- Zachovej **čísla, URL, cesty k souborům** z konverzace, pokud jsou důležité.

### 4. Preview → write

1. Ukaž uživateli **náhled** (cesta + frontmatter + první odstavce).
2. Po schválení (nebo pokud uživatel řekl „ulož“ bez dalších podmínek) **zapiš soubor** do `01-INBOX/daily/`.
3. V chatu odpověz **wikilinkem** na soubor (relativně z vaultu) + 1–2 bullets co je uvnitř.

### 5. Po zápisu

- **Neprováděj triáž** — soubor zůstane v INBOX.
- **Necommituj** SECOND_BRAIN, pokud uživatel neřekne (Drive sync).

## Příklad triggeru

> „Ulož tento plán do Second Brain.“

→ skill vytvoří např. `2026-06-24-daily-celofiremni-edit-priority.md` s odkazem na aktuální UUID.

## Související

- `agenda-capture` — plný capture do projektových tasků / materiálů
- `agenda-triage` — zpracování `01-INBOX/`
