# Pipeline: Second Brain dashboard stabilize
Stav: QA
Plán: docs/plans/2026-10-21-sb-dashboard-stabilize.md
Schvalování plánu uživatelem: ne
Architekt: k=1 c1884de4 · k=2 2a3eb646 r=2/3
Šťoural: g=5 2243c9d4 · A18–A33
Kritik: kolo 4 409f7481 (SCHVÁLENO)
Goal: aktivní
Plán schválen kritikem: kolo 4 na otevření #1 k=2 r=2
Poznámka: F11 strip Review SCHVÁLENO; MINOR dead useEffect pryč; push → QA → T22-reuse → DONE.
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 2/5 · kola QA 2/5 · kola TESTER 1/5 · ENV opravy 0/2
Base (origin/main při vzniku): 39e76570f75ec684f72df128c3aaf19eda1cf206 · Kódový SHA: (strip HEAD) · Review SCHVÁLENO na: 6d93a2a4 (+ MINOR chrome) · QA PASS na: 3a5b962c (P11 latence poznámka) · TESTER PASS na: 3a5b962c
Plán schválen uživatelem: nevyžadováno
Vizuální gate člověka: ano (2026-10-21; busy OK; pozn.: save ~3–4 s = PATCH+export C12)
testerGate: ano (UI produkt — zákaz TESTER skip)

## Zadání (doslovně) a rozhodnutí

Uživatel, 2026-10-21 (po sérii ad-hoc UI fixů a false CAS / silent Uložit / inline status):

> vrať dashboard práci do plné /rbu-pipeline s povinným Testerem / T6 proklikem; ad-hoc pipeline-exceptions pro UI končí

Uživatel, 2026-10-21 (doplnění do plánu):

> navíc chci při ukládání a jakékoliv operaci, která má prodlevu, zobrazit stejný prvek, jako má Wiki ve chvíli, kdy ukládá změnu na stránce

Uživatel, 2026-10-21:

> spusť to

Meta-plán: `~/.cursor/plans/dashboard_pipeline_návrat_6cc510ef.plan.md`

### Rozhodnutí

- Nový ledger (tento soubor); starý `2026-10-19-sb-dashboard.pipeline.md` zůstává historický DONE se skipnutým Testerem — neuzavírat jako „DONE s Testerem“.
- Profil SECOND_BRAIN, **UI produkt**: `testerGate=ano`, plný T6 pack, zákaz `TESTER: přeskočeno (profil SECOND_BRAIN)` bez „bez UI“.
- Ad-hoc řádky do `pipeline-exceptions.md` pro dashboard UI **zakázány**.
- Rozsah: stabilizace chování + vizuální B#/probe proti wireframům + **Wiki busy-overlay** na všechny mutace/prodlevy. Ne redesign od handoffu 00–01.
- Deploy: Coolify dashboard app (image = kódový SHA); push po Review SCHVÁLENO.
- Busy overlay: 1:1 vizuál Wiki (`#busy` / `.busy-overlay` / `.busy-card` / spin + pulse + bar, brand `#e9244a`); React komponenta; `withBusy`; debounce show ≥150 ms; Escape nezavírá.

### Grill g=1 — odpovědi uživatele (2026-10-21)

