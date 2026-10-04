---
name: wiki-firemni-priority
description: "Firemní priority 2HY/FY2026 na RB Wiki — dashboard a karty CP1–CP9. Načti při: firemní priority, CP, company priorities, 2HY dashboard, ukaž priority, uprav prioritu / KAM / EDUtéku / Summit. Bez tohoto skillu priority nezobrazuj z hlavy. Vault Second Brain nečti a v odpovědi ho nenabízej."
---

# Wiki — firemní priority (CP)

Týmová pravda o devíti prioritách 2. pololetí FY2026 je **jen na RB Wiki**, sekce `strategicke-priority-rb-edu/`.

Dashboard = `strategicke-priority-rb-edu/prehled.md`.
Karty = `cp1-identita-edu.md` … `cp9-procesni-jasnost-delivery.md`.

Skill **nečte** Second Brain, Obsidian ani cesty ve vaultu. Když wiki MCP není, viz „Bez wiki MCP“.

Věta do Claude Team / Project instructions je v `project-instructions.md` vedle tohoto souboru.

## Nástroje (pořadí)

1. `wiki_manifest`
2. `wiki_read` (vždy před přepisem; sha si nech)
3. `wiki_section_write` — jen rozcestník sekce a kořen (`path: ""`). **Nikdy** `wiki_write` na `index.md` (B6).
4. `wiki_write` — karty a `prehled.md`.

`expected_sha` z posledního `wiki_read` posílej při každém přepisu. Když zápis kvůli sha selže: zastav, stránku znovu přečti, konflikt ukaž. **Druhý zápis bez věty uživatele „zapiš znovu“ neposílej** (B5).

## Match karty

| Řekne se | Soubor |
|---|---|
| CP1, identita EDU, majitelské zadání | `cp1-identita-edu.md` |
| CP2, ways of working, způsob spolupráce | `cp2-ways-of-working.md` |
| CP3, IT & Data, Technaři jako priorita | `cp3-it-data-team.md` |
| CP4, struktura dat, AI agenti (priorita) | `cp4-struktura-dat-pro-ai-agenty.md` |
| CP5, nahrávky, Sales Feed, vytěžování | `cp5-vytezovani-dat-sales-kam.md` |
| CP6, KAM, key account | `cp6-key-account-management.md` |
| CP7, EDUtéka, eduteka | `cp7-eduteka.md` |
| CP8, Summit, Exponential Summit, ES 2027 | `cp8-exponential-summit.md` |
| CP9, procesní jasnost, delivery proces, Allfred jako priorita | `cp9-procesni-jasnost-delivery.md` |
| firemní priority, dashboard, 2HY, přehled CP | `prehled.md` |

Dva řádky sedí stejně → zeptej se, který. Samotné „IT“ nebo „data“ je CP3 i CP4 → zeptej se.

## Show

Nic nezapisuj. `wiki_read` cíle. Do chatu dej obsah, který je v odpovědi `wiki_read` (žádná věta navíc o stavu plnění). Řekni, že stránka je draft / neověřená, když to hlavička čtení říká.

- Dashboard / „ukaž firemní priority“ → `prehled.md`.
- Jedna priorita → její karta.

## Update (= update-status)

**Kdo smí:** kdokoli. Wiki identitu neověřuj.

**Autor zápisu:** jméno z kontextu (kdo píše). Když ho nemáš, zeptej se „Pod jakým jménem to mám zapsat?“ a **do odpovědi nepiš** (0× `wiki_write`).

### Allowlist (bez flagu)

Jen tohle:

- text pod `### Stav plnění` — jen věty, které uživatel řekl
- `progress` — jen když uživatel řekl jedno z: `v termínu` / `riziko` / `hotovo` / `neznámé`. Jinak `progress` neměň
- milník: přidat jen když je **text i datum**; odškrtnout jen když určí který (řádek dostane „hotovo“, datum zůstane)
- přepočet `nearest_milestone` a `nearest_milestone_date` + stejný řádek v `prehled.md`
- jeden nový řádek v `### Historie změn`

### Lock

Bez jedné z vět „DoD se mění“, „obsah se mění“, „strat. tým schválil“, „strategický tým schválil“ **neměň**:

- pevný blok DoD (vše mezi nadpisem `## DoD + aktuální stav plnění` a `### Stav plnění`) — po zápisu musí být byte-stejný
- `cp_owner` a tělo `## Owner`
- `## Název`, `## Co to konkrétně znamená`, `## Kontext`, `## Klíčové osoby`
- názvy `##`, seznam devíti priorit, odrážky „Co teď není priorita“

Pokus o tuhle změnu → odmítni, 0× write (B3).

