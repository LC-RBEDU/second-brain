---
name: agenda-meeting-prep
description: "Příprava na schůzky do chatu. Ad-hoc (připrav schůzky, příprava na schůzku, co mě dnes čeká) i naplánovaný běh: jen schůzka s dalším účastníkem, výstup do chatu. Nezapisuje do vaultu, neposílá do Slacku."
---

# agenda-meeting-prep

> Příprava na schůzky **na vyžádání**. Výstup jde do chatu, nikam se nezapisuje.

**Zdroje:** Google Calendar MCP (primary), RB Universe MCP (organizace, osoby, dealy účastníků), `00-System/agent-context-light.json` (+ `charters.json` dle potřeby), vault OBSIDIAN, Gmail MCP, Slack MCP, Drive MCP
**Nezapisuje:** ani do vaultu, ani do Slacku. Pokud si Lukáš přípravu chce uložit, řekne si o to zvlášť → `agenda-capture`.

## Kdy spouštět

- „Připrav mi schůzky" / „připrav mi dnešek"
- „Připrav mi zítřek" / „připrav schůzky na čtvrtek"
- „Připrav mi tu schůzku s Albertem" (jedna konkrétní)
- „Co mě dnes čeká za schůzky"

**Nepoužívat** pro „co teď" / „co dnes" — to jsou úkoly, ne kalendář → `agenda-co-ted`.

### Naplánovaný běh (Cowork, cca hodinu dopředu)

Cowork umí jen pevný interval (nejjemnější je hodina), ne spoušť „30 minut před eventem“. Naplánovaný task proto jednou za hodinu v pracovní době:

1. Vezmi schůzky, které **začínají v příštích 70 minutách**.
2. Nech jen ty, kde je **aspoň jeden účastník kromě Lukáše** (`self` nepočítej; `resource` / místnost nepočítej). Bez lidí → přeskoč, včetně bloků bez účastníků, OOO, focus, Reclaim bufferů a Reclaim sync osobních eventů.
3. Když v okně nic takového není → **napiš nula znaků**. Žádné „nic není“.
4. Když je → pro každou takovou schůzku udělej přípravu podle zbytku tohoto skillu a vypiš ji **jen do tohoto chatu**. Do vaultu ani do Slacku ne.
5. Stejný `event id` v tom samém dni neprezentuj podruhé, když už příprava v tomto vlákně je.

RB Universe MCP je na to dost. Pro externího účastníka nebo firmu v názvu pozvánky ho použij (osoba, organizace, otevřený deal). Vault pořád čteš z lokální složky SECOND_BRAIN — bez ní tasky a zápisy nemáš.

---

## 0. Ověř si datum a čas

**Než cokoli načteš, potvrď si aktuální datum.** Nespoléhej na datum z předchozího kroku konverzace ani na `today` v agent-contextu — ten může být starý. Příprava na špatný den je horší než žádná.

Když už část dnešních schůzek proběhla, **řekni to** a zaměř se na to, co je ještě před ním — a na otevřené smyčky z těch, které skončily.

---

## 1. Načti kalendář

```
Google Calendar: list_events
  startTime / endTime = požadovaný den, Europe/Prague
  orderBy = startTime
  pageSize = 50
```

Zpracuj `nextPageToken` — Reclaim generuje hodně bloků.

MCP vrací rovnou: `summary`, `description`, `attendees[]` (email, displayName, responseStatus, organizer, self, resource), `attachments[]`, `conferenceUrl` (už zploštěný), `location`, `recurringEventId`, `eventType`, `visibility`, `transparency`.

### 1a. Filtry — co zahodit

| Zahodit | Signál |
|---|---|
| OOO | `eventType: OUT_OF_OFFICE` |
| Focus time, working location, narozeniny | `eventType` FOCUS_TIME / WORKING_LOCATION / BIRTHDAY |
| Zrušené | `status: cancelled` |
| **Reclaim buffer bloky** | `description` obsahuje `reclaim.ai/landing/about`, **nebo** `id` začíná `reclaim0habit0`, **nebo** název začíná 🚌 😎 🍽 🛡 🆓 |

