# Plán: sb-dashboard-materials

## Zadání a požadavky

| R# | Požadavek | Zdroj |
|---|---|---|
| **R1** | Při ukládání tasků se uloží i související materiály a odkazy na ně (příklad: Slack / web registrace jako u IAD-T168). | Zadání uživatele (doslovně) |
| **R2** | Pole `materials` ve frontmatter: URL i `[[wikilink]]`; při **Uložit** v Detailu i při **Založit** v Nový. | Rozhodnutí z konverzace |
| **R3** | URL z textu Detailu se při save/create **sloučí** do `materials` (harvest). | Rozhodnutí |
| **R4** | Brain `update_task` musí umět YAML **list** bez orphan řádků (incident: line patch nahradil jen `materials:` a nechal `- url`). | Rozhodnutí + incident IAD-T168 |
| **R5** | Ostrý vault zápis IAD-T168 **není** T# této pipeline (už opraveno ve vaultu `36a6a7b4`). | Rozhodnutí |
| **R6** | UI produkt `second-brain-dashboard`: vizuální B# + T# layout probe; Tester povinný (ne skip „profil SECOND_BRAIN“ bez „bez UI“). | Brief + `subagent-ui-gate` |
| **R7** | Nasazení: push `main` → Coolify (Brain + dashboard); lokální gate: pytest Brain + vitest dashboard. | Projektový profil / brief |

**Mimo rozsah**

- Změna export `fields=full` vs `standard` (materials se berou z `api.item` → `frontmatter` při `openDetail`). **CAS baseline materials = `materialsOriginal` (A15), ne rozšíření standard exportu.**
- Redesign Detail panelu / nové stránky.
- Automatické zakládání souborů ve `materials/` z URL (jen frontmatter list stringů).
- Hromadná oprava historických tasků.
- UI coerce / migrace **skalárního** legacy `materials:` (string místo listu) — jen Rizika (**A10**).
- Alembic, RBAC Universe, Celery, subnav Universe, `qa_gate.mjs` — **netýká se** (SECOND_BRAIN).

---

## Předpoklady