Neurčité „uprav KAM“ / „uprav prioritu“ bez toho, co se mění → ukaž kartu (show) a zeptej se. 0× write (B10).

### Po úspěšném zápisu

1. `summary`: `CP6 progress→riziko — Jan Novák` (id + co + jméno).
2. Historie, nejnovější nahoře, vždy jako `###` pod DoD, nikdy jako `## Historie`:
   `- YYYY-MM-DD — Jméno — co se změnilo`
3. Když se měnil milník nebo `progress`, uprav řádek v `prehled.md` (vlastní `wiki_read` + sha).
4. Znovu `wiki_read` a do chatu dej **finální** text. Zmiň, že jde o draft.

### Nejbližší milník

Řádky ve tvaru `- 2026-10-05 — text` nebo `- **2026-10-05 — text**`.
Volitelné „hotovo“ na konci řádku milník vyřadí.

Nejbližší = nejmenší datum **≥ dnes**. Při shodě vyhraje první řádek v souboru. Ten jediný je tučný: `- **datum — text**`.
Žádné budoucí datum → žádné tučné, `nearest_milestone` prázdné, `nearest_milestone_date` prázdné. Datum nevymýšlej.
Nový milník jen z textu a data od uživatele.

`progress` při přepočtu milníku neměň, pokud uživatel neřekl jeden ze čtyř stavů.

## Create

Jednou. Když `prehled.md` v sekci už je, create odmítni (0× write) a řekni, že sekce žije.

Podklad = `create-bundle.md` **vedle tohoto SKILL.md**. Soubor chybí nebo v něm chybí stránka → nezakládej z hlavy.

Před zápisem každé karty přepočítej nejbližší milník (pravidlo výše) k dnešku. Tučné v balíčku platí jen když přepočet vyjde stejně. `cp_owner` ber jen z pole v balíčku. Chybí-li, nech `neznámé`.

DoD kopíruj doslova, včetně CP4. U CP2 nech větu, že DoD je neuzavřené.

První create **nedávej** odkaz na charter Technařů ani na wiki stránku Summitu.

Pořadí:

1. `wiki_section_write` `path: strategicke-priority-rb-edu`, `confirm_create: true`, title `Strategické priority RB EDU`, description `Devět firemních priorit Red Button EDU na 2. pololetí FY2026.`, intro:

   Tady jsou strategické priority Red Button EDU na 2. pololetí FY2026 (do konce února 2027). Říká se jim CP, firemní priority, company priorities nebo priority 2HY. Přehled je na stránce [Přehled priorit](prehled.md). Jedna priorita = jedna karta. Tahle stránka je rozcestník sekce; tabulka priorit je [prehled.md](prehled.md).

2. `wiki_read` cesty `index.md` (kořen). K existujícímu úvodu **přidej jeden odstavec** (starý text nech) a ulož celé intro přes `wiki_section_write` `path: ""` + `expected_sha`:

   Strategické priority na 2. pololetí (2HY / FY2026, do konce února 2027) jsou v sekci Strategické priority RB EDU. Přehled devíti aktivních priorit je na stránce [Přehled priorit](strategicke-priority-rb-edu/prehled.md). Říká se jim taky CP nebo firemní priority.

3. `wiki_write` devíti karet a `strategicke-priority-rb-edu/prehled.md` z balíčku (po přepočtu milníků). `summary`: `CP1 create — <jméno>` (jméno toho, kdo create chtěl).

Steward ve frontmatteru `owner` je `human:lukas` (Lukáš Cypra, objednal create). Update ho nemění. `cp_owner` je owner priority a je to jiné pole.

Wiki bere `generated` jen jako objekt, ne jako `true`:

```yaml
generated:
  by: agent
  at: 2026-10-04T14:30:00.000Z
  via: mcp
  author: human:lukas
```

Když create běží **bez wiki MCP**: stránky nezakládej a stav nevymýšlej. Řekni, že chybí wiki MCP, a že markdown balíček aplikuje agent, který wiki má. Show a update tenhle fallback **nemají**.

## Bez wiki MCP (show a update)

Přesná hláška, nic jiného o obsahu priorit:

`Chybí wiki MCP. Karty firemních priorit bez něj neukážu ani nezměním.`

Žádný dashboard z hlavy. Žádný vault.

## Stav na dashboardu

Sloupec Stav = `progress` karty. Create ho nechá `neznámé`, dokud owner (kdokoli) stav neřekne. Blízký termín sám o sobě není `riziko`.

Sidelined pod tabulkou jsou odrážky bez čísel CP. Nejsou to karty.

## Mimo tento skill

Ranking úkolů ve vaultu (+5) tenhle skill nezapíná. Čtení wiki do snapshotu úkolů je pozdější krok.
