# Pipeline: finalize_meeting

Stav: REVIEW
Plán: docs/plans/2026-11-02-finalize-meeting.md
Schvalování plánu uživatelem: ne
Architekt: agent ID 753d61cf-727f-41e5-b779-208c8048ffc8, otevření plánu #1, generace v otevření k=1/3, kolo r=3/3
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (rbu-base, origin/main při vzniku větve): 5888d5a3674dcfbc6b013b14009c4793164205d0 · Kódový SHA: 9be2e7ae8f7afcdba38e55059fc40b0595ed284b · Review SCHVÁLENO na: 9be2e7ae8f7afcdba38e55059fc40b0595ed284b · QA PASS na: — · TESTER PASS na: přeskočeno až na testerGate (bez UI)
Plán schválen uživatelem: nevyžadováno
Goal: aktivní

## Projekt

SECOND_BRAIN. Kořen `/Users/lukascypra/GitHub/SECOND_BRAIN` (ne starý Drive workspace). Větev z `origin/main` `5888d5a3674dcfbc6b013b14009c4793164205d0`. Lokální `main` je 54 commitů pozadu a má nesouvisející necommitnuté změny (Slack capture / VIP). Do téhle pipeline nepatří.

Nasazení Brain API: Coolify app `second-brain-brain`, build context `vps/`, `https://brain.cyprovi.cz`. Skill v `ŠABLONY/skills/` je lokální symlink, image Brain se nasazuje. Ostrý zápis do vaultu jen jako T# v plánu, jinak pytest / dry-run.

Tester: bez UI → `TESTER: přeskočeno (profil SECOND_BRAIN, bez UI)`. `rbu-tester` nevolat.

## Zadání (doslovně) a rozhodnutí

### Zadání uživatele

> Potřebuji upravit workflow zpracovávající zápisy ze Sembly - viz příloha: /Users/lukascypra/Downloads/brief-finalize-meeting.md
>
> Připrav plán implementace a doptej se na co chybí nebo co je nejasné

> ještě prověř jednou odkaz /Users/lukascypra/Downloads/brief-finalize-meeting.md - je tam aktualizovaná verze

> ok, jdi na to přes /rbu-pipeline

Příloha (celá, ověřeno 2026-11-02 01:52, soubor beze změny oproti verzi, ze které vznikl první návrh):

# Brief pro Cursor: Brain nástroj `finalize_meeting` + oprava procesu zápisů ze schůzek

Stav: návrh k 2. 11. 2026 · Autor: Claude (chat, projekt Second Brain v2) · Schvaluje: Lukáš

## Cíl
Každý přepis schůzky v `01-INBOX/sembly/` skončí jednou ze dvou cest: zápis ve vaultu + přepis v archivu, nebo přepis v archivu s důvodem přeskočení. Žádný přepis nesmí zůstat v Inboxu jen proto, že zápis šel jinam (týmový disk, Slack) nebo nikam (1:1).

## Rozhodnutí Lukáše (2. 11. 2026)
- Vault drží kopii **všech** zpracovaných zápisů, i z cizích týmů (Strategy, Finance, Technaři…) a 1:1.
- Zpracované zápisy chce primárně ve vaultu. Na Drive se nic nemusí udržovat, kromě kopií, které se ukládají na týmové disky (to je dál volitelný krok skillu).
- Firemní skill `rbedu-zapis-ze-schuzky` se nemění (kolegové vault nemají); vault logika patří do osobní vrstvy.

## Zjištění (ověřeno 2. 11. 2026)
- Poslední zápis ve vaultu a poslední archivovaný sembly přepis jsou z 9. 10. (`05-RESOURCES/vystupy/zapisy/2026-10/`, `07-ARCHIV/inbox-processed/2026/10/sembly/`). V `01-INBOX/sembly/` leží 30 přepisů z 12.–30. 10., v archivu žádný.
- Firemní skill `rbedu-zapis-ze-schuzky` (Krok 10–11) končí na týmovém disku a ve Slacku. Do vaultu nezapisuje a Inbox neuklízí.
- Cron triáž skončila 24. 9.; `agent-guide-mimo-cursor.md` zakazuje Coworku/Grokovi archivní skripty. Úklid Inboxu tedy nikdo nevlastní.
- Brain MCP nemá nástroj, který by zapsal materiál do vaultu nebo přesunul soubor z Inboxu: `capture_daily` píše jen do `01-INBOX/daily/`, `ingest_sembly` jen přijímá přepis do `01-INBOX/sembly/`.
- Přepisy v Inboxu nemají frontmatter ani stav, nejde poznat zpracované/nezpracované.
- *Inference:* 1:1 a citlivé schůzky se neukládají, protože Krok 11a skillu žádá „disk týmu, který schůzku konal“ a u 1:1 žádný takový tým není.

