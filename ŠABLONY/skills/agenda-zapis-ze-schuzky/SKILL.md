---
name: agenda-zapis-ze-schuzky
description: >-
  DEEP zápis ze schůzky (Sembly / Plaud): HTML brand RB EDU do ~/Downloads/ + MD
  meeting_summary do 05-RESOURCES/vystupy/zapisy/YYYY-MM/, pak Lukášovy tasky.
  Triggers: zápis ze schůzky, summary z meetingu, zpracuj Sembly/Plaud přepis,
  DEEP triáž sembly/, nebo Plaud v daily/. Default varianta full.
---

# Zápis ze schůzky — HTML + MD (RB EDU)

Zápis čte tým a berou si z něj úkoly. **Nevymýšlej a nepředjímej** — do zápisu
jde jen to, co v přepisu explicitně zaznělo.

**Rozsah:** jen **Sembly** a **Plaud** (meeting přepisy). Slack / mail / Clippings
→ běžný DEEP / `agenda-analyze`, ne tento skill.

**Zdroj pravdy obsahu a HTML shellu:** tento skill + `references/` + `scripts/build_html.py`
+ `assets/`. Kalibrace: Claude skill `zapis-ze-schuzky` (15. 9. 2026).

## Co skill dělá

1. Najde přepis + spáruje kalendář / přílohy osnovy.
2. Napíše plný zápis (default `variant: full`).
3. Vyrobí **HTML** → `~/Downloads/YYYY-MM-DD_<slug>_zapis.html`.
4. Vyrobí **MD** → `OBSIDIAN/05-RESOURCES/vystupy/zapisy/YYYY-MM/…_zapis.md`.
5. U jasných projektů přidá **wikilink stub** do `02-PROJEKTY/<slug>/materials/`.
6. Z tabulky úkolů navrhne **Lukášovy** tasky (Lukáš-only filter) → preview → apply.
7. Archivuje zdroj přes `scripts/archive_inbox_item.py`.
8. Interní schůzku rozešle na Slack (HTML + MD). Pravidlo: `.cursor/rules/internal-meeting-slack.mdc`.

**Sdílená varianta** (`variant: shared`, sufix `_tym`) jen když uživatel řekne
„pro tým“ / „sdílená verze“ — kratší, bez úkolů a citlivin (viz krok Varianta).

Zatím: **preview před zápisem** (jako triáž). Později přejde na rovnou HTML+MD.

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

1. Highlights — 3 klíčové závěry (ne shrnutí agendy).
2. Body osnovy — status, owner, key_people, „co zaznělo“, tasks.
3. Konsolidovaná tabulka úkolů (všichni lidé — MD/HTML pro tým).
4. Plán dalších setkání (když padl).
5. Parkoviště / mimo strukturu.
6. Poznámky k věrohodnosti.

**Statusy:** `discussed` | `mentioned_only` | `not_discussed` | `removed` | `context`  
Body `mentioned_only` / `not_discussed` **nevynechávej**.

**Úkol** jen když byl explicitně zadán a přidělen člověku. Nabídka = úkol označený
jako nabídka. „Měli bychom“ bez vlastníka = ne úkol.

---

## Krok 6 — soubory

### Pojmenování

```
YYYY-MM-DD_<slug-schuzky>_zapis.html
YYYY-MM-DD_<slug-schuzky>_zapis.md
```

Slug: kebab-case, latin, z oficiálního názvu schůzky (kalendář > přepis).

### HTML → `~/Downloads/`

1. Napiš `meta.json` + `body.html` (jen obsah, **žádné** `<style>`).
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
| **full** (default) | Vždy, pokud uživatel neřekne jinak — včetně úkolů, neshod, čísel |
| **shared** | „pro tým“, „sdílená“ — očištěná **a zkrácená**; sufix `_tym`; `redacted: true` |

Sdílená: zachovej highlights + statusy; „co zaznělo“ 1–2 věty; **bez** úkolů
a tabulky úkolů; bez mezd, právních sporů, personálních rozhodnutí, citlivých čísel.

---

## Krok 8 — Lukášovy tasky (povinné po zápisu)

Z konsolidované tabulky / `**tasks**` v MD:

1. Aplikuj **Lukáš-only filter** (`agenda-triage`): task jen kde míček drží Lukáš;
   cizí akce zůstanou v zápisu; hraniční → `Waiting` / „Sledovat: …“.
2. Preview návrhů (projekt, ICE, status, `agent`) — zatím jako triáž.
3. Po schválení: file-per-task + `materials:` / `related_tasks:` na kanónický MD zápis
   **a samonosný kontext ze zápisu** (viz níže — povinné).
4. `python3 scripts/sync_lide_people.py --incremental --paths "…"`  
   `python3 scripts/build_agent_context.py`
5. Archiv zdroje: `python3 scripts/archive_inbox_item.py <source.md>`

### Samonosný kontext v tasku (povinné)

Task musí jít otevřít **bez** nutnosti hned číst celý zápis a pochopit, čeho se týká a co je cíl.
Zápis ve `05-RESOURCES/vystupy/zapisy/` zůstává kanón detailu („co zaznělo“); task nese zhuštěný kontext.

**Zdroj textu:** konsolidovaná tabulka + karta v zápisu (`**Co zaznělo**`, owner, status) —
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

V **preview** tasků u každé položky uveď i návrh Cíl + 1 větu kontextu (ne jen ID a ICE).

---

## Krok 9 — rozeslání

Až jsou HTML a MD na disku. Detail a tabulka kanálů: `.cursor/rules/internal-meeting-slack.mdc` (při rozporu vyhraje pravidlo).

1. Účastníci z kalendáře. Všichni `@redbuttonedu.cz` / `@redbutton.cz` → Slack. Jinak e-mail.
2. Týmová nebo opakovaná schůzka: kanál z pravidla. Není tam → zeptej se, neposílej.
3. Jinak DM / skupinový DM účastníků.
4. Jedna zpráva, oslovení Hoj / Hojte nebo vokativ z `05-RESOURCES/lide/` či historie Slacku. Přílohy: HTML i MD.
5. Známý kanál = pošli, nečekej na další schválení. Příkaz: `python3 scripts/slack_send_message.py`. Token jen z `~/.config/second-brain/slack.env` (user `xoxp-`). Do chatu ho nedávej, login keychain ani Slack cookies nečti.

---

## Preview (zatím)

Před zápisem do Downloads/vaultu ukaž krátce:

- název + datum + účastníci
- 3 highlights
- počet položek osnovy + počet úkolů (Lukáš vs ostatní)
- cílové cesty HTML a MD
- kam to půjde: Slack kanál / DM, nebo e-mail když je někdo mimo RB
- navržené projekty pro `projects:` / materials stubs

Až po „ano“ / „upiš“ zapisuj soubory a tasky.

---

## Checklist

- [ ] Osnova = podklad nebo 4–8 vlastních bloků
- [ ] Neprojednané body se statusem, ne vynechané
- [ ] Úkoly jen explicitní + přidělené
- [ ] Jména + `name_aliases`
- [ ] HTML bez vlastního CSS, přes `build_html.py`
- [ ] MD v `vystupy/zapisy/YYYY-MM/` + `type: material`
- [ ] Stubs v `materials/` u jasných projektů
- [ ] Lukášovy tasky preview → apply
- [ ] Každý task/update ze zápisu: **Z:** + **Cíl** + **Kontext ze zápisu** + checkbox *proč/DoD* + `materials:` na zápis
- [ ] Zdroj archivován
- [ ] Interní zápis na Slacku (HTML + MD), kanál z pravidla nebo dotaz
- [ ] Default = full (ne shared)
