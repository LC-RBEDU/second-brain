# Plán: Návod pro agenty mimo Cursor

Autor: [architekt](35f3b04a-72fb-4efd-9b91-069e7d1b4e0e), otevření #2. Ledger: [2026-10-04-agent-guide-mimo-cursor.pipeline.md](2026-10-04-agent-guide-mimo-cursor.pipeline.md).

## Zadání a požadavky

R1 — Český návod v `OBSIDIAN/00-System` pro Claude Cowork a Grok Bot: co a kam zapisovat, kde se co dozvědí, co dělá cron.

R2 — Režimy se testují pytestem, ne `rbu-tester`.

R3 — Soubor `OBSIDIAN/00-System/agent-guide-mimo-cursor.md`. Nepřepisovat Cursor rules, `agent-bootstrap.md`, `docs/claude-project-instructions.md`, README v `01-INBOX/`. Návod řekne, že věta o archivu po 90 dnech neplatí.

R4 — `cowork-instructions.md`: po loaderu otevřít návod. Když nejde otevřít, do existujícího `.md` nezapisovat; smí jen nový soubor do `01-INBOX/daily/`.

R5 — Popis Grok Bota v aplikaci se nezakládá. V návodu je odstavec ke zkopírování: účet `lukas@redbuttonedu.cz`, cesta `SECOND_BRAIN/OBSIDIAN/`, tři režimy z R16, zákaz `/workspace`, bez celého originálu se existující `.md` nepřepisuje.

R6 — Interaktivní složka = disk. Schedule se složkou a otevřeným Desktopem = jen čtení, ne disk. Telefon a schedule bez složky = vzdálený režim toho agenta. Placeholder není vzdálený režim.

R7 — `archive_inbox_item.py`, `sync_lide_people.py`, `extract_material_text.py` nespouštět a nenahrazovat ručním přesunem. Slack smí Cowork po „pošli“. Git, deploy, VPS ne. `focus` jen na pokyn, max 5 podle `stats.focus_count`. `## Stav (auto)` nepsat. Ranní brief nespouští `build_agent_context.py`.

R8 — Vzdálený Cowork: jen nový soubor do `01-INBOX/daily/`. `Agent_Bus/` a nové soubory v `tasks/` ne, ani na disku (R13).

R9 — Cron: checkboxy v celém těle u ne-epicu → Done, epic ne. Agent sám Done kvůli checkboxům nepřepisuje. Archiv Done/Cancelled bez recurring do dvou hodin, agent soubor nepřesouvá. Recurring Done nechá agent v `tasks/`; cron instanci archivuje a na stejnou cestu zapíše další cyklus. Recurring Cancelled zůstane. Triáž cronem skončila 2026-09-24. README v `01-INBOX/` se nepřepisuje; návod řekne, že lže.

R10 — Diskuse jen na interaktivním disku: `OBSIDIAN/00-System/Agent_Bus/YYYY-MM-DD.md`, Europe/Prague. Zápis znovu načte celý den, staré bloky nechá, přidá `## HH:MM — Cursor|Cowork|Grok` a `téma:`. Cizí blok = načíst znovu. Starší dny ne. Slack kanál v návodu není.

R11 — Append a ořez rozhoduje `scripts/lib/agent_write_guard.py`. Návod na ni odkáže.

R12 — Cizí dirty soubory do commitu nepatří.

R13 — Cowork a Grok nové tasky nezakládají a `next_task_id.py` nespouštějí. Popis toho, co má vzniknout, je nový soubor v `01-INBOX/daily/`. Task založí Cursor na desktopu.

R14 — Grok na telefonu smí změnit řádek jen když `reread == held` a oba mají uzavřený frontmatter. Pak smí nahradit právě jeden řádek. Když čtení nesedí, task se nezapisuje a změna jde do daily. Mazání řádků bez shodného čtení neprojde. Na disku úmyslné smazání, které není prefix, smí. Prefix je `deny_prefix_cut` s `text=None` na disku i na telefonu.

R15 — `target_read` patří jedné cestě. `absent` u nového souboru není failed. `guide_readable=False` a create nového daily je `allow_daily_create`, `claimed_remote=False`. Placeholder přepisovaného cíle je `deny_read_failed` a jiný daily create neblokuje.

R16 — Pořadí: interaktivní složka = disk; schedule se složkou a otevřeným Desktopem = jen čtení; schedule bez složky = telefon toho agenta.