## Rozhraní: MCP tool `finalize_meeting`
Jedna atomická akce (jeden git commit). Za jedno volání buď uloží zápis a archivuje přepis, nebo přepis jen archivuje s důvodem.

| Parametr | Typ | Default | Popis |
|---|---|---|---|
| `transcript_path` | string | – | Cesta přepisu v `01-INBOX/…` (povinné). |
| `expect_oid` | string | null | CAS na přepis; nesedí-li, chyba `oid_mismatch` + aktuální oid. |
| `zapis_md` | string | null | Celý obsah zápisu včetně frontmatteru. Povinné, pokud není `skip_reason`. |
| `meeting_date` | date | z frontmatteru | Pro složku `YYYY-MM/`. |
| `slug` | string | z titulku | Název `YYYY-MM-DD_<slug>_zapis.md`, kebab-case bez diakritiky. |
| `drive_urls` | string[] | [] | Kopie na týmových discích; uloží se do frontmatteru `drive_copies`. |
| `skip_reason` | enum | null | `smoke` \| `empty` \| `duplicate` \| `fragment` \| `other` (+ `skip_note`). Zápis se nevytváří. |
| `dry_run` | bool | false | Vrátí cílové cesty a diff, nic nezapíše. |

### Chování
1. **Zápis (create-only):** `05-RESOURCES/vystupy/zapisy/YYYY-MM/YYYY-MM-DD_<slug>_zapis.md`. Existuje-li soubor, chyba s jeho oid, nepřepisovat.
2. **Validace frontmatteru:** povinné `type: material`, `material_kind: schuzka`, `doc_type: meeting_summary`, `title`, `meeting_date`, `participants`, `variant`. Brain doplní `source_transcript` (cesta v archivu) a `drive_copies`. Vzor: `05-RESOURCES/vystupy/zapisy/2026-10/2026-10-09_luci-luky-claude-team_zapis.md`.
3. **Archivace přepisu:** přesun do `07-ARCHIV/inbox-processed/YYYY/MM/sembly/` stejnou normalizací názvu jako stávající `scripts/archive_inbox_item.py`; do hlavičky `**ZPRACOVÁNO**` + odkaz na zápis (nebo `skip_reason`). Co-located přílohy se přesouvají s přepisem.
4. **Idempotence:** opakované volání se stejným obsahem a už archivovaným přepisem vrací OK bez změny.
5. **Atomicita:** buď oba zápisy (zápis + archiv), nebo žádný. Nikdy stav „zápis existuje, přepis zůstal v Inboxu“.
6. HTML verze se do vaultu neukládá (zůstává mimo vault, jak říká `zapisy/README.md`).
7. Výstup jako objekt: `{zapis_path, archive_path, zapis_oid, commit, warnings[]}`.

### Související malá změna
`get_context` vrací `inbox_sembly_pending` (počet) a `oldest_pending_age_days`, aby ranní brief ukázal „N přepisů v Inboxu starších než 24 h“. Jen čtení.

## Změny skillu (osobní vrstva, repo SECOND_BRAIN, `ŠABLONY/skills/agenda-zapis-ze-schuzky/`)
1. Přepsat na tenký wrapper: vybrat přepis z Inboxu → spustit firemní `rbedu-zapis-ze-schuzky` (Kroky 0–10 beze změny) → po schválení preview (Krok 7) **vždy** `finalize_meeting` (nejdřív `dry_run`) → teprve potom nabídnout Krok 11 (Drive, Wiki, Slack).
2. Odmítnutí sdílení nesmí zabránit uzavření přepisu.
3. 1:1 a citlivé (P&C, jednání s CEO, klient pod NDA): default **jen vault**, otázka na týmový disk se přeskočí; Drive/Slack jen na výslovný pokyn.
4. Třídění přepisu před zápisem: zápis | přeskočit (`skip_reason`). Generické názvy („Meeting Friday…“, „Google Meet …“) určit podle kalendáře.
5. Ve firemním skillu stačí volitelný hook: je-li dostupný Brain nástroj `finalize_meeting`, proveď ho jako Krok 10b. Bez Brainu se nic nemění.

