# Pipeline: Návod pro agenty mimo Cursor

Stav: DONE
Plán: docs/plans/2026-10-04-agent-guide-mimo-cursor.md
Schvalování plánu uživatelem: ne
Architekt: agent ID 35f3b04a-72fb-4efd-9b91-069e7d1b4e0e, otevření plánu #2, generace v otevření 1/3, kolo 2/3
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): a0ea69a979a3ee0576411d0b14048291cdd8bc98 · Kódový SHA: 4a5b18de2ee88d006da90700eb72ac952ddb2697 · Review SCHVÁLENO na: 4a5b18de2ee88d006da90700eb72ac952ddb2697 · QA PASS na: 4a5b18de2ee88d006da90700eb72ac952ddb2697 · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Goal: complete

## Projekt

SECOND_BRAIN. Kořen `~/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN`. Větev `main`, base `a0ea69a`. Nasazení cronu se netýká, pokud se nemění `vps/`. `OBSIDIAN/` je git-ignored. Tester: vždy `TESTER: přeskočeno (profil SECOND_BRAIN)`. Uživatel přesto chce otestovat režimy návodu. Ty testy jsou T# v plánu (pytest nebo skript), ne `rbu-tester`.

## Zadání (doslovně)

Původní: „Chtěl bych vytvořit nějaký .MD soubor, který bude někde v '/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN/00-System' a bude sloužit jako návod na použití mého Second Brainu pro jiné AI agenty než je Cursor. Hodlám Second Brain používat jak v Claude Coworku, tak i v Grok Botovi a oběma chci dát návod, jak s tím pracovat - co a kam mají zapisovat, kde se co dozvědí, jaké aktivity se řeší v cronu VPS a nemá cenu je řešit přímo atd. atd.“

Spuštění pipeline: „pusť se do toho, ale chci to protáhnout přes /rbu-pipeline, včetně otestování různých módů“

## Rozhodnutí

- Návod česky: `OBSIDIAN/00-System/agent-guide-mimo-cursor.md`. Čtenáři jsou Claude Cowork a Grok Bot. Cursor rules a `agent-bootstrap.md` se nepřepisují. `docs/claude-project-instructions.md` se nepřepisuje. Návod řekne, že věta o archivu po 90 dnech v README a v tom docs souboru neplatí.
- `cowork-instructions.md`: po loaderu přečíst návod. Když návod nejde otevřít, do existujícího `.md` nezapisovat, smí jen nový soubor do `01-INBOX/daily/`.
- Popis Grok Bota v aplikaci se nezakládá. V návodu je odstavec ke zkopírování: účet `lukas@redbuttonedu.cz`, cesta `SECOND_BRAIN/OBSIDIAN/`, otevřít návod, tři režimy, zákaz `/workspace`, bez celého originálu se existující `.md` nepřepisuje.
- Režimy: Disk (Cowork složka `SECOND_BRAIN`, nebo Grok Execution on Local Computer a běžící desktop). Schedule se složkou a otevřeným Desktopem = jen čtení, ranní brief vault nezapisuje. Telefon a schedule bez složky = vzdálený. Selhání čtení na Macu (placeholder) není vzdálený režim. Bez celého originálu včetně frontmatteru nezapisovat.
- Vaultové skripty jen tři: `next_task_id.py` vždy s `--type`, `build_agent_context.py` po zápisu tasku, `schedule_reminder.py` po náhledu. `archive_inbox_item.py`, `sync_lide_people.py`, `extract_material_text.py` nespouštět a nenahrazovat ručním přesunem. `slack_send_message.py` smí Cowork po „pošli“. Git, deploy, VPS ne. `focus` jen když to Lukáš řekne, max 5. `## Stav (auto)` nepsat. Ranní brief nespouští `build_agent_context.py`. Upravit `ŠABLONY/cowork-morning-brief.md`, ať to po něm nežádá.
- Vzdálený: Cowork telefon jen nový soubor do `01-INBOX/daily/`. Grok telefon přepis tasku jen s celým originálem. Špatné znovunačtení: vrátit držený originál, pak změnu do daily. Když originál nejde zapsat, do tasku už nepsat. Nový soubor v `tasks/` na mobilu ne. `Agent_Bus/` na mobilu ne.
- Cron: checkboxy v celém těle u ne-epicu → Done, epic ne. Agent sám Done kvůli checkboxům nepřepisuje. Archiv Done/Cancelled bez recurring do dvou hodin, soubor nepřesouvat. Recurring Done nechat v `tasks/`. Recurring Cancelled zůstane. Triáž cronem skončila 2026-09-24, `Triage-Pending` nečekat. README v `01-INBOX/` v tom lže, nepřepisovat ho v tomhle úkolu, návod to řekne.
- Diskuse jen Mac: `OBSIDIAN/00-System/Agent_Bus/YYYY-MM-DD.md`, datum Europe/Prague. Ne věčný soubor, ne soubor na téma. Zápis: znovu načíst celý den, staré bloky beze změny, přidat `## HH:MM — Cursor|Cowork|Grok` a řádek `téma:`. Když přibyl cizí blok, načíst znovu. Starší dny neupravovat. Slack kanál `C0C3E0JFNA0` v návodu není. Slack aplikace @Claude a @Cursor uživatel 4. 10. 2026 z kanálu odebral.
- Cizí dirty soubory v pracovním stromu (wiki-firemni-priority, pipeline-exceptions, playwright, output) do commitu nepatří.
- 2026-10-05: Cowork a Grok nové tasky nezakládají a `next_task_id.py` nespouštějí. Do `01-INBOX/daily/` napíšou, co má vzniknout. Nový task založí až práce z desktopu (Cursor).
- 2026-10-05: Grok na telefonu smí změnit řádek existujícího tasku jen když nové čtení sedí na celý držený originál. Jinak task nechá a změnu zapíše do `01-INBOX/daily/`. Mazání řádků bez toho shodného čtení neprojde.

