---
name: agenda-zapis-ze-schuzky
description: >-
  DEEP zápis ze schůzky (Sembly / Plaud): HTML brand RB EDU do ~/Downloads/ + MD
  meeting_summary do 05-RESOURCES/vystupy/zapisy/YYYY-MM/, pak rovnou založí
  Lukášovy tasky (bez druhého schválení). Triggers: zápis ze schůzky, summary
  z meetingu, zpracuj Sembly/Plaud přepis, DEEP triáž sembly/, nebo Plaud
  v daily/. Default varianta full.
---

**F1 (git vault):** pokud vault je git klon (`SECOND_BRAIN_VAULT` / `~/GitHub/second-brain-vault`), skill = **pull + read only** — žádný FS zápis do klonu. Snapshot = VPS; lidský zápis = GitHub web UI PR. Až F2.


# Zápis ze schůzky — HTML + MD (RB EDU)

Zápis čte tým a berou si z něj úkoly. **Nevymýšlej a nepředjímej** — do zápisu
jde jen to, co v přepisu explicitně zaznělo.

**Rozsah:** jen **Sembly** a **Plaud** (meeting přepisy). Slack / mail / Clippings
→ běžný DEEP / `agenda-analyze`, ne tento skill.

**Zdroj pravdy obsahu a HTML shellu:** tento skill + `references/` + `scripts/build_html.py`
+ `assets/`; jazykový průchod: `ŠABLONY/skills/rbedu-grammar-nazi/`. Kalibrace: Claude skill `zapis-ze-schuzky` (15. 9. 2026).

## Co skill dělá

1. Najde přepis + spáruje kalendář / přílohy osnovy.
2. Napíše plný zápis (default `variant: full`).
2a. Jazykový průchod draftu MD přes `rbedu-grammar-nazi` (GN-1 / GN-2, s fingerprint kontrolou) — Krok 5; běží u `full` i `shared`.
3. Vyrobí **HTML** → `~/Downloads/YYYY-MM-DD_<slug>_zapis.html`.
4. Vyrobí **MD** → `OBSIDIAN/05-RESOURCES/vystupy/zapisy/YYYY-MM/…_zapis.md`.
5. U jasných projektů přidá **wikilink stub** do `02-PROJEKTY/<slug>/materials/`.
6. Z tabulky úkolů **rovnou založí** Lukášovy tasky (Lukáš-only filter) — bez druhého schválení.
7. Archivuje zdroj přes `scripts/archive_inbox_item.py`.
8. Interní schůzku rozešle na Slack (HTML + MD). Pravidlo: `.cursor/rules/internal-meeting-slack.mdc`.