| A# | Předpoklad | Proč / stav |
|---|---|---|
| **A1** | Lokální WIP (necommitnutý) v Brain + dashboard je **správný směr**; IMPLEMENT ho dokončí / drobně doplní, nepřepisuje od nuly. | Kód už pokrývá R2–R4; chybí normalizace/preview/COMPARE/test gaps níže. |
| **A2** | Harvest = jen `http(s)` (přes `extractUrls` / `toHref`); `[[wikilinky]]` jen z textarea Materiály, ne z volného textu Detailu. `www.` / bare domain → `toHref` → `https://…`. | `linkify.js:45-71`; wikilink regex v Detailu není. |
| **A12** | **`canonicalizeMaterialLine(s)`** (kritik NEW-1): trim; pokud řádek vypadá jako `[[…]]` → **passthrough beze změny** (nesmí jít přes `toHref` — ten by přidal `https://` nebo vrátil `null` a wikilink by zmizel). Jinak `toHref(s)`; `null` = neplatná URL → řádek **drop**. Harvest z Detailu zůstává přes `extractUrls` (už kanonické). | R2; `linkify.js:58-70` |
| **A13** | **`materialsKey(value)`** (NEW-2 + NEW-6): jedna serializace pro COMPARE / `baselineOf.materials` / `fieldValue("materials")` / Q9. Vstup **`list \| string \| null/undefined`**: array → map `canonicalizeMaterialLine` (drop null); string → split řádků (trim, drop empty) → stejná kanonizace; null/undefined → `""`. Výstup join `"\n"` (ne `String(array)`). | A5, B8 |
| **A16** | Dirty / Zahodit = **jen form fields** (ne `effectiveMaterials ≠ materialsOriginal`). Jinak harvest-only zacyklí panel (NEW-7). | discardDetailEdits |
| **A15** | **CAS baseline materials** (kritik NEW-5): list export `fields=standard` **neobsahuje** `materials`. `baselineOf(detail)` z `byId` by měl `materials` prázdné i když Detail má položky z `api.item`. Proto **`baseline.materials = materialsKey(draft.materialsOriginal)`** (snapshot z openDetail), **nikdy** `task.materials` / `detail.materials` z list řádku. Concurrent jen když vault FM materials ≠ tento original. | B8, T10 |
| **A14** | Při `openDetail` je `materialsOriginal` (a textarea seed) už zkanonizované stejně jako effective (A12) — raw FM vs URL.href nesmí dělat falešné dirty (kritik NEW-3). | B7, B2 |
| **A3** | Prázdný seznam po clear = zápis `materials: []` (ne smazání klíče). | Existující test `test_render_frontmatter_patch_empty_materials_list`. |
| **A4** | Net-new UI shell **není** — jen pole v existujícím Detail/Nový chrome → **Vizuální gate člověka: ne**; vizuální B# + layout probe ano. | **Potvrzeno Šťoural Q2 / r=2.** Ledger: `Vizuální gate člověka: ne`. |
| **A5** | Konflikt CAS u `materials` stejným `openConflict`; MVP přidá `materials` do `COMPARE_FIELDS`, `fieldValue("materials")` → `materialsKey`, `Q9_LABELS.materials`, conflict rows. **`baselineOf(task)` materials z list řádku nepřidávat** (standard export je nemá) — materials baseline jen při save dle **A15** (`materialsKey(draft.materialsOriginal)`). | Dnes `COMPARE_FIELDS` / `baselineOf` materials nemají (`App.jsx:91`, `:377-386`). |
| **A6** | Řádek materials v `pipeline-exceptions.md` (2026-11-01) se touto pipeline **nahrazuje** jako způsob dodání; historický řádek se nemaže. | Brief. |
| **A7** | Objem `materials` na task ≪ 50 položek; žádný nový N+1 ani změna export payloadu. | MVP frontmatter list. |
| **A8** | Busy mutex stávající (`useBusy` / `withBusy` / `isBusy`): Detail Uložit i Nový Založit → **≤1** úspěšný PATCH/POST materials; dvojklik neprovede druhý zápis. | `saveDetail` guard `isBusy` (`App.jsx:642`); button `disabled={isBusy}`. B9 na A8 odkazuje. |
| **A9** | Selhání Brain/BFF/síť při save materials (i při `editBody` po úspěšném PATCH) → **error dialog** (`kind: "error"`); žádný tichý OK / tiché leaveDetail. | Stávající `setDialog({ kind: "error", … })`; B10 na A9. |
| **A10** | Skalární legacy `materials:` (YAML string místo listu) **mimo rozsah UI** — žádný FE coerce, žádný openDetail special-case. Jen dokumentované Riziko; Brain normalize při PATCH listu může string→řádky (F1), ale UI nepředpokládá scalar display. | **Potvrzeno Šťoural.** |
| **A11** | Dual-write Detail save: 1) PATCH FM (vč. materials) 2) volitelně `editBody` Detail řádku. Když PATCH OK a `editBody` fail → **bez rollbacku** materials; error dialog (B10); materials ve vaultu zůstanou. Dokumentované riziko, ne transakce. | **Potvrzeno Šťoural.** Kód: `App.jsx:679-702`. |

---

## Současný stav (ověřeno v kódu)

### Brain — YAML list patch (WIP, správný směr)

- `vps/second-brain-brain/app/tools/update_task.py:44-112` — `_yaml_value` umí `list`; `_skip_yaml_value` přeskočí staré indented `-` řádky.
- `tests/test_update_task_cas.py:22-55` — regresní testy replace list + empty `[]`.
- `update_task` předá patch bez dedupe/coerce listu — **díra** vůči create.

### Brain — create

- `create_task.py:39-70` — `_normalize_materials`, `_yaml_list_block`; vždy píše `materials`.
- `main.py:385-412` — `CreateTaskBody.materials: list[str] = []`.
- Pytest create s materials **chybí**.

### BFF

- `dashboard_bff/app.py:162-181` — POST create přeposílá materials list.
- PATCH `_clean_patch` nestripuje `materials` — OK.
- BFF test create+materials **chybí**.

### Dashboard UI (WIP, správný směr)

