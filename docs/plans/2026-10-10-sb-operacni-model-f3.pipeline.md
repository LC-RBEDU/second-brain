# Pipeline: SB operační model F3

Stav: REVIEW
Plán: docs/plans/2026-10-10-sb-operacni-model-f3.md
Schvalování plánu uživatelem: ne
Architekt: b5de8d58… · otevření #2 · k=2/3 · r=3/3
Šťoural: 31be6955… · g=6 HOTOVÝ
Kritik: af0b8c4c… · SCHVÁLENO
Kódový SHA: 6fac0fdab41a1413dc96b222363bf25468d0f5e5
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): f893b01b6972b3fc55af6dd44639f1ae31e8548e · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: —
Plán schválen uživatelem: nevyžadováno
Goal: aktivní
Profil: SECOND_BRAIN

## Zadání (doslovně)

ok, spusť krátký smoke a pak F3

(kontext: F0 SCHVÁLENO; F1 cutover DONE; F2 DONE 2026-10-11 — Brain `https://brain.cyprovi.cz`, Grok+Cursor+Claude MCP write; další krok **SB15-4** F3)

## Rozhodnutí z konverzace

- Parent F0: `docs/plans/2026-10-10-sb-operacni-model-f0.md` (B1–B22) — F3 scope tabulka: Slack / Sembly / živá triáž / Gmail hybrid / briefy; R# R11–R13, R12b, R27, R18, R5, R4.
- F2 DONE: vault MCP write u Cursor + Claude (`mcp-remote`) + Grok; smoke `create_task` → **SBD-S20** (cleanup Cancelled); tip base této pipeline = `f893b01`.
- F2 stubs (`f3_stub` → 501) mají F3 nahradit reálnými tools.
- Schvalování plánu: ne (stejně jako F2).
- Soft A17 Free (mailbox mutate = batch + schválení).
- TESTER: přeskočeno (profil SECOND_BRAIN) — po QA.
- Pre-F3 smoke (2026-10-11): MCP `get_context` OK (warm); `create_task` → SBD-S20 v `second-brain-development`.

### Grill g=1 odpovědi (2026-10-11)

- **Q1 = (a)** F3 DONE i při B18 FAIL (OS notif); Slack/chat fallback; SB15-4 `[x]` s výhradou; primár v docs zůstává OS.
- **Q2 = (c)** Batch store = in-memory / process-local Brain (ztráta při restartu OK); ne vault, ne Redis.
- **Q3 = (c)** F3 MVP **bez** anomaly cronu — 4 triggery (ráno, due/Waiting, před schůzkou, evening); anomaly až později.
- **Q4 = (c)** Do F4 L1 triáž čte **jen dump** `01-INBOX/slack` (+ email legacy); live Slack tool = opt-in / připravený, ne default L1 fronta.
- **Q5 = (b)** Proaktivita smí spustit L1+L2 a připravit propose batch; apply až po schválení člověkem.
- **Q6 = (a)** Slack external send po approve = DM/GDM i kanál z preview.
- **Q7 = (a)** Sembly: Brain vyplní MD šablonu z payloadu (deterministicky); n8n thin webhook. **Není** LLM shrnutí při ingestu — LLM DEEP zápis = později skill `agenda-zapis-ze-schuzky` / triáž (viz odpověď uživateli).
- **Q8 = (a)** Brain server-side apply primár po batch approve; client apply povolen (R27).
- **Q9 = (a)** Schválení = chat ve stejném klientovi + `apply(batch_id, ids[])`.
- **Q10 / meeting prep (nové rozhodnutí uživatele):** Dnes přípravu na schůzku dělají různé nástroje (Grok routine, Claude scheduled task, Cursor skill) různě. **Chce jeden obsah přípravy** — rozsahem všechny dostupné zdroje; **primární doručení = Grok**; ostatní kanály nesmí vyrábět konkurenční odlišný brief. Cron „před schůzkou“ = spustit tuto jednotnou pipeline + doručit přes Grok (ne tři paralelní prep generátory).

### Grill g=2 odpovědi (2026-10-11)

