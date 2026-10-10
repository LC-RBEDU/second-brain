---
name: tymovy-disk
description: >-
  Založí a udržuje interní týmový sdílený disk RB EDU ([EDU] Strategy, Finance,
  Technaři…): AGENTS.md, CLAUDE.md, karta týmu.md, index.md, oblasti, osm meta
  složek včetně úkoly/ (file-per-task). Use when týmový disk, shared drive,
  [EDU], karta týmu, AGENTS.md na disku, úkoly týmu. Ne klientský projekt,
  ne /init, ne firemní Wiki jako náhrada disku.
---

# tymovy-disk

**Verze skillu:** 0.6 (Cursor). Diskový standard, který se zapíše do `AGENTS.md`, je **v0.5**.

Skill zakládá a udržuje **interní týmový sdílený disk** `[EDU] <Tým>`. První úroveň řídí tento skill, strukturu uvnitř oblastí řídí owner disku. Lidský popis: RB Wiki `tymove-sekce/technari/struktura-tymoveho-disku.md` (draft). Pilot na Wiki je `[EDU] Strategy`; skill jím není omezený, při zakládání jiného týmu to řekni.

Cursor `AGENTS.md` ze sdíleného disku nenačte, dokud ta složka není workspace. Na začátku práce stáhni `AGENTS.md`, `karta týmu.md` a `index.md` přes `get_drive_file_content`. `CLAUDE.md` je dodatek pro Clauda; konektory z něj v Cursoru nepoužívej.

Šablony řídicích souborů, dohody a úkolu: [templates.md](templates.md). Čti je až při zápisu na disk.

## Kdy ne

- Klientský projekt / akademie → Wiki `tymove-sekce/delivery/struktura-projektu.md` (ověřeno, owner Michal Šrajer), skill `rb-project-start`. V tomhle repu skill `lucy` není.
- Firemní pokyny a rozhodnutí pro celou firmu → RB Wiki. Na disk jen odkaz.
- Osoby, firmy, finance, karta delivery projektu → RB Universe / Pipedrive / Allfred. Na disk jen odkaz.
- E-maily → RB Universe. Na disk se neukládají.
- Lukášův Second Brain vault (`02-PROJEKTY/…`) — oddělený svět; úkoly na disku se do vaultu nekopírují.
- `/init` a `AGENTS.md` / `CLAUDE.md` v git repu. Tenhle skill je nezakládá.

## Než zapíšeš AGENTS.md

Always-on zákaz `/init` výjimku ve skillu sám neotevře. Zapisuj řídicí soubory jen když aktivní pravidlo `no-agents-md-init` výjimku pro týmový disk obsahuje. Když ji nemá, **nezapisuj** a řekni, která kopie chybí (typicky lokální `Red Button Universe/.cursor/rules/no-agents-md-init.mdc`).

## Cílová struktura

```
[EDU] <Tým>/
├── AGENTS.md
├── CLAUDE.md
├── karta týmu.md
├── index.md
├── 01 - <Oblast>/
├── archiv/
│   └── úkoly/           # Done | Cancelled (stejný filename)
├── dohody a rozhodnutí/
├── ostatní/
├── public/
├── schůzky/
├── scripty/
├── šablony/
│   └── úkol.md
└── úkoly/               # otevřené úkoly (ploché)
```

- **Číslované `NN - Název`** = oblasti agendy. Číslo je pořadí, ne datum. Návrh 3–8, zakládej až po odsouhlasení.
- **Meta složky** zakládej vždy všech osm, názvy přesně: `archiv`, `dohody a rozhodnutí`, `ostatní`, `public`, `schůzky`, `scripty`, `šablony`, `úkoly`.
- Pod oblastí nic předem. Vzor `podklady/`, `pracovní/`, `výstupy/` jen po souhlasu ownera, když oblast naroste (orientačně přes 15 souborů nebo víc typů obsahu).
- V kořeni jen čtyři řídicí soubory a složky. Žádný `CURSOR.md` ani `.cursor/rules` na disku.
- Česky s diakritikou. Datované soubory začínají `YYYY-MM-DD ` (mezera). V odkazech mezery a diakritiku kóduj (`karta%20t%C3%BDmu.md`) nebo dej název do backticků.
- Žádné `_final`, `_old`, `v2_FINAL`. Starší verze jde do `archiv/`.

| Soubor | Role |
|---|---|
| `AGENTS.md` | Jediný zdroj instrukcí. Bez názvů skillů a konektorů. |
| `CLAUDE.md` | Pointer na `AGENTS.md` + krátký dodatek pro Clauda. Obsah `AGENTS.md` neopakuje. |
| `karta týmu.md` | Fakta včetně **Prefix úkolů**. Znění dohod ne. |
| `index.md` | Jen rozcestník + datum. Žádné instrukce, fakta ani výpis jednotlivých úkolů. |