- `App.jsx:128-147` — `materialsToText` / `textToMaterials` / `mergeMaterials`. Harvest už jde přes `extractUrls`→`toHref`; **díra**: řádky z textarea + `materialsOriginal` bez `canonicalizeMaterialLine` / bez sjednocení s effective (NEW-4).
- `openDetail` (`:464-496`) — array only z `item.frontmatter.materials` (A10).
- `saveDetail` (`:667-702`) — merge + dual-write `editBody` (A11).
- Náhled / dirty / „Beze změny“ / `discardDetailEdits` — jen raw textarea, ne harvest.
- `COMPARE_FIELDS` / `baselineOf` / `fieldValue` / `Q9_LABELS` — bez materials.
- `linkify.js:45-71` — `extractUrls` → `URL.href`.
- Vitest Detail harvest OK; create / B11 / conflict materials / layout probe materials **chybí**.

### Verdikt WIP

| Oblast | Verdikt |
|---|---|
| Brain list YAML + skip orphans | **Ponechat** |
| create + BFF materials | **Ponechat** |
| Detail/Nový UI + harvest | **Ponechat** |
| Doplnit | normalize update; effectiveMaterials na náhled/Beze změny/save (**ne** dirty — A16); COMPARE+A15 baseline; B11; testy; layout probe |

---

## Návrh

### 1) Brain — sdílená normalizace + update path (R1, R4)

| Soubor | Změna | R# |
|---|---|---|
| `materials_yaml.py` **(nový)** | Sdílený `normalize_materials` (Q4 default). | R2, R4 |
| `update_task.py` | Před patch: normalize materials; neměnit sémantiku `_yaml_value` / `_skip_yaml_value`. | R4 |
| `create_task.py` | Import společného normalizeru. | R2 |
| `test_update_task_cas.py` | Orphan IAD; string→list; dedupe. | R4 |
| `test_create_and_bulk.py` | create materials URL+wikilink. | R2 |

### 2) BFF (R2)

| Soubor | Změna |
|---|---|
| `app.py` | Beze změny. |
| `test_bff.py` | POST create → Brain `materials` list. |

### 3) Dashboard FE

| Soubor | Změna | R# / A# |
|---|---|---|
| `App.jsx` | `canonicalizeMaterialLine` + `effectiveMaterials(draft)` = merge(`canonicalize` na textarea řádky) + `extractUrls(detail)`; **wikilink nikdy přes `toHref`**. Create: stejné. | R2, R3, A12 |
| `App.jsx` | **effectiveMaterials jen na:** (1) náhled `materials:`; (2) řádek „Beze změny“ u materials (srovnání effective vs original); (3) `saveDetail` / create patch. **NE** do dirty/`discardDetailEdits` — dirty = jen form fields (`draft.materials` vs `materialsOriginal`, detail vs detailOriginal, …). Harvest-only bez form editu → Zahodit = leaveDetail (NEW-7). | R3, B2, B11 |
| `App.jsx` | `openDetail`: `materialsOriginal` = `materialsKey`/`canonicalize` z FM listu (A14). | B7, NEW-3 |
| `App.jsx` | `COMPARE_FIELDS += "materials"`; při skládání baseline pro save: **`baseline.materials = materialsKey(draft.materialsOriginal)`** (A15 — ne z list tasku); `fieldValue("materials")` → `materialsKey` (list\|string); `Q9_LABELS.materials`; conflict rows přes `materialsKey`. **Bez A15 = Q9 skoro vždy (BLOCKER).** U `openConflict` mimo saveDetail: pokud baseline materials klíč nemá, **materials concurrent skip** (NEW-10) — nehlásit concurrent jen proto, že current má materials. | A5, A13, A15, B8 |
| `App.jsx` | B4: clear + Detail bez URL → `[]`. B11: clear + URL v Detailu → harvested URL, ne `[]`. | Q1 |
| `App.jsx` | Dual-write: PATCH → editBody; fail editBody → error dialog, bez rollbacku, bez tichého leaveDetail. | A9, A11, B10 |
| Testy | screens: create, harvest-only, B4, B11, conflict+baseline, editBody fail; layout probe B-V5m/B-V6m. | |

### 4) Docs / pipeline meta

- Tento plán; pipeline-exceptions supersede poznámka; ledger `Vizuální gate člověka: ne`.

### 5) Netýká se

