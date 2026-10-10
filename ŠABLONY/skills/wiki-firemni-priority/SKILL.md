---
name: wiki-firemni-priority
description: "Firemní priority 2HY/FY2026 na RB Wiki — dashboard a karty CP1–CP9. Načti při: firemní priority, CP, company priorities, 2HY dashboard, ukaž priority, stav priority, uprav prioritu / KAM / EDUtéku / Summit. Bez tohoto skillu priority nezobrazuj z hlavy."
---

# Wiki — firemní priority (CP)

Jediná pravda o devíti prioritách 2. pololetí FY2026 (do 28. 2. 2027) je **RB Wiki**, sekce `strategicke-priority-rb-edu/`.

- Dashboard = `strategicke-priority-rb-edu/prehled.md`. Ve frontmatteru `title` nech na začátku mezeru (` Přehled priorit 2HY FY2026`) — sekce řadí karty podle názvu a bez ní přehled spadne za CP9. Nadpis v těle stránky mezeru nemá.
- Karty = `cp1-identita-edu.md` … `cp9-procesni-jasnost-delivery.md`
- Sekce `## Název` na kartě není. Název je jen nadpis stránky.
- `## Owner` a `## Klíčové osoby` jsou hned pod nadpisem, pod sebou, každá jako odrážky. Víc lidí = víc odrážek.
- Sekce `## Co to konkrétně znamená` je seznam odrážek, ne odstavec.
- Správce sekce (steward) = **Luboš Malý**. Ověřuje drafty na webu a rozhoduje spory o obsah karet.

Priority nikdy neukazuj z hlavy ani z jiných zdrojů (Drive, Slack, sheet). Když wiki MCP chybí, viz „Bez wiki MCP“.

## Nástroje

1. `wiki_manifest` — jen když nevíš cestu.
2. `wiki_read` — vždy před zápisem; `sha` si nech.
3. `wiki_write` — karty a `prehled.md`. Vždy s `expected_sha` z posledního `wiki_read` a s `model`.
4. `wiki_section_write` — jen rozcestníky (`index.md`). **Nikdy** `wiki_write` na `index.md`.

Pole `generated` neposílej, server ho nastaví sám.

Když zápis selže kvůli sha: zastav se, stránku znovu přečti a ukaž uživateli, co se mezitím změnilo. Druhý zápis pošli **jen** když uživatel řekne „zapiš znovu“.

## Která karta

| Řekne se | Soubor |
|---|---|
| CP1, identita EDU, majitelské zadání | `cp1-identita-edu.md` |
| CP2, ways of working, způsob spolupráce | `cp2-ways-of-working.md` |
| CP3, IT & Data team, Technaři jako priorita, governance nástrojů | `cp3-it-data-team.md` |
| CP4, struktura dat, AI agenti (priorita), wiki jako priorita | `cp4-struktura-dat-pro-ai-agenty.md` |
| CP5, nahrávky, Sales Feed, vytěžování dat | `cp5-vytezovani-dat-sales-kam.md` |
| CP6, KAM, key account | `cp6-key-account-management.md` |
| CP7, EDUtéka, eduteka | `cp7-eduteka.md` |
| CP8, Summit, Exponential Summit, ES 2027 | `cp8-exponential-summit.md` |
| CP9, procesní jasnost, delivery proces, Allfred jako priorita | `cp9-procesni-jasnost-delivery.md` |
| firemní priority, dashboard, 2HY, přehled CP | `prehled.md` |

Sedí dva řádky stejně → zeptej se, který. Samotné „IT“ nebo „data“ = CP3 i CP4 → zeptej se.

## Zobrazit (show)

Nic nezapisuj. `wiki_read` cíle.

### Jedna karta → shrnutí

Do chatu dej **krátké shrnutí**, ne celou kartu:

- **ID + název**, owner priority (`cp_owner`)
- **Stav** (`progress`)
- **Nejbližší milník** + datum
- **Poslední hlášení** — text pod `## Stav plnění` (zkrácený, když je dlouhý)
- **Poslední změna** — nejnovější řádek `## Historie změn` (poslední sekce karty)
- **Upozornění na prošlé milníky** (viz níže)
- Že je stránka draft / neověřená, když to hlavička čtení říká

Na konec: „Celou kartu (DoD, kontext, klíčové osoby, všechny milníky) ukážu na vyžádání.“

Celou kartu dej doslova, jen když o ni uživatel požádá („celou“, „detail“, „DoD“, „ukaž kartu“).

### Dashboard → tabulka z `prehled.md`

Tabulku dej tak, jak je na wiki. Pod ni přidej upozornění na prošlé termíny.

### Prošlý milník (upozornění)

Prošlý = řádek milníku s datem **< dnes**, bez „hotovo“ na konci.

- Na kartě: za každý prošlý milník jeden řádek
  `⚠ Milník „<text>“ (<datum>) prošel a není označený jako hotový. Owner: <cp_owner>.`