R17 — `focus_count` z `agent-context.json` → `stats.focus_count`. Vlastní přepočet jen jako snapshot: aktuální týden, bez pauznutých projektů, včetně Waiting, Backlog a epiců. `FOCUS_INELIGIBLE_STATUSES` není strop pěti.

R18 — Když skill a návod nesedí u skriptů, archivu, focus a `## Stav (auto)`, platí návod. Ranní prompt: refresh po 24 h a `ukliď` z `agenda-co-ted` neplatí, skript nespouštět, soubory nepřesouvat.

Mimo rozsah: `vps/**`, deploy, Slack kanál, přepis bootstrapu, claude-project-instructions, INBOX README, root README, hub README. `rbu-tester` se nevolá.

## Předpoklady

A1 — `decide()` je jedna cesta. Daily po odmítnutém tasku je druhé volání. Na telefonu se modul nespouští; platí stejné kódy v návodu.

A2 — Shodné čtení = `reread == held`, oba mají uzavřený frontmatter a stejné řádky. Náhrada řádku = stejný počet řádků, právě jeden jiný. Prefix = návrh je vlastní prefix originálu. Prefix je `deny_prefix_cut`, ne `deny_read_failed`.

A3 — Když `reread` je jiný úplný dokument než `held`, výsledek je `deny_stale_reread` a `text=None`. `restore_original` jen když na disku leží ořez `held` (živý obsah je prefix). Novější úplný soubor se originálem nepřepisuje.

A4 — `target_read` je `ok` | `absent` | `failed` | `placeholder` a platí jen té cestě. `absent` není failed a není přepnutí na telefon.

A5 — Slack jen Cowork po „pošli“ / „ano“. Grok ne. Ranní běh a schedule se složkou nespouští nic.

A6 — Schedule se složkou, ale bez otevřeného Desktopu, je telefon toho agenta.

A7 — Strop 5 bere `stats.focus_count`. Vlastní přepočet je množina z `build_agent_context.py` řádky 361–370: ne-terminální tasky mimo pauznuté projekty, `focus` aktuálního týdne, včetně Waiting, Backlog a epiců.

A8 — `build_agent_context.py` jen na interaktivním disku a jen s `after_task_write=True` po přepisu existujícího tasku.

A9 — Nových souborů v `01-INBOX/daily/` smí být víc.

A10 — Test návodu se přeskočí, když není `OBSIDIAN/`. Když vault je a návod chybí, test selže.

A11 — `vps/` se nemění. Push se nenařizuje.

## Návrh

### 1. `scripts/lib/agent_write_guard.py`

Bez I/O a bez `datetime.now`. `classify_surface(actor, is_schedule, has_folder, desktop_open)`:

1. schedule a složka a otevřený desktop → `morning_schedule` (jen čtení), ať je actor kdokoliv.
2. schedule bez složky → telefon toho agenta.
3. schedule se složkou a zavřený desktop → telefon toho agenta.
4. ne schedule a lokální složka → `disk_cowork` nebo `disk_grok`.
5. bez složky → telefon toho agenta.

`decide` pro overwrite a `set_focus` v pořadí: morning → deny write; failed/placeholder té cesty → `deny_read_failed`; held bez frontmatteru → `deny_read_failed`; `reread != held` a reread je úplný dokument → `deny_stale_reread`; živý obsah je prefix held → `restore_original`; návrh je prefix → `deny_prefix_cut`; Grok telefon a méně řádků → `deny_phone_line_delete`; shoda a náhrada jednoho řádku nebo disk a ne-prefix → allow. Cowork telefon na `set_focus` je `deny_focus_cowork_phone`. Create mimo daily a dnešní bus je `deny_create`. Create pod `tasks/` je `deny_new_task` všude. `next_task_id.py` je vždy `deny_script`.

Kódy, které testy srovnají doslova: `allow_append_bus`, `deny_foreign_block`, `deny_duplicate_block`, `deny_old_bus_day`, `deny_bus_heading`, `deny_workspace`, `deny_read_failed`, `deny_agent_bus_remote`, `deny_morning_write`, `allow_overwrite`, `deny_prefix_cut`, `deny_phone_line_delete`, `deny_stale_reread`, `restore_original`, `deny_task_after_failed_restore`, `allow_daily_create`, `deny_existing_md`, `deny_new_task`, `deny_create`, `deny_focus_cowork_phone`, `allow_focus`, `deny_focus_without_ask`, `deny_focus_over_5`, `deny_morning_build_context`, `allow_script`, `deny_script`, `allow_slack_send`, `deny_slack`, `deny_archive_move`, `deny_recurring_move`, `deny_status_done_from_boxes`, `deny_stav_auto`.

