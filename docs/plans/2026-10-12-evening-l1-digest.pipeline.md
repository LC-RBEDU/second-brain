# Pipeline: evening-l1-digest

Stav: REVIEW
Plán: docs/plans/2026-10-12-evening-l1-digest.md
Architekt: 2887a5f5… k=2
Šťoural: HOTOVÝ
Kritik: 0e8590d0… **SCHVÁLENO** (kolo 6)
Goal: aktivní
Schvalování plánu uživatelem: ne → rovnou IMPLEMENT
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main): 886f494b836472412c783b0d72d1f3e01652791e · Kódový SHA: 6439d0ed3e39631a8e3d606ea3b3341aea406f8f · Review SCHVÁLENO na: — · QA PASS na: — · TESTER: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Goal: aktivní

## Projekt
SECOND_BRAIN — kořen `~/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN`, větev `main`, base = origin/main před pipeline. Nasazení: push `main` → Coolify `second-brain-hub` (coolify-dev) = ostrý cron nad živým vaultem. Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`. QA: image dle hub README + `--dry-run` evening digest. Tester: vždy přeskočeno (profil SECOND_BRAIN).

## Zadání (doslovně)
čistě L1 je OK, jen potřebuji nějak zajistit, že se do Gitu dostanou informace z e-mailu a Slacku k otevřeným úkolům, případně se mi nabídne možnost založit úkol i ve chvíli, kdy zapomenu říct Claudovi / Saturninovi, aby prošel triáž.

Takže nějaké konkrétní shrnutí dne - např. daily v 18:00 by bylo fajn

(následně) 2) Slack DM sobě není třeba, stačí Saturnin
(následně) a jinak ano /rbu-pipeline rozjeď

## Rozhodnutí
- L1 = live Slack + Gmail Inbox/Sent přes Brain (ne hvězdička n8n).
- Persist: vault MD stačí (grill Q1=a); cesta **`00-System/digests/YYYY-MM-DD-evening-l1.md`** (grill Q2=b) — **ne** `01-INBOX/daily/`.
- Match zdroje (grill Q3=c): **všechny** Brain sources — live Slack, Gmail, residual dumps, daily, sembly — kvůli souvislostem napříč kanály (mail↔Slack, Sembly↔Slack, …).
- Saturnin (grill Q4=c): zkusit **skoro celý digest v chatu**; když bude moc, později zúžit na counts+cesta+top N unmatched.
- Bez tichého logu do otevřených tasků.
- Doručení: **jen Saturnin** — ne Slack DM.
- Evening ~18:00 Po–Pá; cron **ne** propose/apply/auto-create; morning/due mimo.
- OQ wire Gmail v tomto PR = ne; Brain down = degraded MD; match bez epiců; Saturnin fail = exit 0 + deliver=FAIL.
- Grill Q5=b: match všechny open (bez epic); 40/40/8 jen render + truncated.
- Grill Q6=b: exists + deliver≠OK → Saturnin-only retry (bez přepisu MD); exists + OK → full skip.
- Grill Q7=b: heads jen match-input; MD/Saturnin = strukturovaný digest (short snippets); později možné rozšířit na hybrid c.
- A20 empty day = krátký MD+Saturnin; A21 light missing = full agent-context open tasks; A22 multi-hit pod každým ID.
- Critic Q A=**2**: match jehly = task id + title tokeny + **tělo task souboru** (větší kontext → méně duplicitních stories).
- Critic Q B=**1**: display caps 40 matched tasks / 40 unmatched / 8 hits per task + truncated.

## Mimo rozsah
- Zapnutí n8n starred→INBOX
- Slack DM sobě
- Auto-zápis do existujících task souborů
- Auto propose/apply/mailbox
- Claude webhook (jen Saturnin)
- Změna morning/due na plný digest (evening only)

## Průběh
| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-12T13:25 | PLAN | 5cc31609… | plán v1 | — | CreateGoal + architekt |
| 2 | 2026-10-12T13:30 | GRILL | 826f690c… | POTŘEBUJE ODPOVĚDI | 4 BLOKUJÍCÍ Q1–Q4 | → AWAITING_USER |
| 3 | 2026-10-12T13:47 | AWAITING_USER | hlavní | — | — | lidsky přeformulovat grill |
| 4 | 2026-10-12T13:50 | AWAITING_USER | uživatel | 1a 2b 3c 4c | — | → PLAN r=2 |
| 5 | 2026-10-12T13:55 | PLAN | 5cc31609… | plán v2 | — | digests/ + all sources + nearly-full |
| 6 | 2026-10-12T14:00 | GRILL | 0a2ca8b4… | POTŘEBUJE ODPOVĚDI | Q5–Q7 BLOKUJÍCÍ | → AWAITING_USER |
| 7 | 2026-10-12T14:00 | AWAITING_USER | uživatel | 5b 6b 7b | — | → PLAN r=3 |
| 8 | 2026-10-12T14:05 | GRILL | 7ed54f18… | HOTOVÝ | A27–A30 | → CRITIC |
| 9 | 2026-10-12T14:10 | CRITIC | f1c6a5fc… | K PŘEPRACOVÁNÍ | C1–C5 | → AWAITING_USER |
| 10 | 2026-10-12T14:42 | AWAITING_USER | uživatel | A2 B1 | — | → PLAN k=2 |
| 11 | 2026-10-12T14:50 | PLAN | 2887a5f5… | k=2 plán | C1–C7 | |
| 12 | 2026-10-12T14:55 | GRILL | d40a71b0… | HOTOVÝ | — | → CRITIC |
| 13 | 2026-10-12T15:00 | CRITIC | b5acf843… | K PŘEPRACOVÁNÍ | C3, force, Brain auth | → AWAITING_USER |
| 14 | 2026-10-12T16:12 | AWAITING_USER | uživatel | ID match = 1 word-boundary | — | → PLAN r=2 |
| 15 | 2026-10-12T16:30 | IMPLEMENT | hlavní | lib+cron+11 tests; hub 319 passed | — | → lokální commit → REVIEW |
| 16 | 2026-10-12T16:45 | REVIEW | 2906bc05… | K PŘEPRACOVÁNÍ | NEW-1 CAS, NEW-2 tests, NEW-3 FM | → IMPLEMENT |
| 17 | 2026-10-12T16:55 | IMPLEMENT | hlavní | CAS catch + 17 tests; NEW-1/2/3 | — | → REVIEW kolo 2 |
| 18 | 2026-10-12T17:05 | REVIEW | ce0f62ad… | K OPRAVĚ | NEW-4 B3 test, NEW-5 B20 test, NEW-6 | → IMPLEMENT |
| 19 | 2026-10-12T17:10 | IMPLEMENT | hlavní | B3/B20/B4 brain assert; 19 tests | — | → REVIEW kolo 3 |

## Otevřené nálezy
| ID | Závažnost | Typ | Stav | Kolikrát |
|---|---|---|---|---|
| C1 | BLOCKER | PLAN | uzavřený v k=2 (partial vs total) | 1 |
| C2 | MAJOR | PLAN | uzavřený v k=2 (iter_active_tasks ∩ ¬terminal ∩ ¬epic) | 1 |
| C3 | MAJOR | PLAN | uzavřený v k=2 (B6–B9 + B17 + R15 body) | 1 |
| C4 | MAJOR | PLAN | uzavřený v k=2 (HTTP mimo flock + CAS) | 1 |
| C5 | MAJOR | PLAN | uzavřený v k=2 (PAUSED) | 1 |
| C6 | MINOR | PLAN | uzavřený v k=2 (subject) | 1 |
| C7 | MINOR | PLAN | uzavřený v k=2 (B11 větev) | 1 |
| NEW-1 | MAJOR | IMPL | opraveno (DriveConflictError → False / exit 0) | 1 |
| NEW-2 | MAJOR | IMPL | opraveno (B2/B2b/B4b/B8/B10/B14/B21/B22/B24 + truncated_hits) | 1 |
| NEW-3 | MINOR | IMPL | opraveno (truncated_hits assert + json-quoted deliver_detail) | 1 |
| NEW-4 | MAJOR | IMPL | opraveno (test B3 force+OK) | 1 |
| NEW-5 | MAJOR | IMPL | opraveno (test B20 degrade MD write) | 1 |
| NEW-6 | MINOR | IMPL | opraveno (B4 assert Brain called) | 1 |