**Sdílená / stručná varianta** jen když uživatel **výslovně** řekne „pro tým“ /
„sdílená verze“ / „stručný zápis" — kratší, bez úkolů a citlivin (viz krok Varianta).
**Default vždy = plná DEEP extrakce** z celého přepisu (viz „Hloubka zápisu").

**Preview před zápisem** (HTML/MD) zůstává — včetně **konkrétní tabulky úkolů**
(ne jen počty). Po „ano“ / „upiš“ zapisuj soubory **i** Lukášovy tasky ve stejném tahu.
Preview **nesmí** omezit hloubku finálního zápisu — po schválení vždy znovu DEEP z přepisu.

---

## Kdy spouštět

- Explicitně: „udělej zápis“, „summary ze schůzky“, „zpracuj Sembly/Plaud“.
- **DEEP triáž:** zdroj v `01-INBOX/sembly/`, nebo v `01-INBOX/daily/` se signály
  Plaud/Sembly (hlavička, účastníci, délka přepisu) — **ne** krátký daily note.

Ostatní DEEP zůstává u `agenda-triage` Deep + `agenda-analyze`.

---

## Krok 1 — přepis a kalendář

Vault root: `OBSIDIAN/`. Lokálně čti soubory z disku; Drive MCP jen když soubor
není syncnutý.

| Co | Cesta / poznámka |
|---|---|
| Živý inbox Sembly | `01-INBOX/sembly/` |
| Plaud | často `sembly/` nebo `daily/` — detekuj podle obsahu |
| Archiv | `07-ARCHIV/inbox-processed/<rok>/<měsíc>/sembly/` |
| Lidé | `05-RESOURCES/lide/` |
| Drive ID mapa | `references/drive-mapa.md` |

1. Najdi přepis (`YYYY-MM-DD-HHMM-<slug>.md`). Víc kandidátů → seznam, nech vybrat.
2. Z názvu/hlavičky: datum, čas, účastníci.
3. Spáruj kalendář (Google Calendar MCP) — oficiální název + **přílohy** (agenda).
4. Bez události: řekni to, pokračuj; přílohy může dodat uživatel.

Velké přepisy: `scripts/unescape_transcript.py`, čti po blocích.

---

## Krok 2 — osnova

| Situace | Osnova |
|---|---|
| Podklad = agenda / tabulka priorit / roadmapa | **1:1 struktura**, včetně pořadí. Neslučuj, nepřejmenovávej. |
| Bez struktury | Vlastní **4–8** tematických bloků podle diskuse |

U Sheetu: potvrď list + sloupce osnovy (Drive často vrátí listy zřetězené).

Detail polí: `references/struktura-vystupu.md`.

---

## Krok 3 — jména

Převeď přezdívky na plná jména z `05-RESOURCES/lide/`. Do MD `name_aliases`.
Nejistota → zeptej se. Záloha: `references/lide-aliasy.md` (ověř proti složce).

---

## Krok 4 — interní čísla

Kde dává smysl: **produkční** RB Universe MCP (`user-rb-universe`), ne dev.
Nesedí-li číslo: zapiš co zaznělo + v závorce co je v systému. Haléře → dělit 100.

---

## Krok 5 — obsah (povinné sekce)

**Hloubka zápisu (default) — plná DEEP extrakce**

- Default = `variant: full` + **plný** obsah z celého přepisu: husté „Co zaznělo“,
  všechny projednané i neprojednané body osnovy, neshody, čísla, jména, kontext.
- Kalibrace délky: poměr slov zápis/přepis typicky **≥ ~20–25 %** u hodinové schůzky;
  u hlubokých synců (Town Hall prep, Wiki) klidně 40–50 %. **Ne** výčtové 5 karet
  s 2–3 bulletů, když přepis má tisíce slov.
- **DEEP#1 = úplný MD draft už před chat preview** (tmp OK, např. `/tmp/…_zapis.draft.md`).
  Chat preview je jen **výpis** z post-GN-1 MD (highlights, počet osnovy, tabulka úkolů,
  cesty) — ne náhrada hloubky. Po „ano“ / „upiš“ běží **DEEP#2 refresh** z přepisu + merge
  (viz Krok Preview / rbedu-grammar-nazi), ne první vznik plného zápisu.
- Stručná / sdílená verze **jen na výslovné vyžádání** („stručný“, „shared“, „pro tým“
  bez detailů). Bez toho vždy DEEP full.

1. Highlights — pod `## 0. Meta` blok `### Highlights` + přesně 3 top-level `-` (viz `struktura-vystupu.md`).
2. Body osnovy — status, owner, key_people, „co zaznělo“, tasks.
3. Konsolidovaná tabulka úkolů (všichni lidé — MD/HTML pro tým).
4. Plán dalších setkání (když padl).
5. Parkoviště / mimo strukturu.
6. Poznámky k věrohodnosti.

**Statusy:** `discussed` | `mentioned_only` | `not_discussed` | `removed` | `context`  
Body `mentioned_only` / `not_discussed` **nevynechávej**.

**Úkol** jen když byl explicitně zadán a přidělen člověku. Nabídka = úkol označený
jako nabídka. „Měli bychom" bez vlastníka = ne úkol.

### rbedu-grammar-nazi (GN-1 / GN-2) — povinné před preview a před finálním HTML

Skill: `ŠABLONY/skills/rbedu-grammar-nazi/SKILL.md` (volá ho tento skill, ne naopak).
Režim **zápis** (skill ho pozná podle `## 0. Meta`); běží u `variant: full` i `shared`.
Průchod běží **vždy in-process**, bez Cursor agenta: načti SKILL +
`references/language-rules.md` + `references/meeting-language.md`, přepiš celý MD, vrať jen MD,
zapiš ty. Nejde-li skill/MD načíst → **1 věta + stop write** (ne tichý skip).

**CLI fingerprint (exit 0 shoda/OK, 1 mismatch struktury/cardinality, 2 nevalidní after
— např. full highlights ≠3):**

```bash
python3 "ŠABLONY/skills/rbedu-grammar-nazi/scripts/md_fingerprint.py" capture --md <draft.md> --out <fp.json>
python3 "ŠABLONY/skills/rbedu-grammar-nazi/scripts/md_fingerprint.py" compare --before <fp.json> --md <draft.md>
```

**GN-1 (před chat preview):**

1. Sestav úplný MD DEEP#1 → tmp.
2. `capture` → GN-1 (in-process) → zapiš MD → `compare`.
3. Exit **1 nebo 2** → 1× retry GN (in-process OK) → znovu `compare`. Druhý fail
   (1 nebo 2) → **1 věta uživateli + stop write** (žádný preview / zápis).
4. Exit 0 → chat preview = výpis z **post-GN-1** MD.

**Po „ano“ / „upiš“ (GN-2):**

0. **Před** aplikací editací: snapshot **baseline keys** z post-GN-1 konsolidované tabulky /
   card tasks. Match key = `normalize(Kdo)||normalize(title)`; při kolizi stejného wording
   přidej `#` z preview jako tie-break (A31).
1. Aplikuj editace preview → drž `deleted_keys`, `changed_map`, **finální routing tabulku**
   (Vault? / Projekt / Waiting) — SSOT pro Krok 8.
2. DEEP#2 z přepisu → **merge:** karty / Co zaznělo / status / owner / key_people / park /
   meta rámec z DEEP#2; úkoly dle denylist: (a) `deleted_keys` nezapsat i když jsou v DEEP#2;
   (b) `changed_map` → wording/Kdo z preview; (c) z DEEP#2 jen úkoly mimo baseline a mimo
   `deleted_keys`; (d) úkoly jen v upraveném preview zůstanou. Nové z DEEP#2 bez řádku
   v preview → default `Vault?=jen zápis` (+ 1 řádek ve shrnutí).
3. `capture` → GN-2 → `compare` (stejný retry/stop pro exit 1 i 2).
4. Až exit 0: odvoď `meta.json` + `body.html` **1:1 z post-GN MD** (bez druhého language pass)
   → `build_html.py` → write MD/HTML → Krok 8 z **upraveného preview**.

### HTML vzhled — standard (Lucie & Luky / Claude Team, schváleno 2026-10-09)

Platí pro **všechny** další zápisy (`full` i `shared`). Shell = `build_html.py` +
`assets/style.css` (hero sloupec, celá šířka). Agent neskládá vlastní layout ani
side-by-side hero.

**meta.json (deterministicky, bez volného stylu):**

| Pole | Pravidlo |
|---|---|
| `title` / `h1` | ← frontmatter `title` |
| `kicker` | **max 1 krátká úderná věta**. Nesmí být celý highlight, odstavec ani text začínající „Rámec:“ |
| `stamp` | ← `meeting_date` + typ schůzky |
| `meta_lines` | participants + zdroj — v HTML **pod** `hero-main` (účastníci, stamp, zdroj), ne vedle nadpisu |
| `intro` / `eyebrow` / `footer` | jen 1:1 z MD/frontmatter pokud už existují; `intro` ≠ Rámec |

**body.html (povinné):**

1. **Skutečné HTML tagy** — `<strong>`, `<b>`, `<em>`, `<ul>/<li>`. **Nikdy** literální
   markdown (`**tučné**`, `- odrážka`) v body fragmentu.
2. Blok `Rámec:` / meta šum z `## 0. Meta` **zůstává jen v MD vaultu**. Do HTML
   **nepatří** jako `p.lead`, sekce „Rámec“, ani do kickera / hero.
3. Lead v body (pokud vůbec) = max 1 krátká věta jiného účelu než Rámec; default = žádný
   lead z Meta.
4. Komponenty (teze, karty, badge, tabulky) dle `references/struktura-vystupu.md`.

**Layout hero (shell):** kicker + h1 na **celou šířku** (`.hero-main`); účastníci + stamp
+ zdroj **pod** nimi (`.hero-meta`), ne side-by-side.

### Checklist před `build_html.py`

- [ ] `body.html` bez literálního `**` / MD syntaxe — jen HTML tagy
- [ ] `kicker` = 1 krátká věta (ne highlight, ne „Rámec:“)
- [ ] Rámec / `## 0. Meta` šum **není** v body ani v kickeru / `intro`
- [ ] `meta_lines` + stamp jdou do shell meta (pod hero), ne do body leadu
- [ ] žádné `<style>` v body; layout jen přes `build_html.py`

---

## Krok 6 — soubory

### Pojmenování

```
YYYY-MM-DD_<slug-schuzky>_zapis.html
YYYY-MM-DD_<slug-schuzky>_zapis.md
```

Slug: kebab-case, latin, z oficiálního názvu schůzky (kalendář > přepis).

### HTML → `~/Downloads/`

1. Po GN-2 + compare OK: napiš `meta.json` (viz výše) + `body.html` (jen obsah, **žádné** `<style>`; text 1:1 z post-GN MD).
2. Spusť z rootu skillu:

```bash
python3 "ŠABLONY/skills/agenda-zapis-ze-schuzky/scripts/build_html.py" \
  --meta /tmp/zapis-meta.json \
  --body /tmp/zapis-body.html \
  --out "$HOME/Downloads/YYYY-MM-DD_<slug>_zapis.html"
```

Assety: `assets/style.css`, `assets/logo-rb-edu.txt` (offline base64 logo).

### MD → vault

```
OBSIDIAN/05-RESOURCES/vystupy/zapisy/YYYY-MM/YYYY-MM-DD_<slug>_zapis.md
```

Frontmatter **musí** mít (kromě meeting polí z `struktura-vystupu.md`):

```yaml
type: material
material_kind: schuzka
doc_type: meeting_summary
variant: full          # nebo shared
projects:
  - "[[<slug>]]"       # 0–N projektů
related_tasks: []      # doplň po apply tasků
created: YYYY-MM-DD
```

Existující soubor se stejným názvem **nepřepisuj** — zeptej se.

### Wikilink do project materials/

Pro každý jasný `projects:` slug vytvoř (pokud ještě není) krátký stub:

`02-PROJEKTY/<slug>/materials/YYYY-MM-DD — Zápis — <název schůzky>.md`

```yaml
---
type: material
material_kind: schuzka
title: "Zápis — <název>"
created: YYYY-MM-DD
projects:
  - "[[<slug>]]"
zdroje:
  - "[[05-RESOURCES/vystupy/zapisy/YYYY-MM/YYYY-MM-DD_<slug-schuzky>_zapis]]"
---

# Zápis — <název>

Kanónický zápis: [[05-RESOURCES/vystupy/zapisy/YYYY-MM/YYYY-MM-DD_<slug-schuzky>_zapis]].

HTML ke sdílení: `~/Downloads/YYYY-MM-DD_<slug-schuzky>_zapis.html` (mimo vault).
```

**Jedna kopie těla** = soubor v `vystupy/zapisy/`. V `materials/` jen odkaz.

---

## Krok 7 — varianta

| Varianta | Kdy |
|---|---|
| **full** (default) | **Vždy**, pokud uživatel neřekne jinak — plná DEEP extrakce včetně úkolů, neshod, čísel |
| **shared** / stručná | Jen výslovně „pro tým“, „sdílená“, „stručný zápis“ — očištěná **a zkrácená**; sufix `_tym`; `redacted: true` |

Sdílená / stručná: zachovej highlights + statusy; „co zaznělo“ 1–2 věty; **bez** úkolů
a tabulky úkolů; bez mezd, právních sporů, personálních rozhodnutí, citlivých čísel.
**Bez výslovného požadavku shared/stručný nikdy nezkracuj finální zápis.**

---

## Krok 8 — Lukášovy tasky (povinné po zápisu — rovnou založit)

**SSOT routingu** = **upravená chat preview tabulka** (sloupce Vault? / Projekt / Waiting /
„jen zápis“ / „nabídnout rovnou“) — ne holá konsolidovaná tabulka z MD a ne čisté DEEP#2.
**Wording** úkolů ber z **post-merge / post-GN-2 MD**. **Nečekej na druhé „ano“** — po
schválení zápisu tasky zakládej / updatuj ve stejném tahu jako HTML + MD.

1. Aplikuj **Lukáš-only filter** (`agenda-triage`) na řádky s Vault? ∈ {založit, update, Waiting};
   `jen zápis` / cizí akce zůstanou v zápisu.
2. **Drobná `solo` práce** (Vault? = nabídnout rovnou) → nezakládej task;
   v závěrečném shrnutí nabídni „řešit rovnou?“ (viz bootstrap `agent: solo`).
3. Jinak **hned**: `python3 scripts/next_task_id.py <slug> [--type story|…]` → file-per-task
   + `materials:` / `related_tasks:` na kanónický MD zápis **a samonosný kontext**
   (viz níže — povinné). Update existujícího tasku stejně bez druhého schválení.
4. Hotové úkoly ze schůzky (Lukáš už udělal / označil done) → v zápisu nech jako
   **hotovo**; vault task nezakládej, nebo existující odškrtni / Done.
5. Ve **finálním shrnutí** v chatu vždy vypiš tabulku založených / updatovaných tasků
   (`#` | ID — title | projekt | status | 1 věta Cíl) — ať jde ověřit bez otevírání vaultu.
6. `python3 scripts/sync_lide_people.py --incremental --paths "…"`  
   `python3 scripts/build_agent_context.py`
7. Archiv zdroje: `python3 scripts/archive_inbox_item.py <source.md>`

### Samonosný kontext v tasku (povinné)

Task musí jít otevřít **bez** nutnosti hned číst celý zápis a pochopit, čeho se týká a co je cíl.
Zápis ve `05-RESOURCES/vystupy/zapisy/` zůstává kanón detailu („co zaznělo“); task nese zhuštěný kontext.

**Zdroj textu:** wording z post-merge MD (tabulka + karta) + routing z upraveného preview —
ne improvizace mimo zápis.

U **nového** i **update** tasku ze zápisu vždy:

| Pole / místo | Co napsat |
|---|---|
| `materials:` | wikilink na kanónický `…_zapis` (+ materials stub, pokud je) |
| `related_tasks:` na zápisu | plný název task souboru |
| **Z:** | schůzka + datum + wikilink na zápis (případně sekce / `id:` karty) |
| **Cíl:** / **Cíl teď:** | 1–3 věty — co je hotovo, až je story/krok done |
| **Kontext ze zápisu:** | 2–5 vět — rozhodnutí, kdo drží míček, omezení, vazba na jiné priority |
| Checkbox `**ID-N**` | krátký název + `→ *proč:* …; *DoD:* …` (1 věta proč, 1 věta DoD) |

**Update existujícího tasku:** nepřepisuj celou historii; doplň **Kontext ze zápisu**
(datum schůzky), případně **Cíl teď**, nové checkboxy s *proč/DoD*, řádek do logu
s wikilinkem na zápis.

**Ne:** holý checkbox „udělat X“ + jen `materials:` bez vět v těle.  
**Ne:** kopírovat celou kartu „co zaznělo“ do tasku — zůstaň u zhuštění.  
**Ne:** čekat na „schval tasky“ / druhé preview jen pro Lukášovy položky ze zápisu.
**Ne:** v preview zápisu skrývat úkoly za počty („~4 Lukáš“) — viz Krok Preview.

Detail **Cíl** + **Kontext ze zápisu** patří do založeného tasku + finální tabulky po zápisu;
v preview stačí navrhovaný title + 1 věta o čem (editovatelný seznam před „ano“).

---

## Krok 9 — rozeslání

Až jsou HTML a MD na disku. Detail a tabulka kanálů: `.cursor/rules/internal-meeting-slack.mdc` (při rozporu vyhraje pravidlo).

1. Účastníci z kalendáře. Všichni `@redbuttonedu.cz` / `@redbutton.cz` → Slack. Jinak e-mail.
2. Týmová nebo opakovaná schůzka: kanál z pravidla. Není tam → zeptej se, neposílej.
3. Jinak DM / skupinový DM účastníků.
4. Jedna zpráva, oslovení Hoj / Hojte nebo vokativ z `05-RESOURCES/lide/` či historie Slacku. Přílohy: HTML i MD. Na konec vždy kurzívou `_(jménem Lukáše posílá jeho AsIstent)_` — viz `.cursor/rules/asist-send-signature.mdc`.
5. Známý kanál = pošli, nečekej na další schválení. Příkaz: `python3 scripts/slack_send_message.py`. Token jen z `~/.config/second-brain/slack.env` (user `xoxp-`). Do chatu ho nedávej, login keychain ani Slack cookies nečti.

---

## Preview (před „ano“ / „upiš“)

**Až po GN-1 + compare exit 0.** Před zápisem do Downloads/vaultu ukaž výpis z post-GN-1 MD:

- název + datum + účastníci
- 3 highlights
- počet položek osnovy (stačí číslo + 1 řádek témat)
- **konkrétní úkoly** — tabulka níže (povinné; hlavní místo úprav před schválením)
- cílové cesty HTML a MD
- řádek „Jazykový průchod: proběhl / přeskočen (důvod)“
- kam to půjde: Slack kanál / DM, nebo e-mail když je někdo mimo RB
- navržené projekty pro `projects:` / materials stubs

### Úkoly v preview (povinné)

**Nestačí** „~4 Lukáš · ~2 Kateřina“. Vypiš **každý** řádek z konsolidované tabulky
úkolů (post-GN-1), který po „ano“ buď založíš / updatuješ ve vaultu, nebo necháš jen v zápisu.

Tabulka (`#` povinné — ať jde říct „škrtni 3“, „uprav 1“):

| # | Kdo | Navrhovaný title / znění | Vault? | Projekt (návrh) |
|---|---|---|---|---|
| 1 | Lukáš | … | založit | `rb-universe-development` |
| 2 | Lukáš | … | update existujícího **ID — title** | … |
| 3 | Kateřina | … | jen zápis | — |

- **Vault?** = `založit` | `update **ID — title**` | `jen zápis` (cizí / nabídka bez Lukášova míčku) | `Waiting` (sledovat)
- Title u Lukášových řádků = formulace, která půjde do `title:` task souboru (max ~80 znaků).
- U cizích: stejně konkrétní znění — ať jde škrtnout / přepsat ownera / přesunout na Lukáše.
- Drobná `solo` → řádek s Vault? = `nabídnout rovnou (bez tasku)`.
- Žádný úkol → napiš explicitně „úkoly: žádné“.

Úpravy uživatele („upiš“, „škrtni 2“, „3 na Waiting“) → nejdřív **baseline keys** z pre-edit
preview, pak aplikuj edit → `deleted_keys` / `changed_map` + finální routing. Pak DEEP#2 +
merge + GN-2 (viz Krok 5). Po úspěšném write **Krok 8** podle **upravené** preview tabulky
(+ wording z post-merge MD), ne podle původního draftu v hlavě ani čistého DEEP#2.

**Po „ano“:** finální HTML/MD = DEEP#2 + merge + GN-2 z přepisu, ne roztažený preview.
Preview = kontrola úkolů a **routing** (Vault?/Projekt) + Slack — ne šablona hloubky „Co zaznělo“.

---

## Checklist

- [ ] Osnova = podklad nebo 4–8 vlastních bloků
- [ ] **DEEP#1** úplný MD před GN-1; chat preview až po compare 0
- [ ] GN-1 / GN-2 (`rbedu-grammar-nazi`, in-process) + `md_fingerprint` CLI (compare exit 1 **nebo** 2 → retry 1×; 2. fail = stop)
- [ ] **Plná DEEP** (default) — husté „Co zaznělo“; stručné jen na výslovné vyžádání
- [ ] Finál = DEEP#2 + merge (denylist), ≠ roztažený preview
- [ ] Baseline keys před editací; škrtnuté řádky se z DEEP#2 nevrátí
- [ ] Neprojednané body se statusem, ne vynechané
- [ ] Úkoly jen explicitní + přidělené
- [ ] Preview: konkrétní tabulka úkolů (# | Kdo | title | Vault? | projekt) — ne jen počty
- [ ] Krok 8 routing z upraveného preview; wording z post-merge MD
- [ ] `### Highlights` + 3× `-` (full); meta.json bez volného stylu
- [ ] HTML standard: kicker 1 věta; Rámec jen v MD; body = HTML tagy (ne `**`); hero full-width + meta pod ním
- [ ] Checklist před `build_html.py` (výše) splněný
- [ ] Jména + `name_aliases`
- [ ] HTML bez vlastního CSS, přes `build_html.py` (až po GN-2)
- [ ] MD v `vystupy/zapisy/YYYY-MM/` + `type: material`
- [ ] Stubs v `materials/` u jasných projektů
- [ ] Lukášovy tasky založené / updatované ve stejném tahu (bez druhého schválení)
- [ ] Finální tabulka tasků v chatu (# | ID — title | projekt | status | Cíl)
- [ ] Každý task/update ze zápisu: **Z:** + **Cíl** + **Kontext ze zápisu** + checkbox *proč/DoD* + `materials:` na zápis
- [ ] Zdroj archivován
- [ ] Interní zápis na Slacku (HTML + MD), kanál z pravidla nebo dotaz; podpis kurzívou
- [ ] Default = full DEEP (ne shared / ne stručný)
