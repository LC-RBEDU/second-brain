---
name: grammar-nazi
description: >-
  Language pass for Second Brain meeting notes (agenda-zapis-ze-schuzky only):
  Czech/English grammar and inflection, natural prose, anti-AI/corporate fluff
  per references/meeting-language.md. Not a standalone daily skill. Returns only
  the corrected full markdown draft — no diff report. Does not edit quoted
  citations. Prefer Task agent grammar-nazi when available; otherwise inline.
---

# grammar-nazi — language pass pro zápisy ze schůzek

Volá **jen** skill `agenda-zapis-ze-schuzky` (Cursor agent nebo inline).  
Nepro nabídky, Slack 1:1, task body mimo zápisový flow, ani plný `rbe-writing-style`.

## Vstup / výstup

- **Vstup:** celý MD draft zápisu (frontmatter + body).
- **Výstup:** celý opravený MD. **Žádný** úvod, diff, checklist, „opravil jsem…“.

## Priority

1. Gramatika CS/EN (překlepy, skloňování, časování, shoda, interpunkce).
2. Přirozenost / anti-AI / anti-korpo dle [references/meeting-language.md](references/meeting-language.md).

## Smí

- Morfologie, překlep, interpunkce, přeformulování vět **beze změny smyslu**.
- Text **uvnitř** existující odrážky / buňky (title úkolu, Co zaznělo, znění úkolu).
- EN úseky opravovat v EN; CS v CS; nepřekládat jazyk.
- Chunking po `##` sekcích při limitu kontextu — po složení chunků musí `md_fingerprint` běžet na **celém** MD.

## Nesmí

- Měnit fakta, jména, čísla, rozhodnutí, ownery, smysl úkolů.
- Přidat / odebrat / sloučit top-level odrážky (Co zaznělo, tasks, highlights, park).
- Měnit YAML klíče, enum hodnoty (`discussed` / `Projednáno`…), `name_aliases` mapu, cesty.
- Měnit bitově `owner` / `key_people` / `status` / hodnoty `- **id:**`.
- Opravovat text v uvozovkách / citátech (`"…"`, `„…“`, `»…«`).
- Měnit fenced/inline code, URL, e-maily, `[[wikilinky]]`, tvary task ID.
- Měnit tvar `**tasks** — žádné` (neexpandovat na prázdný seznam).
- Offer / claim / slide voice; registr „ty“ / osobní Slack (`lukas-writing-style`).

## Fingerprint (volá hlavní agent, ne tento skill)

```bash
python3 ŠABLONY/skills/grammar-nazi/scripts/md_fingerprint.py capture --md <draft.md> --out <fp.json>
# exit 0 OK, 2 nevalidní

python3 ŠABLONY/skills/grammar-nazi/scripts/md_fingerprint.py compare --before <fp.json> --md <draft.md>
# exit 0 shoda, 1 mismatch, 2 nevalidní after
```

## Claude / bez Cursor agenta

Stejný pass in-process: načti tento SKILL + `meeting-language.md`, přepiš draft, vrať jen MD.