**Pozor na rozdíl dvou Reclaim odkazů:**

- `reclaim.ai/landing/about` + `utm_medium=buffer-event` = **buffer blok** (Travel, Decompress) → zahodit
- `reclaim.ai/signup` + `utm_medium=calendar-sync-event` = **sync reálného osobního eventu** → nezahazovat, viz 1c

### 1b. Co zahrnout

Ad-hoc („připrav dnešek“):

- Celodenní eventy
- Eventy bez účastníků
- `visibility: private` — **ano, u ad-hoc přípravy se zahrnuje**

Naplánovaný běh: event bez dalšího člověka **vynech úplně**, i celodenní. `private` ber jen když má jiného účastníka.

### 1c. Reclaim sync osobních eventů

Reclaim tahá reálné osobní eventy z jiného kalendáře (Fitko, oslavy, komunitní akce). Nejsou to buffery, ale příprava se na ně nedělá.

→ **Jeden řádek v přehledu dne** kvůli orientaci v čase, bez bloku.

### 1d. Deduplikace

Tentýž event se může objevit dvakrát — jednou jako Reclaim sync z jiného účtu, jednou jako vlastní záznam. Poznáš to podle podobného názvu a překryvu času.

→ Slouč do jednoho řádku, ponech variantu s víc daty.

### 1e. HTML v popisu

`description` chodí jako HTML (`<ul><li>`, `<br>`, `<a href>`). Strippni značky a **zachovej strukturu odrážek** — ta bývá tou skutečnou agendou.

---

## 2. Načti agent-context — light first

Pro tento skill je primární **`00-System/agent-context-light.json`**. Plný `agent-context.json` nechávej ostatním skillům (`agenda-co-ted`, …).

**Light obsahuje:**

- `projects[]` — bez `charter_*`; má `people: [jména]` z hub `## People`
- `tasks[]` — **všechny otevřené** tasky (včetně Waiting/Backlog), `materials_count` místo `materials[]`
- `top_priority*`, `upcoming_deadlines`, `focus_suggestions`, `open_epics` — **pole ID** (string), ne objekty → lookup do `tasks[]`

**Charter narativ** (scope / kontext / cíl) → `00-System/charters.json` jen pro 1–2 slugy, kterých se schůzka týká. `generated_at` musí sedět s light.

**Postup:**

1. Existuje-li light → čti **ten** (+ charters jen pro namapované projekty)
2. Jinak fallback na plný `agent-context.json` — **jen jednou za běh**
3. Detail konkrétního tasku (operativní kroky, log) → jeho `.md` soubor, jen když víš který a proč

⚠️ **Zkontroluj `generated_at`.** Starší než 24 hodin → upozorni v přehledu dne a ber čísla jako orientační.

---

## 3. Klasifikace

| Typ | Podmínka |
|---|---|
| 🔴 **A** — externí / rozhodovací | účastník, který není interní, **nebo** má přílohu |
| 🟡 **B** — interní projektová | jen interní účastníci **a** dá se namapovat projekt |
| ⚪ **C** — rutina / 1:1 | vše ostatní |

Opakovaný event **není** automaticky C. Účastníky s `resource: true` (zasedačky) ignoruj.

### Kdo je interní

1. Adresa na doméně `redbuttonedu.cz` **nebo** `redbutton.cz`, **nebo**
2. adresa patří člověku v `05-RESOURCES/lide/`, který má v `email` / `emails` aspoň jednu adresu na jedné z těch domén (i když zrovna píše z externí — např. Lenka Turečková / Rainfellows)

→ Klasifikace **B** (interní projektová), ne A. Žádný allowlist ve skillu — datový model + `is_internal` v lib.

Když sporný účastník v `lide/` chybí nebo nemá druhou adresu, **navrhni doplnění**; needituj person soubory sám.

---

## 4. Mapování na projekt — primární a vedlejší

