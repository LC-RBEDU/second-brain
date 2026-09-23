---
name: agenda-triage
description: "INBOX triage in MrLUC Second Brain v2 vault, pending batch approval from cron, or re-priority. Triggers: projeď inbox, schval pending triáž, apply batch, udělejme triage. Modes: BATCH, DEEP, PENDING (read 00-System/Triage-Pending/*.json with v2 schema). Creates task files in 02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md (human-readable filename, em-dash U+2014; subtasks číslované **<ID>-N**), archives to 07-ARCHIV/inbox-processed/. Spotify/podcast link or show title in Slack/email/inbox → queue via MCP spotify (not a vault task). ALWAYS preview before write."
---

# agenda-triage (v2)

> Pravidelný průchod nasbíraného. Capture ukládá rychle, triage pročistí. **V2:** vytváří `task .md` soubory v `02-PROJEKTY/<slug>/tasks/` (file-per-task), Bases dashboard se aktualizuje sám.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Kdy spouštět

- "Projeď inbox" / "udělejme triage" / "co tam mám nasbíráno"
- V `01-INBOX/*` je >5 nezpracovaných položek
- "Schval pending triáž" / "apply batch" → mód **PENDING**

## Módy

```
Mám N položek v INBOXu.
  [B]atch — rychlý souhrn, potvrzení najednou
  [D]eep — položka po položce
  [P]ending — schválení 00-System/Triage-Pending/*.json (cron návrh)
  [R]e-priority — delegace na agenda-priority-review

Default: B (nebo P pokud uživatel žádá pending).
```

## Triage routing (PARA)

| Typ obsahu | Kam |
|------------|-----|
| Lukášův akční krok | `add_task` → `02-PROJEKTY/<slug>/tasks/` |
| Referenční materiál | `05-RESOURCES/<kategorie>/` nebo project `materials/` + `topics:` |
| Zodpovědnostní postřeh bez akce | `area_log` → `03-AREAS/<area>.md` sekce `## Log rozhodnutí` |
| Neznámá osoba ve zdroji | `add_person` → `05-RESOURCES/lide/<Jméno>.md` ze `_ŠABLONA-person.md` |
| Nová info o známé osobě | `update_person` → patch frontmatter/sekcí person souboru |
| Spotify odkaz / název podcastu, pořadu, epizody | **fronta** přes MCP `spotify` — ne task (viz níže) |

**„Kandidát na projekt" = vlastník procesu, ne téma.** Skoro každý úkol jde popsat jako proces. Rozhoduje, kdo agendu reálně vlastní a tahá za nitky (např. karty / dobíjení / platby → Finance). Firemní procesy = sepsání návodu až jako druhý krok. Detail dřív: `LL-2026-09-07-kandidat-na-projekt-uri-vlastnik-procesu` (Superseded → tento skill).

Pravidla Resources: `.cursor/rules/resources-para.mdc`. Přílohy: co-located binárka + sidecar `.md` v `materials/<téma>/` (viz PARA rule); parsuj `## Přílohy` z INBOX `.md`; po apply spusť `extract_material_text.py`.

## Spotify / podcasty — do fronty, ne do vaultu

Spotify **nemá oficiální MCP**. V Cursoru je community server `spotify` (`@xavifabregat/spotify-mcp` v `~/.cursor/mcp.json`). Tokeny: `~/.spotify-mcp/`. Premium + běžící Spotify app (telefon/desktop) — jinak API frontu odmítne.

**Kdy:** v Slacku, e-mailu, Sembly, Clippings, daily i pending JSONu je
- URL `open.spotify.com/…` nebo URI `spotify:episode:` / `spotify:show:` / `spotify:playlist:`
- holý název podcastu / pořadu / epizody (doporučení, „poslechni“, „mrkni na“)

**Postup (BATCH i DEEP i PENDING — vedle běžného routingu):**
1. Najdi cílovou **epizodu** (ne jen show, pokud jde o konkrétní díl). MCP `search` umí track/album/artist/playlist — **show/episode ne**. Hledej `GET https://api.spotify.com/v1/search?type=show,episode` s access tokenem z `~/.spotify-mcp/tokens.json`, nebo queue rovnou z URI v odkazu.
2. Přidej do fronty: MCP `queue` (URI), případně `PUT /v1/me/player/queue?uri=…`.
3. 0 devices / 404 player → v preview „fronta přeskočena — otevři Spotify“; **neblokuj** zbytek triáže.
4. MCP/token chybí → řekni to jednou; dál triáž bez fronty.

