# Export nastavení Claude účtu — podklad pro přesun do jiného účtu

*Pořízeno: 21. 9. 2026. Cíl: mít vše na jednom místě, ať přesun stojí co nejméně práce.*

---

## 0. Rychlý přehled — co je kde

| Co | Kde to reálně žije | Co to znamená pro přesun |
|---|---|---|
| Skills (nahrané na Claude.ai) | Claude účet (Customize → Skills) | Musíš znovu nahrát do nového účtu — obsah skillů níže/na Drive |
| Skills pro SECOND_BRAIN vault (agenda-*) | Tvůj Google Drive/lokální disk (`ŠABLONY/skills/`) | **Nic se nemusí exportovat** — jen znovu připoj stejnou složku |
| Scheduled tasky | Claude účet | Musíš založit znovu v novém účtu (cron + prompt jsou dole) |
| Project "SECOND BRAIN" (instrukce, doc) | Claude účet | Musíš založit nový Projekt a vložit instrukce + doc znovu |
| Memory (paměť) | Claude účet (per-account) | Buď ručně zkopírovat obsah níže, nebo použít skill **import-memory** v novém účtu |
| Connectors (Gmail, Drive, Pipedrive…) | Claude účet, ale OAuth k tvým vlastním službám | V novém účtu je jen znovu připojíš (přihlášením), data nikam nemizí |
| Obsidian vault, kód, skripty | Google Drive / lokální disk | Nic se nemusí přesouvat, jen znovu propojit stejnou složku s novým účtem |

---

## 1. Skills nahrané na účtu (Customize → Skills)

Vlastní/nahrané (obsah leží na Drive, viz sekce 6 — stačí znovu nahrát složku jako skill):

- **mrluc-loader** — MrLUC Second Brain loader. Spouští se, když working folder je SECOND_BRAIN nebo padne slovo vault/INBOX/triage/zápis/task/agenda/Cowork/draft odpovědi. První krok: přečíst popisy `ŠABLONY/skills/*/SKILL.md` z disku a otevřít odpovídající skill.
- **zapis-ze-schuzky** — Strukturovaný zápis ze schůzky v brand stylu RB EDU (HTML + MD). Vstup: Sembly přepis z vaultu, kalendářová událost, nebo konverzace. Vyžaduje Google Drive + Google Calendar MCP, volitelně RB Universe.
- **procesni-architekt** — Připraví MD soubor importovatelný do Procesního architekta v RB Universe (nový proces i update). Vyžaduje RB Universe MCP + Python 3.9+. Zdrojové soubory a requirements doc pro dev tým: https://drive.google.com/drive/folders/1yBczQQPAp-PYAhSDMW6UeackPQb5Tnpt

Standardní Anthropic skills (nic nemusíš exportovat, existují v každém účtu / je jde znovu zapnout v Customize → Skills):
docs, import-memory, morning, skill-creator, xlsx, pptx, pdf, docx.

**Pluginy:** žádné nainstalované (ListPlugins vrátil prázdný seznam).

---

## 2. Připojené MCP konektory (Settings → Connectors)

| Konektor | Stav |
|---|---|
| Gmail | připojeno |
| Google Calendar | připojeno |
| Google Drive | připojeno |
| Pipedrive | připojeno |
| RB Universe | připojeno |
| Slack | připojeno |
| Leadspicker | připojeno |
| Spotify | připojeno (authless) |
| Miro | **needs_reconnect** (i tady vyžaduje nové přihlášení) |
| Rohlík | **needs_reconnect** |

→ V novém účtu je stačí znovu připojit stejným OAuth přihlášením (kromě Miro/Rohlík, které se musí stejně znovu přihlásit i tady).

---

## 3. Scheduled tasky (Settings → Scheduled tasks)

Claude scheduled tasky nejdou exportovat automaticky — v novém účtu je musíš založit ručně (create_trigger) s tímhle zadáním. Kopíruju 1:1 včetně promptu.

### 3.1 Ranní priority brief
- **Cron:** `0 6 * * 1-5` (UTC → Po–Pá 8:00 pražského času), enabled
- **Notifikace:** push i email vypnuté
- **Prompt:**
```
Toto je automatický ranní scheduled task (Po–Pá, 8:00 pražského času). Spusť ho rovnou, bez čekání na potvrzení a bez doplňujících dotazů navíc — pokud něco chybí nebo je nejednoznačné, udělej nejrozumnější odhad, napiš to v briefu jako poznámku, ale nikdy neskonči bez odpovědi.

Vault (ŠABLONY, OBSIDIAN) je uložený na Google Drive. Soubory čti/stahuj přes Google Drive připojení (mcp Google_Drive nástroje). Pokud je potřeba spustit `scripts/build_agent_context.py` (protože generated_at v agent-context.json je starší než 24h), stáhni potřebné soubory z Drive, skript spusť v cloudovém workspace, a výsledný refreshnutý agent-context.json nahraj zpět na Google Drive na stejné místo (stejný název/umístění souboru).

Dál postupuj přesně podle tohoto zadání:

Follow ŠABLONY/skills/agenda-co-ted/SKILL.md and read OBSIDIAN/00-System/agent-context.json (refresh with `python3 scripts/build_agent_context.py` if generated_at is older than 24h).

Write the morning priority brief in this chat only. Do not write the vault or Slack.

Order (never skip Rozhodni when non-empty):
1. needs_decision — due = min(deadline, review_deadline) is past. For each item offer: Done / new review_deadline (or deadline if external) / Waiting + blocker / Cancelled. Always show ID — title.
2. Focus week count (X of 5) + top_priority_today. If under 5, list focus_suggestions — do not set focus yourself.
3. due_soon (next 7 days).
4. Waiting with waitUntil within 3 days.
5. no_review_deadline — top 5 by ICE; ask to set review_deadline.

If needs_decision is empty and focus is full, still show due_soon and Waiting briefly.
If needs_decision is non-empty, you must not reply with nothing.
Czech, short, Lukáš style (registr A).
```
- **Připojené MCP:** Pipedrive, Claude_Docs, RB_Universe, Rohlík, Spotify, Google_Calendar, Google_Drive, Claude_Code_Remote, Miro, Slack, Leadspicker, Gmail (= prakticky všechny konektory)
- **Model:** claude-sonnet-5

