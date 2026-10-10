# Pipeline: SB operační model F0

Stav: DONE
Plán: docs/plans/2026-10-10-sb-operacni-model-f0.md
Schvalování plánu uživatelem: ano
Architekt: d0dac2c7… / hlavní agent · otevření #1, k=2/3, r=3/3
Šťoural: 655fd8bb… g=5 · HOTOVÝ GRILL
Kritik: agent ID c1075c30-e023-45d2-9794-8fb1a1bb8a38 · SCHVÁLENO (0 BLOCKER/MAJOR)
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW — · kola QA — · kola TESTER — · ENV opravy —
Base (origin/main před pipeline): 674a82a9373cc02a790e24a2ecf48222ccd61719 · Kódový SHA: n/a (F0 jen dokument) · Review SCHVÁLENO na: přeskočeno (F0 jen dokument) · QA PASS na: přeskočeno (F0 jen dokument) · TESTER PASS na: přeskočeno (profil SECOND_BRAIN + F0 jen dokument)
Plán schválen uživatelem: ano — B1–B22 (2026-10-10)
Goal: complete
TESTER: přeskočeno (profil SECOND_BRAIN + F0 jen dokument)

## Zadání (doslovně)

Zvažuji změnu způsobu fungování mého Second Brainu z toho důvodu, že se mění můj operační model a hledám cestu, jak můj SB více přizpůsobit této změně.

V čem spočívají změny:
1. Pracuji už nejen v Cursoru, ale také v Claude Desktop a Claude mobile a čím dál víc také v Grok Bot Desktop a Mobile - tzn. ne vždy je můj Mac zapnutý, ne vždy jsem u Cursoru, abych mu zadal potřebné příkazy
2. Do Obsidian aplikace jako takové chodím velmi málo - 2-3x týdně, nemám návyk tam chodit ani kvůli dashboardu, ani kvůli taskům a materiálům - vše řeším z Cursoru či přes Claude/Grok Bota a maximálně edituji konkrétní dokument
3. Triáž většinou řeším 1x denně - většinou večer, ale v podstatě ad-hoc a vadí mi, že ve chvíli, kdy jdu do triáže, tak některé informace v Inboxu už jsou zastaralé (Slack zprávy zodpovězené, e-maily veřešené atd.)
4. Je mi velmi blízký způsob práce Grok Bota, kdy mám rozdělené činnosti mezi různé boty, kteří jsou orchestrováni jedním. Mají přístup i k nástrojům bez MCP/API, reagují proaktivně, případně velmi jednoduše nastavují rutiny. Chtěl bych se přiblížit tomuto stylu práce.

Co bych rád zachoval, protože mi to přijde funkční a dobré:
1. rozdělení úložiště na jednotlivé projekty
2. práce s .MD soubory
3. kombinace projekt -> task u některých projektů a projekt -> epic -> story -> task u jiných.

Vše ostatní (pro jasnost upřesňuji,že tím myslím Google Drive, VPS, GitHub, Cursor jako takový) jsem potenciálně schopen vyměnit, opustit nebo začít používat něco jiného.

Chci, abys provedl důkladnou analýzu možností, které by byly využitelné pro tento setup, doptal se na vše, co pro tuto analýzu nebo následné doporučení potřebuješ a doporučil mi nejlepší možnou variantu. Je to takto srozumitelné a jasné? Ptej se

## Rozhodnutí z konverzace

- Pipeline: F0 nejdřív (cílová architektura + rozpad na fáze, jen dokument); každá další fáze vlastní pipeline. Grill analýzy v pipeline (architekt dostane analýzu, Šťoural griluje plán včetně rozhodnutí).
- Hlavní vstup: rovnocenně Claude, Grok, Cursor (jeden mozek).
- Grok styl: subagentí, proaktivita, computer use, paměť, mobil.
- Autonomie: vault zapisovat sami; navenek jen se schválením.
- Push: Grok app, Claude app, Slack.
- Data: netrénovat; ne rizikové dodavatele (ByteDance, DeepSeek…). Workspace/Claude Team/VPS/GitHub OK.
- Údržba: hybrid. Rozpočet: ≤ 50 USD/měsíc nad Ultra + Claude Team.
- Vault: privátní GitHub. Obsidian: opustit.
- Přílohy: běžné v repu; Drive jen nativní Google / sdílené / velké.
- YAML frontmatter: zachovat; Obsidian wikilinky ve FM → ID/slugy.
- Triáž: živě ze zdrojů s ověřením stavu. Inbox: vlastní poznámky + Sembly.
- Slack: DM/GDM, @zmínky, vlastní vlákna, emoji. Ne Saved/To-dos/Remind me. Ne oslovení jménem bez tagu.
- Sembly: webhook → inbox → zpracování zápisu.
- Deterministická logika: VPS crony, ne LLM rutiny.
- Dashboard: Claude artifact přes brain API (ne nutně vlastní web).
- Skilly: jeden SSOT v repu → plugin do všech tří klientů.
- Boti: ladit až F5 (lze zrušit/vytvořit). Dnes Saturnin + specialisti.
- Proaktivita: ráno, deadline/Waiting, před schůzkou, anomálie, večerní triáž.
- VPS: doporučeno zachovat jako jádro.
- Týmové task listy: mimo SB; sync později.
- F0 REVIEW/QA/Tester: přeskočeno (jen dokument) — viz pipeline-exceptions.md.
- Vault kotva: **SB15 — Nový operační model SB — multi-klient, Grok orchestrace, GitHub vault**; materiál `OBSIDIAN/02-PROJEKTY/second-brain/materials/2026-10-10 — Analýza nového operačního modelu SB.md`.