**Není to task.** Poslech ≠ Lukášův operativní krok. Nezakládej `add_task` „Poslechnout X“.
- Zdroj je **jen** poslech/doporučení → queue + `archive_only`.
- Zdroj má **i** závazek → queue **a** běžný task routing zbytku.
- V preview vždy uveď, co šlo do fronty (název + URI), nebo proč ne.

Ad-hoc mimo INBOX („hoď to do fronty“) = stejný postup, bez zápisu do vaultu.

## Lidé — automatická detekce (každý zdroj)

Pro každý INBOX / pending zdroj:
1. Extrahuj zmíněné osoby (jména + aliasy z `05-RESOURCES/lide/` frontmatter).
2. **Neznámá** → proposal `add_person` (role/org/email z textu).
3. **Nový kontakt/narozeniny/role/téma** u známé → proposal `update_person`.
4. Preview v batchi; apply až po schválení. Po apply spusť `sync_lide_people.py`.

## Hub narativ po apply

Po schválení batch s novými tasky pro projekt **nabídn** doplnění `## Kontext` hubu (nové téma z triáže) + `updated:`.

Pokud batch vyžaduje **nový projekt** (nový slug): naved na [[00-System/Templates/new-project-workflow]] — nejdřív hub + `## Zdroje dat`, pak tasky.

## Auto-routing „komplexních" zdrojů

V BATCH i PENDING módu skill **automaticky** detekuje komplexní materiál a routuje ho do DEEP, místo aby ho mlel přes default add_task flow.

**Komplexní materiál** = ten, ze kterého se zákonitě bude rozsekávat víc tasků nebo se z něj stane samostatný materiál. Sdílená heuristika `vps/second-brain-hub/lib/triage_complexity.py` (volá ji i cron `triage_run.py`); pravidla v OR:

- Subdir `01-INBOX/sembly/` → **vždy** DEEP → skill **`agenda-zapis-ze-schuzky`** (HTML+MD zápis).
- Subdir `01-INBOX/daily/` + signály Plaud/Sembly přepisu → stejně `agenda-zapis-ze-schuzky`.
- Subdir `01-INBOX/email/sent/` → **nikdy** DEEP (commitment fast-path).
- Subdir `01-INBOX/Clippings/` → BATCH nebo DEEP dle `triage_complexity` (dlouhé clipy); viz `01-INBOX/Clippings/README.md`.
- `word_count > 800` nebo `line_count > 100`.
- 3+ H2/H3 headingů v těle.
- 5+ otevřených checkboxů `- [ ]`.
- Sekce `## Přílohy` s alespoň jednou položkou → **DEEP** (materiály + sidecar).
- **Inline odkaz** na Google Docs/Sheets/Slides nebo pdf/docx v těle → **DEEP** (materializace při interaktivním DEEP flow).
- Signální fráze: „Action items", „Akční kroky", „Úkoly", „Závěry", „Decision points", „Rozhodnutí", „Next steps", „Další kroky".
- Override v souboru: `<!-- triage:deep -->` nebo `<!-- triage:simple -->` má precedenci přede vším ostatním.

Cron označuje takový návrh `requires_deep_analysis: true`, `kind: "deep"`, `proposalType: "deep_analysis"`, `target_path: null`, `frontmatter: null`, `body: "DEEP analysis required..."` a v summary `…-summary.md` přidává sekci **DEEP candidates** s důvody.

## Batch

1. Načti `01-INBOX/*/`
2. Pro **`01-INBOX/slack/`** nejdřív relevance (`vps/second-brain-hub/lib/triage_slack_relevance.py`) → archive / batch / deep (viz sekce Slack INBOX níže).
3. Pro ostatní položky zavolej **`is_complex_source(rel, body)`** (`vps/second-brain-hub/lib/triage_complexity.py`).
4. Komplexní zdroj → automaticky DEEP flow pro ten jeden zdroj (viz níže), zbytek dál v BATCH.
5. Pro non-DEEP položku: extrahuj, navrhni projekt + ICE + status (Next/Backlog/Waiting) + `agent` (none/assist/solo) + **`review_deadline`** (povinné u Next/Doing — kdy se k tomu vrátit; `deadline` jen při externím závazku). **`solo` lookup → nejdřív „řešit rovnou?“, ne `add_task` s podtasky** (viz Agent níže).
6. Generuj ID (scan `02-PROJEKTY/<slug>/tasks/` + `07-ARCHIV/tasks-done/<slug>/`)
7. Preview všech BATCH položek najednou + výpis DEEP candidates (skill agenda-capture struktura).
   **Nad ~10 položek předkládej po blocích** — viz níže.
8. Po OK: zápis task `.md` souborů, archiv source → `07-ARCHIV/inbox-processed/YYYY/MM/` (**včetně co-located příloh** — viz níže)

