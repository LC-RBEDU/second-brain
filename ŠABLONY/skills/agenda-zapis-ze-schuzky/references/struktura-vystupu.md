# Struktura výstupů — HTML komponenty a MD schéma

## HTML — dostupné komponenty

Do `body.html` se píše **jen obsah**, žádné `<style>`. Shell (hlavička s logem, hero,
patička) dělá `build_html.py` z `meta.json`.

**Standard vzhledu (schváleno 2026-10-09, Lucie & Luky):** hero = kicker + h1 na celou
šířku; účastníci / stamp / zdroj **pod** hero (ne vedle). Detail a checklist → skill
`agenda-zapis-ze-schuzky` → „HTML vzhled — standard“.

### body.html — markup (povinné)

- Piš **skutečné HTML** (`<strong>`, `<b>`, `<em>`, `<ul>`, `<li>`, `<p>`).
- **Zakázáno** nechat v body literální Markdown ze zdroje (`**tučné**`, `- ` jako text).
- Blok **Rámec** / meta šum z MD `## 0. Meta` do body **nevkládej** (ani jako
  `p.lead` / sekce „Rámec“). Patří jen do vault MD; HTML hero bere krátký `kicker`
  z `meta.json` (1 věta), ne celý Rámec ani celý highlight.
- **`## 0. Meta` nikdy jako `section.area`** (ani „0 — oblast / Meta / 0 karty“).
  Highlights → `.big-thesis`; oblasti v HTML až od `## 1.` …

### Highlights — tři teze

Přesně tři bloky, jinak se rozbije barevný rytmus (červená / tmavá / zelená).

```html
<div class="section-label">Tři věci, které z toho vypadly</div>
<div class="big-thesis">
  <div class="thesis">
    <div class="num">01</div>
    <strong>Nadpis teze</strong>
    <p>Dvě až tři věty, proč to je důležité.</p>
  </div>
  <!-- 02, 03 -->
</div>
```

### Jak číst dokument (volitelné, ale doporučené)

```html
<section class="howto">
  <h3>Jak tenhle dokument číst</h3>
  <ul>
    <li>Struktura odpovídá <b>…</b></li>
    <li><b>Úkoly jsou pouze ty, které explicitně zazněly.</b></li>
  </ul>
</section>
```

### Oblast (položka sloupce B / tematický blok)

```html
<section class="area">
  <div class="area-head">
    <div>
      <div class="section-label">CO — sloupec B</div>
      <h2>Název oblasti</h2>
    </div>
    <div class="col">3 aktivity</div>
  </div>
  <!-- karty -->
</section>
```

### Karta (položka sloupce D / podtéma)

```html
<article class="card">
  <div class="card-head">
    <div>
      <h3>Název aktivity</h3>
      <div class="owner">Vlastní: Jméno · klíčoví: Jméno, Jméno</div>
    </div>
    <div class="badge b-done">Projednáno</div>
  </div>
  <div class="block">
    <h4>Co zaznělo</h4>
    <ul class="bullet-list">
      <li>…</li>
    </ul>
  </div>
  <div class="block tasks">
    <h4>Úkoly, které padly</h4>
    <ul>
      <li><b>Jméno</b> — úkol.</li>
    </ul>
  </div>
</article>
```

**`div.owner` (povinné):** `klíčoví` = `key_people` **bez** `owner` (dedupe
case-insensitive). Když po odebrání ownera nikdo nezbyde → jen `Vlastní: …`
(bez `· klíčoví:`). Sestavuj přes `scripts/owner_line.py`
(`format_owner_div` / `format_owner_line`) — ne ručně kopíruj celý seznam
účastníků včetně ownera.

Karta bez diskuse dostane navíc třídu `quiet`: `<article class="card quiet">`.

### Badge podle statusu

| Status | Třída | Text |
|---|---|---|
| `discussed` | `b-done` | Projednáno |
| `mentioned_only` | `b-touch` | Jen zmíněno |
| `not_discussed` | `b-none` | Neprojednáno |
| `removed` | `b-out` | Vyřazeno |
| `context` | `b-touch` | Kontext |

### Parkoviště

Dvousloupcová mřížka karet:

```html
<div class="park">
  <article class="card"><h3>Téma</h3>
    <div class="block"><ul class="bullet-list"><li>…</li></ul></div>
  </article>
</div>
```

### Konsolidovaný seznam úkolů (povinné v HTML)

MD sekce `## Konsolidovaný seznam úkolů` → v `body.html` **vždy HTML `<table>`**,
ne `div.block.tasks` / `<ul>` uvnitř karty. `block tasks` + šipkové `<li>` patří
**jen** na kartu oblasti („Úkoly, které padly“), ne na závěrečný přehled.

Preferovaný vzor (Finance Sync / Lucie&Luky / Strategická 5. 10.):

```html
<section class="area">
  <div class="area-head">
    <div>
      <div class="section-label">Úkoly</div>
      <h2>Konsolidovaný seznam</h2>
    </div>
  </div>
  <table>
    <thead><tr><th>Kdo</th><th>Úkol</th><th>Kontext / termín</th><th>Sekce</th></tr></thead>
    <tbody>
      <tr><td class="who">Jméno</td><td>Úkol</td><td>termín</td><td>1.2</td></tr>
    </tbody>
  </table>
</section>
```

Sloupec `Sekce` je volitelný (stačí 3 sloupce). Alternativa bez `section.area`:
jen `<div class="section-label">Úkoly, které padly</div>` + stejná `<table>`.
**Zakázáno:** `<h4>Úkoly ze schůzky</h4>` + flat list s šedým `(kontext · sekce)`.