Signály, sečti:

| Signál | Body |
|---|---|
| `description` obsahuje `[[Hub]]` na existující projekt | **rovnou použij, přebíjí vše** |
| Název eventu obsahuje slug nebo alias projektu | +5 |
| Účastník je v `projects[].people` (light) nebo má projekt v `05-RESOURCES/lide/` — viz práh níže | +3 |
| Klíčové slovo z hubu v názvu | +1 (max +3) |

**Práh účastníků podle velikosti schůzky:**

- 2 účastníci (1:1) → stačí **jeden** účastník s projektem
- 3 a víc → potřeba **dva**

Bez tohoto rozlišení by žádné 1:1 nikdy nedosáhlo na projekt — druhý člověk nemůže být dva.

Prahy: **≥5** mapuj · **3–4** mapuj s `⚠️ odhad` · **<3** bez projektu.

### 4a. Schůzka může patřit do víc projektů

Zvlášť u 1:1 s kolegou, který si přinese vlastní agendu, míří jednotlivé body do různých projektů — jeden do Pipedrive, druhý do Sales, třetí do M&A.

→ **Urči primární projekt** (nejvyšší skóre, nebo ten, kam míří většina agendy) a **vedlejší vypiš u konkrétních bodů**, ne v hlavičce bloku. Hlavička s pěti wikilinky nikomu nepomůže.

Když si nejsi jistý, **řekni to**. Nevymýšlej si projektovou příslušnost.

---

## 5. Okno „od minule"

- Opakovaná schůzka → počet dní od předchozího výskytu (min 3, max 60)
- Jednorázová → **14 dní**

---

## 6. Sběr kontextu

Sekce bez obsahu **se nevykreslují**. Nikdy nevyplňuj prázdnou sekci frází „nic nenalezeno".

| Sekce | A | B | C | Zdroj |
|---|---|---|---|---|
| **Agenda z pozvánky** | ✅ | ✅ | ✅ | odrážky z `description` |
| Cíl | ✅ | ✅ | ✅ | `description` + charter projektu |
| Účastníci | ✅ | — | — | `05-RESOURCES/lide/` |
| Kontext projektu | ✅ | ✅ | — | charter v agent-contextu |
| Přílohy | ✅ | ✅ | — | `attachments[]` → Drive MCP |
| **Waiting — čekáš na nich** | ✅ | ✅ | ✅ | tasky `Status: Waiting` |
| **Ty dlužíš** | ✅ | ✅ | ✅ | viz 6.2 |
| Otevřené tasky | ✅ | ✅ | ✅ | `Doing` + `Next` |
| Sliby z minula | ✅ | ✅ | ✅ | viz 6.2 |
| Logistika | ✅ | ✅ | ✅ | `location`, `conferenceUrl` |

**Do žádného bloku negeneruj navrhované otázky.**

U **C** je jádrem dvojice Waiting / Ty dlužíš. Když je obojí prázdné → `Nic nevisí. Volný sync.`

### 6.0 Agenda z pozvánky má přednost přede vším

Když má pozvánka **vlastní agendu** v popisu, je to nejcennější vstup, jaký můžeš dostat — člověk napsal vlastníma rukama, co chce probrat.

→ Postav blok **kolem ní**: projdi bod po bodu a ke každému dohledej, co k němu ve vaultu, Slacku a mailu je. Teprve co zbyde, doplň z obecné heuristiky.

Když agenda chybí, nastupuje zbytek pravidel v obvyklém pořadí.

### 6.1 Přílohy

Pro každou položku v `attachments[]` otevři přes Drive MCP (`read_file_content`).

⚠️ **Počítej s rolling dokumenty.** Zápisy typu „Meeting notes" bývají jeden soubor s ročním nánosem sekcí od nejnovější. Ber **poslední jednu až dvě sekce**, ne celý soubor. Trvalé sekce s pravidly (SSOT) zmiň, ale necituj celé.

Když soubor nejde přečíst, uveď jen název a odkaz.