### Předkládání po blocích

Analýzu si udělej celou dopředu, ale **nepředkládej ji jako jeden souvislý report**. Nad ~10
položek se k tomu nedá vyjádřit — uživatel musí odpovídat na patnáct věcí naráz a odpoví na dvě.

- Jeden blok = **jedno téma nebo jeden zdroj**. Konec bloku = otázka „takhle, nebo jinak?“.
- Pokračuj až po odpovědi na předchozí blok.
- Na začátku jedna věta, **kolik bloků celkem bude** — ať uživatel ví, do čeho jde.
- Výjimka: čistý `archive_only` / `drop` shrň hromadně počtem, tam se po jednom nic nezískává.

### Archiv INBOX + přílohy (povinné při apply)

Při každém `archive_only` / DEEP apply / `archiveAfterApply` **nepřesouvej jen `.md`** — vždy zavolej SSOT helper:

```bash
python3 scripts/archive_inbox_item.py "01-INBOX/<typ>/<soubor>.md"
# nebo hromadně osiřelé přílohy (`.md` už v archivu):
python3 scripts/archive_inbox_item.py --orphans
```

Implementace: `vps/second-brain-hub/lib/inbox_archive.py` · `list_colocated_attachments()`.

| Zdroj | Co-located přílohy (stejná složka INBOX) |
|-------|------------------------------------------|
| `email/` · `email/sent/` | `{md_stem}__{název}` (n8n Gmail/sent workflow) |
| `slack/` capture_n8n | `{YYYY-MM-DD-HHMM}-{slackFileId}-{název}` — sdílený prefix s `.md` capture |
| `sembly/` · `daily/` | stejná logika jako email (`stem__`) pokud n8n přiloží binárku |

Po apply s materiálem: binárku **volitelně** zkopíruj do `02-PROJEKTY/<slug>/materials/` + sidecar (`agenda-capture` / PARA rule); originál + přílohy stejně patří do `07-ARCHIV/inbox-processed/` vedle `.md`.

**Post-flight:** po batchi spusť `--orphans` — chytí případy, kdy `.md` šel do archivu bez příloh.

### Odeslané e-maily (`01-INBOX/email/sent/`)

- Capture: n8n `workspace-sent-to-inbox.json` (Workspace `lukas@redbuttonedu.cz`, frontmatter `source: sent`)
- Cron `triage_run.py` + `triage_commitments.py`: závazky (`kind: commitment`) nebo fallback u mailu bez závazku
- **Drop list** (`triage_commitments._SENT_INBOX_DROP_RULES`): shoda `to` + `subject` / `subject_contains` → **n8n neukládá** do INBOX (`workspace-sent-to-inbox.json`); cron `purge_dropped_sent_inbox` **smaže** případné staré soubory (+ přílohy `stem__*`) bez triáže. Mj. `finance@` + Fakturace dealu, Audits, OOO.
- **Manuální triáž (agenda-triage):** při BATCH/DEEP/PENDING — pokud soubor v `01-INBOX/email/sent/` odpovídá drop listu (normalizovaný `to` + `subject` z frontmatter / hlavičky, stejná logika jako `should_drop_sent_from_inbox` v `workspace-sent-format-markdown.js`), použij **`proposalType: drop`**: **smaž** zdroj + přílohy `stem__*`, **ne** archivuj, **ne** vytvářej task. V preview uveď „DROP (sent inbox rule)" — apply bez dalšího potvrzení, pokud user schválil batch obsahující drop.
- Každý návrh v batchi má **`proposalType`**:
  - `add_task` — vytvoří `02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md` (em-dash U+2014, sanitized title) + frontmatter `aliases: [<ID>]` + očíslované subtasky `**<ID>-N**`
  - `update_task` — patchne frontmatter / body existujícího task souboru
  - `archive_only` — jen přesune source do archivu
- Souhrn: `00-System/Triage-Pending/YYYY-MM-DD-HHMM-summary.md` — české odrážky po souborech (typ, projekt, archiv po schválení)
- **`archiveAfterApply`**: default `true` — po schválení `add_task` z odeslaného mailu přesuň zdroj do `07-ARCHIV/inbox-processed/` + `**ZPRACOVÁNO**` v hlavičce
- PENDING: u commitmentů zkontroluj `notes` (citace) a `confidence`

### Slack INBOX (`01-INBOX/slack/`)

Ve složce jsou **dva typy zdrojů** — triáž vždy vyhodnotí relevanci (cron i manuální BATCH/DEEP/PENDING):