## Provozní zákazy

- `archiv/` — defaultně nečti, necituj, nevyvozuj. **Vstup jen se silným důvodem:** (a) výslovný pokyn člověka, (b) alokace dalšího ID úkolu — list **názvů** v `archiv/úkoly/` (ne těla), (c) potvrzený lifecycle přesun / reopen úkolu. Bez důvodu neprocházej.
- `Archiv stávajícího obsahu/` no-go není. Číst smíš a řekneš, že jde o nerozřazený obsah. Nové soubory do ní nezakládej.
- Prázdná `public/` se zakládá spolu s ostatními meta. Soubor do ní až po kontrole důvěrnosti (finance, osobní data, 1:1, NDA) a potvrzení člověkem.
- `set_drive_file_permissions` a `manage_drive_access` nevolej. Oprávnění mění owner disku.
- Nahrávky ve `schůzky/` nemaž a nearchivuj bez pokynu.
- Dashboard na disku nežije (včetně dashboardu úkolů). V oblasti jen `.md` s odkazem. Kód → `scripty/`.
- Znění dohody jen v `dohody a rozhodnutí/YYYY-MM-DD název.md`. Práce s ownerm a termínem = soubor v `úkoly/`; dohoda/zápis schůzky jen odkaz na ID.
- Mazání a přepis existujícího souboru jen po samostatném potvrzení a ukázání diffu. `trashed: true` nevolej.
- `scripty/`: podsložka jazyka až s prvním skriptem. Ke skriptu krátký popis.
- `šablony/`: týmové šablony včetně `úkol.md`. Firemní jen odkaz.
- V `ostatní/` při shluku stejného tématu navrhni ownerovi novou oblast.

## Úkoly (file-per-task)

Otevřené: `úkoly/<ID> — <Název>.md` (ploché). Hotové/zrušené: `archiv/úkoly/` stejný filename.

**YAML:** `id`, `title`, `owner`, `oblast`, `status`, `deadline` | `review_deadline`, při Waiting povinné `wait_until`, volitelné `odkazy`.

| Pole | Pravidlo |
|---|---|
| `status` | `Backlog` \| `Doing` \| `Waiting` \| `Done` \| `Cancelled` — **bez** `Next` |
| `deadline` | Hard externí termín. Když je nastaven, `review_deadline` vymaž. V AGENTS: hard = `deadline`. |
| `review_deadline` | Jen když není `deadline` — kdy se k úkolu vrátit. |
| `wait_until` | Jen u `Waiting` (ISO datum). Po datu **navrhni** návrat (Backlog/Doing); status sám neměň. |
| `owner` | Zobrazované jméno z tabulky lidí na kartě. |
| `oblast` | Přesný název složky oblasti (`01 - Fakturace`), ne jen číslo. |
| ICE / `focus` | Na týmový disk **nedávej**. |

**Tělo:** `## Zadání`, `## Progress`, `## Přílohy` (jen odkazy), `## Komentáře` (append-only: `- YYYY-MM-DD HH:mm — Jméno: …`; staré nearavuj).

**ID:** Prefix z `karta týmu.md` (**Prefix úkolů**, např. `STR`). Formát `PREFIX-N` (kladné celé N, bez paddingu). Filename `<ID> — <Název>.md`. Další N = 1 + max z názvů v `úkoly/` **a** `archiv/úkoly/` (list metadata, ne čtení těl). Bez `_next_id.md`. Před create znovu listni rodiče (souběh). Prefix chybí → doptat, nehádat.

**Zápis:** nový úkol, změna polí, komentář, status — vždy preview/diff a **potvrzení** člověka. Žádné tiché solo.

**Lifecycle**

1. **Done | Cancelled:** jedno potvrzení = zápis `status` + přesun do `archiv/úkoly/` (stejný filename).
2. **Reopen:** po potvrzení přesun zpět do `úkoly/`, stejné ID, status `Backlog` nebo `Doing` (dle člověka; default Backlog), řádek do `## Komentáře` (reopen).
3. **Historie / „co jsme dokončili“:** jen po výslovném pokynu (koukni do `archiv/úkoly/`). Žádný `DONE.md` / dashboard.

**Hranice:** dohoda a zápis schůzky odkazují na ID; checklist v dohodě není SSOT. Oddělené od vaultu a Universe — volitelné `odkazy`, žádný sync.

## Nástroje

