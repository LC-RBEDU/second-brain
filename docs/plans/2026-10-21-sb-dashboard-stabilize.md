# Plán: Second Brain dashboard stabilize (2026-10-21) — k=2 r=2

## Zadání a požadavky

R1 — Plná `/rbu-pipeline` + povinný Tester / T6; zákaz ad-hoc `pipeline-exceptions` pro dashboard UI.  
Zdroj: uživatel „vrať dashboard práci do plné /rbu-pipeline…; ad-hoc pipeline-exceptions pro UI končí“.

R2 — Nový ledger `docs/plans/2026-10-21-sb-dashboard-stabilize.pipeline.md`; starý `2026-10-19-sb-dashboard.pipeline.md` zůstává historický DONE se skip Testerem.  
Zdroj: rozhodnutí v ledgeru.

R3 — SECOND_BRAIN UI produkt: `testerGate=ano`, plný T6; zákaz `TESTER: přeskočeno (profil SECOND_BRAIN)` bez „bez UI“.  
Zdroj: skill `subagent-orchestration` § UI produkt + ledger.

R4 — Stabilizace chování + vizuální B#/probe proti stávajícímu shellu; Wiki busy-overlay. **Ne** redesign od handoffu 00–01.  
Zdroj: uživatel + ledger.

R5 — Busy 1:1 Wiki: `BusyOverlay` + `withBusy` (mutex); debounce show ≥150 ms; min visible ≥200 ms; Escape overlay nezavírá; během busy **disable primary** (`disabled` + `aria-busy`). Napojení všech mutací/prodlev: `saveDetail` (+ `editBody`), `move`, `confirmDoing` / `confirmWaiting`, `patchDate`, `submitCleanup`, `proposeFocus` / `applyFocus`, `createTask`, `openDetail`, Boot / `onRefresh`, Q9 „Přesto uložit“. Logo z Coolify rb-wiki → `web/public/logo.svg`.  
Zdroj: uživatel „stejný prvek jako Wiki“ + Q3b + A9–A13.

R5b (**C12 volba 1**) — Po úspěšném zápisu busy **zůstane i přes** `onRefresh` export: jeden plynulý čekací stav, dokud nedorazí data. Mutex **nesmí** zahodit programový refresh. Mutace uvnitř `withBusy` po success `await onRefresh()` **ještě před** finally hide (stejný busy slot); reentrant `load` povolený **jen** pro export. Po ok patch musí proběhnout **1×** `GET /api/export`.  
Zdroj: kritik C12 + odpověď uživatele volba 1.

R6 — Inventura (1)–(8): CAS/false Q9, silent Uložit vč. `!ok` bez reason + `editBody`, inline rodič, `move` null, `confirm*` tichý close, chybějící busy, debug `7873` do 1. Tester PASS pak strip celého `web/src`, historický skip Testera.  
Zdroj: inventura v ledgeru + Q1b.

R7 — Po Review SCHVÁLENO: push `main` → Coolify dashboard; lokální gate = pytest BFF + `npm test` (vitest) ve `web/`.  
Zdroj: profil SECOND_BRAIN + README dashboardu.

R8 — Shell gate 2026-10-19 zůstává `ano`. Busy: povinný lidský vizuální gate (Q2b); bez `ano` není DONE.  
Zdroj: Q2b.

R9 — Debug ingest `7873` ponechat do 1. Tester PASS; strip z celého `web/src` (`App.jsx` + `chrome.jsx` + `rg`); pak REVIEW → push → QA → T22-reuse. DONE jen na strip SHA.  
Zdroj: Q1b + A15–A17.

Mimo rozsah: změna Brain API / vault schématu; redesign wireframů; hub cron; `pipeline-exceptions.md` pro UI; strip debugu před Tester PASS.

## Předpoklady

