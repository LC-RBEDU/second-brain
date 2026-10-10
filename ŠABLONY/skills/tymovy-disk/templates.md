# Šablony řídicích souborů

Základ z Claude Team skillu v0.4; diskový standard na disku je **v0.5** (úkoly file-per-task). Cursor delta: příslušnost k týmu doplňuje člověk; věta o org chartu a „doplnit z RB Universe“ v kartě nejsou.

Placeholdery `{{…}}` nahraď. Blok v HTML komentáři smaž, když se nehodí.

## AGENTS.md

```markdown
# {{NAZEV_DISKU}} – instrukce pro AI agenty

Jsi na týmovém disku týmu **{{TYM}}** firmy Red Button EDU. Tento soubor je **jediný zdroj instrukcí** pro všechny agenty (Claude, ChatGPT, Cursor, GrokBot, Gemini…). Agent-specifické doplňky jsou jen v jejich souborech (např. `CLAUDE.md`) a tento soubor neopakují.

**Pořadí načtení:** 1. tento soubor → 2. [`karta týmu.md`](./karta%20t%C3%BDmu.md) (fakta o týmu) → 3. [`index.md`](./index.md) (rozcestník).

## TL;DR

{{JEDNOVETNE_POSLANI_TYMU}}

## Přístup a důvěrnost – POVINNÉ

- **Celý disk je důvěrný pro tým {{TYM}}.** Obsah nevynášej mimo tým, nevkládej do soukromých nástrojů a necituj ho lidem mimo tým.
- **Výjimka je jen složka `public/`** – obsah určený i lidem mimo tým. Než do ní cokoli uložíš nebo přesuneš, ověř, že neobsahuje důvěrné údaje (finance, osobní data, 1:1, NDA), a nech to potvrdit člověkem.
- **Oprávnění nikdy neměníš.** Sdílení řeší owner disku: {{OWNER}}.
- Mazání a přepisování existujících souborů vždy jen po potvrzení uživatelem.

## Struktura

Dva typy složek: **číslované `NN - Název`** = oblasti agendy týmu, **nečíslované malými písmeny** = meta složky.

### Oblasti

{{SEZNAM_OBLASTI, např.:
- `01 - Fakturace/` – vydané a přijaté faktury, podklady k fakturaci
- `02 - Rozpočty/` – roční a projektové rozpočty
}}

Pod oblastí není povinná struktura; řídí ji owner disku.

### Meta složky

- `archiv/` – neaktuální věci. **Soft archiv:** defaultně nečti, necituj, nevyvozuj. Vstup jen se silným důvodem (výslovný pokyn; alokace ID úkolu — list názvů v `archiv/úkoly/`; potvrzený přesun/reopen úkolu). Hotové a zrušené úkoly: `archiv/úkoly/`.
- `dohody a rozhodnutí/` – interní dohody a rozhodnutí týmu, soubor na položku: `YYYY-MM-DD název.md`. Znění dohod žije jen tady (karta má jen seznam s odkazy). Práce s ownerm a termínem patří do `úkoly/` — odkaz na ID. Dohody a rozhodnutí pro celou firmu patří na RB Wiki, tady jen odkaz.
- `ostatní/` – co se hodí a nesedí jinam. Nic nenechávej ležet v kořeni.
- `public/` – sdílené i mimo tým (viz Přístup a důvěrnost).
- `schůzky/` – zápisy, přepisy a nahrávky týmových schůzek, název začíná `YYYY-MM-DD`. Follow-up s ownerm → odkaz na ID v `úkoly/`.
- `scripty/` – skripty a malé aplikace týmu, podsložky podle jazyka (`python/`, `php/`, …). Ke každému skriptu krátký popis (k čemu je, jak se spouští, kdo ho udržuje).
- `šablony/` – týmové šablony (včetně `úkol.md`).
- `úkoly/` – otevřené úkoly týmu, jeden soubor na úkol: `<ID> — <Název>.md`. Prefix a pravidla viz sekce Úkoly.

**Dashboardy** na disku nežijí – na disku je jen `.md` s odkazem na živý dashboard (RB Universe, artefakt, Looker Studio…) v oblasti, kam věcně patří. Kód dashboardu, pokud existuje, patří do `scripty/`. Žádný dashboard úkolů.

<!-- Jen pokud disk obsahoval data před založením struktury; jinak smaž: -->
### Přechodná složka `Archiv stávajícího obsahu/`

- Obsah disku z doby před zavedením této struktury (k {{DATUM}}). Postupně se rozřadí do oblastí a meta složek.
- **Není to soft archiv jako `archiv/`** – obsahuje i živé dokumenty. Číst ji smíš.
- Když z ní čerpáš, uveď, že jde o nerozřazený obsah, a ověř aktuálnost u uživatele. Nové dokumenty do ní nezakládej.

## Úkoly

Každý otevřený úkol je jeden Markdown v `úkoly/`. Hotové (`Done`) a zrušené (`Cancelled`) přesuň do `archiv/úkoly/` (stejný název souboru).

- **ID:** prefix z karty týmu (**Prefix úkolů**) + pomlčka + číslo, např. `{{PREFIX}}-12`. Filename: `<ID> — <Název>.md`. Další číslo = 1 + maximum z názvů v `úkoly/` a `archiv/úkoly/` (stačí list názvů).
- **Status:** `Backlog` | `Doing` | `Waiting` | `Done` | `Cancelled` (bez `Next`).
- **Termín:** hard závazek = `deadline`. Soft „kdy se vrátit“ = `review_deadline` jen když není `deadline`. U `Waiting` povinné `wait_until` — po datu navrhni návrat, status sám neměň.
- **Owner** = jméno z tabulky lidí na kartě. **Oblast** = přesný název složky oblasti.
- **Změny** (nový úkol, pole, komentář, status, přesun, reopen) jen po potvrzení člověka. Komentáře jen připisuj, staré nearavuj.
- ICE a týdenní focus na tento disk nepatří.

## Pravidla práce

- **Kam co patří:** obecné firemní pokyny, návody a rozhodnutí = RB Wiki (wiki.redbuttonedu.cz). Osoby, firmy, finance, projekty = RB Universe / Pipedrive / Allfred. Na disk patří pracovní dokumenty, přílohy, důvěrné věci týmu a týmové úkoly. Jedna věc má jedno místo – **odkaz místo kopie**.
- **Údržba `index.md`:** po přidání, přejmenování nebo smazání složky či souboru na první úrovni nebo v meta složkách hned aktualizuj `index.md` a jeho datum. Jednotlivé úkoly do indexu nevypisuj.
- **Údržba `karta týmu.md`:** při změně lidí, rolí, rytmu, priorit, prefixu úkolů nebo seznamu platných dohod uprav kartu a datum ověření.
- **Pojmenování:** česky s diakritikou; datované soubory začínají `YYYY-MM-DD `; žádné `_final`/`_old` – starší verze do `archiv/`.
- **Nic nenechávej ležet v kořeni** kromě čtyř řídicích souborů.
- **Neověřené informace** nikdy nepodávej jako fakt – označ je.
- **Jazyk a tón:** česky, tykání, lidsky a konkrétně, bez korporátní vaty.

## Stav

- {{DATUM}}: disk podle standardu týmových disků RB EDU v0.5.
```