| Typ | Signály | Typický původ |
|-----|---------|---------------|
| **capture_n8n** | `**Čas:**`, `## Komentář`, `## Forwardovaný obsah` | `slack-cowork-inbox-with-attachments.json` (:cowork: / reakce v capture kanálu) |
| **thread_dump** | `**Vlákno:**`, `**Kanál:**`, citované `> **Jméno**` nebo `**Jméno** HH:MM` | export celého vlákna s Lukášovou interakcí (reakce mimo capture kanál) |

**Routing (SSOT:** `vps/second-brain-hub/lib/triage_slack_relevance.py` **, volá `triage_run.py`):**

| Route | Kdy | `proposalType` | Preview label |
|-------|-----|----------------|---------------|
| **ARCHIVE** | pasivní účast / uzavřený kontext; **inbound bez odpovědi sem nesmí** (to je DEEP). Inbound s odpovědí smí, ale preview = 1 řádek (viz sweep) | `archive_only` (`kind: slack_thread_archive`) | Slack archiv (bez tasku) |
| **BATCH** | záměrný `## Komentář` nebo krátký Lukášův commitment | `add_task` | Vytažení úkolu |
| **DEEP** | dlouhé vlákno, forward-only capture, víc stran bez jednoho tasku, **inbound (`@Lukáš` / `adresováno mně` / `@zmínka` / spec) bez Lukášovy odpovědi** | `deep_analysis` | DEEP analysis required |

**Sweep ARCHIVE dávky (povinné — v souladu s `.cursor/rules/slack-inbox-triage.mdc`):**

Heuristika označí archivem skoro všechno a občas se plete — 10. 8. 2026 jich takhle propadlo šest
z 24, včetně neodpovězeného DM o upgradu Traefiku. Tichý hromadný archiv bez rozlišení inboundu
nedělej.

Čtyři vrstvy preview (v tomto pořadí):

1. **Inbound řádky (vždy):** každé archive vlákno s `adresováno mně` / `@zmínka` / `@Lukáš` /
   `@lukas` / spec přílohou = **1 řádek** (kdo, o čem, odpověděl jsi?, zbývá míček?).
   Tagovaný / adresovaný uživatel to musí vidět i po své odpovědi. **Mlčení tu neplatí.**
2. **Kalendář cross-check (povinné):** u vláken / e-mailů se signálem „bookni“, „najdeme čas“,
   „1:1“, „mrkni do kalendáře“, nebo kde zbývající míček = domluva callu — **před návrhem
   tasku/Waiting** načti kalendář (`user-google-workspace` `get_events`, query jméno/e-mail,
   ~14 dní dopředu). Hit → do řádku datum+čas, follow-up = vyřešené (archive). Miss → teprve
   Waiting/hold. Stejně u DEEP, když action item je „domluvit schůzku“. Detail:
   `.cursor/rules/slack-inbox-triage.mdc`.
3. **DM/GDM vždy 1 řádek (vet):** každé archive DM / group DM = **1 řádek** (kdo, o čem,
   otevřený míček / update běžícího tasku / nic k přijetí) — i bez inbound signálu a i když
   už jsi odepsal. Heuristika „archive“ neznamená „bez hodnoty“; může to být kontext
   k běžícímu tasku nebo závazek ještě nepřijatý do vaultu. **DM/GDM nikdy do šumu počtem.**
4. **Šum počtem:** **jen** veřejné kanály bez inboundu + stale nižší `_vN`. Jen tady:
   **mlčení = archiv**. U DM/GDM, inbound a kalendáře **mlčení ≠ archiv**.

**Formát tabulky v chatu (povinné — viz `task-mention-convention.mdc`):**

| # | Kdo / kanál | O čem (téma z obsahu) | Míček / stav |
|---|-------------|------------------------|--------------|
| 1 | … | věcná věta z vlákna, ne „later / bez odpovědi“ | … |

- První sloupec **`#`** — ať jde říct „řádek 3 jinak“.
- **O čem** = předmět zprávy (co člověk chce / o čem je diskuse). Routing meta („saved later“, „bez tvé odpovědi“, „interakce bez commitmentu“) patří jen do sloupce Míček/stav, ne místo tématu.

Inbound **bez** Lukášovy odpovědi sem nepatří — to je **DEEP** (rule + `detect_inbound_work_for_lukas`).

**Verze vlákna (povinné — nejdřív tohle, teprve pak relevance):**
n8n ukládá `*_v1.md`, `*_v2.md`, `*_v3.md` u stejného **Thread TS**. Platí **jen nejvyšší `_vN`**. Nižší verze = `archive_only`, **nesmíš z nich tahat závazky** (zastaralý snapshot — 25. 8. 2026: Leadspicker / Poppe hotel vypadaly otevřené, v aktuální verzi už byly hotové).