`allow_script` jen `build_agent_context.py` (disk, `after_task_write`) a `schedule_reminder.py` (disk, `preview_shown`). Guard nic nezapisuje.

### 2. Návod ve vaultu

Česky, gitignored. Pořadí režimů hned na začátku a v odstavci pro Groka. Append bus jen na interaktivním disku. Přepis tasku se stejnou podmínkou `reread == held` jako bus. Nové tasky jen jako text v daily. Focus z `stats.focus_count`. Cron podle crontab, včetně lži o 90 dnech a `Triage-Pending`. Když skill a návod nesedí, platí návod. Tabulka reason kódů. Žádné `C0C3E0JFNA0`. Žádný pokyn spouštět `next_task_id.py`.

### 3. `cowork-instructions.md`

Otevři návod. Když nejde, jen nový daily. Když skill a návod nesedí u skriptů, archivu, focus a `## Stav (auto)`, platí návod.

### 4. `ŠABLONY/cowork-morning-brief.md`

Prompt smí odkázat `agenda-co-ted`, ale musí říct: refresh po 24 h neplatí, `ukliď` neplatí, `build_agent_context.py` nespouštět, soubory nepřesouvat, vault ani Slack nepsat. Staré `generated_at` napsat do chatu a snapshot použít. Smazat výzvu spustit skript.

### 5. Testy

`scripts/tests/test_agent_write_guard.py`. Režimy nečtou vault.

## Kontrakt (B#)

- B1–B3 append bus na disku; `/workspace` deny. T1, T2.
- B4 placeholder/failed přepisované cesty: `deny_read_failed`, `claimed_remote=False`. T3.
- B5 jiný request, create daily, zatímco jiná cesta selhala: `allow_daily_create`. T3.
- B6–B10 Cowork telefon a nečitelný návod: jen nový daily; focus, bus, task, archiv deny; schedule bez složky = telefon. T4.
- B11–B21 Grok telefon a disk: jeden řádek allow, prefix deny s `text=None`, neshoda čtení nezapíše task a pustí daily, mazání na telefonu deny, diskové smazání uprostřed allow, bus a create tasku deny. T5.
- B22–B25 morning a schedule se složkou: žádný zápis, ani dnešní bus, ani build context, ani Slack. T6.
- B26–B31, B35 skripty: `next_task_id` deny i s `--type`; build jen po přepisu na disku; reminder po náhledu; Slack jen Cowork po „pošli“; založení tasku je daily. T7.
- B32 create pod `tasks/` deny všude. T1.
- B33 create dnešního bus při `absent` allow. T1.
- B34 jiný create `deny_create`. T1.
- B36–B39 archiv deny; recurring zůstává na cestě jen při shodném čtení; když status už není Done, držené tělo se nezapíše. T8.
- B40–B47 focus: bez pokynu deny; count 5 a task mimo pětici deny; count 4 allow; už v pětici při count 5 allow; Cowork telefon deny i při count 4; morning deny; Grok telefon jen při shodném čtení. T9 a T4. Allow focusu není allow_overwrite.
- B48–B52 bus: první blok, cizí blok, duplicita, starý den, špatná hlavička. T1.
- B53 návod má reason kódy, nemá channel ID ani `next_task_id`. T10.
- B54 morning prompt bez vět o 24 h, `ukliď`, skriptu a přesunu selže, i když odkáže skill. T11.
- B55 cowork-instructions má cestu, daily fallback a přednost návodu. T12.
- B56 disk, smazání řádku uprostřed, není prefix, čtení sedí: `allow_overwrite`. T5.

## Výkon (P)

Guard srovná dva řetězce jedné cesty. SQL 0. Vault neotevírá. Morning a schedule se složkou `build_agent_context.py` nespouštějí. Důkaz je pytest T1–T12. QA nespouští Coolify, dokud diff nesahá na `vps/`.

## Testy (T#)

T1 mód 1 (B1, B32–B34, B48–B52). T2 mód 2 (B2, B3). T3 mód 3 (B4, B5). T4 mód 4 (B6–B10, B42). T5 mód 5 (B11–B21, B56). T6 mód 6 (B22–B25) včetně schedule se složkou a append bus deny. T7 mód 7 (B26–B31, B35). T8 mód 8 (B36–B39). T9 mód 9 (B40, B41, B43–B47). T10 návod. T11 morning prompt. T12 cowork-instructions.