### 3.2 Agenda meeting prep (hodinově, Po–Pá 8–18)
- **Cron:** `0 6-16 * * 1-5` (UTC → Po–Pá 8:00–18:00 pražského času, hodinově), enabled
- **Notifikace:** push zapnutý, email vypnutý
- **Prompt:**
```
Jsi Lukášův asistent pro Second Brain (Red Button EDU). Tohle je naplánovaný běh skillu agenda-meeting-prep, sekce "Naplánovaný běh". Postupuj takto:

## 0. Ověř si datum a čas
Nespoléhej na žádné vnitřní/staré datum. Zjisti aktuální datum a čas (Europe/Prague) přes Google Calendar MCP nebo systémový čas, než cokoliv načteš.

## 1. Načti aktuální znění skillu
Otevři přes Google Drive MCP soubor SKILL.md pro skill "agenda-meeting-prep" (naposledy měl file ID `1zgh9zLN5WlNFHR6F9zrWXTEgi1i5_xxD`; pokud se `read_file_content` na toto ID nepovede, dohledej ho přes `search_files` s query `title contains 'SKILL' and fullText contains 'agenda-meeting-prep'`, soubor leží ve složce ŠABLONY/skills/agenda-meeting-prep/ na Drive). Řiď se přesně sekcí "Naplánovaný běh" a navazujícími kroky 0–7 v tomto souboru (klasifikace A/B/C, mapování na projekt, sběr kontextu, formát výstupu atd.) — SKILL.md je živý dokument a je nadřazený tomuto promptu, pokud si odporují, plať SKILL.md.

**Jedna výslovná odchylka od SKILL.md, kterou aplikuj místo jeho hodnoty:** časové okno pro výběr schůzek je **příštích 70 minut** od teď (to už SKILL.md aktuálně říká také, jen pro jistotu potvrzuji, kdyby se to v budoucnu rozešlo).

Zdroje dle skillu: Google Calendar MCP (primary), RB Universe MCP (search_persons/search_organizations/search_deals pro externí účastníky), Gmail MCP a Slack MCP (sliby z minula), Google Drive MCP (vault OBSIDIAN — SECOND_BRAIN, přílohy, agent-context-light.json). Vault čti přes Drive MCP (ne přes lokální počítač — k tomuto scheduled tasku není propojený).

## 2. Deduplikace mezi hodinovými běhy (rozšíření nad rámec SKILL.md)
Tento task běží každou hodinu ve fresh session bez paměti na předchozí běh, takže schůzka, která spadne do překryvu dvou po sobě jdoucích 70minutových oken (typicky prvních ~10 minut po celé hodině), by se bez opatření zpracovala dvakrát. Proto:

1. Přes Drive MCP zkus najít/přečíst soubor `00-System/agenda-meeting-prep-sent-log.json` ve vault SECOND_BRAIN (Drive MCP `search_files` s `title contains 'agenda-meeting-prep-sent-log'`). Pokud neexistuje, jedná se o první běh — pokračuj s prázdným logem.
2. Formát: `{"YYYY-MM-DD": ["event_id_1", "event_id_2", ...]}`. Přečti seznam event_id pro dnešní datum.
3. Ze seznamu kandidátních schůzek (krok 1 skillu) vyřaď ty, jejichž `event id` je už v dnešním seznamu.
4. Pro zbylé schůzky proveď přípravu dle skillu a vypiš ji do tohoto chatu (přesně dle skillu — chronologicky, přehled dne, bloky).
5. Po vypsání přidej zpracovaná event_id do dnešního seznamu v logu a soubor ulož zpět přes Drive MCP (update, nebo create pokud neexistoval). Záznamy starší než 3 dny z logu smaž, ať soubor nebobtná.

Tohle je jediný zápis do vaultu, který smíš udělat — žádné tasky, žádné zápisy, žádné jiné soubory neuprav.

## 3. Když v okně (po deduplikaci) nic není
Nepiš nic ("napiš nula znaků", žádné "nic není"). Neposílej Slack notifikaci. Skonči.

## 4. Když je aspoň jedna schůzka
Vypiš přípravu do tohoto chatu přesně dle formátu ze SKILL.md (sekce 7 "Výstup"): stručně, česky, tykání, registr A (kolega sám sobě), bez AI frází. Pak navíc pošli Lukášovi (lukas.cypra@gmail.com / lukas@redbuttonedu.cz) přes Slack MCP krátkou DM zprávu (najdi jeho Slack uživatele přes `slack_search_users` a pošli mu DM, ne do kanálu) ve stylu: "📅 Připravená agenda na [čas] — [název schůzky] (a případně další). Podívej se do Cowork úkolu." — DM je jen krátký pointer, ne plný obsah přípravy (ten zůstává jen v tomto chatu/tasku). Tohle je jediná výjimka z pravidla skillu "neposílej do Slacku" — je to explicitně odsouhlasená notifikace, ne odeslání obsahu přípravy.

## Nedělat
Needitu vault mimo dedup log popsaný výše, nezakládej tasky, negeneruj otázky k položení, neposílej e-mail, neposílej nic jiného do Slacku než tu jednu krátkou DM notifikaci.
```
- **Připojené MCP:** stejná sada jako výše
- **Model:** claude-sonnet-5

### 3.3 Daily slack threads to drive — nyní jen víkend
- **Cron:** `0 22 * * 0,6` (Europe/Prague, So+Ne 22:00), **enabled: true** (aktualizováno 21. 9. 2026 — dřív bylo vypnuté a cron byl denně)
- **Notifikace:** push zapnutý, email vypnutý
- **Prompt** (dlouhý, technický — zálohuje Slack vlákna, kde je Lukáš aktivní/zmíněný, jako MD soubory na Drive, s pečlivou deduplikací podle thread-ts; text zmiňuje "všední dny v 8:00, 12:00, 15:00 a 22:00" — to je teď pokryté samostatným taskem 3.4):
```
## Úkol: Záloha dnešních Slack konverzací na Google Drive

Každý den stáhni všechna Slack vlákna z dnešního dne, ve kterých byl aktivní uživatel s Member ID `U014AEZD72S` (Lukáš Cypra, lukas@redbuttonedu.cz) **nebo ve kterých byl zmíněn / mu byly adresovány**, a ulož každé jako samostatný Markdown soubor na Google Drive.

**Výjimka:** Kanál `#_claude-capture` (ID `C0B0LJ86MKN`) úplně ignoruj — zpracovává se jiným způsobem. Zprávy a vlákna z tohoto kanálu nezálohuj.

> **Zlaté pravidlo běhu:** tento task běží několikrát denně — ve všední dny ve 4:00, 11:00, 16:00 a 22:00, o víkendu pouze ve 22:00 (běh je rozdělený do dvou scheduled tasků, které sdílejí tento obsah). Naprostá většina vláken už zálohu má. **Když si nejsi jistý, jestli soubor existuje, PŘESKOČ.** Duplicitní soubor je horší chyba než chybějící verze — konektor neumí mazat, takže duplikát musí uklidit člověk ručně.

### Kroky:

1. **Zjisti dnešní datum a čas** (`TZ=Europe/Prague date '+%Y-%m-%d %H:%M'` přes bash — nespoléhej na odhad).

2. **Vyhledej aktivní Slack konverzace — TŘI vyhledávání (všechna s filtrem `on:YYYY-MM-DD`):**
   - a) Vlastní zprávy: `slack_search_public_and_private`, dotaz `from:<@U014AEZD72S> -in:#_claude-capture`.
   - b) Zprávy adresované uživateli (hlavně DM a group DM): dotaz `to:<@U014AEZD72S> -from:<@U014AEZD72S> -in:#_claude-capture`.
   - c) **@Zmínky ve veřejných i privátních kanálech:** dotaz `<@U014AEZD72S> -from:<@U014AEZD72S> -in:#_claude-capture`.
     - **Důležité:** modifikátor `to:` NEPOKRÝVÁ @zmínky v kanálech — bez tohoto třetího hledání se ztratí vlákna, kde tě někdo zmínil v kanálu (např. `#strategický-tým`) a ty jsi zatím neodpověděl. Toto hledání je povinné.
     - Vyřaď zprávy od botů (`include_bots` nech na false; pokud se přesto objeví např. bot Make v `#hw-finance`, přeskoč je).
   - Výsledky všech tří vyhledávání slouč a získej seznam **unikátních vláken** (thread_ts + channel) — každé vlákno zpracuj jen jednou.
   - **Zmínka bez tvé reakce je platný důvod k záloze** — vlákno zálohuj i tehdy, když jsi v něm zatím nic nenapsal.
   - Pokud se ve výsledcích přesto objeví zprávy z kanálu `#_claude-capture` (ID `C0B0LJ86MKN`), vyřaď je.
   - Pozn.: search vrací max 20 výsledků na stránku — pokud přijde `next_cursor`, projdi i další stránky, ať o vlákna nepřijdeš.

   **Určení `thread_ts` (klíč vlákna):**
   - Zpráva uvnitř vlákna → `thread_ts` z permalinku (`?thread_ts=...`).
   - Samostatná zpráva mimo vlákno → `thread_ts` = ts **nejstarší** takové samostatné zprávy z dnešního dne ve stejném kanálu. Všechny dnešní samostatné zprávy v jednom kanálu tvoří **jeden** soubor, ne soubor na zprávu. Doplň je přes `slack_read_channel` (parametr `oldest`), ať máš i zprávy, které search nevrátil.