- **Q11 = (c)** Proaktivita **nezakládá** apply-batch — jen L1/L2 náhled + „jdi do triáže“; propose až v živé session. (změkčuje prakticky Q5=b: cron nepřipraví mailbox/Slack batch k apply.)
- **Q12 = (a) teď; později možná (c)** Apply jen **human OAuth** (service token → 403). Pozdější cesta: signed approve token z chatu pro service apply — dluh post-F3, ne v F3 DONE.
- **Q13 = (b)** Coolify Brain dostane **Universe read credentials** (a Drive dle potřeby skillu), ať `prepare_meeting` má plný rozsah jednoho generátoru.
- **Q14 = (b)** F3 DONE povoleno s výhradou, pokud T13 (vypnutí paralelních prep) není hotové — B21 FAIL v ledgeru, SB15-4 `[x]` OK.
- **Q15–Q18** (default, bez námitky): oddělený Grok meeting-prep webhook; Meeting-Preps retention 14 dní; idempotence skip pokud brief existuje; proactivity notif bez cron propose (sladěno s Q11=c) = „jdi na triáž“ + krátký náhled, ne batch id.

### Grill g=3 HOTOVÝ — neblokující A# (2026-10-11)

- **A19** — Trigger „před schůzkou“ = jen `meeting_prep_dispatch` (ne čtvrtý triage ping). `proactivity_dispatch` = ráno + due/Waiting + evening.
- **A20** — Partial apply: best-effort per id + report úspěchů/failů; ne tiché OK.
- **A21** — Cron prep: skip pokud existuje; ad-hoc `force=true` OK.
- **A22** — Časy: ráno ~08:00, evening ~18:00, due tick v pracovní době (TZ Prague).
- **A23** — Coolify Brain `replicas=1` (in-memory batch).

### Grill g=4 HOTOVÝ — A24–A25 (2026-10-11)

- **A24** — T8/B14* DONE gate = Cursor client apply (Gmail MCP + Slack); Claude/Grok best-effort connector / „proveď v Cursoru“ neblokuje DONE.
- **A25** — Smíšený batch: po 1× „ano“ jen vratné id; nevratné jen po 2. otázce na ta id.

### Grill g=5 HOTOVÝ — A27–A29 (impl)

- **A27** — Propose audit = RAM; žádný povinný mark_applied po client apply.
- **A28** — meeting_prep_dispatch cadence každých 15 min; look-ahead 70 min.
- **A29** — Drive prep: SA nebo OAuth; B31 degradace.

### Grill g=6 HOTOVÝ — A34–A37 (impl; dříve A30–A33 — přejmenováno kvůli kolizi s F0 A30)

- **A34** — `meeting_prep_dispatch --dry-run` = 0 vault write `prepare_meeting`, 0 Grok/deliver; jen kandidáti + log.
- **A35** — `proactivity_dispatch --dry-run` = smí číst; 0 OS/Slack/chat; 0 propose/batch.
- **A36** — T7d helper: SSOT JSON `{succeeded[], failed[{id,error_reason}]}`; cesta souboru = impl detail.
- **A37** — crontab meeting_prep `*/15 8-23 * * *` Europe/Prague.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-11 | PLAN | 5bbbd45d… | draft plán | — | F3 Slack/Sembly/Gmail/briefy; zápis f3.md |
| 2 | 2026-10-11 | GRILL | 9ed5ebbb… | POTŘEBUJE ODPOVĚDI | — | Q1–Q6 BLOKUJÍCÍ; Q7–Q10 NEBLOKUJÍCÍ → AWAITING_USER |
| 3 | 2026-10-11 | AWAITING_USER | — | grill | — | Goal paused |
| 4 | 2026-10-11 | PLAN | 5bbbd45d… (r=2) | draft plán | — | g=1 + meeting prep unifikace; zápis f3.md |
| 5 | 2026-10-11 | GRILL | 4dc18be1… | POTŘEBUJE ODPOVĚDI | — | Q11–Q14 BLOKUJÍCÍ → AWAITING_USER |
| 6 | 2026-10-11 | AWAITING_USER | — | grill g=2 | — | Goal paused |
| 7 | 2026-10-11 | PLAN | 5bbbd45d… (r=3) | draft plán | — | g=2 zapracováno; zápis f3.md |
| 8 | 2026-10-11 | GRILL | f77466eb… | HOTOVÝ GRILL | — | A19–A23 NEBLOKUJÍCÍ → CRITIC |
| 9 | 2026-10-11 | CRITIC | e84f4aaf… | K PŘEPRACOVÁNÍ | 1 BLOCKER + MAJOR | C1–C8; AWAITING_USER NEW-1 |
| 10 | 2026-10-11 | AWAITING_USER | — | critic | — | Goal paused — auth apply path |
| 11 | 2026-10-11 | PLAN | cd81c83d… (k=2 r=1) | draft plán | — | C1–C8 vyřešeno v plánu |
| 12 | 2026-10-11 | GRILL | b9cb7c95… | HOTOVÝ GRILL | — | A24–A25 → CRITIC |
| 13 | 2026-10-11 | CRITIC | 1be98e70… | K PŘEPRACOVÁNÍ | 3 MAJOR | C9–C14; C1–C8 uzavřeny |
| 14 | 2026-10-11 | PLAN | cd81c83d… (r=2) | draft plán | — | C9–C14 zapracováno |
| 15 | 2026-10-11 | GRILL | f7c05fa5… | HOTOVÝ GRILL | — | A27–A29 → CRITIC |
| 16 | 2026-10-11 | CRITIC | a8803ead… | K PŘEPRACOVÁNÍ | 2 MAJOR + 2 MINOR | NEW-1…NEW-4 |
| 17 | 2026-10-11 | PLAN | b5de8d58… (r=3) | draft plán | — | C15–C18 zapsáno na disk |
| 18 | 2026-10-11 | GRILL | 31be6955… | HOTOVÝ GRILL | — | A34–A37 → CRITIC |
| 19 | 2026-10-11 | CRITIC | af0b8c4c… | SCHVÁLENO | 3 MINOR | → IMPLEMENT |
| 20 | 2026-10-11 | IMPLEMENT | hlavní | lokální gate OK | — | brain 44 + hub/scripts 356 pytest; commit pending |
| 21 | 2026-10-11 | REVIEW | — | start | — | po commitu |