## CLAUDE.md

```markdown
# {{NAZEV_DISKU}} – dodatek pro Clauda

> **Nejdřív načti [`AGENTS.md`](./AGENTS.md)** – jediný zdroj instrukcí pro tento disk. Tento soubor obsahuje jen věci specifické pro Clauda a nic z `AGENTS.md` neopakuje.

## Jen pro Clauda

- **Údržba disku:** strukturu a řídicí soubory (`AGENTS.md`, `CLAUDE.md`, `karta týmu.md`, `index.md`) udržuj skillem `tymovy-disk`.
- **RB Wiki:** začni `wiki_manifest`, pak `wiki_read`. Sekce týmu: {{WIKI_SEKCE_TYMU}}. Zápis na Wiki jen po potvrzení uživatelem.
- **RB Universe:** členové týmu, finance a projekty ber z konektoru RB Universe, neodhaduj je.
- **Google Drive:** `.md` soubory zakládej s `disableConversionToGoogleType: true`, ať zůstanou Markdownem.
- {{DALSI_CLAUDE_SPECIFICKE_POKYNY – jinak smaž}}
```

## karta týmu.md

Cursor delta oproti Claude šabloně: pod tabulkou lidí není věta o org chartu. Zdroj členů je člověk. Řádek „Členové týmu, data | RB Universe“ je rozdělený.