### 6.2 Sliby z minula a „Ty dlužíš"

Stejná sada zdrojů pro **všechny typy A / B / C**, v okně z bodu 5:

1. **Gmail MCP** — vlákna s účastníky; `in:sent` pro to, co jsi slíbil ty
2. **Slack MCP** — kanály projektu a DM s účastníky
3. `01-INBOX/sembly/` a `02-PROJEKTY/*/materials/` — zápisy s překryvem účastníků (≥2 shodní lidé); sekce `## Akční body`
4. `materials[]` u tasků — často odkazují přímo na zápis z minulé schůzky

**Gmail a Slack dávej první.** Věci staré pár hodin ve vaultu ještě nejsou — a právě ty bývají tím, co na schůzce padne.

Rozlišení směru:
- **Ty dlužíš** = Lukáš je aktér — odesílatel v `in:sent`, přiřazený v Sembly akčních bodech, task `agent: none` se `Status: Doing/Next`, **nezodpovězená prosba od účastníka**
- **Waiting** = tasky `Status: Waiting`, kde je účastník blocker, **nebo otevřená otázka, kterou jsi jmenovitě položil někomu, kdo na schůzce bude**

Když je směr nejednoznačný → do „Sliby z minula" jako neutrální položka. **Nehádej.**

Co se prokazatelně uzavřelo, **označ jako uzavřené** a nepředkládej k řešení.

### 6.3 Externí a RB Universe

U účastníka mimo `@redbuttonedu.cz` / `@redbutton.cz` (nebo firmy v názvu pozvánky) se nejdřív zeptej **RB Universe MCP** — `search_persons`, `search_organizations`, `search_deals`. Ber jen to, co nástroj vrátí. Nic z toho nevymýšlej a dev Universe nepoužívej.

Když Universe ani vault nic nemají:

```
👤 Jana Nováková (jana@ahold.cz) · přijala — nemáme kontext
```

`responseStatus` česky: `accepted` → přijal/a, `tentative` → možná, `declined` → odmítl/a, `needsAction` → nepotvrdil/a.

---

## 7. Výstup

Krátký přehled dne, pak blok na každou schůzku chronologicky.

```
📅 Čtvrtek 10. 9. — 2 schůzky
Osobní v kalendáři: Fitko 15:00
Odfiltrováno: 5 Reclaim bufferů

━━━━━━━━━━━━━━━━━━━━
🟡 10:00–11:00 · Luky C./Verča K.
   1:1 · [[Pipedrive a další nástroje]] ⚠️ odhad · Impact Hub, Hub 6

   Agenda z pozvánky — 4 body:
   1. … → [[Pipedrive a další nástroje]], navazuje na PD7
   4. … → [[M&A Odyssey]]

   📌 Ty dlužíš: …
   ⏳ Čekáš na ní: …
```

Úkoly vždy jako **`ID — název`**, nikdy samotné ID.

Registr A (kolega sám sobě), tykání, česky, stručně. Bez AI frází a patosu.

**Prázdný den** → jedna věta, žádné bloky.

Na závěr **zdroje dat** a označení, co je ověřené a co odhad.

---

## Nedělat

- Negenerovat otázky k položení
- Nezapisovat do vaultu ani neposílat do Slacku
- Neměnit `focus`, ICE, deadline
- Needitovat person soubory — jen navrhnout
- Nedomýšlet si projektovou příslušnost — u nejistoty `⚠️ odhad`
- Neuvádět Reclaim buffery jako schůzky
- Nespoléhat na datum z kontextu konverzace
- Nenačítat plný agent-context, když existuje light varianta

## Handoff

Skill žije v `ŠABLONY/skills/agenda-meeting-prep/`. Změny kódu, testy, commit → **Cursor**.

## Proaktivní varianta

Skill je ad-hoc. Když chce Lukáš ranní ping, `agenda-remind` mu pošle Slack DM v 7:45 s textem „připrav schůzky" — přípravu si pak vyvolá sám.