1. Seskup `01-INBOX/slack/*.md` podle Thread TS (`**Thread TS:**` v body, fallback filename `_<ts>_vN.md`).
2. Pro každý thread vezmi **jen max `_vN`**. V těle hledáš `← AKTUÁLNÍ`.
3. Až na té aktuální verzi volej `evaluate_slack_inbox_relevance(..., stale_rels=…)`.
4. Helper: `stale_slack_rel_paths` / `stale_slack_rel_paths_from_items` v `triage_slack_relevance.py` (cron `triage_run.py` to už předává).

**Manuální triáž:** před návrhem tasku zavolej stejnou logiku — `evaluate_slack_inbox_relevance(rel, body, stale_rels=…)`. Nepředpokládej, že každý slack soubor = úkol. U ARCHIVE apply = jen přesun do `07-ARCHIV/inbox-processed/` (stejně jako `archive_only` u sent mailů).

**Ignorovat (přestat sledovat) — odděleně od ARCHIVE:**

- `archive_only` / `ZPRACOVÁNO` **nesmí** stáhnout vlákno z VPS watchlistu (`slack_poll` dál hledá nové odpovědi).
- Teprve když Lukáš v triáži řekne **ignoruj / nesleduj toto vlákno**, zavolej:

```bash
python3 scripts/slack_watch_ignore.py <channel_id> <thread_ts>
```

- `channel_id` / `thread_ts` z frontmatter dumpů (`channel_id:`, `thread_ts:`). U flat IM/MPIM je `thread_ts` = `0`.
- V preview tabulce měj akci **ignorovat (přestat sledovat)** jako samostatnou volbu, ne jako synonymum ARCHIVE.
- Vyžaduje Drive env (`VAULT_DRIVE_ID` + OAuth) — stejné jako jiné vault skripty.

Pending JSON může nést `slack_route`, `slack_source_kind`, `slack_relevance_reasons` — ukaž je v preview.

## Deep

Pro každou položku (přímo spuštěnou v DEEP módu **nebo** auto-routnutou z BATCH/PENDING):

### Meeting přepis (Sembly / Plaud) → `agenda-zapis-ze-schuzky`

**Kdy:** zdroj v `01-INBOX/sembly/`, **nebo** v `01-INBOX/daily/` se signály meeting přepisu
(Plaud/Sembly hlavička, seznam účastníků, dlouhý dialog). Slack / mail / Clippings sem **ne**.

1. **Deleguj celý DEEP** na skill `agenda-zapis-ze-schuzky` (načti jeho `SKILL.md`).
2. Výstupy: HTML `~/Downloads/…_zapis.html` + MD `05-RESOURCES/vystupy/zapisy/YYYY-MM/…_zapis.md`
   (+ wikilink stubs v `materials/` u jasných projektů). Default `variant: full`.
3. Tento zápis **nahrazuje** starý krátký DEEP materiál / `agenda-analyze` typ `schuzka`.
4. Z MD tabulky úkolů → Lukáš-only filter → preview tasků → apply → archiv zdroje
   (`archive_inbox_item.py`). Detaily a checklist ve skillu zápisu.
5. **Samonosný task (povinné):** při apply ze zápisu nestačí holý checkbox + `materials:`.
   Task musí nést **Z:** (wikilink na zápis), **Cíl**, **Kontext ze zápisu** (2–5 vět
   z karty / tabulky) a u nových kroků `→ *proč:* …; *DoD:* …`. Plné znění = skill
   `agenda-zapis-ze-schuzky` → Krok 8 „Samonosný kontext v tasku“.

### Ostatní DEEP zdroje

1. Read sourceFile naplno (ne jen prvních pár řádků).
2. Shrnutí 3–5 bullety: o čem to je, klíčové entity, decision points.
3. Návrh **více tasků** + případných **materiálů** + cross-linků (`materials: [[...]]`) — **při extrakci aplikuj Lukáš-only filter (viz níže)**.
4. Projdi s uživatelem po jednom: OK / uprav / přeskoč / drop.
5. Zápis task `.md` + materiál `.md` souborů; archiv source → `07-ARCHIV/inbox-processed/YYYY/MM/` přes `scripts/archive_inbox_item.py` (`.md` + co-located přílohy).

## Lukáš-only filter (vault je single-user)

Vault patří **jednomu uživateli (Lukáš)**. Tasky v `02-PROJEKTY/<slug>/tasks/` jsou **operativní akce, které Lukáš sám provede / drží míček**. Ne todo list pro celou firmu, ne sumář meetingu. Aplikuj **před** přípravou návrhů (krok 3 v Deep, BATCH extrakce, i v PENDING reviewu).