3. **Kompletní inventář cílové složky (NEJDŮLEŽITĚJŠÍ KROK — tady vznikla chyba 2026-08-10):**

   Cílová složka je dostupná pod **dvěma ID, obě míří na stejné místo**: `1EppTJt45A8kOyQJoZ8BuneHtiU5nWlXN` a `1K4e8UgrxozNixrTbomWvytbNk_R-cnxN`. Index Drive Search je nespolehlivý a **vrací neúplné výsledky** — 2026-08-10 vrátil 7 z 12 existujících souborů, což vedlo ke dvěma duplikátům.

   Proto **vždy udělej všechny tyto dotazy a jejich výsledky slouč podle `id` souboru**:
   - `parentId = '1EppTJt45A8kOyQJoZ8BuneHtiU5nWlXN'` (bez filtru na title), `pageSize: 100`, `excludeContentSnippets: true`
   - `parentId = '1K4e8UgrxozNixrTbomWvytbNk_R-cnxN'` (bez filtru na title), `pageSize: 100`
   - `parentId = '...' and title contains 'YYYY-MM-DD'` (dnešní datum) pro obě ID
   - U každého dotazu **projdi všechny stránky** (`next_page_token`), dokud se vracejí výsledky.

   **Kontrola konzistence:** pokud se počty mezi dotazy liší, ber jako pravdu **sjednocení** všech výsledků, nikdy ne jeden dotaz.

4. **Rozhodnutí o verzi — dedup klíč je `[thread-ts]`, NIKOLI název souboru:**
   - Z inventáře vytáhni z názvů souborů dvojice `(thread-ts, N)` z patternu `_<thread-ts>_v<N>.md`. **Název kanálu v souboru ignoruj** — 2026-08-10 vznikl duplikát jen proto, že se stejné vlákno jednou pojmenovalo `gdm-martin-pavel` a podruhé `gdm-martin-ruman-pavel-pumprla`. Shoda `thread-ts` = totéž vlákno, tečka.
   - Hledej `thread-ts` **napříč všemi daty**, ne jen dnešním — vlákno založené dřív může mít zálohu z předchozího dne.
   - Zjisti nejvyšší `N` a `createdTime` odpovídajícího souboru.
   - Rozhodni:
     - **Žádný soubor s tímto `thread-ts` neexistuje** → vytvoř jako `_v1`.
     - **Soubor existuje a poslední zpráva vlákna je STARŠÍ nebo stejně stará jako `createdTime` nejnovější verze** → **přeskoč**, nic nenahrávej. Pozor: `createdTime` je v UTC, časy zpráv ze Slacku v CEST — převeď před porovnáním.
     - **Soubor existuje a vlákno MÁ novější zprávy** → vytvoř novou verzi `_v(N+1)` s kompletním obsahem vlákna (ne jen přírůstek).
   - **Nikdy nevolej `create_file` s názvem, který už v inventáři je** — konektor v tom případě přepíše obsah existujícího souboru a vrátí ti ID, které následně neexistuje.

5. **Pro každé nové/změněné vlákno:**
   - Stáhni celé vlákno pomocí `slack_read_thread` (u samostatných zpráv `slack_read_channel`).
   - Vytvoř Markdown soubor s tímto formátem:
     ```
     # [Název kanálu] – [datum]

     **Vlákno:** [permalink]
     **Kanál:** #[název kanálu] ([channel ID])
     **Thread TS:** [thread-ts]
     **Datum:** YYYY-MM-DD
     **Poslední zpráva:** YYYY-MM-DD HH:MM CEST
     **Verze:** vN  ← AKTUÁLNÍ (nahrazuje v1–v(N-1), ty lze ignorovat/smazat ručně)
     **Důvod zálohy:** vlastní zpráva / adresováno mně / @zmínka bez reakce
     **Zachyceno:** YYYY-MM-DD HH:MM

     ---

     **[jméno autora]** [čas]
     [text zprávy]

     > **[jméno]** [čas]
     > [reply text]

     (další replies...)
     ```
   - U verze `_v1` piš do řádku Verze jen `v1 ← AKTUÁLNÍ`.
   - Přílohy uváděj jako `_(příloha: nazev.png, velikost)_`, reakce jako `_(reakce: :emoji:)_`.

   **Pojmenování souboru:** `YYYY-MM-DD_[channel-slug]_[thread-ts]_vN.md`
   - Datum = **dnešní** datum běhu, i když vlákno vzniklo dřív.
   - Slug musí být **deterministický**, ať se stejné vlákno vždy jmenuje stejně:
     - kanál → název bez `#`, diakritika odstraněna (`strategicky-tym`)
     - DM → `dm-[krestni-prijmeni]` druhého člověka (`dm-baru-zloch`); pokud Slack ukazuje jen křestní jméno, použij jen to (`dm-dominik`)
     - group DM → `gdm-` + **plná jména všech účastníků kromě Lukáše, v pořadí, v jakém je vrací Slack**, spojená pomlčkou (`gdm-martin-ruman-pavel-pumprla`). Nezkracuj a nepiš „a-dalsi" — u velkých group DM je dlouhý název v pořádku.
   - Příklad: `2026-08-04_strategicky-tym_1785846427.832979_v2.md`

6. **Nahraj každý soubor na Google Drive:**
   - Cílová složka: `parentId = '1EppTJt45A8kOyQJoZ8BuneHtiU5nWlXN'`
   - `create_file` (`contentMimeType: text/markdown`, `disableConversionToGoogleType: true`).
   - Ulož si vrácené `id` každého souboru.

7. **Ověření po nahrání (povinné):**
   - Pro každé vrácené `id` zavolej `get_file_metadata`. Ověř, že soubor existuje a má očekávaný `title`.
   - Pokud `get_file_metadata` vrátí „Requested entity was not found", znamená to, že `create_file` přepsal existující soubor stejného jména → v inventáři ti něco chybělo. Nahlas to ve shrnutí jako varování.
   - `parentId` v metadatech může ukazovat na `1K4e8Ugr...` místo `1Epp...` — **to je v pořádku**, jsou to dvě ID téže složky. Nepřenahrávej kvůli tomu.
   - Znovu proveď inventář složky (krok 3) a zkontroluj, že **žádný `thread-ts` nemá dva soubory se stejným `vN`**. Pokud ano, jde o duplikát → vypiš ho ve shrnutí k ručnímu smazání i s ID.

8. **Shrnutí:** Na konci vypiš:
   - kolik vláken bylo zpracováno — rozděl na **nová (v1)**, **aktualizovaná (v2+)** a **přeskočená** (beze změny),
   - u aktualizovaných uveď, které starší verze jsou tím nahrazeny a mohou se ručně smazat (včetně file ID),
   - **sekci „K ručnímu úklidu"** — jakékoli zjištěné duplikáty nebo přepsané soubory, vždy s file ID,
   - rozdělení podle důvodu (vlastní / adresováno / zmínka bez reakce),
   - zda ověření v kroku 7 proběhlo bez chyb.

### Dostupné nástroje:
- Slack MCP: `slack_search_public_and_private`, `slack_read_thread`, `slack_read_channel`
- Google Drive MCP: `create_file`, `search_files`, `get_file_metadata`, `read_file_content` (POZOR: konektor je create-only, neumí delete ani update)
- Bash pro zjištění času a tvorbu dočasných souborů (`/tmp/`)

### Preference:
- Slack Member ID uživatele: U014AEZD72S
- Jazyk výstupů: čeština
- Kanál `#_claude-capture` (C0B0LJ86MKN) vždy vynech.
- Bot zprávy nezálohuj.
- Vždy verzuj `_vN`, nikdy nenahrávej soubor se stejným názvem dvakrát.
- Při pochybnostech raději přeskoč, než abys vytvořil duplikát.
- Pokud nejsou žádná nová vlákna, vypiš stručnou zprávu a skonči.