Spuštění: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q`.

## Pořadí

F1 guard a T1–T9, nejdřív testy. F2 návod, T10. F3 cowork-instructions, T12. F4 morning brief, T11. F5 celý pytest. F6 commit jen F1, F3, F4 plus plán a ledger. Návod v gitu není. `vps/` neměnit.

## Rizika

Návod je jen na Drive. Guard nenutí model, který návod neotevře. `restore_original` se nesmí použít na novější úplný soubor (B39). README dál lžou. Append není zámek. `next_task_id.py` pro Cursor zůstává. `focus_count` počítá i Waiting, Backlog a epicy.

## Otevřené otázky

1. Slack z Groka po „pošli“. Předpoklad: ne.
2. Text Drive placeholderu guard nezná; volající nastaví `target_read`.
3. Schedule se složkou a zavřeným Desktopem je telefon toho agenta.

## Nálezy

C1–C9 vyřešeny v tomto plánu.

## Kolo 3 — závazné pořadí (přepisuje sekci 1, pokud se liší)

`decide` vybere funkci podle `op`. Focus nevolá overwrite. Create nevolá overwrite. Allow je až poslední krok.

`decide_focus`: 1 morning `deny_morning_write`. 2 `cowork_phone` `deny_focus_cowork_phone` i při pokynu a count 4. 3 bez pokynu `deny_focus_without_ask`. 4 `already_in_focus` false a `focus_count >= 5` → `deny_focus_over_5`; už v pětici nebo count < 5 pokračuje. 5 checkbox-Done → `deny_status_done_from_boxes` a Stav (auto) → `deny_stav_auto`, na disku i na `grok_phone`, ještě před allow. 6 `grok_phone` jen při `reread == held` → `allow_focus`, jinak `deny_stale_reread`. 7 disk: `reread != held` je restore jen při prefixu, jinak `deny_stale_reread`, teprve pak `allow_focus`. Žádný krok nevolá `allow_overwrite`.

`decide_create`: 1 morning každý create včetně daily a bus při `absent` → `deny_morning_write`. 2 dnešní Agent_Bus: ne-disk → `deny_agent_bus_remote`. `guide_readable=False` → bus deny (žádný `allow_append_bus`). failed nebo placeholder té cesty → `deny_read_failed`. Allow jen `disk_*`, čitelný návod, `target_read` ok nebo absent, platný blok, a při ok navíc `reread == existing`. 3 `guide_readable=False` u ostatních cest: existující md `deny_existing_md`, nový daily allow. 4 create pod `tasks/` → `deny_new_task` všude. 5 nový daily při `absent` → `allow_daily_create`; existující → `deny_existing_md`. 6 jinak `deny_create`.

`decide_overwrite`: 1 morning deny. 2 failed/placeholder té cesty `deny_read_failed`. 3 `cowork_phone` → `deny_existing_md` i při jednom řádku. 4 `guide_readable=False` → `deny_existing_md` i na disku. 5 `reread != held`: prefix na disku `restore_original`, jinak `deny_stale_reread` včetně neúplného čtení. 6 návrh je prefix → `deny_prefix_cut`. 7 checkbox Done → `deny_status_done_from_boxes`. 8 Stav (auto) → `deny_stav_auto`. 9 `grok_phone` a právě jeden řádek a `reread == held` → `allow_overwrite`. 10 `grok_phone` cokoliv jiného → `deny_phone_not_one_line`. 11 disk a `reread == held` a není prefix → `allow_overwrite` včetně smazání uprostřed. 12 jinak `deny_existing_md`.

Strop focus: count 5 a task ještě není v pětici → deny. Count 4 → allow. Už v pětici při count 5 → allow. Citace: `scripts/build_agent_context.py` řádky 527, 531–532, 536, 664. Ne 361–370.

Schedule se složkou a otevřeným desktopem = morning. Zavřený desktop = telefon. Cowork telefon do existujícího `.md` nezapisuje. C1 náhrada řádku při shodném čtení, prefix `deny_prefix_cut`. C2 `target_read` na jednu cestu, daily při nečitelném návodu allow. C3 create tasku deny, create dnešního bus allow. C4 focus na Cowork telefonu a morning deny, Grok telefon jen při shodném čtení. C5 morning prompt a přednost návodu před skillem. C6 `next_task_id` deny, nové tasky jen daily. C7 `stats.focus_count`, ne `FOCUS_INELIGIBLE_STATUSES`. C8 schedule se složkou je jen čtení. C9 přepis tasku vyžaduje `reread == held`; staré Done tělo se přes novější cyklus nezapíše.