**Lukášův task = ano**, pokud:
- Lukáš je commitment owner ("já udělám", "musím", "připravím", "zavolám", "potvrdím", "domluvím", "rozhodnu")
- Lukáš je svolavatel / zodpovědný (i když exekuci deleguje — drží termín a follow-up)
- Strategický krok, kde Lukáš drží rozhodnutí

**Lukášův task = NE**, pokud:
- Akci dělá někdo jiný (Luboš připraví, Pavel implementuje, Slávek napíše, klient dodá)
- Je to volně zmíněná oblast bez konkrétního Lukášova kroku
- Je to názor / postoj v diskusi bez akce
- Jde o cizí projekt / téma, kde Lukáš jen poslouchal

**Hraniční (Waiting / sledovat)** — pokud Lukáš čeká na výstup od konkrétní osoby a chce to evidovat:
- Status: `Waiting`, `waitUntil: <date>`, title: `Sledovat: <kdo> dodá <co>`
- Pokud je to nepodstatné nebo informace bez follow-up, vynech.

**Cizí akce → kontext**, ne task:
- Patří do `## Poznámky / log` souvisejícího Lukášova tasku, nebo do `materials/` jako záznam meetingu, nebo do `## Otevřené otázky` projektu.
- NIKDY nevytvářej task soubor `<ID> — <Cizí osoba akce>.md`.

**Preview report konvence:**
- Pro každý nalezený signál uveď "**Drží míček:** Lukáš / Luboš / Pavel / …"
- Tasky s "Drží míček: Lukáš" → preview k apply.
- Ostatní → vlož do "Vyřazeno z preview (cizí míček)" sekce.
- User pak může explicitně říct "i tenhle uložit jako Waiting" — apply pouze po konfirmaci.

**Zmínka tasku v chatu (povinné):** vždy **`ID — title`** z frontmatter, ne samotné ID (`SBD4` bez názvu = špatně). Tabulky: sloupce ID + Název. Viz `.cursor/rules/task-mention-convention.mdc`.

## Agent (none / assist / solo) — gate před add_task

`agent` vyplň u každého návrhu. Není to dekorace.

| Hodnota | Kdo | Typicky |
|---------|-----|---------|
| `none` | Lukáš, agent nepomáhá | rozhodnutí, call, fyzická věc |
| `assist` | Lukáš + agent | draft, rozbor, příprava podkladů |
| `solo` | agent sám | lookup v Allfredu / Universe / Gmail / Drive, „sedí PE?“, „je faktura?“ |

**Drobná `solo` = otázka, ne task.** Bootstrap: taková práce se nezakládá jako task — záznam v `00-System/Agent-Log/YYYY-MM.md`.

Když je položka `solo` a jde o ověření / lookup / jednu odpověď (Slack „nevíš, jestli se to propsalo?“):

1. **Nezakládej** `add_task` s `## Operativní kroky` typu „ověřit X“ + „odepsat Y“.
2. V preview **jedna otázka:** „Tohle umím ověřit sám (Allfred / Universe / …). Řešit rovnou?“
3. `ano` → udělej v session, výsledek do Agent-Log + wikilink na projekt, zdroj `archive_only`. Task jen když je to větší nebo na to někdo čeká (pak slim, bez vymyšlených podkroků).
4. `ne` / později → `archive_only` + log, nebo Waiting jen když user chce evidenci.

Špatně (AF26, 31. 8.): Kamila — SLSP PE přes Work → task s **AF26-1 — ověřit PE** + **AF26-2 — odepsat** (`assist`).
Správně: „PE v Allfredu umím ověřit. Řešit rovnou?“

## PENDING (cron)

1. Načti nejnovější `00-System/Triage-Pending/*-batch.json`.
2. Rozděl proposals na **2 fronty**:
   - `simple_queue` — `requires_deep_analysis != true` (default BATCH apply route).
   - `deep_queue` — `requires_deep_analysis == true` (`kind: "deep"`, `proposalType: "deep_analysis"`).
3. Pokud `deep_queue` není prázdná, řekni uživateli:
   > Nalezeno N návrhů (M simple, K DEEP). Začneme DEEP, protože vyžadují víc pozornosti. Pokračovat? [yes/skip-deep/simple-only]
4. **DEEP fronta**: pro každý zdroj projet DEEP analysis flow s pre-loaded `sourceFile` z Pending JSONu. Po schválení DEEP zápisu:
   - Smazat ten proposal z Pending JSONu (CAS write s `expect_mtime`).
   - Přesunout zdroj do `07-ARCHIV/inbox-processed/YYYY/MM/`.