DB/migrace, RBAC, Celery, subnav, export fields, skalární FM UI (A10).

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| **B1** | Detail materials URL+wikilink; Uložit | PATCH list obsahuje **oba**; wikilink beze změny (A12); FM bez orphan | R1,R2,R4 | T1, T3, **T18** |
| **B2** | URL v Detailu; textarea prázdné/partial; Uložit | union v materials; náhled ukáže změnu (effective) | R3 | T2, T4 |
| **B3** | Nový: materials + URL v Detail; Založit | POST union; YAML list | R2,R3 | T5, T6 |
| **B4** | Prázdná textarea **a** Detail bez URL; Uložit | `materials: []` | R2,R4 | T1, T7 |
| **B5** | update_task list patch na multi-line materials | blok nahrazen; 0 orphan | R4 | T1 |
| **B6** | patch materials jako multiline string | normalize → list | R4 | T8 |
| **B7** | openDetail: FM list, export bez materials | textarea + `materialsOriginal` zkanonizované (A14); bez falešného dirty | R2 | T9 |
| **B8** | CAS + concurrent materials | Q9 jen když vault ≠ `materialsKey(materialsOriginal)`; baseline **z original** (A15), ne z list exportu; `materialsKey` list\|string (A13) | A5, A13, A15 | T10 |
| **B9** | Dvojklik Uložit | busy mutex (**A8**); ≤1 PATCH | A8 | T11 |
| **B10** | (a) PATCH error → dialog (**A9**). (b) PATCH OK + editBody fail → dialog, materials zůstávají, bez rollbacku (**A11**) | A9, A11 | T11, T16 |
| **B11** | Clear textarea + URL v Detailu; Uložit | re-harvest URL v materials, ne `[]` | R3, Q1 | T17 |
| **B-V5m** | Detail | aria Materiály a odkazy; looksBare false | R6 | T12 |
| **B-V6m** | Nový | aria Materiály nového tasku; looksBare false | R6 | T12 |

### Checklist A

1. Prázdná data — B4, B7, B11.  
2. None/coerce — B6; scalar → A10.  
3–4. Netýká se.  
5. Session; bez nové RBAC.  
6. CAS B8; ne Celery.  
7. Archiv reject BFF.  
8. B9 ← A8.  
9. B10 ← A9 (+ A11).  
10. Zpětná kompatibilita + A10.  
11. Netýká se PD↔Allfred.

---

## Výkonový rozpočet (P)

Stejná tabulka jako v1: 1 task FM I/O; payload ≪ 10 KB; 1 PATCH (+ volitelně 1 editBody); FE O(n); cíl api_ms &lt; 500 ms, UI warm &lt; 1,5 s. Body 1–11 checklistu B — SQL/worker/stránkování **netýká se**.

---

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | pytest | gate | test_update_task_cas.py | B1,B4,B5 |
| T2 | vitest | gate | screens.test.jsx harvest | B2 |
| T3 | pytest | gate | orphan IAD | B5 |
| T4 | vitest | gate | effectiveMaterials: náhled + Beze změny; **negativní:** harvest-only bez form editu → dirty false / Zahodit leaves (A16) | B2 |
| T5 | vitest | gate | createTask harvest | B3 |
| T6 | pytest | gate | test_create_and_bulk.py | B3 |
| T7 | vitest | gate | B4 clear + Detail bez URL | B4 |
| T8 | pytest | gate | string coerce | B6 |
| T9 | vitest | gate | openDetail list FM | B7 |
| T10 | vitest | gate | (a) list task bez materials + item FM list → materials edit bez falešného Q9; (b) vault≠original → Q9; (c) materialsKey list i string | B8 |
| T11 | vitest | gate | busy + PATCH error dialog | B9,B10(a) |
| T12 | vitest probe | gate | layout-views B-V5m/B-V6m | B-V* |
| T13 | pytest BFF | gate | test_bff.py | B3 |
| T14 | Playwright-smoke | gate/QA | Coolify Detail Materiály | B-V5m |
| T15 | Playwright-T6-full | **Tester** | Coolify po deployi | B1–B4,B11,B-V* |
| T16 | vitest | gate | PATCH OK + editBody fail | B10(b) |
| T17 | vitest | gate | B11 re-harvest | B11 |
| T18 | vitest | gate | Detail (+ ideálně Nový): URL+wikilink → PATCH/POST zachová `[[wikilink]]` | B1 |