```markdown
# Karta týmu – {{TYM}}

Fakta o týmu, čitelná pro člověka i agenta. Detailní interní verze; veřejné shrnutí pro celou firmu je na Wiki: {{ODKAZ_WIKI}}.

*Naposledy ověřeno: {{DATUM}}* – u údajů, které se mění, piš datum, ke kterému platí. Prázdné pole nech jako `(doplnit)` – je vidět na první pohled.

## Poslání a odpovědnost

- **Poslání:** {{POSLANI}} *(doplnit)*
- **Za co tým odpovídá:** {{ODPOVEDNOST}} *(doplnit)*
- **Co k týmu nepatří:** {{OUT_OF_SCOPE}} *(doplnit)*

## Lidé a role

| Kdo | Role v týmu | Na co se ho ptát |
|---|---|---|
| {{JMENO}} | {{ROLE}} | {{TEMA}} |

Příslušnost k týmu doplňuje člověk. RB Universe MCP interní sestavu týmu nemá.

## Owner disku

- **Owner (steward):** {{OWNER}} – odpovídá za strukturu první úrovně, oprávnění a pravidelnou revizi přístupů (zejména `public/`).
- **Poslední revize přístupů:** {{DATUM_REVIZE}} *(doplnit)*

## Prefix úkolů

- **Prefix:** `{{PREFIX}}` – ID úkolů ve tvaru `{{PREFIX}}-N` (soubory v `úkoly/` a `archiv/úkoly/`).

## Rytmus týmu

| Co | Kdy | Kde / kanál |
|---|---|---|
| {{SCHUZKA}} | {{FREKVENCE}} | {{KANAL}} |

## Priority

- **Firemní priority (CP), které tým vlastní:** {{CP_ODKAZY – odkazy na karty na Wiki}} *(doplnit)*
- **Interní priority týmu:** {{INTERNI_PRIORITY}} *(doplnit)*

## Platné dohody

Znění dohod žije ve složce `dohody a rozhodnutí/` – tady jen seznam s odkazy.

| Dohoda | Od | Soubor |
|---|---|---|
| {{NAZEV_DOHODY}} | {{DATUM}} | `dohody a rozhodnutí/{{SOUBOR}}` |

## Zdroje

| Co | Kde |
|---|---|
| Veřejné shrnutí týmu (Wiki) | {{ODKAZ_WIKI}} |
| Rozhraní nástrojů (kam co patří) | RB Wiki → Týmové sekce → Technaři → Rozhraní nástrojů |
| Členové týmu | doplňuje člověk |
| Data firmy (finance, projekty) | RB Universe |
| Otevřené úkoly týmu | `úkoly/` |
| Slack kanál týmu | {{SLACK}} *(doplnit)* |
```

## index.md