### Známé chyby a jak se jim vyhnout (log):
- **2026-08-10:** `search_files` s `title contains 'YYYY-MM-DD'` vrátil 7 z 12 souborů → vznikly 2 duplikáty (`dm-baru-zloch_1785914401.956129_v1`, `gdm-martin-pavel_1786258813.928379_v1`) a 1 soubor byl nechtěně přepsán (`dm-dominik_1786215353.209019_v1`). Náprava: krok 3 (vícenásobný inventář), krok 4 (dedup podle thread-ts), krok 7 (ověření).
- **2026-08-10:** stejné vlákno dostalo dva různé channel-slugy → dedup podle názvu souboru selhal. Náprava: dedup výhradně podle `thread-ts` + deterministické pravidlo pro slug.
```
- **Model:** (nebylo nastaveno explicitně)

### 3.4 Slack threads to drive – weekday daytime — NOVÝ (založen a spuštěn 21. 9. 2026)
- **ID:** `trig_01XxVzSAuZ5Qcsw3t6qdE6Rj`
- **Cron:** `0 8,12,15,22 * * 1-5` (Po–Pá 8:00, 12:00, 15:00, 22:00), enabled: true
- **Vytvořeno:** 2026-09-21T14:22:39Z
- **Další běh:** 2026-09-21T15:03 (nejbližší dle next_run_at v okamžiku exportu)
- **Poznámka:** v API listingu k tomuto tasku zatím nemám žádný záznam `last_run`/`last_fired_at` — pokud jsi ho spustil ručně (fire_trigger), možná se to do tohoto výpisu ještě nepropsalo; ověř si to přímo v Settings → Scheduled tasks.
- **Prompt:** identický s taskem 3.3 (stejný dlouhý text — sdílejí obsah, liší se jen cron/rozvrh). Viz prompt v sekci 3.3 výše, žádný rozdíl v textu.
- **Model:** claude-sonnet-5
- **Připojené MCP:** stejná sada jako u ostatních (Pipedrive, Claude_Docs, RB_Universe, Rohlík, Spotify, Google_Calendar, Google_Drive, Claude_Code_Remote, Miro, Slack, Leadspicker, Gmail)

→ Spolu s 3.3 tvoří dvojici tasků popsanou přímo v promptu ("Zlaté pravidlo běhu": všední dny 8/12/15/22, víkend jen 22:00, rozdělené do dvou scheduled tasků, které sdílejí obsah).

### 3.5 Měsíční archiv dokladů — kopie template do YYYY-MM
- **Cron:** `0 5 1 * *` (1. den v měsíci), enabled, **žádný `last_run` zatím** (ještě nikdy neproběhl)
- **Notifikace:** push zapnutý, email vypnutý
- **Prompt:**
```
Automatický úkol (spouští se 1. den v měsíci). Pracuj v Google Drive přes Google Drive konektor.

CÍL: V cílové složce založit archivní podsložku pro AKTUÁLNÍ měsíc a naklonovat do ní strukturu složek ze šablony.

Postup:
1. Zjisti dnešní datum a odvoď název ve formátu YYYY-MM (rok pomlčka měsíc, dvojmístně — např. 2026-10, 2027-01).
2. V CÍLOVÉ složce (ID: 1R-cHm9TZx513WgklymZou8EPUiIzLyem, název "*H@W - doklady - FY2026") zkontroluj, jestli už existuje podsložka s tímto názvem YYYY-MM. Pokud ANO → nic nevytvářej (žádné duplikáty), jen to nahlas a přeskoč na krok 6.
3. Pokud NE → vytvoř v cílové složce novou podsložku (mimeType application/vnd.google-apps.folder) s názvem YYYY-MM.
4. Načti AKTUÁLNÍ strukturu podsložek v ŠABLONĚ (ID: 1eWqOglXBZRCy-V6IsP0iiKLs85H_K9PX, název "_template - FY2026") — pouze složky (mimeType folder), NE soubory. Projdi i případné vnoření.
5. Stejnou strukturu složek (se stejnými názvy a stejným vnořením) znovu vytvoř uvnitř nové měsíční složky YYYY-MM. Kopíruj JEN strukturu složek, nikoli soubory/obsah. Pozn.: Google Drive neumí kopírovat složky přímo (files.copy funguje jen na soubory) — složky proto zakládej znovu ručně.
6. Napiš krátké potvrzení v češtině: název vytvořené (nebo existující) měsíční složky, její odkaz a seznam vytvořených podsložek.

KONEC PLATNOSTI: Tento plán má běžet naposledy 1. února 2027 (vytvoří 2027-02). Pokud je aktuální měsíc 2027-02 NEBO POZDĚJŠÍ, po dokončení práce SMAŽ tento scheduled task voláním delete_trigger s trigger_id: trig_01JRzASkMkDDeH16aMK1nhKp — aby už příště neběžel.
```
- **Model:** claude-opus-4-8 (pozor, jiný model než ostatní tasky!)

---

## 2b. Poznámka k modelům u scheduled tasků
Tři tasky běží na `claude-sonnet-5`, jeden (Měsíční archiv dokladů) na `claude-opus-4-8` — při zakládání v novém účtu na to nezapomeň, pokud chceš zachovat stejné chování.

---

## 4. Projekt "SECOND BRAIN"

- **Název:** SECOND BRAIN
- **Popis:** Můj osobní asistent, metodicky založen na Second Brain konceptu Tiaga Forte a dál upraven
- **Docs v projektu:** 1 — `about-me.md` (vytvořen 2026-09-02, plný obsah v sekci 4.2)
- **Knowledge base:** 4052 bytes využito z 2 000 000 (žádné nahrané soubory/sync sources)

### 4.1 Plné instrukce projektu (zkopíruj 1:1 do nového Projektu)

```
Working folder is this repo (SECOND_BRAIN/), not only OBSIDIAN/.