## Módy k otestování

Uživatel chce otestovat režimy. Profil SECOND_BRAIN testera nespouští. Ověření je v T# (čitelný důkaz, ne jen „v návodu ta věta je“):

1. Disk Cowork: složka `SECOND_BRAIN`, append do dnešního `Agent_Bus` bez smazání starých bloků.
2. Disk Grok: stejný append, když je Execution on Local Computer. `/workspace` není cíl.
3. Placeholder / čtení selhalo: nezapisovat, nehlásit vzdálený režim.
4. Cowork telefon, návod nejde otevřít: jen nový soubor do `01-INBOX/daily/`, existující `.md` ne.
5. Grok telefon: přepis tasku jen s celým originálem. Ořez vrátí originál. `Agent_Bus/` ne.
6. Schedule ranní brief: vault nezapisuje, `build_agent_context.py` nespouští.
7. Skripty: tři vaultové, `next_task_id.py --type`. Slack až po „pošli“. Archiv inboxu nespouštět.
8. Archiv a recurring: soubor nepřesouvat. Recurring Done nechat v `tasks/`.
9. `focus` jen na výslovný pokyn, max 5.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-04 23:50 | PLAN | — | — | — | Ledger založen. Start architekta. |
| 2 | 2026-10-04 23:55 | PLAN | [architekt](35f3b04a-72fb-4efd-9b91-069e7d1b4e0e) | plán | — | Guard `scripts/lib/agent_write_guard.py`, návod ve vaultu, T1–T12 pro 9 módů. Přechod na CRITIC. |
| 3 | 2026-10-05 00:10 | CRITIC | [kritik](454e8c76-37c4-4e2e-b1b9-56be2d34e379) | K PŘEPRACOVÁNÍ | 6 BLOCKER, 3 MAJOR | C1 a C6 jsou blokující otázky. Přechod na AWAITING_USER. |
| 4 | 2026-10-05 00:25 | PLAN | [architekt](35f3b04a-72fb-4efd-9b91-069e7d1b4e0e) | plán v2 | C1–C9 zapracovány | Žádné nové tasky. Telefon smí změnit řádek jen při shodném čtení. |
| 5 | 2026-10-05 00:40 | CRITIC | [kritik](ef16d82e-a151-40f3-b501-aafc1df89794) | SCHVÁLENO | 0 | Pořadí kola 3. Schvalování plánu nevyžadováno. |
| 6 | 2026-10-05 00:55 | IMPLEMENT | hlavní agent | testy zelené | — | Guard + pytest T1–T12. Návod je jen na Drive. |
| 7 | 2026-10-05 01:20 | REVIEW | [reviewer](5000395d-d822-4ce2-8b04-99f302b2ce17) | SCHVÁLENO | 0 | Na SHA 4a5b18d. |
| 8 | 2026-10-05 01:25 | QA | [QA](f1b3be55-0053-4d58-98fd-3057a25cb373) | PASS | 0 | pytest 287 passed, exit 0. Coolify se netýká. |
| 9 | 2026-10-05 01:26 | TESTER | — | přeskočeno | — | TESTER: přeskočeno (profil SECOND_BRAIN) |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| C1 | BLOCKER | PLAN | otevřený, čeká na uživatele | 1 |
| C2 | BLOCKER | PLAN | otevřený | 1 |
| C3 | BLOCKER | PLAN | otevřený | 1 |
| C4 | BLOCKER | PLAN | otevřený | 1 |
| C5 | BLOCKER | PLAN | otevřený | 1 |
| C6 | BLOCKER | PLAN | otevřený, čeká na uživatele | 1 |
| C7 | MAJOR | PLAN | otevřený | 1 |
| C8 | MAJOR | PLAN | otevřený | 1 |
| C9 | MAJOR | PLAN | otevřený | 1 |