### Odpovědi na grill kolo 1 (2026-10-10)

- **Q1a** — Ultra/Team mimo strop ≤50 USD; computer-use je součást base Ultra (klientská schopnost Desktopu), ne položka stropu.
- **Q2a** — Po F2 tvrdé API-only: Cursor/Claude/Grok zapisují vault jen přes Brain API (MCP); žádný tichý filesystem/git commit.
- **Q3b** — Zachovat `materials/` + sidecar; R9 = binárky v gitu u materiálů (ne nová složka `files/`); Drive jen Google-native / sdílené / nad limitem.
- **Q4c** — Primární push = Claude/Grok app (Grok notifikace dobré; Claude otestovat); Slack DM jen fallback. (odchylka od doporučení Šťourala (a))
- **Q5b** — F1: n8n INBOX writers (Sembly/Gmail) dočasně vypnout / Sembly manuálně dokud F3 přepojí na brain. (odchylka od doporučení (a) Drive→git bridge)
- **Q6a** — Dashboard: Claude artifact = cíl; fail-path = MCP App / chat `get_context` / Slack brief; ne VPS web.
- **Q7** — Vault repo = `LC-RBEDU/second-brain-vault` (private).
- **Q8** — Obsidian Sync + Drive Desktop jako writer vypnout před F1 writer cutover; po F4 volitelný read-only klon.

### Odpovědi na grill kolo 2 (2026-10-10)

- **Q9b** — F1: klienti vault jen čtou; zápisy jen VPS cron (+ výjimečně ruční PR). Cursor write až F2 přes Brain API.
- **Q10a** — Primární push = nativní OS notifikace na Mac + iPhone (uživatel). Technický gate F3: umí-li Claude/Grok app push z VPS; fail-path Slack DM, cíl zůstává OS notifikace.
- **Q11d** — Gmail živá triáž: hvězdička **nebo** míček na Tobě; Workspace + osobní mailbox.
- **Q12a** — Mobile capture F1–F2: akceptovat výpadek (ručně / chat); neponechávat mobile-capture n8n.
- **Q13b** (NEBLOKUJÍCÍ) — LFS práh rozhodne F1, ne F0.
- **Q14a** (NEBLOKUJÍCÍ) — Computer use jen Desktop klient; Brain API bez UI automace.
- **Q15a** (NEBLOKUJÍCÍ) — Klienti rovnocenní vůči Brain API; Saturnin není povinná brána.

### Odpovědi na kritik kolo 1 (2026-10-10)

- **C4 / Gmail „míček“ → přepsáno:** Agent kouká na **všechny e-maily** a pomáhá zpracovat mailbox: vyházet odpad, archivovat věci bez nutné reakce, připravit reakce tam, kde jsou potřeba. (ne jen star∨míček discovery)
- **C3:** Lokální klon vaultu = **fetch/pull only**; žádný `git push` z Macu. Write = VPS deploy key (+ GitHub web PR výjimka).
- **C8:** Stale Slack INBOX F1–F2 **akceptováno** do F3; zapsat do rizik.

### Odpovědi na grill kolo 4 (2026-10-10)

- **Q16** — Grok / tooling v rámci Cursor licence = provozní base **mimo** ≤50 (stejná logika jako Ultra/Team); do ≤50 jen nové usage-based / navýšení kvůli SB. (mapuje na Šťoural **a**)
- **Q17c** — Hybrid: L1 discovery (inbox + sent, oba mailboxy) preferovaně přes Brain (P5 + audit); apply (trash/archive/send) smí Brain **nebo** klientský connector/plugin. Klienti (Claude/Grok) stejně mají vlastní connectory — tvrdé zabránění client-direct nestojí za úsilí. **Hard requirement:** uživatel vždy ví o trash/archive/send (schválení / batch návrh); všichni klienti umí načíst správné **příchozí i odchozí** maily.
- **Q18a** (default) — 1 session = 1 invocace triage skillu; overflow → další invocace, Date ASC.
- **Q19a** (default) — „celý mailbox“ = celý Inbox obou účtů (+ sent pro kontext); ne All Mail / Spam jako MVP.