## Backlog k vyřešení (30 přepisů v `01-INBOX/sembly/`, stav 2. 11. 2026)
Klasifikace je *Inference* z dat a názvů na Drivu; před importem ověřit proti konkrétnímu souboru.
- **Zápis už existuje na týmovém disku (~13):** 13. 10. Finance Sync, 13. 10. Lukáš–Mária, 14. 10. Ty, já a Claude, 14. 10. Míša K. onboarding, 16. 10. Technaři sync, jedna z generických 16. 10. (Velín – ukázka), 20. 10. (Google Meet 11:42 = pravděpodobně Finance Sync), 20. 10. Lukáš–Mária, 20. 10. Lukáš–Pavel, 23. 10. Technaři sync, 26. 10. Strategická schůzka, 26. 10. čAI session, 30. 10. Jindra & Lukáš. Postup: načíst poslední verzi MD z Drive, `finalize_meeting` s `drive_urls`. Pozor: u 30. 10. jsou na Drivu dva zápisy vzniklé ve stejný čas (*Unverified:* duplikát?).
- **Zápis chybí (~15):** 12. 10. Strategická, 14. 10. Ceník, jedna generická 16. 10., 19. 10. Strategická, 19. 10. Huddle, 19. 10. Lucka & Lukáš, 20. 10. Navigátor portfolia, 22. 10. Alena Červenková, 22. 10. Dominik & Lukáš, 23. 10. Jan, 26. 10. Town hall, 27. 10. Lukáš–Mária, 27. 10. Domča, 29. 10. LukyLucka, 29. 10. Luboš. Postup: skill po dávkách, nejdřív citlivé 1:1.
- **Přeskočit (2):** 12. 10. `n8n-cutover-smoke` a `n8n-webhook-smoke` (`skip_reason: smoke`).
- Každý přesun jde přes preview a potvrzení Lukášem (pravidlo: úpravy souborů potvrzuje uživatel).

## Akceptační kritéria
1. `finalize_meeting(dry_run=true)` vrací cílové cesty a nic nezapíše.
2. Po ostrém volání je zápis ve `zapisy/YYYY-MM/`, přepis v archivu s `**ZPRACOVÁNO**` a v Inboxu už není; vše v jednom commitu.
3. Opakované volání je bezpečné; existující zápis se nepřepíše.
4. Chybný `expect_oid` vrací `oid_mismatch` + aktuální oid.
5. `skip_reason` archivuje bez vytvoření zápisu.
6. Zápis bez povinného frontmatteru je odmítnut s konkrétním důvodem.
7. `get_context` ukazuje `inbox_sembly_pending`; po úklidu backlogu = 0.
8. pytest: prázdný Inbox, kolize názvu, co-located příloha, atomický rollback při selhání druhé půlky, idempotence.

## Otevřené body
1. **Plaud a další zdroje:** *Unverified*, zda jdou do Inboxu stejnou cestou jako Sembly. `ingest_sembly` je pojmenovaný pro Sembly; zvážit obecný `ingest_transcript` s polem `source`, případně doplnit zdroje.
2. **Rozjetí kopií:** pozdější úpravy zápisu na Drivu se do vaultu nepropíšou. Návrh: vault = snapshot s `drive_copies`, Drive = sdílená verze. Potvrdit Lukášem.
3. **Obecnější varianta:** místo jednoho nástroje dva (`save_material` + `archive_inbox_item`) by pomohla i `Clippings/` a `daily/`. Rozhodnout při implementaci.

### Rozhodnutí z konverzace