### Plán dalších setkání

Tabulka `datum | co | kdo | pozn.` (stejný `section.area` vzor jako u úkolů).
Seznam v kartě jen když jsou termíny ≤ 3.

**Tvrdé — jen setkání/eventy:** řádek = budoucí schůzka, recurring meeting, offsite,
workshop, call **jako kalendářní event**. **Nikdy** úkol s deadlinem / action item
(„rozhodnout X do konce měsíce“, „doplnit milníky do huddle“, „call s Y“ bez slotu
v kalendáři jako samostatný event — pokud je to follow-up úkol, patří do Úkolů).
Příští recurring Strategy / Huddle doplň z kalendáře, když v přepisu chybí datum.
Test: „šlo by to založit v Google Calendar?“ — ne → do konsolidované tabulky úkolů.

**HTML footer:** default žádný. Zakázaný boilerplate o vaultu / Downloads / Rámci.

---

## MD — schéma pro AI agenty

MD nečte člověk, čtou ho agenti kolegů. Proto jednotná pole a stabilní `id`.

### Frontmatter (povinný)

```yaml
---
doc_type: meeting_summary
title: "Název schůzky"
meeting_date: 2026-09-14
source_transcript: "cesta k Sembly přepisu ve vaultu"
source_structure: "odkud je osnova — list tabulky + sloupce, nebo 'vlastní osnova'"
period: "období, kterého se schůzka týká"
audience: "komu je zápis určen"
variant: full          # full | shared
language: cs
participants: [ ... ]
drive_folder: "https://drive.google.com/drive/folders/<ID>"  # povinné — kanonické MD pro tým
extraction_rules:
  - "Obsahuje POUZE to, co v přepisu explicitně zaznělo."
  - "Úkoly jsou pouze explicitně zadané a přidělené konkrétní osobě."
  - "Body bez diskuse jsou zachovány se statusem, ne vynechány."
status_values: [discussed, mentioned_only, not_discussed, removed, context]
name_aliases:
  Přezdívka: Plné Jméno
---
```

U `variant: shared` přidej i `redacted: true` a jednu větu, co bylo vynecháno.

**`drive_folder` (povinné):** URL sdílené Drive složky, kam se po zápisu nahraje kanonické MD
pro tým. Lookup: tabulka ve `.cursor/rules/internal-meeting-slack.mdc` (Strategická /
Strategy sync má folder). Jiná schůzka bez řádku → zeptej se. Vault
`05-RESOURCES/vystupy/zapisy/` = pracovní kopie; Slack dostane jen odkaz na Drive MD
+ HTML jako přílohu. V `## 0. Meta` doplň řádek `Úložiště MD: …`.

### Položka

```markdown
### 2.1 JAK: Název aktivity
- **id:** `oblast/aktivita`
- **status:** discussed
- **owner:** Jméno
- **key_people:** Jméno, Jméno   # bez ownera; v HTML přes owner_line.py

**Co zaznělo**
- …

**tasks**
- [ ] Jméno — úkol.
```

Když úkoly nepadly, napiš `**tasks** — žádné`. Nikdy pole nevynechávej — agent by
nepoznal rozdíl mezi „nebyly" a „nezpracováno".

`id` je stabilní slug `oblast/aktivita` bez diakritiky. Při aktualizaci zápisu ze
stejné série schůzek drž stejné `id`, ať se dají porovnat v čase.

### Tasky odvozené ze zápisu

Po zápisu jdou do `02-PROJEKTY/…/tasks/` řádky podle **upravené chat preview** tabulky
(Vault? / Projekt / Waiting) — wording z **post-merge MD** (konsolidovaná tabulka + karta).
Task musí být **samonosný** (Cíl + Kontext ze zápisu + *proč/DoD* u kroků) a mít
`materials:` na tento MD — detail ve skillu `agenda-zapis-ze-schuzky` → Krok 8.
Zápis zůstává kanónem „co zaznělo“; task je zhuštěný závazek, ne kopie karty.

### Meta — Highlights (povinné u `variant: full`)

Pod `## 0. Meta` vždy blok `### Highlights` a **přesně 3** top-level odrážky `- …`
(stejné tři teze jako v HTML). U `variant: shared` je blok povinný jen když ho
vstupu už máš — pak také přesně 3.

```markdown
## 0. Meta

Rámec: …

Úložiště MD: https://drive.google.com/drive/folders/<ID>  # kanonické sdílení (Drive); vault = pracovní kopie

### Highlights
- První klíčový závěr.
- Druhý klíčový závěr.
- Třetí klíčový závěr.
```

`Rámec:` zůstává **jen v MD** (agentí kontext). Do HTML hero / lead / kicker se
nekopíruje — viz skill „HTML vzhled — standard“.
`Úložiště MD:` patří do Meta; v HTML stačí **jedna krátká věta** v howto / meta
(ne starý footer boilerplate o vaultu/Downloads).

Fingerprint (`rbedu-grammar-nazi` / `md_fingerprint.py`) počítá jen tyto top-level `-`.

### Povinné sekce

1. `## 0. Meta` — rámec schůzky + `### Highlights` (3× `-` u full)
2. `## 1.–N.` — oblasti a položky
3. `## Co v prioritách vědomě není` (když to zaznělo)
4. `## Mimo strukturu / Parkoviště`
5. `## Konsolidovaný seznam úkolů` — tabulka `Kdo | Úkol | Kontext/termín | Sekce`
6. `## Plán dalších setkání` (když padl)
7. `## Poznámky k věrohodnosti`
