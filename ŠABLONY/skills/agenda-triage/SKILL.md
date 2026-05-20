---
name: agenda-triage
description: "Use this skill when the user wants to process accumulated items in CLAUDE COWORK/INBOX/, re-prioritize existing AGENDA topics, or asks 'projeď inbox', 'udělejme triage', 'co tam mám nasbíráno', 'co je nového', 'urovnej to'. Two modes: BATCH (rychle všechno najednou s krátkým souhrnem) and DEEP (jeden po druhém s diskusí). Updates AGENDA/<topic>.md with proper metadata, refreshes 00-System/Index.md, and moves processed items to HOTOVO/processed/. ALWAYS show preview before persisting."
---

# agenda-triage

> Pravidelný (ad-hoc) průchod nasbíraného. Capture skill ukládá rychle, triage pročistí.

## Kdy spouštět

- "Projeď inbox" / "udělejme triage" / "co tam mám nasbíráno"
- Uživatel se vrátil po pauze a chce vědět, co je nového
- Když je v `INBOX/*` >5 položek nezpracováno

## Volby módu

Zeptej se na začátku:

```
Mám 7 položek v INBOXu (3× sembly, 2× slack, 2× cowork-uploads).
Mód:
  [B]atch — rychlý souhrn, navrhnu vše najednou, ty potvrdíš (5 min)
  [D]eep — jeden po druhém, projdeme metadata podrobně (15–20 min)

Default: B.
```

## Batch mód

1. Načti všechny položky z `INBOX/*/`
2. Pro každou: extrahuj obsah, navrhni téma + kvadrant + ICE
3. Postav konsolidovaný preview podle vzoru z `agenda-capture` (viz krok 6 tam)
4. Po potvrzení proveď zápis a archivaci (stejně jako capture skill)
5. Update `00-System/Index.md`

## Deep mód

Pro každou položku:

```
[1/7] INBOX/sembly/2026-04-28-strategy-mtg.md

Shrnutí: 47min meeting o Q3 plánu. 4 akční body identifikované.

Akční bod 1 z 4:
  "Přepracovat sales pipeline reporting pro CEO"

Návrh: AGENDA/ceo-reporting.md (existuje)
  Q1 (urgent: zítra 1:1)
  ICE: I=9 (CEO klíčový stakeholder), C=6 (nevíme rozsah), E=3 (jen úprava existujícího)
  Score: 18
  Vrátit se: zítra
  Blokováno: nic

OK / uprav (téma|kvadrant|ICE) / přeskoč / drop
```

Po projetí všech bodů z položky se posune na další.

## Refresh _index.md

Po každém triage:
1. Pro každý `AGENDA/<slug>.md`:
   - počet aktivních úkolů (řádky `- [ ]`)
   - top priorita = nejvyšší Score mezi aktivními
   - last update = datum dnes (pokud byly změny)
2. Sestav tabulku v `00-System/Index.md` (sortováno podle počtu aktivních úkolů sestupně)
3. Pokud nějaké téma má 0 aktivních úkolů a 0 v backlogu → navrhni archivaci celého tématu

## Re-prioritizace existujících úkolů

Pokud uživatel řekne "udělej re-priority" nebo "Eisenhower přepočítej":
1. Projdi všechna aktivní témata
2. Pro každý úkol s `vrátit se < dnes` → flagni jako "po termínu"
3. Pro úkoly v Q2 → zkontroluj jestli ICE skóre stále dává smysl podle aktuálních info v sekci Materiály
4. Vrať konsolidovaný report:
   - Po termínu: X
   - Q1 dnes: Y
   - Q2 top 3 dle Score: Z