- Rozsah tohoto kroku (volba uživatele `tool-only`): jen nástroj `finalize_meeting`, úprava osobního skillu, počítadlo v `get_context` a testy. Backlog 30 přepisů až potom, každý přes preview. Do implementace backlog nepatří.
- Firemní skill (volba uživatele `personal-only`): `rbedu-zapis-ze-schuzky` se nemění. Bod 5 briefu (hook Krok 10b) se neimplementuje.
- Firemní skill není v tomhle gitu ani v `~/.cursor/skills/`. Osobní `ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md` zůstává zdrojem obsahu a HTML pro Cursor. Neměnit ho na odkaz na skill, který tu nejde načíst. Mění se uzavření: po schválení preview vždy `finalize_meeting` (nejdřív dry-run), sdílení (Drive / Wiki / Slack) až potom a odmítnutí sdílení archivaci nezablokuje. 1:1 a citlivé default jen vault.
- Jeden atomický nástroj, ne `save_material` + `archive_inbox_item`.
- Vault je snapshot. `drive_copies` jsou jen URL. Pozdější úprava na Drive se do vaultu nepropisuje.
- Plaud: nový `ingest_transcript` se nezakládá. `finalize_meeting` smí vzít markdown z `01-INBOX/…`. Archiv podle podsložky inboxu (`sembly` nebo `daily`), stejná normalizace názvu jako `scripts/archive_inbox_item.py` / `inbox_archive_dest`.
- n8n workflow `ingest_sembly` se nemění.
- Tasky z tabulky zápisu zůstávají mimo commit `finalize_meeting` (stávající Brain `create_task`).
- Schvalování plánu uživatelem: ne (`/rbu-pipeline` bez „se schválením“).
- Re-read briefu 2026-11-02 01:52: obsah stejný, plán se kvůli tomu neměnil.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-11-02 01:54 | PLAN | — | — | — | Ledger založen. CLARIFY hotové z předchozího chatu. Start architekta k=1 r=1. |
| 2 | 2026-11-02 02:10 | PLAN | 753d61cf-727f-41e5-b779-208c8048ffc8 | plán k=1 r=1 | — | Plán zapsán do docs/plans/2026-11-02-finalize-meeting.md. Přechod CRITIC. |
| 3 | 2026-11-02 02:25 | CRITIC | 2aedb319-0ae4-4f07-b4f5-46f8ed579a8f | K PŘEPRACOVÁNÍ | C1 BLOCKER, C2–C4 MAJOR, C5 MINOR | Nálezy přečíslovány z NEW-n. Resume stejného architekta, r=2. |
| 4 | 2026-11-02 02:40 | PLAN | 753d61cf-727f-41e5-b779-208c8048ffc8 | plán k=1 r=2 | C1–C5 označeny vyřešeno | Čeká na nového kritika. |
| 5 | 2026-11-02 02:55 | CRITIC | 365d4629-aab3-42c0-99f7-3f257dc6d978 | K PŘEPRACOVÁNÍ | C3 MAJOR podruhé | C1 C2 C4 C5 vyřešeny. Resume architekta r=3 jen na C3. |
| 6 | 2026-11-02 03:10 | CRITIC | 47c585be-fd70-4573-8639-b74543f25e6c | SCHVÁLENO | 0 | C1–C5 vyřešeny. Schvalování plánu nevyžadováno. Přechod IMPLEMENT. |
| 7 | 2026-11-02 03:20 | REVIEW | 0bb9e22b-3fec-496b-9a1d-aa0ad847e0d8 | SCHVÁLENO | 0 | Review na 9be2e7a. |
| 8 | 2026-11-02 03:09 | IMPLEMENT | — | gate exit 0 | — | `pytest vps/second-brain-hub/tests` + finalize: 413 passed. |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| D1 | BLOCKER | IMPL | opraveno v 9be2e7a, čeká na review | 1 |
| D2 | MAJOR | IMPL | opraveno v 9be2e7a, čeká na review | 1 |
| D3 | MAJOR | IMPL | opraveno v 9be2e7a, čeká na review | 1 |
| D4 | MAJOR | IMPL | částečně: přidány archive/oid/cesta testy, T9/T12/T15/T16 pořád chybí | 1 |
| D5 | MAJOR | IMPL | opraveno v 9be2e7a, čeká na review | 1 |
| D6 | MINOR | IMPL | opraveno v 9be2e7a, čeká na review | 1 |
| C1 | BLOCKER | PLAN | vyřešen v #6 | 1 |
| C2 | MAJOR | PLAN | vyřešen v #6 | 1 |
| C3 | MAJOR | PLAN | vyřešen v #6 | 2 |
| C4 | MAJOR | PLAN | vyřešen v #6 | 1 |
| C5 | MINOR | PLAN | vyřešen v #6 | 1 |