**T6 pack:** harvest-only; Nový; B4 clear; **B11** clear+URL; **wikilink round-trip (T18)**; adversarial double-save; Zahodit po form edit; harvest-only clean Zahodit leaves; layout.  
**Vizuální gate člověka: ne (A4).**  
**Mimo T#:** ostrý IAD-T168 (R5).

---

## Pořadí implementace

1. **F1** — normalize + update_task; T1/T3/T8  
2. **F2** — create pytest T6  
3. **F3** — effectiveMaterials + B4/B11 + COMPARE/baselineOf/fieldValue/Q9; T2/T4/T7/T9/T10/T17  
4. **F4** — T5, T13, T16, T11  
5. **F5** — layout probe T12  
6. **F6** — lokální gate → commit `main` (bez push do REVIEW)  
7. **F7** — push → Coolify → QA → testerGate → Tester T15  
8. **F8** — ledger gate ne; DONE audit  

---

## Rizika a zpětná kompatibilita

1. Orphan regres → T1/T3.  
2. Harvest / B11 překvapení (clear nevymaže, dokud URL v Detailu) — náhled přes effective.  
3. **URL.href vs ruční řádek** — kanonizace v merge.  
4. **Dual-write (A11)** — materials OK, Detail ne; bez rollbacku.  
5. **Skalární legacy FM (A10)** — mimo UI.  
6. Export standard bez materials do openDetail.  
7. Jiné list klíče MCP — `_skip_yaml_value` obecně; mimo MVP.  
8. Souběh bez baselineOf → tichý overwrite / falešný casOnly.  
9. UI gate: Tester ano; vizuální gate člověka ne.
10. Wikilink přes toHref → smazání (NEW-1) — A12 + T18.
11. `String(materials[])` ve fieldValue → falešný concurrent (NEW-2) — A13 + T10.
12. materialsOriginal raw vs effective kanonické → falešné dirty (NEW-3) — A14.

---

## Otevřené otázky pro uživatele

*Žádný otevřený seznam — uzavřené defaulty:*

| # | Default |
|---|---|
| Q1 | B11 re-harvest |
| Q2 | Vizuální gate = ne (A4) |
| Q3 | COMPARE + baselineOf.materials ano (A5) |
| Q4 | `materials_yaml.py` ano |
| Q5 | Harvest www/bare přes toHref (A2) |
| Q6 | Skalární UI mimo rozsah (A10) |
| Q7 | Dual-write bez rollbacku (A11) |
| Q8 | canonicalize wikilink passthrough (A12); materialsKey (A13); original kanonický (A14) |
| Q9 | CAS baseline z materialsOriginal (A15); materialsKey dual input (NEW-6) |

---

## Delta oproti plánu v1 (Šťoural r=2)

- B4 zpřesněn; **B11** nové; B10 rozšířen.  
- A8–A11 doplněny; A4 potvrzeno.  
- COMPARE: explicitní baselineOf.materials.  
- effectiveMaterials vyjmenován.  
- Rizika dual-write / scalar / URL.href.  
- Otázky uzavřeny.  
- T16, T17; T6 pack B4/B11.

## Delta oproti r=2 (kritik NEW-1…4 → r=3)

- **A12** `canonicalizeMaterialLine`: `[[wikilink]]` passthrough; `toHref` jen URL-like.  
- **A13** `materialsKey` pro COMPARE / baselineOf / fieldValue / Q9.  
- **A14** `openDetail` → kanonický `materialsOriginal`.  
- B1 + **T18** FE wikilink round-trip; B7/B8 text; WIP claim upřesněn (NEW-4).  
- Rizika 10–12.

## Delta oproti r=3 (kritik NEW-5/NEW-6 → r=4)

- **A15:** baseline.materials = materialsKey(draft.materialsOriginal), ne list export.
- **A13** rozšířen: materialsKey(list|string|null).
- B8 + T10 fixture bez falešného Q9.

## Delta oproti r=4 (kritik NEW-7/NEW-8 → r=5)

- **A16** + §3: effectiveMaterials ne do discard dirty; dirty = form only.
- **A5** upřesněno vůči A15 (ne materials z list řádku).
- T6 pack Zahodit sémantika opravena.

## Delta oproti r=5 (kritik NEW-9/NEW-10 → r=6)

- T4 + WIP verdikt: effectiveMaterials ne dirty (A16).
- openConflict: skip materials concurrent when baseline lacks materials key.