- **Q1 (b):** Debug ingest `7873` **nechat** v kódu přes IMPL → Review → QA → Tester. Odstranit až **po Tester PASS** (pak strip commit + Review/QA/Tester na čistém SHA, nebo minimálně strip + krátký re-gate dle plánu r=2). Důvod uživatele: při FAIL Testera by se logy jinak musely znovu doplňovat.
- **Q2 (b):** Lidský vizuální gate na busy-overlay **aspoň jednou** — screenshot/live důkaz, že převzetí z Wiki sedí; `Vizuální gate člověka: ano (2026-10-21; busy OK; pozn.: save ~3–4 s = PATCH+export C12)
- **Q3 (b):** Busy i na **první load / refresh exportu** („Načítám…“); `editBody` uvnitř `saveDetail` `withBusy`.
- **Q4 (a):** B3 rozšířit — `!ok` bez `error_reason` vždy dialog; `editBody` `!ok`/throw → error dialog, zůstat na Detailu.
- **Q5–Q9 NEBLOKUJÍCÍ** → A9–A13: globální busy mutex (drop concurrent); null-patch copy; min visible 200 ms; logo Coolify rb-wiki; úklid dialog jen při rejectu bez lines.

### Grill g=2 — HOTOVÝ GRILL (NEBLOKUJÍCÍ A14–A17)

- **A14:** Boot/refresh busy = B12 (ne kolize B10).
- **A15:** DONE = Tester PASS na strip SHA (T22-reuse); T6 vlny 1 nestačí po F11.
- **A16:** F8 busy gate před F9 QA; strip neopakuje lidský busy gate.
- **A17:** F12 = Review → push → QA → T22-reuse.

### Inventura vad (CLARIFY seed — session + kód)

| # | Symptom | Kde | Stav kódu (HEAD 635bf313 + origin+2) | Poznámka |
|---|---|---|---|---|
| 1 | Falešný CAS / Konflikt při úmyslné změně statusu (Next→Done) | Detail Uložit | částečně fix (`44221705`, `fa79b60e`) | ověřit end-to-end + regrese |
| 2 | Uložit tiše nic neudělá | Detail | částečně fix (`03c442e8` error dialog) | chybí busy; ověřit všechny error_reason |
| 3 | Inline status u rodiče s dětmi = no-op | Radar / Projekt tabulka | částečně (`635bf313` non-terminal); Done/Cancelled → dialog | ověřit epic/story všechny statusy |
| 4 | `move` tichý `return` když `kanbanPatch` null mimo Done/Cancelled | `App.jsx` move | stále | nesmí být tiché selhání |
| 5 | `confirmDoing` / `confirmWaiting` při neznámé chybě zavře dialog bez hlášky | App.jsx | stále | |
| 6 | Žádný busy / loading UI při zápisu | celá SPA | chybí | Wiki-parita povinná |
| 7 | Debug ingest `7873` v App.jsx | App.jsx | přítomné | Q1b: pryč až po Tester PASS |
| 8 | Původní pipeline bez Testera | historický ledger | DONE skip | důvod této pipeline |
| 9 | Sweep živého UI (Playwright) | dashboard.cyprovi.cz | pending v PLAN/T6 | Architect zahrne do B#/T#; plný sweep = Tester |

## Průběh
| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-21 | CLARIFY | hlavní | inventura seed | — | → PLAN o#1 k=1 r=1 |
| 2 | 2026-10-21 | PLAN | c1884de4 | plán r=1 zapsán | — | → GRILL g=1 |
| 3 | 2026-10-21 | GRILL | 6ba7c634 | POTŘEBUJE ODPOVĚDI | 4 BLOKUJÍCÍ Q1–Q4 | → AWAITING_USER (z: grill) |
| 4 | 2026-10-21 | AWAITING_USER | uživatel | Q1b Q2b Q3b Q4a | — | → PLAN r=2 (resume architekt) |
| 5 | 2026-10-21 | PLAN | c1884de4 | plán r=2 zapsán | — | → GRILL g=2 |
| 6 | 2026-10-21 | GRILL | 7a087ce6 | HOTOVÝ GRILL | A14–A17 NEBLOKUJÍCÍ | → CRITIC kolo 1 |
| 7 | 2026-10-21 | CRITIC | 903a99db | K PŘEPRACOVÁNÍ | 5 MAJOR C1–C5 | → PLAN r=3 |
| 8 | 2026-10-21 | PLAN | c1884de4 | plán r=3 C1–C8 vyřešeno | — | → GRILL g=3 |
| 9 | 2026-10-21 | GRILL | d807f3d6 | HOTOVÝ GRILL | A18–A21 NEBLOKUJÍCÍ | → CRITIC kolo 2 |
| 10 | 2026-10-21 | CRITIC | 1055ce49 | K PŘEPRACOVÁNÍ | 3 MAJOR C2,C9,C10 | → PLAN k=2 r=1 (nový architekt) |
| 11 | 2026-10-21 | PLAN | 2a3eb646 | k=2 r=1 zapsán (C2,C9–C11) | — | → GRILL g=4 |
| 12 | 2026-10-21 | GRILL | 11e4961f | HOTOVÝ GRILL | A24–A26 NEBLOKUJÍCÍ | → CRITIC kolo 3 |
| 13 | 2026-10-21 | CRITIC | 4b1f9ba5 | K PŘEPRACOVÁNÍ | 1 BLOCKER C12 + 2 MAJOR | → AWAITING_USER (busy vs refresh) |
| 14 | 2026-10-21 | AWAITING_USER | uživatel | C12 = volba 1 (busy přes refresh) | — | → PLAN k=2 r=2 |
| 15 | 2026-10-21 | PLAN | 2a3eb646 | k=2 r=2 C12–C16 vyřešeno | — | → GRILL g=5 |
| 16 | 2026-10-21 | GRILL | 2243c9d4 | HOTOVÝ GRILL | A27–A33 NEBLOKUJÍCÍ | → CRITIC kolo 4 |
| 17 | 2026-10-21 | CRITIC | 409f7481 | SCHVÁLENO | 0 BLOCKER 0 MAJOR 1 MINOR | → IMPLEMENT |
| 18 | 2026-10-21 | IMPLEMENT | hlavní | blokováno Plan mode | — | → AWAITING_USER (Agent mode) |
| 19 | 2026-10-21 | IMPLEMENT | hlavní | F1–F5 hotovo | — | BusyProvider/Overlay + mutace + vitest 48/48; → F6 commit → REVIEW |
| 20 | 2026-10-21 | REVIEW | c6d226f5 | K OPRAVĚ | 1 BLOCKER NEW-1 + 4 MAJOR | → IMPLEMENT oprava |
| 21 | 2026-10-21 | IMPLEMENT | hlavní | NEW-1…NEW-5 + MINOR | — | openDetail/busy race/bridge/T3/T15b; commit bc199965 |
| 22 | 2026-10-21 | REVIEW | 89e04d45 | SCHVÁLENO | 0 BLOCKER 0 MAJOR | → push + deploy + F8 busy gate |
| 23 | 2026-10-21 | QA | — | pending F8 | — | deploy a892094b healthz 200; čeká busy visual gate |
| 24 | 2026-10-21 | AWAITING_USER | uživatel | F8 busy overlay | — | ne: logo 404 + Uložení selhalo |
| 25 | 2026-10-21 | IMPLEMENT | hlavní | F8 oprava | — | Dockerfile public/; Brain timeout 60s; deploy 2823ba39 logo 200 |
| 26 | 2026-10-21 | AWAITING_USER | uživatel | F8 znovu | — | ano (busy OK; save ~3–4 s) |
| 27 | 2026-10-21 | QA | 12566887 | PASS s výhradami | P11 save ~3–4 s | → testerGate T6 pack |
| 28 | 2026-10-21 | AWAITING_USER | uživatel | T6 pack | — | ano — plný pack |
| 29 | 2026-10-21 | TESTER | rbu-tester | FAIL | B11 NEW-1/NEW-2 | Focus Potvrdit + Detail Uložit 2× API |
| 30 | 2026-10-21 | IMPLEMENT | hlavní | B11 mutex | — | globalBusyHeld + no StrictMode + consume proposalId; commit 907709b1 push |
| 31 | 2026-10-21 | REVIEW | 9a6b9ec7 | SCHVÁLENO | 0 BLOCKER 0 MAJOR 2 MINOR | NEW-1 komentář; NEW-2 proposalId pre-clear |
| 32 | 2026-10-21 | IMPLEMENT | hlavní | MINOR NEW-1/2 | — | clear proposalId až v withBusy fn; komentář mutex; commit 3a5b962c |
| 33 | 2026-10-21 | QA | b03e2f0f | PASS | P11 ~8.9 s poznámka | B11≤1 mutace; B20 1× export; Escape OK |
| 34 | 2026-10-21 | TESTER | 905adadf | PASS | — | B11=1 mutace; B20; C14; pack 12/12 na 3a5b962c |
| 35 | 2026-10-21 | IMPLEMENT | hlavní | F11 strip | — | commit 6d93a2a4; App 9 + chrome 1; rg 7873=0; vitest 50/50 |
| 36 | 2026-10-21 | REVIEW | e0369b7f | běží | — | strip-only diff vs 3a5b962c |

### Kritik kolo 3 — odpověď uživatele (2026-10-21)

- **C12 / NEW-1 (volba 1):** Po úspěšném zápisu zůstane busy i přes následný `onRefresh` export — jeden plynulý čekací stav (Ukládám… → případně Načítám… / stejný overlay), dokud nedorazí nová data. Mutex nesmí shodit programový refresh; refresh běží uvnitř stejného busy (nebo reentrant load), až pak `finally` hide.
- **C14 client guard (NEBLOKUJÍCÍ default):** Založit Doing/Waiting bez dat → error dialog (ne tichý return).

## Otevřené nálezy
| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| C1 | MAJOR | PLAN | vyřešen v r=3 | 1 |
| C2 | MAJOR | PLAN | vyřešen v k=2 r=1 (T17 hard expect) | 2 |
| C9 | MAJOR | PLAN | vyřešen v k=2 r=1 (B-V8) | 1 |
| C10 | MAJOR | PLAN | vyřešen v k=2 r=1 (B19 withBusy throw) | 1 |
| C11 | MINOR | PLAN | vyřešen v k=2 r=1 (subtitle copy) | 1 |
| C12 | BLOCKER | PLAN | vyřešen v k=2 r=2 (B20 busy přes refresh) | 1 |
| C13 | MAJOR | PLAN | vyřešen v k=2 r=2 (error bridge) | 1 |
| C14 | MAJOR | PLAN | vyřešen v k=2 r=2 (createTask guard dialog) | 1 |
| C15 | MINOR | PLAN | vyřešen v k=2 r=2 (data-busy-subtitle) | 1 |
| C16 | MINOR | PLAN | vyřešen v k=2 r=2 (StrictMode generation) | 1 |
| C3 | MAJOR | PLAN | vyřešen v r=3 | 1 |
| C4 | MAJOR | PLAN | vyřešen v r=3 | 1 |
| C5 | MAJOR | PLAN | vyřešen v r=3 | 1 |
| C6 | MINOR | PLAN | vyřešen v r=3 | 1 |
| C7 | MINOR | PLAN | vyřešen v r=3 | 1 |
| C8 | MINOR | PLAN | vyřešen v r=3 | 1 |
| NEW-1…5 | BLOCKER/MAJOR | IMPL | vyřešen v REVIEW kolo 2 (89e04d45) | 1 |

## Připraveno po F8 `ano` (nespouštět dřív)

### F9 QA brief
- URL: https://dashboard.cyprovi.cz · image SHA `a892094b`
- Gate: `cd vps/second-brain-dashboard/web && npm test` + BFF pytest
- Smoke: Boot busy, Uložit → busy přes export (B20), Escape nechá overlay, primary disabled

### F10 T6 pack (rbu-tester)
Chrome · Radar (≥8 dlaždic) · Mapa Strom/Mindmapa · Projekt/Kanban · Detail+busy+B20 · Nový C14 guard · Úklid · Chybně zadané · Focus (Radar dlaždice + B14) · Busy cross-cut · Boot/refresh · double-click mutex

### F11 strip mapa (po 1. Tester PASS)
`rg 7873` v `web/src`: App.jsx (~9×) + chrome.jsx (1×) → smazat `#region agent log` bloky; `rg` = 0 = T16