- Na dashboardu: řádek, kde `Termín` < dnes → stejné upozornění pro danou CP.
- Upozornění je jen v chatu. **Nic nezapisuj**, `progress` neměň. Blízký nebo prošlý termín sám o sobě není `riziko`.
- Nabídni: „Chceš nahlásit stav nebo milník odškrtnout?“

## Nahlásit stav (update)

**Kdo smí:** kdokoli. Identitu neověřuj.

**Autor zápisu:** jméno toho, kdo píše (z kontextu Claude). Když ho nemáš, zeptej se „Pod jakým jménem to mám zapsat?“ a nic nezapisuj.

### Co se smí měnit bez dalšího

- text pod `## Stav plnění` — jen věty, které uživatel řekl (nepřeformulovávej)
- `progress` — jen když uživatel řekl jedno z: `v termínu` / `riziko` / `hotovo` / `neznámé`. Jinak ho neměň
- milník: **přidat** (jen s textem i datem od uživatele), **odškrtnout** (uživatel určí který; řádek dostane na konec „hotovo“, datum zůstane), **posunout termín** (uživatel řekne který a nové datum; po posunu seřaď milníky podle data)
- přepočet `nearest_milestone` a `nearest_milestone_date` + stejný řádek v `prehled.md`
- jeden nový řádek v `## Historie změn` (poslední sekce karty, ne pod DoD)

### Zamčené

Bez jedné z vět „DoD se mění“, „obsah se mění“, „strat. tým schválil“, „strategický tým schválil“ **neměň**:

- blok DoD (vše mezi `## Definition of Done` a `## Stav plnění`) — po zápisu musí být byte-stejný
- `cp_owner` a tělo `## Owner`
- `## Co to konkrétně znamená`, `## Kontext`, `## Klíčové osoby`
- frontmatter `owner`, `type`, `title`, `description`, `tags`, `id`, `period`
- názvy nadpisů `##`, seznam devíti priorit, odrážky „Co teď není priorita“

Pokus o změnu bez té věty → odmítni, nic nezapisuj a řekni, že obsah karet schvaluje strategický tým (steward Luboš Malý).

Neurčité „uprav KAM“ / „uprav prioritu“ bez toho, co se mění → ukaž shrnutí karty a zeptej se. Nic nezapisuj.

### Postup zápisu

1. `wiki_read` karty → změna → `wiki_write` s `expected_sha`.
   `summary`: `CP6 progress→riziko — Jan Novák` (ID + co + jméno).
2. Do historie přidej řádek **nahoru** (nejnovější první), vždy do `## Historie změn` na konci karty:
   `- YYYY-MM-DD — Jméno — co se změnilo`
3. Když se měnil milník nebo `progress`: `wiki_read` `prehled.md` → uprav řádek CP (milník, termín ve tvaru `5. 10. 2026`, stav) → `wiki_write` s jeho `expected_sha`.
4. Znovu `wiki_read` karty a ukaž **shrnutí** (jako v Zobrazit). Zmiň, že jde o draft.

### Nejbližší milník

Nadpis sekce na kartě je jen `## Přehled milníků`. Že je nejbližší tučný, je tohle pravidlo, ne součást nadpisu.

Řádky ve tvaru `- 2026-10-05 — text` nebo `- **2026-10-05 — text**`. „hotovo“ na konci řádku milník vyřadí.

Nejbližší = nejmenší datum **≥ dnes** mezi nevyřazenými. Při shodě data vyhraje první řádek v souboru. Jen ten je tučný: `- **datum — text**`.
Žádné takové datum → nic tučně, `nearest_milestone: ""`, `nearest_milestone_date: ""`. Datum nevymýšlej.

## Bez wiki MCP

Přesně tahle hláška, nic dalšího o obsahu priorit:

`Chybí wiki MCP. Karty firemních priorit bez něj neukážu ani nezměním.`

## Založení sekce (create) — šablona pro další období

Pro 2HY FY2026 už proběhlo (4. 10. 2026). Balíček `create-bundle.md` vedle tohoto souboru je **šablona** pro příští pololetí, ne aktuální stav — aktuální stav je vždy na wiki.

- Když `prehled.md` v sekci existuje → create odmítni, nic nezapisuj, řekni, že sekce žije.
- Nový create jen s **novým** balíčkem od uživatele a po souhlasu stewarda. Z hlavy nezakládej.
- Postup: `wiki_section_write` sekce (`confirm_create: true`, až po potvrzení uživatele) → doplnit odstavec do kořenového `index.md` přes `wiki_section_write` `path: ""` + `expected_sha` (starý text nech) → `wiki_write` karet a `prehled.md`. Před zápisem každé karty přepočítej nejbližší milník k dnešku. DoD kopíruj doslova.

## Stav na dashboardu

Sloupec Stav = `progress` karty. Dokud owner stav nenahlásí, je `neznámé`.
Odrážky pod „Co teď není priorita“ nejsou karty.