### Rozhodnutí C1 / apply UX (2026-10-11)

Uživatel: „jo, takhle je to OK“ na doporučení:

- **UX:** „ano, udělej XXX“ → u **vratných** (archive, kopie, přesun, Gmail koš jako obnovitelný) proveď; u **nevratných** (odeslat Slack/e-mail, permanent delete) druhá otázka v téže appce, pak proveď.
- **Technika F3:** primár **client apply** (Gmail/Slack connector / skript) po tomto UX; Brain = propose + audit; Brain `*/apply` zůstává service→403 (Q12=a); OAuth Brain apply / signed token = post-F3 dluh, ne primár path.
- Gmail trash = vratné (default), dokud uživatel neřekne jinak.

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav | Kolikrát vznesen |
|---|---|---|---|---|
| C1 (NEW-1) | BLOCKER | PLAN | vyřešen v k=2 (client apply + 1×/2×) | 1 |
| C2 (NEW-2) | MAJOR | PLAN | vyřešen v k=2 | 1 |
| C3 (NEW-3) | MAJOR | PLAN | vyřešen v k=2 | 1 |
| C4 (NEW-4) | MAJOR | PLAN | vyřešen v k=2 | 1 |
| C5 (NEW-5) | MAJOR | PLAN | vyřešen v k=2 | 1 |
| C6 (NEW-6) | MAJOR | PLAN | vyřešen v k=2 | 1 |
| C7 (NEW-7) | MINOR | PLAN | vyřešen v k=2 | 1 |
| C8 (NEW-8) | MINOR | PLAN | vyřešen v k=2 | 1 |
| C9 (NEW-1 kolo2) | MAJOR | PLAN | vyřešen v r=2 | 1 |
| C10 (NEW-2) | MAJOR | PLAN | vyřešen v r=2 | 1 |
| C11 (NEW-3) | MAJOR | PLAN | vyřešen v r=2 | 1 |
| C12 (NEW-4) | MAJOR | PLAN | vyřešen v r=2 | 1 |
| C13 (NEW-5) | MINOR | PLAN | vyřešen v r=2 (70 min) | 1 |
| C14 (NEW-6) | MINOR | PLAN | vyřešen v r=2 (due hourly) | 1 |
| C15 (NEW-1 kolo3) | MAJOR | PLAN | vyřešen v r=3 — B33 client; T8/T19 | 1 |
| C16 (NEW-2) | MAJOR | PLAN | vyřešen v r=3 — B36/B37 dry-run | 1 |
| C17 (NEW-3) | MINOR | PLAN | vyřešen v r=3 — A27–A29 v plánu | 1 |
| C18 (NEW-4) | MINOR | PLAN | vyřešen v r=3 — sembly L93 | 1 |