## Mimo rozsah F0

- Implementace kódu, migrace vaultu, deploy brain API, změna botů, změna n8n.
- F1–F5 implementace (jen rozpad a kontrakty mezi fázemi).

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-10 | CLARIFY→PLAN | hlavní | — | — | Vault SB15 + materiál; ledger založen; start architekt |
| 2 | 2026-10-10 | PLAN | 78560e0e… | plán hotov | — | A7 doplněno měřením 782 MB / 7432 souborů; zápis do .md; → GRILL |
| 3 | 2026-10-10 | GRILL | d754609f… | POTŘEBUJE ODPOVĚDI | — | 5 BLOKUJÍCÍCH (Q1–Q6); Q7/Q8 NEBLOKUJÍCÍ s doporučením |
| 4 | 2026-10-10 | AWAITING_USER (z: grill) | hlavní | — | — | Goal paused; čeká odpovědi Q1–Q6 |
| 5 | 2026-10-10 | PLAN | 78560e0e… (resume r=2) | plán upraven | — | Q1a Q2a Q3b Q4c Q5b Q6a + Q7/Q8 zapracováno do .md |
| 6 | 2026-10-10 | GRILL | 30c9ce69… | POTŘEBUJE ODPOVĚDI | — | Q9–Q12 BLOKUJÍCÍ; Q13–Q15 NEBLOKUJÍCÍ |
| 7 | 2026-10-10 | AWAITING_USER (z: grill) | hlavní | — | — | Goal paused; čeká Q9–Q12 |
| 8 | 2026-10-10 | PLAN | 78560e0e… (resume r=3) | plán upraven | — | Q9b Q10a Q11d Q12a + A13–A15 zapracováno |
| 9 | 2026-10-10 | GRILL | d6bc7b83… | HOTOVÝ GRILL | — | A14–A21 doc-pass; → CRITIC |
| 10 | 2026-10-10 | CRITIC | c833203d… | K PŘEPRACOVÁNÍ | 5 MAJOR | NEW-1…5; blokující Q pro uživatele (míček, lokální klon) |
| 11 | 2026-10-10 | AWAITING_USER (z: grill) | hlavní | — | — | Goal paused; čeká odpovědi na NEW-4 / NEW-3 |
| 12 | 2026-10-10 | PLAN | (nový architekt k=2) | — | — | Odpovědi: Gmail full mailbox assist; fetch-only; stale Slack OK do F3 |
| 13 | 2026-10-10 | PLAN | k=2 zapsán do .md | plán hotov | — | C1–C8 zapracováno v plánu; Goal renewed |
| 14 | 2026-10-10 | GRILL | a1d0293e… g=4 | POTŘEBUJE ODPOVĚDI | — | Q16–Q17 BLOKUJÍCÍ; Q18–Q19 NEBLOKUJÍCÍ (default a) |
| 15 | 2026-10-10 | AWAITING_USER (z: grill) | hlavní | — | — | Goal paused; čeká Q16–Q17 |
| 16 | 2026-10-10 | PLAN | d0dac2c7… resume r=2 | plán hotov | — | Q16/Q17c/Q18a/Q19a/A24–A28; zápis .md hlavním agentem |
| 17 | 2026-10-10 | GRILL | 655fd8bb… g=5 | HOTOVÝ GRILL | — | A29/A30 doporučeny a zapsány; → CRITIC |
| 18 | 2026-10-10 | CRITIC | ebb16ad0… | K PŘEPRACOVÁNÍ | 2 MAJOR | NEW-1 A29 sync; NEW-2 P5 Inbox/Sent; NEW-3 path |
| 19 | 2026-10-10 | PLAN | hlavní (r=3) | plán upraven | — | NEW-1…3 opraveny; P5 Sent = thread-join |
| 20 | 2026-10-10 | CRITIC | c1075c30… | SCHVÁLENO | 0 | NEW-1…3 + C1 uzavřeny |
| 21 | 2026-10-10 | AWAITING_USER (z: schválení plánu) | hlavní | — | — | Goal paused; čeká schválení B1–B22 |
| 22 | 2026-10-10 | DONE | hlavní | — | — | B1–B22 schváleno; SB15-1 [x]; materiál F0 ve vaultu; REVIEW/QA/Tester přeskočeny |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav | Kolikrát vznesen |
|---|---|---|---|---|
| C1–C8, NEW-1…3 | — | PLAN | uzavřeno (kritik c1075c30 SCHVÁLENO) | — |