```markdown
# Index – {{NAZEV_DISKU}}

Jen rozcestník – kde co leží. Instrukce jsou v `AGENTS.md`, fakta o týmu v `karta týmu.md`.

**Poslední aktualizace:** {{DATUM}} ({{CO_SE_ZMENILO}})

## Kořen

| Soubor / složka | Co obsahuje |
|---|---|
| `AGENTS.md` | Instrukce pro všechny agenty. **Načíst jako první.** |
| `CLAUDE.md` | Pointer na `AGENTS.md` + dodatek jen pro Clauda. |
| `karta týmu.md` | Fakta o týmu – poslání, lidé, owner, prefix úkolů, rytmus, priority, seznam platných dohod. **Načíst jako druhé.** |
| `index.md` | Tento rozcestník. **Načíst jako třetí.** |
{{RADKY_OBLASTI, jeden řádek na oblast, např.:
| `01 - Fakturace/` | Vydané a přijaté faktury, podklady k fakturaci. |
}}
| `archiv/` | Soft archiv (neaktuální). Hotové/zrušené úkoly v `archiv/úkoly/`. Agent sem nechodí bez silného důvodu (viz `AGENTS.md`). |
| `dohody a rozhodnutí/` | Interní dohody a rozhodnutí týmu, `YYYY-MM-DD název.md`. |
| `ostatní/` | Co se hodí a nesedí jinam. |
| `public/` | Sdílené i mimo tým – jiná oprávnění. |
| `schůzky/` | Zápisy a nahrávky týmových schůzek, `YYYY-MM-DD …`. |
| `scripty/` | Skripty a malé aplikace týmu, podsložky podle jazyka. |
| `šablony/` | Týmové šablony (včetně `úkol.md`). |
| `úkoly/` | Otevřené úkoly týmu (`<ID> — <Název>.md`). Jednotlivé úkoly sem nevypisuj. |
| `Archiv stávajícího obsahu/` | Přechodná složka – obsah před zavedením struktury, k rozřazení. Číst smíš (viz `AGENTS.md`). |

<!-- Jen pokud disk obsahoval data před založením struktury; jinak smaž (i řádek v tabulce Kořen): -->
## Archiv stávajícího obsahu (k {{DATUM}})

Obsah disku před zavedením struktury, k postupnému rozřazení. Živé dokumenty, agent je číst smí.

| Položka | Typ |
|---|---|
| {{PUVODNI_POLOZKA}} | {{TYP}} |
```

## Dohoda / rozhodnutí

Soubor `dohody a rozhodnutí/YYYY-MM-DD název.md`. Checklist v dohodě není SSOT — práce s ownerm patří do `úkoly/`.

```markdown
# {{NAZEV}}

- **Typ:** dohoda / rozhodnutí
- **Datum:** {{DATUM}}
- **Kdo se dohodl / rozhodl:** {{KDO}}
- **Platí od / do:** {{PLATNOST}}
- **Týká se celé firmy?** ne / ano → Wiki: {{ODKAZ}}

## Kontext
{{PROC_SE_ROZHODOVALO}}

## Co platí
{{CO_PLATI}}

## Dopady a odkazy na úkoly
{{ODKAZY_NA_ID, např. STR-3 — …; nebo (zatím žádné)}}
```

## šablony/úkol.md

Soubor na disku: `šablony/úkol.md` (kopie této šablony). Nový úkol = kopie do `úkoly/<ID> — <Název>.md`.

```markdown
---
id: {{PREFIX}}-{{N}}
title: {{NAZEV}}
owner: {{JMENO_Z_KARTY}}
oblast: {{NN - Název oblasti}}
status: Backlog
# deadline: YYYY-MM-DD          # hard; když nastavíš, review_deadline smaž
# review_deadline: YYYY-MM-DD   # jen bez deadline
# wait_until: YYYY-MM-DD        # povinné u status: Waiting
# odkazy: []                    # volitelné URL / wikilinky
---

# {{PREFIX}}-{{N}} — {{NAZEV}}

## Zadání

{{CO_UDELAT}}

## Progress

-

## Přílohy

- (odkazy, ne kopie)

## Komentáře

- {{DATUM}} {{CAS}} — {{JMENO}}: založeno
```