5. **Simple fronta**: stávající BATCH apply (per-proposal `proposalType`).
6. JSON v2 schema (každý návrh):

```json
{
  "proposalType": "add_task" | "update_task" | "archive_only" | "deep_analysis" | "add_person" | "update_person" | "area_log",
  "target_path": "02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md",
  "frontmatter": {
    "id": "RBU30",
    "type": "task",
    "title": "Titulek lidsky čitelný",
    "project": "[[RB Universe]]",
    "slug": "rb-universe-development",
    "aliases": ["RBU30"],
    "status": "Next",
    "ice_i": 7, "ice_c": 8, "ice_e": 5,
    "materials": ["[[some-material]]"],
    "source": "...",
    "deadline": null,
    "review_deadline": "2026-09-27",
    "waitUntil": null
  },
  "body": "...",
  "sourceFile": "01-INBOX/...",
  "archiveAfterApply": true,
  "confidence": 0.85,
  "notes": "...",
  "requires_deep_analysis": false,
  "deep_reasons": [],
  "needs_link": false
}
```

**`needs_link` (cron):** pokud návrh nemá `project:` + `materials:` pro DEEP zdroj, nastav `needs_link: true` a **neaplikuj automaticky** (stejně jako `deep_analysis`).

Body návrhu musí mít subtasky se prefixem `**<ID>-N**` v `## Operativní kroky`.
Když návrh vzniká ze **zápisu schůzky** (`vystupy/zapisy` / `agenda-zapis-ze-schuzky`),
tělo musí být **samonosné** (Z + Cíl + Kontext ze zápisu + *proč/DoD* u nových kroků) —
viz skill zápisu, Krok 8.

7. Ukaž změny podle `proposalType`. **Nikdy neaplikuj bez explicitního „ano" / „apply"**.
8. Po schválení:
   - `add_task` → vytvoř `target_path` se YAML frontmatterem + body.
   - `update_task` → patchne frontmatter + append do body (CAS-aware).
   - `archive_only` → přesun source.
   - `deep_analysis` → **nikdy se neaplikuje automaticky**; přepni do DEEP flow (krok 4) pro daný `sourceFile`.
   - **Archiv batch: oba soubory** — `*-batch.json` **a** `*-summary.md` se stejným prefixem (`YYYY-MM-DD-HHMM-`) přesunout z `00-System/Triage-Pending/` do `00-System/Triage-Applied/`. Nikdy nenech v Pending jen md bez JSONu (sirotek). Naming: pokud byl batch jen zavřen bez nového apply manifestu, použij sufix `-closed` (`*-batch-closed.json`, `*-summary-closed.md`).
   - **Sanity check**: po apply zkontroluj, že `Triage-Pending/` neobsahuje žádné `*.md` ani `*.json` se starším datem než dnešek (sirotci z předchozích triage).

## Hygiena tasků (RE-ID / přesun mezi projekty / přejmenování hubu)

Při jakékoli z těchto operací **vždy** projeď post-flight checklist, jinak nechá vault stale references a Obsidian při otevření hodí "nespecifikovanou chybu":

**1. Wikilinky v vault.** Hromadně updatni cesty / názvy:
- `[[02-PROJEKTY/<slug>/<file>]]` → nová cesta (např. po přesunu do `materials/` / `outputs/`)
- `[[<starý-id>]]` → `[[<nový-id>]]` po RE-ID (active i archived tasks)
- `project: '[[<starý hub>]]'` → `project: '[[<nový hub>]]'` po přejmenování hubu (frontmatter všech tasků v `02-PROJEKTY/<slug>/tasks/` i `07-ARCHIV/tasks-done/<slug>/`)
- `projects: ['[[<starý hub>]]']` v materials/outputs frontmatteru
- **POZOR na kolizi basename**: nový hub filename **nesmí kolidovat** s žádným souborem v `03-AREAS/` — viz [[00-System/Templates/wikilink-convention]] sekce "Pravidlo unikátnosti basename". Pokud kolize, přejmenuj area soubor s suffixem ` (oblast)` (např. `03-AREAS/Marketing (oblast).md`) a updatuj všechny `[[03-AREAS/Marketing]]` references na `[[03-AREAS/Marketing (oblast)]]`.

Použij Python skript s replace logikou (ne sed — kvůli diakritice a non-ASCII filenames).

**2. Bases `kanbanState`.** `00-System/Bases/All-tasks.base` má v `kanbanState.cardOrders.note.status.<column>:` ručně přetažené pořadí karet — list cest k task souborům. Po RE-ID / přesunu / smazání tasku tam zůstanou stale references na neexistující soubory. Když Obsidian rendruje kanban a klikne na stale link, hodí "nespecifikovanou chybu".