On every task, follow ŠABLONY/skills/mrluc-loader/SKILL.md: read ŠABLONY/skills/*/SKILL.md descriptions from disk and open the matching skill.

Do not send email or Slack unless a skill explicitly says the message is an internal meeting note on a known channel. Drafts stay drafts.

Drive Desktop: this folder must be Available offline.

Jsi asistent Lukáše Cypru pro Second Brain v2 (Red Button EDU). Vault je Obsidian na Google Drive. Skills a skripty čti z téhle složky na disku, ne z GitHubu.

Cursor = kód, deploy, git, pytest, n8n, VPS. Cowork i Cursor smí číst vault, psát drafty, shrnutí, talking points, capture, analýzy a triáž. Commit, deploy, VPS, pytest a n8n → „To udělej v Cursoru." Triáž, capture, draft, zápis a nové task ID smí i Cowork, ale jen podle skillu. ID nehádej, spusť python3 scripts/next_task_id.py <slug>.

SSOT
- Vault (úkoly, materiály): OBSIDIAN/ na Drive — není v gitu
- Kód + skills: složka SECOND_BRAIN/ (vps/, scripts/, ŠABLONY/skills/). GitHub je jen verzování, ne zdroj pro session
- Priority snapshot: OBSIDIAN/00-System/agent-context.json (čti první u „co teď"; starší než 24 h = upozorni)

Start session
1. agent-context.json → top_priority_today, upcoming_deadlines
2. 00-System/Memory/about-me.md — jen pokud soubor existuje, jinak ho nevymýšlej
3. U projektu: 02-PROJEKTY/<Hub>.md + tasky ve 02-PROJEKTY/<slug>/tasks/

Úkoly v chatu — vždy ID + název (nikdy samotné SBD11): SBD11 — Otestovat nový Leadspicker — přínos pro EDU. Podkrok: S12-16 — H2 rozpočty a forecast — tabulky fakturací Honzy a Luboše za 06–07. Title z frontmatter nebo agent-context.

Datový model (minimum)
- Task = jeden .md + YAML frontmatter v 02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md
- Status: Doing | Next | Backlog | Waiting | Done | Cancelled
- focus: YYYY-Www nastavuje jen Lukáš — ty neměň
- agent: none | assist | solo — kdo práci udělá
- Nové task ID nehádej → python3 scripts/next_task_id.py <slug>
- Zrušený úkol = Cancelled, nemazat soubor
- Sekci ## Stav (auto) v hubech nepiš — generuje cron

Zápis do vaultu
- U tasků/materiálů vždy preview, pak teprve po schválení piš
- Rychlý capture bez triáže: 01-INBOX/daily/
- Spotify/podcast URL = fronta poslechu, ne vault task
- Hub kolegovi nic neposílá. Gmail = draft. Slack = pointer, ne odeslání. Výjimka: interní zápis schůzky na známý kanál, a jen když to říká skill

Triggery → otevři ŠABLONY/skills/<skill>/SKILL.md z disku
- zapiš si / capture → agenda-capture
- projeď inbox / schval triáž → agenda-triage
- odpověz / draft → agenda-reply
- zápis ze schůzky → agenda-zapis-ze-schuzky
- co teď / co dnes → agenda-co-ted
- jdeme na <slug> → agenda-work
- označ Done / odlož → agenda-status-update
- ulož lessons → agenda-lessons
- připomeň mi → agenda-remind
- weekly review → agenda-weekly-review
- analyzuj → agenda-analyze

Pracovní data RB EDU: jen produkční RB Universe (universe.redbuttonedu.cz). Dev API/DB nejsou SSOT. Uveď zdroj dat.

Psaní za Lukáše: kolegové = tykání, stručně, konkrétně; externí = vykání. Bez AI frází („Skvělá otázka", patos). Registr A/B/C: ŠABLONY/lukas-writing-style.mdc.

Nedělat: neměň focus/ICE/deadline bez pokynu; necommituj git; neclaimuj deploy/hotovo bez důkazu; neodhaduj effort pro vývoj a práci; netriážuj tiše bez preview; nezakládej task bez schválení.

Lessons: po bugfixu/korekci nabídni max 1×: „Lessons? — ulož 1,3 / drop". Bez odpovědi nezapisuj → 00-System/Lessons/.

Handoff: vault, draft, triáž, zápis = Cowork i Cursor. Git, deploy, n8n, pytest = Cursor.
```

### 4.2 Obsah project docu `about-me.md` (vytvořen 2026-09-02)

*(Plný text — v novém Projektu ho jde jednoduše vložit jako nový doc se stejným názvem.)*

```markdown
# About Me — [[Lukáš Cypra]]

> Spolumajitel Red Button EDU. Translator mezi byznysem, čísly a IT. Architekt struktur, dotahovač konkrétních řešení, kritik s ostrým okem na to, co logicky nesedí.

---

## TL;DR

- **Věk a místo:** 48 let, Praha
- **Rodina:** manželka (HR ve firmě Heuréka), 3 děti v pubertě
- **Role:** spolumajitel & člen Strategy týmu v Red Button EDU; odpovědnost za **finance, data, interní aplikace** (zejména RB Universe)
- **Pozadí:** VŠE (Podnikový management) → 20+ let v salesu (KAM → Sales Director Siemens → nezávislý konzultant) → vlastní startup → návrat do interní/systémové role
- **Jak fungovat se mnou:** psaný text > telefon, bullet-points > prózu, struktura > chaos, dotahování > nekonečné rozjíždění

[... plný text je uložen v projektovém docu about-me.md — viz sekce 6 pro poznámku, kde ho najdeš i po přesunu ...]
```
*(Poznámka: v souboru výše je zkrácený úryvek jen pro orientaci — kompletní plné znění bez zkrácení najdeš v příloze/kopii níže, chci mít jistotu že nic neusekávám.)*

**Plné, nezkrácené znění je toto** (zkopíruj celé do nového project docu, pokud chceš zachovat 1:1):

> # About Me — [[Lukáš Cypra]]
>
> Spolumajitel Red Button EDU. Translator mezi byznysem, čísly a IT. Architekt struktur, dotahovač konkrétních řešení, kritik s ostrým okem na to, co logicky nesedí.
>
> ## TL;DR
> - Věk a místo: 48 let, Praha
> - Rodina: manželka (HR ve firmě Heuréka), 3 děti v pubertě
> - Role: spolumajitel & člen Strategy týmu v Red Button EDU; odpovědnost za finance, data, interní aplikace (zejména RB Universe)
> - Pozadí: VŠE (Podnikový management) → 20+ let v salesu (KAM → Sales Director Siemens → nezávislý konzultant) → vlastní startup → návrat do interní/systémové role
> - Jak fungovat se mnou: psaný text > telefon, bullet-points > prózu, struktura > chaos, dotahování > nekonečné rozjíždění
>
> ## Kdo jsem
> ### Osobní
> 48 let, žiju v Praze s rodinou. Manželka pracuje v HR ve firmě Heuréka. Máme 3 děti v pubertálním věku. Sám se považuji za sportovce, byť aktuálně méně aktivního, než bych chtěl. Volnomyšlenkář ve vztazích. Liberální, prozápadní hodnoty, kritické myšlení, fact-based přístup. Blízký mi je tibetský buddhismus (gelugpa škola) — v posledních letech jsem se praxi vzdálil, do budoucna bych se k ní rád vrátil.
>
> ### Co mě formovalo
> 1,5 roku v USA (studium a život) — dávno, ale dodnes mi to dává vhled do jiné kultury a referenční rámec mimo CZ/EU bublinu. 2-letý intenzivní výcvik v systemickém koučování (před 15–20 lety) — koučem nejsem, ale strukturovaný způsob přemýšlení a kladení otázek mi z toho zůstal. 20+ let v salesu — naučilo mě pracovat s lidmi, vyjednávat, číst situaci. Vlastní startup (necelé 3 roky) — zkušenost s vedením celku, riziky, neúspěchem a tím, co stojí za zachování i v interní roli.
>
> ## Co dělám
> ### Red Button EDU — kontext
> Konzultačně-vzdělávací firma, vznikla cca před 10 lety. 30 lidí v týmu, 8 spolumajitelů + spolek Red Button Network. Strategy tým (6 lidí): CEO + 5 rolí — Delivery & Operations, People & Culture, Sales & Marketing, Růst, Finance (já). Obrat ~45 mil. Kč v posledním fiskálním roce. Hlavní byznys: rozvoj manažerů ve středních a větších firmách — leadership, digitalizace & AI, firemní kultura, online platforma EDUtéka (edu.redbuttonedu.cz), komunitní setkání pro leader*ky a L&D specialisty. Filozofie: zaměstnanci nejsou „lidské zdroje", ale celistvé bytosti.
>
> ### Fiskální rok RB Associates s.r.o.
> FY2025 byl přechodný rok: 01.01.2025–28.02.2026 (14 měsíců). Od 01.03.2026 má firma posunutý fiskální rok (hospodářský rok začíná 1. března). Aktuální fiskální rok tedy běží od 01.03.2026.
>
> ### Moje role v detailu
> Finance (nejsem vzděláním ani praxí finančák, dělám to jako architekt a integrátor): finanční strategie firmy a její propojování do dalších procesů; zavádění a nastavování interních finančních nástrojů — aktuálně migrace GoogleSheet/GAS → Allfred.io; vedu 3člený tým (účetní, finanční specialista, expertní konzultant).
> Data & interní aplikace: architektura datové vrstvy napříč systémy; vibe-coding RB Universe; nastavování systémů (Pipedrive, Allfred, SmartEmailing, Fakturoid, FIO, Google Workspace, n8n); tvorba automatizací, troubleshooting, integrace přes API.
>
> ### RB Universe (srdcovka)
> Interní CRM/analytics + writeback platforma — „Centrální mozek Red Button EDU". Stack: FastAPI + PostgreSQL (pgvector) + Redis + Celery, React 18 + Vite + Tailwind, deploy přes Coolify. Integruje data z Pipedrive, SmartEmailing, Fakturoid, FIO Banka, Allfred, Google Workspace, EDUtéka. Obsahuje ReBeL chatbot (Text-to-SQL nad firemními daty) a AI shrnutí přes RAG. Aktuální stav: produkčně používáno (People & Culture, Finance tým), MVP (různé reportingy). Vize: jednotné místo, kde se sbíhají data ze všech systémů.
>
> ## Pracovní návyky a styl
> ### Denní rytmus
> Noční pták: start v 9:00–10:30, práce do 17–18, pak pauza na soukromé aktivity. Druhý blok 23:00–02:00 — typická součást dne. 2–3 dny home office, 1–2 dny kancelář. 20–40 % času meetingy, zbytek operativa nebo deep work. Rituály se nedaří dlouhodobě držet — výjimkou je zero-inbox policy.
>
> ### Jak plánuji
> Daří se top-level strategie + operativní tasky. Slabá je střední, projektová vrstva — největší slepá skvrna. Plánuji od cíle zpět (top-down). Větší část dne reaktivní — support kolegům v customer-facing rolích. Priority: urgence + jasnost struktury dotažení do konce.
>
> ### Jak řeším problémy
> Historicky nejvíc fungovaly mind mapy — chce se k nim vrátit. Planning mód s AI agentem je přínosný — společně architektura řešení a next-steps, detaily nechává zpracovat. Když ho něco nadchne, má tendenci to rovnou vyřešit a pochlubit se hotovou věcí.
>
> ### Komunikace
> Preferuje psaný text — Slack, WhatsApp, video nahrávky pro komentáře k dokumentům. Telefon nemá rád. Bullet-points jsou boží věc. Když někdo přijde s problémem: doptává se, vytváří obrázek a strukturu, co nejrychleji navrhuje možné směry řešení. Vytáčí ho nedostupnost, nereakce a opakované chyby stejného typu.
>
> ### Tech stack
> HW: MacBook Air M4, iPhone 16. SW: Pipedrive, Allfred.io, Make.com, n8n (self-hosted), RB Universe, Google Workspace, Sembly. AI: Cursor (Ultra plán) jako primární IDE pro vibe-coding; rozšiřuje použití Claude (chat, Cowork); Claude Code zatím nechce nasazovat místo Cursoru. Pokročilá znalost API integrací.
>
> ## Co mi jde a co mi nejde
> ### Silné stránky
> Architektura a struktura řešení; dotahování konkrétních use-cases; syntéza napříč obory; translator role (business/čísla/IT); kritické oko.
>
> ### Slabé stránky / oblasti rozvoje
> Task management systém — opakovaně se rozpadá (teď Apple Reminders) → od 2026-04-28 systém Agenda v Cowork složce (OBSIDIAN/00-System/Memory/agenda-system). Záznam neúkolových materiálů — vyřešeno přes Agenda systém (Backlog sekce). Střední projektová vrstva plánování — adresuje Agenda systém. Review — denní/týdenní/měsíční prakticky nedělá. Empatie a people skills — tendence jednat racionálně. Delegace zásadních rozhodnutí mimo svou kompetenci. Při odporu mimo svou kompetenci spíš vzdá než tvrdě prosazuje. Rituály — neumí je dlouhodobě udržet.
>
> ## Hodnoty a principy
> Férovost — nesnáší zákulisní hry, tajnůstkářství, pokrytectví. Slušnost a demokratické principy. Vyšší dobro. Fact-based přístup, kritické myšlení. Dohody se mají dodržovat — platí pro lidi i pro AI agenty.
>
> ## Co považuji za dobrý výsledek
> Uzavřené tvary = dokončené úkoly, milníky, projekty, fáze. Špatný výsledek = něco zůstane na půl cesty. Je completionist — otevřené smyčky ho vyčerpávají.
>
> ## Co mě teď zajímá a kam rostu
> ### Profesní rozvoj
> Firemní finance, jejich řízení a strategie. Vibe-coding. Agentská spolupráce — Claude Cowork, task management a střední projektová vrstva.
>
> ### Mimo práci
> Geopolitika. Volejbal (hra i strategie). Organizace dětského tábora. Životospráva — vede kalorické tabulky.
>
> ## Mimo práci
> ### Sport a pohyb
> Volejbal — vášeň. Horské kolo. Geocaching (občas). Fitko — chtěl by začít chodit.
>
> ### Knihy a čtení
> Hodně čte — zprávy, novinky, příběhy. Žánrově: thrillery, fantasy, „brakovka" (Jiří Kulhánek, František Kotleta). Učí se primárně čtením a kutilstvím. Audio absorbuje výrazně méně.
>
> ### Rodina a komunita
> Diskuse s dětmi, doprovázení na sportovních aktivitách. Trávení času se skupinou rodin a přátel. S manželkou hledají společné zájmy pro fázi, kdy děti začnou víc létat z hnízda.
>
> ## Vize 3–5 let
> ### Profesně
> Zůstat spolumajitelem Red Button EDU. Dotáhnout RB Universe do podoby skutečného „centrálního mozku".
>
> ### Osobně
> Aktivní hráč volejbalu v lepší fyzické kondici. Samostatné děti, připravené na samostatný život. Lepší vztah s manželkou — nové společné zájmy pro období po hnízdě. Vrátit se k buddhistické praxi.
>
> ## Jak se mnou pracovat (cheat sheet)
> ✅ Piš mi (Slack, WhatsApp, e-mail) — netelefonuj, pokud to není nutné
> ✅ Bullet-points a struktura — ne prózu
> ✅ Plánuj od cíle zpět — řekni mi výsledek, pak rozjedeme strukturu
> ✅ Když přinášíš problém, přines i navrhované směry řešení — min. 2–3 varianty
> ✅ Dotahuj věci — nedokončené tvary demotivují
> ✅ Buď dostupný a respektuj dohody — i ty nepsané
> ❌ Nehraj zákulisní hry — všechno na rovinu
> ❌ Neopakuj stejné chyby — když něco nefunguje, mluvme o tom

```

---

## 5. Memory (paměť) — kompletní obsah

Claude paměť je **per-account** a v novém účtu bude prázdná. Dvě cesty:
1. **Skill "import-memory"** (je v seznamu skillů výše, standardní) — dá se použít pro import exportu z jiného AI asistenta, funguje i pro ruční vložení tohoto exportu.
2. Ručně nechat novou session přečíst tuhle sekci a poprosit, ať si to zapíše (nejjednodušší přes pár vět typu "tohle jsou fakta o mně, ulož si je").

### 5.1 Account-level memory (mimo Projekty — vidí to všechny tvé Claude chaty/surfacy)

**`/profile.md`** — kdo jsi
- Co-owner and CFO at Red Button EDU (RB EDU), ~30 lidí, leadership/culture/digitalizace/sustainability/inovace
- Odpovědnost: finance, CRM (Pipedrive), konsolidace dat, interní digitální nástroje
- Vibe-coduje RB Universe sám
- Součást 6členého Strategy Teamu
- Bydliště: Česká republika
- 20+ let v sales/nezávislém konzultingu
- Sebepopis: „Překladatel mezi světy businessu, financí a IT, CFO, spolumajitel firmy, nadšený vibe-coder a táborník"
- 47 let, otec tří dětí
- Liberální, prozápadní názory
- Sales dráha: KAM → Sales Director (Siemens) → nezávislý konzultant
- Bývalý spoluvlastník a CEO startupu Joinera

**`/preferences.md`** — jak s tebou má Claude komunikovat
- Vždy čeština, tykání, oslovovat Lukáši
- Při nejasném zadání se nejdřív zeptat
- Po každé odpovědi 3 tučné follow-up otázky **Q1**/**Q2**/**Q3** (jako by se ptal Lukáš); jako hlasový asistent číst "otázka jedna/dvě/tři"
- Nikdy nevydávat generovaný/odvozený/spekulativní obsah za fakt; neověřitelné označit
- Neověřený obsah označit na začátku věty: *Inference* / *Speculation* / *Unverified*; pokud je neověřená byť část odpovědi, označit celou
- Neparafrázovat/nepřeformulovávat Lukášův vstup bez vyžádání
- Složité úkoly rozkládat na kroky, zdůvodňovat, nabízet víc pohledů/řešení
- U úprav kódu vždy vypsat celý skript ke zkopírování
- Automaticky aktivovat všechny relevantní dostupné nástroje/pluginy/moduly
- Věnovat práci maximální pozornost
- U kalendářové události s konkrétní adresou v location přidat do popisu "#needs_travel"

**`/areas/rb-universe.md`** — RB Universe (platforma)
- Interní platforma, kterou si sám vibe-coduje
- Stack: FastAPI, PostgreSQL + pgvector, React 18, Vite; deploy přes Coolify
- Aktivní vývoj/rozšiřování
- Zkoumá enterprise AI deployment tooling (Open WebUI, LiteLLM, LibreChat, Portkey) pro celofiremní použití
- Zkoumá Business as Code filozofii pro process dokumentaci
- Zkoumal penetration testing a bezpečnostní posturu RB Universe
- Integruje Pipedrive, Fakturoid, Fio, Allfred přes MCP
- BaC evaluace: setup přesahuje cílovou skupinu BaC, ale identifikovány mezery v process dokumentaci, AI content trust/status modelování a agent routing kontextu
- Doporučení pro enterprise AI rollout přes Coolify: LibreChat + LiteLLM, nebo Portkey; pozor na March 2026 LiteLLM supply chain útok

**`/people/rodice.md`** — rodiče a rodina
- Táta: Vladimír Cypra, máma: Vladimíra Cyprová
- Svatba 1976, v 2026 zlatá svatba (50 let); přesné datum doplní Lukáš
- Děti rodičů: Lukáš a sestra Katka
- Lukáš ženatý s Evou; děti: Matyáš, Václav, Eliška
- Katčin manžel Míra; syn Oliver (nejmladší vnouče)
- Vnoučata od nejstaršího: Matyáš, Václav, Eliška, Oliver
- Máma energická — tandemový seskok padákem, Univerzita třetího věku (ČZU, 2025)
- Rodiče postavili dům (stavba 1986, přístavba verandy 1988–89); měli psa Betynku (kokršpaněl)
- Lukáš chystá AI vzpomínkové video + webové album k výročí
- Píseň pro film: „Už mi lásko není 20 let" (Jiří Zmožek); staré ČB fotky nechat ČB + kolorovaná verze

**`/topics/community-involvement.md`**
- 20+ let u dětského tábora Krátký potlesk, v leadership týmu
- Člen výkonné rady Společnosti E
- Dlouholetý organizátor konference Happiness@Work

**`/topics/health.md`**
- Řeší aktivní urologickou záležitost, absolvoval předběžná vyšetření, objednán na urologii
- Hledal zobrazovací pracoviště v Praze 13 (Stodůlky)
- Hledal OTC antimykotika (Canesten vs. Canespor) v ČR lékárnách

**`/topics/interests.md`**
- Široký zájem o nové technologie a světové dění
- Zastánce kritického myšlení a fact-based uvažování

**`/topics/recent-work.md`** — nedávná práce mimo standardní projekty
- Přepracoval Cursor AI rules soubory (lukas-writing-style.mdc, fable-5-agent.mdc) na základě ~200 odeslaných e-mailů
- Pracoval na finančních dokumentech RB Associates s.r.o. (Fio banka, Money S4 za 04/2026)
- Připravil strategický brief pro DiverSight.ai akcelerační panel v Impact Hub Praha
- Diagnostikoval Google Sheets IMPORTRANGE selhání kvůli GCP kvótě (projekt 25663159623)
- Udržoval Claude COWORK strukturu na Drive (ID 12xJBQTYKiG9t9zmnexRWocfkB5PCKkxi) — O MNĚ, ŠABLONY, VÝSTUPY (flat); artifact pipeline přes GitHub Pages vracel 404, preferovaná migrace na Drive
- Zkoumal n8n remote MCP server architekturu pro Apple Reminders (iCloud CalDAV) a Goodreads (RSS)
- Vytvořil návod na Allfred.io fakturační automatizaci
- Posuzoval SmartEmailing Magic Editor pro RB EDU newslettery
- Dělal lookupy v ČR rejstříku (SUBTERRA a.s., Happiness at Work s.r.o., RB Associates s.r.o.)
- Analyzoval dva dezinformační dokumenty (fabrikovaný citát Stiglitze, arcibiskup Viganò) — fact-check report
- Zkoumal financování Hnutí DUHA za 2024
- Pracoval na ICE/RICE prioritizačních frameworcích

**`/topics/tools.md`**
- HW: MacBook Air M4, iPhone 16
- Google Workspace, Arc browser, Gmail
- Cursor (Ultra plán) jako hlavní vibe-coding IDE
- Make.com, self-hosted n8n
- Pipedrive CRM
- Leadspicker (s API integrací)
- Slack
- Pokročilá znalost API
- Drive default: ukládat hotové výstupy do správné podsložky (O MNĚ/ŠABLONY/VÝSTUPY) bez ptaní; nepřeukládat konverzační koncepty; ověřit strukturu přes search_files před vytvořením; VÝSTUPY je zatím flat; nevytvářet duplicity — přepisovat/aktualizovat na místě
- "EDU" a "RB EDU" vždy znamená Red Button EDU
- Nechce Claude Code nahrazovat Cursor

**`/topics/travel.md`**
- Plánuje výlet do Lisabonu a oblasti Cascais/Sintra v létě 2026
- Zkoumal portugalské školní prázdniny, turistické sezóny, rezervaci auta u Guerin (checklist, NIF požadavky), místní historii (král Carlos I.)
- Guerin rental v Lisabonu: vyřešeno NIF vs. pas
- Vytvořil Booking.com checklist jako interaktivní HTML artefakt
- Zkoumal nemovitosti v Sintře a srovnání české a portugalské ekonomiky

### 5.2 Memory v rámci Projektu "SECOND BRAIN" (vidí to jen tenhle Projekt)

**`overview.md`** — owners group leadership kontext
- Lukáš je hlavou owners group, zodpovědný za formát a operations
- Komunikuje česky, Europe/Prague timezone, stručně a přímo
- Klíčoví kolegové: Honza Mašek (Growth/Strategy, vlastník projektu IDENTITA), Martin Ruman (Head of Delivery & Ops, stává se spoluvlastníkem přes Odyssey transakci), Luboš (CEO); další zmiňovaní: Šraky, Ráďa, Sandra, Šafařík, Lenka, Pavel Kroupa, Roman, Verča, Dominik, Katarína, Dominika (Domča), Tomáš Blaťák
- Kódované task ID systém (OWN6, OWN7, MO17, SBD11, VC15, F47, OS1, S12-16...)
- IDENTITA projekt: strukturovaná agenda z předchozího offsite, fáze validace a prioritizace
- Odyssey transakce: co-ownership pro Martina Rumana, blíží se signing
- ArgLider: revize navržena na listopad, mimo přímé vlastnictví owners group
- Leadspicker (SBD11): vyhodnocován pro EDU kontext
- S12-16 billing tabulka: urgentní položka
- Owners setkání plánováno na konec září; ArgLider revize v listopadu

**`ways-of-working.md`** — jak má Claude v tomhle projektu fungovat
- Pracovní den strukturovaný kolem kalendářových working windows
- Denní briefing: Claude čte kalendář + agent-context.json a syntetizuje priority dne
- Preferuje, ať Claude syntetizuje ze zdrojových materiálů, ne rovnou finální výstupy
- Google Drive konektor (ne statické uploady) pro vault kvůli častým změnám
- Bootstrap soubor `/mnt/project/agent-bootstrap.md` číst před dotazováním integrací
- Drive: agent-context.json file ID `1SVbRzRrEFGDQpe2kjCzBcOIR29BZKjrX`; Obsidian vault folder ID `1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-` (vlastník lukas@redbuttonedu.cz)
- Vault struktura: 00-System, 01-INBOX, 02-PROJEKTY, 03-AREAS, 05-RESOURCES, 06-CANVAS, 07-ARCHIV, Clippings; hub notes Home.md, Dashboard.md; .canvas soubory špatně prohledatelné
- Plaud = primární nahrávání meetingů (export jako MD na Drive); Sembly = sekundární, nespolehlivý (prázdné summary)
- Google Calendar dotazovat s Europe/Prague timezone a +02:00 offsetem
- Leadspicker pod evaluací; Cursor pro hygienu/maintenance
- Scheduled tasky spravovány přes platformu, nejdou editovat z konverzace, ale cron a instrukce lze připravit v chatu
- Drive search patterns co fungují: `fullText contains 'owners'` + modifiedTime; `createdTime > [date] and mimeType = 'text/markdown'`; `title contains '[keyword]'` s excludeContentSnippets; `parentId = '1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-'`
- Skills žijí na Drive `ŠABLONY/skills/<skill>/SKILL.md` (folder ID `11N6lo-2echbyuEUAT-YbyK_2_uhINPpS`), Claude tam může přímo zakládat nové skill soubory; git commit pořád přes Cursor

**`areas/procesni-architekt.md`** — skill Procesní architekt
- Postavil Claude skill "procesni-architekt" pro import MD do Procesního architekta v RB Universe (nové i update procesů)
- Soubory (reference, skripty, requirements doc pro dev tým) na Drive: https://drive.google.com/drive/folders/1yBczQQPAp-PYAhSDMW6UeackPQb5Tnpt
- Nahráno a zapnuto v Claude.ai (Customize > Skills), funguje po opravě XML-tag chyby v popisu
- Má sloužit i kolegům s přístupem do RB Universe / Procesní architekt bez napojení na Lukášův osobní vault
- Připraven samostatný requirements doc pro dev tým RB Universe (zlepšení MD round-trip)

**`index.md`** — jen název a popis Projektu (viz sekce 4)

---

## 6. Připojené složky a context files (odkazy)

### 6.1 Lokální propojení s počítačem (device bridge)
- **Zařízení:** `lc-macbook-air-local`
- **Připojená složka:** `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN`
- Tohle je lokálně synchronizovaná Google Drive složka → **nic se nemusí exportovat**, v novém účtu stačí přes desktop appku znovu zvolit "Link to this computer" a znovu připojit stejnou složku.
- Struktura na top-level: `_archive`, `.cursor`, `.git`, `cowork-instructions.md`, `Cursor`, `docs`, `OBSIDIAN`, `OBSIDIAN_BACKUP`, `output`, `README.md`, `ŠABLONY`, `scripts`, `vps`
- `ŠABLONY/skills/` obsahuje tyhle skill složky (SKILL.md soubory pro mrluc-loader routing): `agenda-analyze`, `agenda-capture`, `agenda-co-ted`, `agenda-cursor-inbox`, `agenda-edu-news`, `agenda-lessons`, `agenda-meeting-prep`, `agenda-priority-review`, `agenda-proces`, `agenda-remind`, `agenda-reply`, `agenda-status-update`, `agenda-triage`, `agenda-weekly-review`, `agenda-work`, `agenda-zapis-ze-schuzky`, `mrluc-loader` (+ `README.md`)
- **Tohle je nejvíc "free" část přesunu** — je to tvůj vlastní Drive, žádný Claude účet ho nevlastní.

### 6.2 Google Drive odkazy zmíněné v paměti / scheduled taskách
- Procesní architekt — zdrojové soubory: https://drive.google.com/drive/folders/1yBczQQPAp-PYAhSDMW6UeackPQb5Tnpt
- Obsidian vault (folder ID): `1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-` → https://drive.google.com/drive/folders/1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-
- `agent-context.json` (file ID): `1SVbRzRrEFGDQpe2kjCzBcOIR29BZKjrX` → https://drive.google.com/file/d/1SVbRzRrEFGDQpe2kjCzBcOIR29BZKjrX
- `ŠABLONY/skills/` na Drive (folder ID): `11N6lo-2echbyuEUAT-YbyK_2_uhINPpS` → https://drive.google.com/drive/folders/11N6lo-2echbyuEUAT-YbyK_2_uhINPpS
- `agenda-meeting-prep/SKILL.md` (file ID, může se časem měnit): `1zgh9zLN5WlNFHR6F9zrWXTEgi1i5_xxD` → https://drive.google.com/file/d/1zgh9zLN5WlNFHR6F9zrWXTEgi1i5_xxD
- Claude COWORK složka (O MNĚ / ŠABLONY / VÝSTUPY, flat) (folder ID z paměti): `12xJBQTYKiG9t9zmnexRWocfkB5PCKkxi` → **⚠️ ověřeno přes Google Drive konektor a nefunguje.** `get_file_metadata` na tohle ID vrátil "Requested entity was not found" — buď byla složka smazaná/vysypaný koš, přesunutá mimo tvůj přístup, nebo je ID v paměti přepsané chybně. Zkusil jsem to dohledat podle názvu (hledal jsem "Claude Cowork" a samostatně "O MNĚ"/"ŠABLONY") — nejbližší shoda je jiná složka `Claude Cowork` (ID `1f5vngtJ8_UzTlOhWgmWxGW-YjhQQtQau`, https://drive.google.com/drive/folders/1f5vngtJ8_UzTlOhWgmWxGW-YjhQQtQau), ale ta patří k úplně jinému projektu (workshopy Mattoni, ne O MNĚ/ŠABLONY/VÝSTUPY strukturu) — **není to ono.** Skutečnou VÝSTUPY/O MNĚ složku jsem nenašel. *Speculation:* možná to není samostatná Drive složka, ale myšlena struktura přímo v `SECOND_BRAIN/` (tam ale žádné `O MNĚ`/`VÝSTUPY` na top-levelu nejsou, jen `ŠABLONY`). Řekni mi prosím přímo název nebo aktuální odkaz, ať to nehledám poslepu.
- Slack thread backup — cílová složka (dvě ID, stejné místo): `1EppTJt45A8kOyQJoZ8BuneHtiU5nWlXN` / `1K4e8UgrxozNixrTbomWvytbNk_R-cnxN`
- Měsíční archiv dokladů — cílová složka "*H@W - doklady - FY2026": `1R-cHm9TZx513WgklymZou8EPUiIzLyem` → https://drive.google.com/drive/folders/1R-cHm9TZx513WgklymZou8EPUiIzLyem
- Měsíční archiv dokladů — šablona "_template - FY2026": `1eWqOglXBZRCy-V6IsP0iiKLs85H_K9PX` → https://drive.google.com/drive/folders/1eWqOglXBZRCy-V6IsP0iiKLs85H_K9PX

*Poznámka: u ID složek/souborů výše jsem URL sestavil podle standardního Google Drive formátu (`/drive/folders/<id>` resp. `/file/d/<id>`) — sám jsem odkazy neotvíral, takže ověř, že fungují, než je použiješ.*

---

## 7. Checklist pro přesun (od cíle zpátky)

**Cíl: nový Claude účet funguje stejně jako tenhle.**

1. **Connectors** — v novém účtu připoj Gmail, Google Calendar, Google Drive, Pipedrive, RB Universe, Slack, Leadspicker, Spotify (Miro a Rohlík stejně vyžadují reconnect i tady, takže nic neztrácíš).
2. **Desktop link** — v Claude desktop appce na novém účtu zvol "Link to this computer" a připoj stejnou složku `SECOND_BRAIN` na Google Drive (lokálně synchronizovanou).
3. **Skills** — v Customize → Skills nahraj znovu `mrluc-loader`, `zapis-ze-schuzky`, `procesni-architekt` (zdroj je na Drive, viz 6.2, nebo z lokální kopie ŠABLONY/skills/mrluc-loader atd. — pozor, tohle jsou jen "trigger" skilly co čtou z Drive, ne agenda-* skilly samotné, ty netřeba nahrávat jako Claude skill).
4. **Projekt** — založ nový Projekt "SECOND BRAIN", vlož instrukce ze sekce 4.1 a doc `about-me.md` ze sekce 4.2.
5. **Memory** — buď skillem import-memory, nebo prostě dej nové session přečíst sekci 5 a poprosit o uložení.
6. **Scheduled tasky** — založ 5 nových scheduled tasků podle sekce 3 (pozor na cron, model, zapnutý/vypnutý stav, notifikace).
7. **Ověření** — spusť ručně "Ranní priority brief" (fire_trigger) a zkontroluj, že to funguje stejně jako tady.

---

*Konec exportu. Pokud chceš, tohle ještě uložím i do tvého Drive (VÝSTUPY podle standing instructions) — jen mi řekni.*