A1 — Brain kontrakt beze změny; BFF jen proxy (`vps/second-brain-dashboard/bff/`).  
A2 — `kanbanPatch` null jen při terminal close s otevřenými dětmi (`writes.js:41–50`); non-terminal vždy `{ status }`.  
A3 — CAS silent retry / casOnly force zůstává v `openConflict` (ověřeno `App.jsx:347–376`); falešný Q9 nesmí při casOnly.  
A4 — Logo = asset z Coolify rb-wiki; F1 → `web/public/logo.svg` (složka `public/` dnes chybí).  
A5 — Objem exportu ~500 open tasks (ověřit `GET /api/export` count před QA).  
A6 — Shell gate 2026-10-19 = `ano`.  
A7 — Žádné `pipeline-exceptions` pro dashboard UI.  
A8 — Checklist A/B: body 4–7, 11 u SPA = netýká se (viz B# / P).  
A9 — Mutex: **uživatelský** druhý call během busy neodešle mutaci; primary `disabled` + `aria-busy`. **Výjimka C12:** programový `onRefresh`/`load` exportu smí běžet reentrantně uvnitř aktivního busy slotu mutace — mutex ho **nezahodí**.  
A10 — Null patch copy: Done/Cancelled → open_child + id; jinak generický text + id.  
A11 — Min visible overlay 200 ms (měřeno od prvního show do hide; refresh uvnitř slotu neresetuje na nový debounce flash).  
A12 — Logo Coolify rb-wiki.  
A13 — Úklid: dialog jen při `ok === false` bez `failed`/`pending` lines.  
A14–A18 — Boot/`onRefresh` = **B10** (B12 = `createTask`).  
A15 — DONE = Tester PASS na **strip** SHA (T22-reuse).  
A16 — F8 busy gate před F9 QA; strip neopakuje lidský busy gate.  
A17 — F12 = Review → push → QA → T22-reuse.  
A19 — T17 = hard vitest B-V* + looksBare===false; T18 busy screenshot; T19 ledger `ano`.  
A20 — `patchDate` ⊂ B9 (+ B2/B3); žádný tichý fail.  
A21 — T6 „Focus“ = Radar dlaždice + B14 (ne B-V-Focus).  
A22 (**C10**) — throw/network u R5 mutací → error přes **error bridge** (A24), ne holé `setDialog` v provideru; `finally` hide.  
A23 (**C11**) — neprázdný busy subtitle; selektor **`[data-busy-subtitle]`** povinný (C15).  
A24 (**C13**) — `BusyProvider` vystaví `onError` callback / lehký bus:  
- `Boot` registruje `onError → setError(...)` (textový stav před App mount / export fail),  
- `App` registruje `onError → setDialog({ kind: "error", text })`.  
Provider **nikdy** nevolá `setDialog` přímo (App state mimo strom Boot).  
A25 (**C14**) — `createTask` client guard (`Doing` bez deadline / `Waiting` bez waitUntil, dnes `App.jsx:762–763` tichý `return`) → **error dialog** s čitelným textem; T12 `expect` dialog.  
A26 (**C16**) — StrictMode: `withBusy` / Boot `load` nese `generation` (nebo `AbortController`); zastaralý běh nevolá `setState` po unmount; `finally` vždy clear busy i při unmount/abort.
A27 — C12 copy: ponechat mutační title/subtitle do hide (ne přepínat na Načítám…).
A28 — Export ≫2k mimo plán.
A29 — T22-reuse = plný cross-cut vč. B20.
A30 — B10 setError jen Boot-only (`!data`); po App mount = bridge→setDialog.
A31 — Reentrant load uvnitř mutace: žádný druhý debounce/drop; 1× GET /api/export.
A32 — openConflict success nevolá vlastní onRefresh, pokud caller už await refresh ve slotu.
A33 — C14 guard dialog: čitelná CS copy; T12 assert dialog + smysl.

## Současný stav (ověřeno v kódu)

| Soubor:řádky | Fakt |
|---|---|
| `web/src/ui/App.jsx:29–48` | `ERROR_TEXT` + `errorMessage` |
| `App.jsx:245–270` | `openDetail` bez try/catch, bez busy |
| `App.jsx:282–417` | `openConflict` CAS retry/casOnly; `!ok` bez reason → tichý `return false` (416) |
| `App.jsx:419–518` | `saveDetail` catch síť→dialog; `editBody` bez ok/catch; po ok volá `onRefresh?.()` mimo busy |
| `App.jsx:520–598` | `move` / `confirm*` silent větve |
| `App.jsx:695–723` | `submitCleanup` reject bez lines bez dialogu |
| `App.jsx:737–780` | focus partial; **`createTask` guard 762–763 tichý return**; po ok `onRefresh?.()` fire-and-forget |
| `App.jsx:790–813` | `patchDate` bez catch/busy |
| `App.jsx:1060–1100` | view Issues = Chybně zadané (B-V8) |
| `App.jsx:1638+`, `1776–1778` | Nový: radiogroup; CTA **„Založit“** |
| `App.jsx:2063–2071` | Q9 Přesto uložit fire-and-forget |
| `App.jsx` + `chrome.jsx:40+` | debug `7873` |
| `web/src/main.jsx:63–84` | Boot holé „Načítám“; `onRefresh={load}`; StrictMode (89–92); error jen `setError` string |
| `web/src/index.css` | bez `.busy-*` |
| `web/public/` | neexistuje |
| `web/src/ui/debug-views.probe.test.jsx` | layout probe log-only (bez `expect`) |
| Wiki SSOT | Coolify rb-wiki `layout.js` + `wiki.css` |

## Návrh

### 0) Wiki SSOT — selektory a copy (R5, C6, C8, C11, C15)

F1 ověřit Coolify rb-wiki, port 1:1:

**Selektorová smlouva:**

- `#busy.busy-overlay` (z ≥ 60, blur, `cursor: wait`)
- `[role=status][aria-live=polite]`, `[aria-busy=true]`
- `.busy-card`, `.busy-pulse`, SVG spin, `img[src="/logo.svg"]`
- `[data-busy-text]` (title)
- **`[data-busy-subtitle]`** (subtitle — **povinný**, C15) — neprázdný text
- `.busy-bar`
- brand `#e9244a`
- `@media (prefers-reduced-motion: reduce)`: vypnout pulse + bar

**Copy (title / subtitle):**

| Operace | Title `[data-busy-text]` | Subtitle `[data-busy-subtitle]` |
|---|---|---|
| saveDetail / editBody / Q9 | Ukládám… | Zapisuji změnu do vaultu |
| move / confirm* / patchDate | Ukládám… | Ukládám změnu úkolu |
| submitCleanup | Provádím úklid… | Zapisuji dávku do vaultu |
| proposeFocus / applyFocus | Ukládám fokus… | Nastavuji focus týden |
| createTask | Zakládám úkol… | Vytvářím nový záznam |
| openDetail | Načítám… | Otevírám detail úkolu |
| Boot / standalone refresh | Načítám… | Stahuji export otevřených úkolů |
| **refresh uvnitř mutace (C12)** | **ponechat mutační title** (A27) | **ponechat mutační subtitle** do hide — nepřepínat na Načítám… |

Escape na overlay ignorovat. R#: R5, R8.

### 1) `BusyProvider` + `BusyOverlay` + `withBusy` (R5, R5b, A9, A22–A26)

Soubory:

- `web/src/ui/BusyContext.jsx` — context + `withBusy` + error bridge
- `web/src/ui/BusyOverlay.jsx` — portál / fixed overlay
- `web/public/logo.svg`

**API (kontrakt):**

```text
BusyProvider({ children, onError })
withBusy(title, subtitle, fn, options?)
  options.refresh?: () => Promise<void>   // C12: await uvnitř slotu před hide
  options.kind?: "mutation" | "export" | "read"
```

**Error bridge (C13 / A24):**

1. Provider drží `onErrorRef` (prop `onError` + volitelně `useBusyErrorHandler(fn)` z App).  
2. V `catch` volá `onErrorRef.current?.(message)` — **nikdy** `setDialog`.  
3. `main.jsx` Boot: `<BusyProvider onError={(msg) => setError(msg)}>` — před App / export fail.  
4. `App` mount: registruje handler → `setDialog({ kind: "error", text: msg })` (přepíše/rozšíří bridge pro dialogy, dokud je App mounted).  
5. Po unmount App obnovit Boot handler (nebo stack handlerů).

**Mutex + C12 reentrancy (A9 zpřesnění):**

| Vstup | Chování |
|---|---|
| Uživatel klikne druhou mutaci při `busy` | drop (return); primary disabled |
| Uvnitř aktivního `withBusy` mutace: `await options.refresh()` / `onRefresh` | **povolit** — stejný slot, žádný druhý overlay debounce „start“; žádný drop |
| Standalone Boot `load` / manuální refresh bez vnějšího slotu | vlastní `withBusy("Načítám…", …)` |
| Po ok mutaci | **povinně** `await onRefresh()` (1× `/api/export`) **před** finally hide — B20 |

Implementační preferovaná varianta (volba 1):

```text
await withBusy(title, subtitle, async () => {
  const result = await api.patch(...);
  // handle !ok / dialogs — při fail: return bez refresh
  if (!ok) return;
  await onRefresh(); // reentrant export; busy stále visible
});
// finally: min-200ms pak hide
```

Alternativa ekvivalentní: `withBusy` po success `fn` automaticky `await refresh` pokud `options.refresh` předáno — preferuj explicitní `await onRefresh()` v call site kvůli čitelnosti B20.

**StrictMode (C16 / A26):**

- Každý `withBusy` / `load` inkrementuje `generation` nebo používá `AbortController`.  
- Po `await`: pokud `generation !== current` nebo `signal.aborted` → nesetovat data/dialog ze zastaralého běhu; **přesto** finally clear busy jen pokud generation match (nebo refcount busy).  
- Unmount Provider: clear timers (debounce show), `busy=false`, abort in-flight export pokud ještě nemá consumer.

**Disable primary:** všechny `btnPrimary` + InlineStatus + kanban drop ignore když `busy` (user mutex).

### 2) Napojení R5 mutací + C12 refresh (F2)

| Funkce | Soubor | Busy + refresh |
|---|---|---|
| Boot `load` | `main.jsx` | withBusy Načítám…; 401 OAuth; !ok → onError/setError |
| `onRefresh` jako standalone | přes `load` | stejné |
| `openDetail` | `App.jsx` | withBusy read; catch→bridge; **bez** export refresh |
| `saveDetail` (+ editBody) | `App.jsx` | mutace; po ok **await onRefresh** v slotu (C12); editBody fail→dialog, stay Detail, bez refresh |
| Q9 Přesto uložit | `App.jsx:2063+` | async withBusy; po ok await onRefresh |
| `move` / confirm* / `patchDate` | `App.jsx` | po ok await onRefresh |
| `submitCleanup` | `App.jsx` | po ok await onRefresh |
| `proposeFocus` | `App.jsx` | typicky bez full export pokud jen dialog; po `applyFocus` ok → await onRefresh |
| `createTask` | `App.jsx` | guard→dialog (C14); po ok await onRefresh |
| openConflict success paths | kde dnes `onRefresh?.()` | přesunout do caller `withBusy` slotu (ne dvojí export) |

**Invariant B20:** po úspěšném PATCH/POST/cleanup/apply/create, které dnes volají `onRefresh`, musí network log / mock ukázat **právě 1×** `/api/export` v tomtéž busy slotu; overlay nesmí zmizet mezi koncem mutace a koncem exportu.

### 3) Silent paths (R6, Q4a, A10, A13, C14)

| Změna | Chování | B# |
|---|---|---|
| `openConflict` `!ok` bez reason | error dialog přes App (ne ticho) | B3 |
| `editBody` fail/throw | dialog, stay Detail, bez refresh | B3 |
| `openDetail` throw | bridge→dialog; finally hide | B15 |
| `move` null | vždy dialog A10 | B6 |
| `confirm*` unknown/throw | dialog (ne close) | B7 |
| **`createTask` guard** | Doing w/o deadline / Waiting w/o waitUntil → **error dialog** (ne `return`) | B12 / C14 |
| `createTask` `!ok` | error dialog | B12 |
| cleanup reject bez lines | dialog A13 | B13 |
| Q9 | await + busy + refresh | B2, B20 |

Debug `7873` do F11.

### 4) Layout probe T17 (C2, C9)

Přepsat `debug-views.probe.test.jsx` → hard `expect` (např. `layout-views.probe.test.jsx`):

- B-V1…B-V8 DoD + `looksBare === false` kde platí  
- FAIL = FAIL `npm test`  
- Log-only nestačí

B-V6 CTA = **„Založit“** (`App.jsx:1777`).

### 5) Dvě deploy vlny + pipeline

Stejné jako r=1: feature+debug → F8 gate → QA → Tester → strip → REVIEW → push → QA → T22-reuse → DONE.  
`testerGate=ano`. Žádné pipeline-exceptions.  
Netýká se: Alembic, RBAC Universe, Celery, MCP, `qa_gate.mjs`.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | Next→Done, stale oid, casOnly | silent retry/force; žádný falešný Q9; Done; busy; pak export v témž slotu | R5b–6 | T1, T20 |
| B2 | concurrent změna | Q9; Přesto uložit await+busy+export | R5–6 | T2, T20 |
| B3 | error_reason / !ok bez reason / editBody fail / network | dialog (App bridge); editBody→Detail; finally hide; **bez** export při fail | R5–6, Q4a | T3, T3b, T20 |
| B4 | rodič+děti → non-terminal | PATCH OK; busy; primary disabled; export 1× | R6 | T4, T21 |
| B5 | rodič+děti → Done/Cancelled | open_child dialog; žádný PATCH/export | R6 | T5, T21 |
| B6 | kanbanPatch null | vždy dialog A10 | R6 | T6 |
| B7 | confirm* unknown/throw | error dialog; busy finally | R6, C10 | T7, T21 |
| B8 | Doing/Waiting bez data (move) | doplňovací dialog; po Potvrdit busy+PATCH+export | R6 | T8, T21 |
| B9 | mutace ≥150 ms vč. patchDate | Wiki overlay; Escape ne; ≥200 ms; finally hide | R5 | T9, T11, T22 |
| B10 | Boot / standalone onRefresh ≥150 ms | busy Načítám… + subtitle; 401 bez stuck; chyba → Boot `setError` (bridge) | R5, Q3b, C13 | T15b, T22 |
| B11 | druhý **user** klik během busy | primary disabled; 0 druhá mutace; overlay zůstane | R5, A9 | T10, T22 |
| B12 | createTask guard / !ok / throw | **guard → error dialog** (C14); !ok/throw dialog; po ok busy+export | R5–6, C14 | T12, T22 |
| B13 | cleanup ok / lines / reject bez lines | busy; panel nebo dialog A13; po ok export | R5–6 | T13, T22 |
| B14 | focus propose/apply | busy + dialogy; apply ok → export v slotu | R5 | T14, T22 |
| B15 | openDetail slow/throw | busy; catch→dialog; finally; bez export | R5 | T15, T22 |
| B16 | po strip | rg 7873/ingest v web/src = 0 | R9 | T16 |
| B17 | před strip / 1. Tester | debug smí zůstat | R9 | — |
| B18 | DONE | busy gate ano + Tester PASS strip SHA | R8–9 | T23 |
| B19 | R5 mutace throw/network | bridge→Boot setError nebo App setDialog; finally hide | R5, C10, C13 | T3b, T7, T12–T15, T22 |
| B20 (**C12**) | ok mutace, která má refreshnout UI | busy **nepřerušen** mezi koncem zápisu a koncem exportu; **1×** `/api/export`; mutex nezahodí programmatic refresh; teprve pak hide (≥ min 200 ms) | R5b | T9b, T20–T22 |
| B21 (**C16**) | StrictMode double-mount / unmount mid-busy | žádný stuck overlay; žádný setState po unmount; generation/abort | R5 | T9c |

### Checklist A

1. Prázdná data — prázdná tabulka OK (looksBare: `tables≥1`).  
2. Chybějící hodnoty — B8, B12 guard.  
3. Hranice období — netýká se FY; Prague today.  
4. Měny — netýká se.  
5. Oprávnění — 401 Boot (B10).  
6. Sync Celery — netýká se.  
7. Archiv — stávající filtry.  
8. Duplicitní akce — B11; programmatic refresh ≠ duplicitní mutace (B20).  
9. Externí chyba — B3, B19 + bridge C13.  
10. Zpětná kompatibilita — Brain API beze změny.  
11. PD↔Allfred — netýká se.

### Vizuální B#

| B# | DoD (T17 hard) | looksBare | T# |
|---|---|---|---|
| B-V1 Chrome | nav `#444444`; „Second Brain“; active `#a11834`; Rubik | N/A | T17, T22 |
| B-V2 Radar | H1 Radar; ≥8 dlaždic; po výběru table | **false** po výběru | T17, T22 |
| B-V3 Mapa | Strom/Mindmapa aria-label | **false** | T17, T22 |
| B-V4 Projekt | epic/stories nebo kanban 4 sloupce | **false** | T17, T21–22 |
| B-V5 Detail | section Detail max-w-xl; Uložit | **false** | T17, T20 |
| B-V6 Nový | radiogroup; **Založit** | **false** | T17, T22 |
| B-V7 Úklid | seznam + Náhled | **false** | T17, T22 |
| B-V8 Chybně zadané | section + table Task/Pravidla/Projekt | **false** | T17, T22 |
| B-V-busy | SSOT + `[data-busy-text]` + **`[data-busy-subtitle]`** neprázdný; `#e9244a`; reduced-motion | N/A | T11, T18, T22 |

## Výkonový rozpočet (P)

1. **Objem** — ~500 open tasks (A5); ověřit count na prod dashboardu.  
2. **SQL** — netýká se FE; BFF 1× export / 1× mutace.  
3. **Python load** — beze změny.  
4. **Externí** — jen Brain; C12 přidá 1× export **za** success mutaci (už dnes `onRefresh` — jen timing busy).  
5. **Stránkování** — stávající full export; mimo rozsah.  
6. **Payload** — beze změny.  
7. **Cache** — žádná nová.  
8. **Násobení** — B11 ≤1 user mutace; B20 přesně 1 export po ok (ne 0, ne 2).  
9. **Frontend** — debounce 150 / min 200; jeden overlay slot přes mutaci+export.  
10. **Worker** — netýká se.  
11. **Cíl** — UX warm &lt; 1,5 s typicky; cold export sledovat; overlay bez mezery (B20). Měření: mock timers T9b + Playwright network.

## Testy (T#)

| T# | Typ | Owner | Soubor | B# |
|---|---|---|---|---|
| T1 | vitest | gate | `screens.test.jsx` | B1 |
| T2 | vitest | gate | dtto | B2 |
| T3 | vitest | gate | !ok bez reason → dialog | B3 |
| T3b | vitest | gate | editBody fail stay Detail; throw→bridge dialog | B3, B19 |
| T4–T8 | vitest | gate | B4–B8 | B4–B8 |
| T9 | vitest fake timers | gate | debounce 150 / min 200 | B9 |
| T9b | vitest | gate | ok patch → busy remains until export resolves; **1×** export; hide až poté | **B20** |
| T9c | vitest | gate | unmount/abort mid-busy → busy cleared; no throw | **B21** |
| T10 | vitest | gate | double user withBusy → 1 mutace | B11 |
| T11 | vitest | gate | SSOT + `[data-busy-subtitle]` neprázdný | B-V-busy, C15 |
| T12 | vitest | gate | createTask Doing bez deadline / Waiting bez waitUntil → **error dialog**; !ok/throw | B12, C14 |
| T13–T15 | vitest | gate | cleanup/focus/openDetail | B13–B15, B19 |
| T15b | vitest | gate | Boot busy; chyba → setError (ne setDialog) | B10, C13 |
| T16 | rg/shell | gate | po strip | B16 |
| T17 | vitest hard | gate | layout probe B-V1…B-V8 | B-V* |
| T18 | Playwright-smoke | gate/člověk | busy screenshot + subtitle attr | B-V-busy |
| T19 | ruční | člověk | ledger busy gate `ano` | R8 |
| T20–T22 | Playwright-T6-full | Tester | vč. B20 plynulý busy přes refresh; Chybně zadané; Boot bridge | B1–B15, B19–B20, B-V* |
| T22-reuse | Playwright-T6-full | Tester | po strip | B16, B18 |
| T23 | ruční audit | hlavní | DONE | B18 |

Lokální gate: `pytest vps/second-brain-dashboard/bff/tests` + `cd …/web && npm test`.  
T6 pack: chrome, Radar, Mapa, Projekt, Detail+busy+**B20**, Nový (**C14 guard**), Úklid, Chybně zadané, Focus, Busy cross-cut, Boot/refresh, double-click.

## Pořadí implementace

F1 — Busy CSS + Overlay/Provider/`withBusy` + logo + **`data-busy-subtitle`** + error bridge API (C13) + StrictMode generation (C16).  
F2 — Napojení R5 + **C12 await onRefresh v slotu** + disable primary + Boot.  
F3 — Silent paths + **C14 createTask guard dialog** + openDetail catch + Q9 await.  
F4 — Debug ponechat.  
F5 — T17 hard B-V*; T9/T9b/T9c/T11/T12/T15b.  
F6 — gate + commit.  
F7 — REVIEW → push.  
F8 — lidský busy gate.  
F9 — QA.  
F10 — Tester T20–T22.  
F11 — strip `7873`.  
F12 — REVIEW → push → QA → T22-reuse.  
F13 — DONE (B18).

## Rizika a zpětná kompatibilita

1. CAS force — regrese T1/T20.  
2. C12 delší busy — záměr; min 200 ms + export latency.  
3. Dvojí `onRefresh` (openConflict + caller) — při IMPL sloučit na 1× export (B20).  
4. Error bridge špatně zapojený → tiché chyby v Boot — T15b.  
5. StrictMode double load — generation povinná (B21).  
6. Logo chybí → FAIL T11/T18.  
7. Dvě deploy vlny — DONE jen strip SHA.  
8. Brain nedotčen.

## Otevřené otázky pro uživatele

Žádné. C12 copy → A27; objem ≫2k → A28; T22-reuse → A29.

---

## C# → vyřešeno / odmítnuto

| ID | Verdikt | Kde |
|---|---|---|
| C1 | vyřešeno (zůstává) | Plné B# + checklist A |
| C2 | vyřešeno (zůstává) | T17 hard expect + looksBare |
| C3 | vyřešeno (zůstává) | Souvislé B1–B21 |
| C4 | vyřešeno (zůstává) | Strip celý `web/src` |
| C5 | vyřešeno (zůstává) | Disable primary / user mutex |
| C6 | vyřešeno (zůstává) | Wiki SSOT §0 |
| C7 | vyřešeno (zůstává) | openDetail catch |
| C8 | vyřešeno (zůstává) | reduced-motion |
| C9 | vyřešeno (zůstává) | B-V8 |
| C10 | vyřešeno (zůstává) | B19 + throw cesty |
| C11 | vyřešeno (zůstává) | subtitle copy |
| C12 | **vyřešeno** | R5b, A9 zpřesnění, B20, T9b; await onRefresh v busy slotu; mutex neháže programmatic export |
| C13 | **vyřešeno** | A24, §1 error bridge; Boot setError / App setDialog; T15b |
| C14 | **vyřešeno** | A25, B12, T12 — guard → error dialog |
| C15 | **vyřešeno** | §0 `[data-busy-subtitle]`; T11 |
| C16 | **vyřešeno** | A26, B21, T9c — generation/abort + finally clear |

## Delta oproti k=2 r=1

1. **C12 / R5b / B20 / T9b:** po ok zápisu busy drží přes `await onRefresh()`; 1× `/api/export`; mutex výjimka pro programmatic export.  
2. **C13 / A24:** `onError` bridge — Boot `setError`, App `setDialog`; provider bez holého `setDialog`.  
3. **C14 / A25 / T12:** createTask client guard → error dialog (ne tichý return).  
4. **C15:** povinný atribut `data-busy-subtitle` v SSOT + T11.  
5. **C16 / A26 / B21 / T9c:** StrictMode generation/abort + clear busy při unmount.  
6. A9–A26 zpřesněny kvůli C12–C16; Q1b–Q4a a C1–C11 obsah beze změny záměru.