Fix: po každé migraci tasků (RE-ID, přesun, smazání) **smaž celý `kanbanState` blok** z `All-tasks.base`. Bases se vrátí na default order (`order:` + `sort:` config). Nový state si user postaví organicky přetahováním karet.

```yaml
# All-tasks.base — sekce ProjectKanban
- type: kanban
  name: ProjectKanban
  filters: ...
  groupBy: ...
  order: ...
  # ⬇ smaž tento blok kompletně:
  # kanbanState:
  #   cardOrders:
  #     note.status:
  #       Next:
  #         - 02-PROJEKTY/<starý>/<task>.md
  #         ...
```

**3. Hub frontmatter `aliases`.** Pokud přejmenováváš hub `<starý>.md` → `<nový>.md`, přidej `<starý>` do `aliases` v novém hubu — body wikilinky `[[<starý>]]` v ostatních souborech zůstanou funkční:

```yaml
aliases:
- <slug>
- <starý hub název>
- <nový hub název>
```

**4. Hub sekce `## Materiály` / `## Výstupy`.** Manuální seznamy odkazů aktualizuj na nové cesty / přesuň do správné sekce (materials vs. outputs).

**5. `agent-context.json`.** Přebuduj přes `python3 scripts/build_agent_context.py` (vault root).

**6. Final sanity grep.** Před uzavřením operace:

```bash
# žádné staré cesty / IDs ve frontmatteru ani body
grep -rl --include='*.md' --include='*.json' -F "[[<starý>]]" \
  02-PROJEKTY/ 07-ARCHIV/ 00-System/

# žádné stale refs v Bases
grep -F "kanbanState" 00-System/Bases/All-tasks.base
```

## Refresh dashboard + agent context

V2 — žádný cron build pro dashboard nepotřebuje. **Bases dashboard** (`OBSIDIAN/Dashboard.md`) čte přímo z task `.md` frontmatterů.

**Po každém zápisu** (apply triage batch / commit task changes):

1. (Volitelně) update `open_tasks_count` v hub `.md` frontmatteru pro každý dotčený slug
2. **Vždy spusť** `sync_lide_people` — wikilinky v nových/změněných souborech + rebuild tabulek `05-RESOURCES/lide/*.md`:

```bash
python3 scripts/sync_lide_people.py --incremental --paths "<vault-relative cesty oddělené středníkem ;>"
```

`--paths` = vše z batchi: nové/aktualizované tasky, materiály, archivované capture (`02-PROJEKTY/...`, `07-ARCHIV/inbox-processed/...`). Separátor je **středník** (`;`) — čárka v názvu souboru je OK. Přeskoč JSON/summary v `Triage-Pending/`.

3. **Vždy spusť** `python3 scripts/build_agent_context.py` (vault root) — refresh `00-System/agent-context.json` pro Cursor agenta
4. V chatu uveď výsledek: `tasks_created=N tasks_updated=M archived=K lide_sync: linkified=L profiles_rebuilt=P agent_context_refreshed=yes`

## Refresh Index

Po triage update `00-System/Index.md` — list aktivních projektů (Bases embed udělá většinu, manuální texty doplň pokud potřeba).

## Re-prioritizace

"Eisenhower přepočítej" → skill `agenda-priority-review` nebo projdi aktivní task soubory (po termínu, fokus tohoto týdne, Next top 3).

## Kontext před startem

- `00-System/Memory/about-me.md`
- `00-System/Index.md`
- `00-System/Templates/konvence-a-slovnik.md`
- `00-System/Templates/task-convention.md`

## Zrušení místo zavření

Když z inboxu vyplyne, že **existující** task už není potřeba — vyřešil ho nebo převzal někdo jiný,
rozhodnutí padlo jinak, věc se pohltila jiným úkolem — navrhni `status: Cancelled`, ne `Done`.

- Do logu tasku napiš **důvod a kdo to teď drží** (`řeší [[Dominik Holíček|Dominik]]`).
- `Done` znamená „udělal jsem to". Zrušené úkoly v „recently done" nafukují statistiku o práci,
  která se nestala.
- **Soubor nemaž.** Cron `archive_done_tasks.py` ho přesune do `07-ARCHIV/tasks-done/<slug>/`
  a ID tím zůstane obsazené — smazané ID by `next_task_id.py` přes `max+1` přidělil někomu jinému.
- Platí i pro přesun mezi projekty: nový ID v cíli, původní `Cancelled` s ukazatelem.