Účet `user-google-workspace`, `user_google_email: lukas@redbuttonedu.cz`. Sdílený disk nezakládej.

- Seznam disků: `list_drive_items` s `resource_type: shared_drives`, stránkuj dokud je `nextPageToken`, pak teprve nabídni výběr. Kořen: `drive_id` = `folder_id` = ID toho disku, stejně stránkuj (`page_size` 100).
- **Nikdy `root`.** `create_drive_file.folder_id` i `create_drive_folder.parent_folder_id` mají default `root` (Můj disk). Oba argumenty vždy předaj a nastav na ID kořene vybraného disku. `create_drive_folder` parametr `drive_id` nemá.
- Meta složka jen `create_drive_folder`. Řídicí soubor a úkol jen `create_drive_file` s `content` a `mime_type: text/markdown`. `create_drive_file` složku nevytvoří a do Google Docu obsah nepřevádí. `import_to_google_doc` na řídicí soubory nepoužívej. `disableConversionToGoogleType` API odmítne; zůstává jen v šabloně `CLAUDE.md`.
- MIME po zápisu ber z metadat výpisu nebo z odpovědi vytvoření. `get_drive_file_content` u Google Docu vrací text, tím MIME neověříš.
- Přesun: `update_drive_file` s `add_parents` a `remove_parents`. `update_drive_file` s `content` jen po diffu a samostatném potvrzení, a jen když vlastní MIME toho ID je `text/markdown`, `text/plain` nebo `text/x-markdown`. Shortcut a Google Doc se obsahem nepřepisují.
- Když přesun vrátí chybu oprávnění, vypiš přesný seznam a přesun nech člověku nebo Drive for Desktop. Ve streamovacím režimu Desktop vrací prázdný výpis nebo „Resource deadlock avoided“, dokud člověk složku neotevře ve Finderu nebo ji nedá offline. Webové UI Disku na přesuny nepoužívej.
- Wiki: `wiki_manifest` → `wiki_read`. Shrnutí týmu je obyčejná stránka přes `wiki_write` (draft, při přepisu `expected_sha`), až po potvrzení. Rozcestník `index.md` sekce `wiki_write` nemění; na ten patří `wiki_section_write`. Nová sekce jen po souhlasu (`confirm_create`).
- Členy týmu z MCP, Slacku ani kalendáře neskládej. `get_org_chart` je KAM organigram klienta, `search_persons` je CRM. V kartě nech `(doplnit)` a zeptej se. Formulace „doplnit z RB Universe“ a „zdroj pravdy je org chart“ do karty nepatří. `get_events` smí doplnit rytmus schůzek, ne seznam lidí. Firemní priority týmu ber z Wiki (skill `wiki-firemni-priority`); na kartě jen odkazy.

## Pořadí na kořeni

Nejdřív stránkovaný výpis. Víc položek stejného jména → stop a člověk vybere.

Platná meta = kanonické jméno a MIME `application/vnd.google-apps.folder`. Platný řídicí soubor = kanonické jméno a MIME `text/markdown`, `text/plain` nebo `text/x-markdown` (Drive u `.md` často uloží `text/plain`). Google Doc, shortcut a jiný MIME platné nejsou.

„Struktura už začala“ = v kořeni je aspoň jedna platná meta nebo aspoň jeden platný řídicí soubor.

1. Kořen je prázdný, nebo v něm je jen složka `Archiv stávajícího obsahu/` → bez přesunu založ chybějící meta a chybějící čtyři soubory.
2. Struktura už začala a každé kanonické jméno je v kořeni nejvýš jednou. Platné nepřesouvej. Chybějící meta a chybějící řídicí soubory založ na místě. Kanonické jméno s neplatným MIME po potvrzení přesuň do `Archiv stávajícího obsahu/` a teprve pak založ chybějící jméno. Druhou položku stejného jména nezakládej. Nekanonické položky jen vypiš.
3. Struktura nezačala a kořen není prázdný → po potvrzení složka `Archiv stávajícího obsahu/`, pak přesuň všechna potvrzená ID z kořene. Složku archivu nepřesouvej. Pak teprve kostra z bodu 1. Položky archivu vypiš do `index.md`.
4. Před každým `create_drive_folder` znovu vypiš rodiče. Jedna platná složka stejného jména → její ID. Prázdná `public/` se zakládá s ostatními meta. Po založení `archiv/` založ i prázdnou `archiv/úkoly/` (parent = ID `archiv/`).

Před založením ukaž přesný seznam složek a souborů a nech ho potvrdit, pokud ho člověk výslovně nezadal sám.

## Kroky 0–6 (nový disk)

