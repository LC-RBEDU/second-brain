# Struktura výstupů — HTML komponenty a MD schéma

## HTML — dostupné komponenty

Do `body.html` se píše **jen obsah**, žádné `<style>`. Shell (hlavička s logem, hero,
patička) dělá `build_html.py` z `meta.json`.

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

### Tabulka úkolů

```html
<table>
  <thead><tr><th>Kdo</th><th>Úkol</th><th>Kontext / termín</th></tr></thead>
  <tbody>
    <tr><td class="who">Jméno</td><td>Úkol</td><td>termín</td></tr>
  </tbody>
</table>
```

### Plán dalších setkání

Buď vlastní `section.area` s kartou, nebo tabulka `datum | co | kdo | pozn.`
Použij tabulku, když jsou termíny víc než tři.

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

### Položka

```markdown
### 2.1 JAK: Název aktivity
- **id:** `oblast/aktivita`
- **status:** discussed
- **owner:** Jméno
- **key_people:** Jméno, Jméno

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

Po zápisu jdou Lukášovy řádky z konsolidované tabulky do `02-PROJEKTY/…/tasks/`.
Task musí být **samonosný** (Cíl + Kontext ze zápisu + *proč/DoD* u kroků) a mít
`materials:` na tento MD — detail ve skillu `agenda-zapis-ze-schuzky` → Krok 8.
Zápis zůstává kanónem „co zaznělo“; task je zhuštěný závazek, ne kopie karty.

### Povinné sekce

1. `## 0. Meta` — rámec schůzky, highlights
2. `## 1.–N.` — oblasti a položky
3. `## Co v prioritách vědomě není` (když to zaznělo)
4. `## Mimo strukturu / Parkoviště`
5. `## Konsolidovaný seznam úkolů` — tabulka `Kdo | Úkol | Kontext/termín | Sekce`
6. `## Plán dalších setkání` (když padl)
7. `## Poznámky k věrohodnosti`