### 0 — Cílový disk

Ujasni disk (název `[EDU] <Tým>` nebo odkaz). `AskQuestion` jen když je víc disků na výběr. Bez potvrzení konkrétního disku nic nezakládej. Pak pořadí na kořeni výše.

### 1 — Co už existuje

- Wiki: sekce týmu v `tymove-sekce/`. Karta na ni odkazuje, neopisuje ji.
- Firemní priority, které tým vlastní: skill `wiki-firemni-priority`, na kartě odkazy.
- Rytmus: `get_events`, když je v kalendáři vidět. Účastníky schůzek neber jako seznam členů.

### 2 — Doptání

Ke každému chybějícímu poli se zeptej v chatu a počkej na odpověď. `(doplnit)` je stav až po položené otázce. Minimum:

1. Název týmu a disku, jednovětné poslání.
2. Owner (steward) disku.
3. Členové a role.
4. Oblasti (návrh 3–8).
5. Rytmus, priority, existující dohody (každá pak soubor v `dohody a rozhodnutí/`).
6. Co z karty má být veřejné shrnutí na Wiki.
7. **Prefix úkolů** (krátký uppercase, např. `STR`, `FIN`).

### 3 — Potvrzení

`AskQuestion` na seznam oblastí (názvy a pořadí). Meta složky a čtyři soubory se neodsouhlasují.

### 4 — Založ

Meta složky (včetně `úkoly/`), podsložka `archiv/úkoly/`, oblasti, čtyři řídicí soubory ze [templates.md](templates.md), soubor `šablony/úkol.md`. Placeholdery `{{…}}` nahraď. HTML komentář v šabloně smaž, když se nehodí.

### 5 — Wiki

Když tým nemá veřejné shrnutí, ukaž návrh (mise, lidé, na co se ptát koho, věta „detail na týmovém disku – jen pro tým“). `wiki_write` až po `AskQuestion` ano/ne.

### 6 — Ověř

- Osm meta s přesnými názvy; existuje `úkoly/` a `archiv/úkoly/`; oblasti dle odsouhlasení.
- Čtyři řídicí soubory a `šablony/úkol.md` — textové MIME, ne Google Doc.
- V kartě je Prefix úkolů (nebo proběhla otázka).
- `CLAUDE.md` neopakuje `AGENTS.md`. AGENTS uvádí standard v0.5.
- `index.md` sedí s kořenem (řádek `úkoly/`, ne výpis úkolů), včetně `Archiv stávajícího obsahu`, když vznikl.
- U každého `(doplnit)` proběhla otázka.
- Shrň, co vzniklo a co zůstalo `(doplnit)`. Když přesun musí dodělat člověk, vypiš zbývající položky.

## Migrace existujícího disku (standard před v0.5)

Po potvrzení na konkrétním `[EDU] <Tým>` (nehromadně všechny disky):

1. Založ chybějící `úkoly/` a `archiv/úkoly/`.
2. Nahraj `šablony/úkol.md`, pokud chybí.
3. Diff `AGENTS.md` (v0.5 + úkoly + soft archiv) → potvrzení → zápis.
4. Diff `index.md` (řádek `úkoly/`, text `archiv/`) → potvrzení → zápis.
5. Diff `karta týmu.md` (+ Prefix úkolů; doptat hodnotu) → potvrzení → zápis.

Nepřepisuj zbytek AGENTS bez diffu. Backfill úkolů z jinde ne.

## Údržba

- Po přidání, přejmenování nebo smazání položky na první úrovni nebo v meta složkách hned uprav `index.md` a datum. Obsah oblastí a jednotlivých úkolů se do indexu nevypisuje.
- Změna struktury nebo pravidel jen v `AGENTS.md`.
- Po úpravě zkontroluj, že `CLAUDE.md` nepřebírá obsah `AGENTS.md`.
- Lidé, role, owner, rytmus, priority, prefix úkolů nebo seznam dohod → `karta týmu.md` a „Naposledy ověřeno“. Když se mění veřejné shrnutí, navrhni úpravu Wiki a nezapisuj bez potvrzení.
- Nová nebo změněná dohoda → soubor v `dohody a rozhodnutí/` (odkazy na ID úkolů), v kartě odkaz. Zrušenou přesuň do `archiv/`.
- Úkoly: založení / změna / komentář / Done|Cancelled (status+přesun) / reopen — vždy po potvrzení. Po datu `wait_until` jen návrh návratu.
- Disk se AGENTS v0.4 a bez `úkoly/` → nabídni migraci (výše), netvoř tiše.
- Čas od času srovnej index a kartu s výpisem kořene.
