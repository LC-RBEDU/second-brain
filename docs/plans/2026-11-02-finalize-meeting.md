# Plán: finalize_meeting

Architekt: [753d61cf-727f-41e5-b779-208c8048ffc8](753d61cf-727f-41e5-b779-208c8048ffc8), otevření #1, generace k=1, kolo r=3.
Ledger: [2026-11-02-finalize-meeting.pipeline.md](2026-11-02-finalize-meeting.pipeline.md).

## Zadání a požadavky

R1 — Jeden atomický Brain nástroj `finalize_meeting`: za jedno volání buď uloží zápis a archivuje přepis, nebo přepis jen archivuje s důvodem. Jeden git commit. Zdroj: brief „Rozhraní“ + rozhodnutí „jeden atomický nástroj, ne `save_material` + `archive_inbox_item`“.

R2 — Parametry: `transcript_path` (povinné, `01-INBOX/…`), `expect_oid` (null, CAS, při neshodě `oid_mismatch` + aktuální oid), `zapis_md` (povinné, když není `skip_reason`), `meeting_date` (default z frontmatteru, složka `YYYY-MM/`), `slug` (default z titulku, `YYYY-MM-DD_<slug>_zapis.md`, kebab-case bez diakritiky), `drive_urls` (default `[]`, do frontmatteru `drive_copies`), `skip_reason` (`smoke` | `empty` | `duplicate` | `fragment` | `other` + `skip_note`), `dry_run` (default false, cílové cesty a diff, nic nezapíše). Zdroj: tabulka briefu.

R3 — Create-only zápis `05-RESOURCES/vystupy/zapisy/YYYY-MM/YYYY-MM-DD_<slug>_zapis.md`. Existující soubor s jiným obsahem se nepřepisuje; chyba nese jeho oid. Platí i když přepis v inboxu už není. Zdroj: brief „Chování“ bod 1 a akceptace 3.

R4 — Frontmatter zápisu musí mít `type: material`, `material_kind: schuzka`, `doc_type: meeting_summary`, `title`, `meeting_date`, `participants`, `variant`. Brain doplní `source_transcript` (cesta v archivu) a `drive_copies`. Chybějící pole = odmítnutí s konkrétním důvodem. Řez frontmatteru je první zavírací fence (`task_io.FRONTMATTER_RE`), `yaml.safe_load` jen nad tím řezem. Tělo včetně pozdějších `---` zůstane. `safe_load` nad celým `zapis_md` se nevolá. `parse_task_text` se nevolá, protože `YAMLError` polyká do prázdného dictu. Zdroj: brief bod 2, akceptace 6, nález C1.

R5 — Archivace stejnou normalizací cesty jako `scripts/archive_inbox_item.py` / `inbox_archive_dest`: `07-ARCHIV/inbox-processed/YYYY/MM/<podsložka>/`. Podsložka podle inboxu (`sembly` nebo `daily`). Do hlavičky `**ZPRACOVÁNO**` a odkaz na zápis, nebo `skip_reason`, a pod tím celé původní tělo přepisu. Co-located přílohy jedou s přepisem. Zdroj: brief bod 3 + rozhodnutí o Plaud bez nového `ingest_transcript`.

R6 — Idempotence: stejný obsah a už archivovaný přepis = OK bez změny. Nikdy stav „zápis ve vaultu a přepis pořád v Inboxu“ po úspěšném volání. Výjimka uprostřed session nesmí nechat půlku na disku. 404 jen když chybí inbox, archiv i cílový zápis. Inbox chybí a zápis má jiné bajty → 409 `zapis_exists` + oid. Archiv existuje a hlavička nesedí → 409 `archive_exists`. Zdroj: brief body 4–5, akceptace 2–3 a 8, nález C2.

R7 — HTML do vaultu nepatří. Tasky z tabulky zápisu nepatří do commitu (zůstává Brain `create_task`). Vault je snapshot; `drive_copies` jsou jen URL, pozdější úprava na Drive se do vaultu nepropisuje. Zdroj: brief bod 6 + rozhodnutí.

R8 — Výstup `{zapis_path, archive_path, zapis_oid, commit, warnings[]}`. `dry_run=true` nic nezapíše. `skip_reason` archivuje bez souboru zápisu a v archivu zůstane text přepisu. Zdroj: brief bod 7 a akceptace 1 a 5.

R9 — `inbox_sembly_pending` (počet) a `oldest_pending_age_days` jako živé čtení `01-INBOX/sembly`, ne z 15min snapshotu `agent-context*.json`. Pole vrací plný `get_context` i `get_context_light` (ranní brief čte light). Zdroj: brief „Související malá změna“ + omezení v tomto briefu.

R10 — Osobní skill `ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md` zůstává zdrojem obsahu a HTML. Po schválení preview vždy `finalize_meeting` (nejdřív `dry_run`), sdílení (Drive / Slack, a Wiki pokud už v tom kroku je) až potom. Odmítnutí sdílení archivaci nezablokuje. 1:1 a citlivé (P&C, jednání s CEO, klient pod NDA) default jen vault, bez otázky na týmový disk; Drive/Slack jen na výslovný pokyn. 1:1 se pozná z názvu nebo kalendáře (`1:1`, „Lukáš–…“) nebo z výslovného pokynu, ne z počtu účastníků. Pojmenovaná týmová schůzka se dvěma lidmi jde dál do Kroku 9. Třídění před zápisem: zápis, nebo přeskočit (`skip_reason`). Generické názvy („Meeting Friday…“, „Google Meet …“) brát z kalendáře. Zdroj: rozhodnutí z konverzace, které má přednost před bodem 1 a 5 briefu.

R11 — pytest: prázdný / chybějící přepis, kolize názvu, co-located příloha, atomický rollback druhé půlky, idempotence, špatný `expect_oid`, špatný frontmatter, fence `---` v těle zápisu, `skip_reason` i s tělem přepisu v archivu, počítadlo. Ostrý zápis do produkčního vaultu není test. Zdroj: akceptace 8 + nasazení v bloku Projekt.

R12 — `related_tasks` na zápisu se po `create_task` nedoplňuje a zůstává, jak přišlo ve `zapis_md` (prakticky `[]`). Stub v `02-PROJEKTY/<slug>/materials/` se nezakládá. Druhý commit na soubor zápisu není. Odkaz žije na tasku: `create_task` ve svém jednom commitu zapíše neprázdné `materials` (wikilink na `…_zapis`). Samonosný text jde do existujícího `detail`. Tělo zůstává tenká šablona (`**Z:** brain-api`, `**Detail:** …`). **Cíl:**, **Kontext ze zápisu:** a checkbox `**ID-N**` se nezakládají. Zdroj: rozhodnutí k C3, kolo 3.

Mimo rozsah: zpracování 30 přepisů v `01-INBOX/sembly/`; úprava `rbedu-zapis-ze-schuzky` a hook Krok 10b; nový `ingest_transcript`; změna n8n `ingest_sembly`; Slack capture v pracovním stromu; `save_material`; přepis existujícího zápisu; zápis tasků a HTML uvnitř commitu `finalize_meeting`; materials stub i mimo ten commit; druhý commit, který by do zápisu dopsal `related_tasks`.

Schvalování plánu uživatelem: ne.

## Předpoklady

A1 — Inbox pro tento nástroj je jen plochý soubor `01-INBOX/sembly/<soubor>.md` nebo `01-INBOX/daily/<soubor>.md`. Jiná podsložka, vnořená cesta, `..` a `.keys` jsou 400. Plaud v `daily/` tím projde. Nový ingest se nezakládá.

A2 — `meeting_date` ve frontmatteru je povinné (`YYYY-MM-DD`). Parametr, když přijde, se musí rovnat frontmatteru, jinak 400 `meeting_date_mismatch`. Složka `zapisy/YYYY-MM/` i název souboru berou tohle datum. Archivní `YYYY/MM/` dál bere datum z **názvu přepisu** (`inbox_archive_dest`), ne z `meeting_date`. Když se měsíce liší, volání projde a ve `warnings` je `archive_month_differs`.

A3 — Slug z parametru musí matchovat `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Default je NFKD titulku, bez diakritiky, lower, ostatní znaky na `-`, max 60 znaků. Kolize jména zápisu se neřeší sufixem `-2` (to dělá jen `ingest_sembly`).

A4 — `skip_note` je povinné právě při `skip_reason=other`. U ostatních důvodů je volitelné. `zapis_md` a `skip_reason` zároveň = 400. Ani jedno = 400.

A5 — `drive_urls`: po stripu jen `http://` a `https://`, max 20. Prázdné položky se zahodí. Brain jimi přepíše `drive_copies`. `drive_folder` ve `zapis_md` nástroj nepožaduje a nemaže (u 1:1 chybí).

A6 — `participants` je povinné a neprázdné (neprázdný string, nebo list s aspoň jednou neprázdnou položkou). `variant` je neprázdný string, bez enumerace `full`/`shared`.

A7 — Opakované volání se stejným `zapis_md` / stejným skip markem a přepisem už v archivu vrací OK, `commit: null`, i když `expect_oid` patří starému inbox oid (ten soubor už není). `oid_mismatch` jen když inbox soubor **existuje** a oid nesedí. Když zápis už existuje a bajty se rovnají tomu, co by nástroj zapsal, a přepis je pořád v inboxu, nástroj zápis nepřepisuje a ve stejném commitu jen archivuje (dokončení, ne overwrite).

A8 — Počítadlo = počet `*.md` přímo v `01-INBOX/sembly/` (ne rekurze, ne `.keys`). `oldest_pending_age_days` = max(0, nejvyšší stáří ve dnech) proti dnešku v `Europe/Prague` (`TZ` jako `capture_daily`). Datum z prefixu `YYYY-MM-DD` v názvu, jinak `modified_time`. Count 0 → věk `null`. Věk ≥ 1 je „starší než 24 h“. Dnešní přepis v počtu je a věk má 0. Chybějící složka = 0 / null. Jiná chyba `list_dir` shodí context (žádná tichá nula).

A9 — Ranní brief číslo opravdu ukáže až když ho `agenda-co-ted` vypíše. Jedna řádka v tom skillu je součást R9. Bez ní light JSON pole má, dashboard ne.

A10 — 1:1 pro skill je jen název nebo předmět kalendáře: token `1:1`, nebo en-dash / em-dash ve tvaru „Lukáš–…“. Stejný účinek má výslovný pokyn v tom tahu. K tomu citlivé třídy z R10. Počet účastníků sám 1:1 nedělá. Pojmenovaná týmová schůzka se dvěma lidmi jde do Kroku 9. Nástroj citlivost ani 1:1 nerozpoznává.

A11 — Sdílení po finalize u tohoto skillu zůstává dnešní Krok 9 (Drive MD + Slack HTML). Wiki se nepřidává. `drive_copies` u nové schůzky jsou v commitu prázdné, protože upload je až po finalize. Složka, kterou agent zná předem, zůstává ve `zapis_md` jako `drive_folder`, ne v `drive_copies`.

A12 — Dnes to tak nejde. `create_task` parametr `materials` nemá (`create_task.py:176-191`), `_render_task` ho natvrdo dává `[]` (`:74`) a každý list vypíše jako `k: []` (`:91-93`). MCP (`mcp_app.py:337-349`) ani REST (`main.py:367-393`) pole nemají. Bez úpravy rendereru by task po finalize wikilink neměl a skill podle tabulky Samonosný kontext by sáhl na zápis a dostal 409 `zapis_exists`. Proto se mění `create_task`, ne soubor zápisu. `create_task` a každá položka v `items` dostanou `materials: list[str] | None = None`. Prázdné nebo vynechané = `[]`. Neprázdný seznam: 1–20 položek, každá neprázdný string, jinak 400 `bad_materials`. Neprázdný list se zapíše jako YAML seznam, položky v uvozovkách. `**Z:**` a `**Detail:**` se nemění. REST `CreateTaskBody.materials`, MCP `materials_json`.

A13 — Commit message: `brain: finalize_meeting <archive_rel>`. Session dál commituje jen když je diff (`commit_if_dirty`).

A14 — Co-located příloha se bere stejným pravidlem jako `list_colocated_attachments` (slack prefix `YYYY-MM-DD-HHMM-` nebo e-mailový prefix `__`). Nepárový soubor ve složce se nehýbe. Příloha musí být už v gitu (tracked). Untracked příloha = 400, nic se nezapíše. Sembly přepis sám přílohu obvykle nemá; test ji commitne do fixture.

A15 — Žádný produkční vault write. Deploy Brain image je podmínka, aby MCP/REST nástroj viděly; skill je symlink a do image nepatří.

A16 — Shoda archivu, když inbox soubor už není, se pozná podle hlavičky, kterou by tohle volání zapsalo. Tělo pod hlavičkou se při replayi znovu neskládá. Jiná hlavička = `archive_exists`. Bajty zápisu se srovnávají s obohaceným `zapis_md` vždy, když tohle volání zápis má.

## Současný stav (ověřeno v kódu)

`vps/second-brain-brain/app/tools/ingest_sembly.py:39-75` — mutate přes `brain_vault(mode="mutate")`. Idempotence je soubor `01-INBOX/sembly/.keys/<key>.path`, ne obsah zápisu. Kolize jména řeší sufixem. Do archivu ani do `zapisy/` nepíše.

`vps/second-brain-brain/app/main.py:439-445` — `POST /v1/ingest_sembly`, `AuthPrincipal`. `GET /v1/context` (`143-144`) a `GET /v1/context/light` (`147-166`, jen human OAuth, service/dev → 403).

`vps/second-brain-brain/app/mcp_app.py:67-69` — MCP má plný `get_context`, light endpoint v MCP není (`docs/plans/2026-10-10-sb-operacni-model-f4.md` to tak nechává). `ingest_sembly` je `421-423` a chyby jdou přes `_call`. `update_task` (`108-120`) a `bulk_update` (`381-393`) vrací `oid_mismatch` jako `CallToolResult(is_error=True)`, protože `_call` (`45-53`) schová `BrainClientError` do `RuntimeError` a klient vidí jen „Error executing tool“.

`vps/second-brain-brain/app/tools/get_context.py:39-67` a `get_context_light.py:41-53` — čtou `00-System/agent-context.json` / `agent-context-light.json`. Freshness 15 min je `app/context_freshness.py`. Builder `vps/second-brain-hub/lib/agent_context_build.py:328` a zápis light `620-622` inbox sembly nepočítá. Pole přilepené do JSON by do dalšího rebuildu zestárlo.

`vps/second-brain-brain/app/vault_deps.py:84-98` a `119-131` — read: bez fetch, bez commitu, bez discard. Mutate/rebuild: fetch, dirty check, commit, discard při výjimce. Jeden `with` = jeden commit.

`vps/second-brain-hub/lib/git_io.py:229-249` — při výjimce `git reset --hard HEAD`. `commit_if_dirty` (`715-723`) commituje jen při staged diffu, message default `hub: vault update <ts>`. `write_text` (`573-588`) soubor jen zapíše, `git add` je až v commitu. Nový soubor je tedy untracked. `reset --hard` untracked **nesmaže**. `_is_dirty` (`348-350`) je `git status --porcelain`, takže `??` další mutate session shodí jako `vault_dirty_start` (`200-227`). `move` (`663-688`) selže, když cíl existuje; na rozdíl od `archive_inbox_capture` cíl nemaže.

`vps/second-brain-hub/lib/inbox_archive.py:74-102` — `inbox_archive_dest`: druhý segment cesty je kind (`sembly`, `daily`, …), rok/měsíc z prefixu názvu `YYYY-MM-`. Bez prefixu `ValueError`. `list_colocated_attachments` (`105-124`) bere jen ne-md sousedy s e-mailovým nebo slack timestamp prefixem. `mark_processed` (`127-135`) vlepí `**ZPRACOVÁNO**` do H1 a odkaz na zápis nemá. `archive_inbox_capture` (`145-178`) při existujícím cíli soubor smaže (`_move_file`, `140-141`) a pak přepisuje. To finalize nesmí volat.

`scripts/archive_inbox_item.py:49-56` — CLI obal nad `archive_inbox_capture`. Skill ho dnes volá.

`vps/second-brain-brain/app/tools/update_task.py:111-122` — `dry_run` je `mode="read"`; `expect_oid` se kontroluje i v dry-run a vrací 409 s `oid`. `BrainClientError.as_dict` (`errors.py:84-90`) oid přidá, když je na výjimce.

`vps/second-brain-hub/lib/task_io.py:26` — `FRONTMATTER_RE` je non-greedy první zavírací fence; group 2 je zbytek souboru včetně pozdějších `---`. `parse_task_text` (`59-72`) při `YAMLError` vrátí prázdný frontmatter, na validaci zápisu se nepoužije. Vault zápis `2026-10-06_finance-sync_zapis.md` má další `---` v těle (řádek 89 a dál). `yaml.safe_load` nad celým souborem by spadl na druhý dokument.

`vps/second-brain-brain/app/tools/capture_daily.py:27-28` — dnešek `ZoneInfo(TZ or Europe/Prague)`.

`vps/second-brain-brain/app/sembly_template.py:125-128` — inbox název `YYYY-MM-DD-HHMM-<title>.md`. Prefix pro `inbox_archive_dest` i pro slack-style přílohu sedí. `_slug_title` (`10-15`) diakritiku nechává; slug zápisu musí být přísnější.

`ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md:3-8` a `25-34` — skill sám píše MD do `05-RESOURCES/vystupy/zapisy/` a v Kroku 8 bod 7 (`353`) archivuje `scripts/archive_inbox_item.py`. Krok 9 (`388-406`) je Drive + Slack až po souborech na disku. `drive_folder` je v šabloně povinné (`274`). F1 banner (`11`) zakazuje FS zápis do klonu. Firemní `rbedu-zapis-ze-schuzky` v tomto gitu ani jako cíl symlinku není; skill se na něj neodkazuje a odkazovat nesmí.

`vps/second-brain-brain/Dockerfile:14-15` — do image jde `second-brain-hub/lib/` jako `/app/lib/` a `app/`. Nový modul v `app/tools/` a úprava `inbox_archive.py` / `git_io.py` se nasadí tímhle COPY, Dockerfile se nemění.

`vps/second-brain-brain/tests/test_ingest_sembly_collision.py:15-41` — fake vault + patch `brain_vault`. `tests/test_bulk_oid.py:110-153` — reálný `GitVault` a rollback **tracked** souboru. Nový untracked soubor ten test nehlídá.

`docs/agent_playbooks/quality-checklists.md` v repu není.

## Návrh

### Hub lib (sdílená cesta archivu a discard)

`vps/second-brain-hub/lib/inbox_archive.py` — vyjmout čistou funkci `inbox_archive_rel(rel: str) -> str` z date-prefix větve `inbox_archive_dest` (řádky 74–102). Vrací `07-ARCHIV/inbox-processed/{year}/{month}/{kind}/{name}` s posix lomítky. `inbox_archive_dest` ji použije a jen připojí `vault /`. Větev `sb-personal` / `sb-workspace` zůstane v `inbox_archive_dest` (čte soubor). `finalize_meeting` volá jen `inbox_archive_rel`. Bez prefixu dál `ValueError` → nástroj 400 `inbox_date_unparsed`.

Tamtéž `attachment_belongs(md_name, other_name) -> bool` se stejnými pravidly jako `list_colocated_attachments` (`115-123`). Stávající funkce ji použije, chování testů `vps/second-brain-hub/tests/test_inbox_archive.py` se nemění. `mark_processed` a `archive_inbox_capture` (včetně mazání existujícího cíle) se nemění. Skript `scripts/archive_inbox_item.py` se nemění. Skill ho přestane volat.

`vps/second-brain-hub/lib/git_io.py` `end_session` (`229-249`) — v větvi `discard_dirty_on_error` po `reset --hard` přidat `git clean -fd` (bez `-x`). Session na začátku vyžaduje prázdný porcelain a drží flock, takže untracked v tu chvíli vznikly v této session. `commit_if_dirty` (`715-723`): když `message` je None, vzít `getattr(self, "commit_message", None)`, jinak dnešní `hub: vault update …`. Prázdný atribut nechat propadnout na default.

`GitVault.is_tracked(rel) -> bool` přes `git ls-files --error-unmatch -- <rel>`. Nástroj ho použije na přepis a na každou přílohu před zápisem.

### Brain nástroj

Nový `vps/second-brain-brain/app/tools/finalize_meeting.py`.

`finalize_meeting(*, transcript_path, expect_oid=None, zapis_md=None, meeting_date=None, slug=None, drive_urls=None, skip_reason=None, skip_note=None, dry_run=False, env=None) -> dict`.

Čistá validace bez vaultu (A4, A5, tvar cesty A1). Pak jedna session: `dry_run` → `brain_vault(mode="read")` jako `update_task` (`111`); ostré volání → `mode="mutate"`. Žádný předběžný read short-circuit (read nefetchuje, `vault_deps.py:86-91`, a mohl by prohlásit idempotenci ze starého klonu).

Řez `zapis_md` (R4): `FRONTMATTER_RE` z `task_io`. `safe_load` jen group 1. Group 2 je tělo a do dumpu jde beze změny, včetně každého pozdějšího `---`. Žádný match → 400 `bad_frontmatter`. `YAMLError` nebo výsledek není `dict` → 400 `bad_frontmatter`. Po validaci polí se zapíše `source_transcript` a `drive_copies`. `related_tasks`, když v řezu je, zůstane. Složený soubor je fence + `yaml.safe_dump(sort_keys=False, allow_unicode=True)` + fence + group 2.

Uvnitř session funkce `decide(vault)`:

1. Normalizovat cestu. `inbox_archive_rel`. Kind jen `sembly`|`daily`.
2. Když volání má `zapis_md`, složit cílovou cestu a obohacené bajty řezem výše. To jde i bez souboru v inboxu.
3. Načíst přepis. Když soubor je: `is_tracked`, jinak 400 `transcript_untracked`. `expect_oid` proti `meta.oid`; neshoda → 409 `oid_mismatch` + aktuální oid. Přílohy přes `attachment_belongs`; untracked → 400; cíl existuje → 409 `attachment_exists` dřív než zápis.
4. Když inbox soubor je a cílový zápis má jiné bajty → 409 `zapis_exists` + oid. Když bajty sedí → zápis se nezapisuje znovu. Když archiv existuje a hlavička plus původní tělo nesedí → 409 `archive_exists`. Existující archiv se nemaže.
5. Když inbox soubor není, v tomhle pořadí a bez zápisu, dokud není idempotentní shoda: (1) zápis existuje a bajty se liší → 409 `zapis_exists` + oid; (2) archiv existuje a hlavička nesedí → 409 `archive_exists`; (3) zápis i hlavička archivu sedí, nebo je to skip a hlavička sedí → OK `idempotent`, `commit: null`; (4) sedí jen jedna půlka → 409 `inconsistent_state`; (5) není inbox, archiv ani zápis → 404 `transcript_not_found`.

Hlavička archivu (nová, `mark_processed` se nevolá, protože neumí odkaz):

```text
**ZPRACOVÁNO**
Zápis: 05-RESOURCES/vystupy/zapisy/YYYY-MM/YYYY-MM-DD_<slug>_zapis.md

<původní tělo>
```

Skip:

```text
**ZPRACOVÁNO**
skip_reason: smoke
skip_note: …

<původní tělo přepisu>
```

`skip_note` řádek jen když note je. Pod hlavičkou je vždy celé původní tělo. Při replayi bez inboxu stačí shoda hlavičky (A16). Když hlavička nesedí, 409 `archive_exists`, ne tichá oprava.

Zápis, který by `decide` udělal, a který už na disku je bajtově stejný, zatímco přepis v inboxu pořád je: `apply` zapíše jen archiv (A7). Tím úspěšné volání neskončí s zápisem ve vaultu a přepisem v inboxu.

`apply` po `decide` bez chyby, jen když ne `dry_run` a ne čistá idempotence: `write_text` zápisu (jen když se má vytvořit), `write_text` archivu, `delete` inbox md, `move` příloh. Žádné `unlink` existujícího cíle. Před opuštěním `with` nastavit `vault.commit_message`. Po `with` `head_sha()`; když se SHA nezměnil, `commit: null`.

Idempotence bez inboxu je krok 5 výše: 409 `zapis_exists` / `archive_exists` / `inconsistent_state`, nebo OK, nebo 404 jen když chybí inbox, archiv i zápis.

`dry_run` vrací stejný objekt plus `dry_run: true`, `would_write`, `idempotent`, `transcript_oid`, a nic nevolá `write_text`/`delete`/`move`. Kolize a špatný oid jsou stejné 409 jako ostré volání.

Úspěšný objekt vždy obsahuje klíče z R8. U skip je `zapis_path` i `zapis_oid` null. `warnings` je `list[str]`. Navíc `idempotent`, `dry_run`, `transcript_oid`, `attachment_paths` (agent je potřebuje, briefí klíče zůstávají).

### REST a MCP

`vps/second-brain-brain/app/main.py` — `FinalizeMeetingBody` a `POST /v1/finalize_meeting` hned za `rest_ingest_sembly` (`443-445`). Stejný `AuthPrincipal`. Žádná nová auth politika. `BrainClientError` handler (`132-134`) už vrací `as_dict()` včetně oid.

`vps/second-brain-brain/app/mcp_app.py` — tool `finalize_meeting`. `drive_urls_json` jako JSON list (stejný styl jako `patch_json`). Každý `BrainClientError` vracet jako `CallToolResult(is_error=True, structured_content=as_dict())`, ne přes `_call`. Jinak agent neuvidí `missing_fields` ani oid. `BrainVaultError` nechat na `_call` jako ostatní vault chyby (503). Jedna věta do `instructions` (`59-64`): uzavření přepisu je `finalize_meeting`, ne `archive_inbox_item`.

`docs/brain-api-runbook.md:164` — do výčtu routes přidat `POST /v1/finalize_meeting`.

### Počítadlo

Nový `vps/second-brain-brain/app/tools/sembly_pending.py`: `sembly_pending_stats(vault, *, today) -> dict` podle A8. `list_dir(..., pattern="*.md", recursive=False)` (`git_io.py:506-542`, oid se nepočítá). `DriveNotFoundError` → 0 / null.

`get_context.py` — těsně před return ve warm větvi (`53`) i v rebuild větvi (`67`) přilepit obě pole na **vracený** dict `context`. Žádný `write_json` snapshotu. Rebuild session je pořád jedna; `list_dir` je navíc v ní.

`get_context_light.py` — stejně před return (`53`), pořád v tom read `with`. Stale light dál 503 dřív, než se počítadlo čte.

`ŠABLONY/skills/agenda-co-ted/SKILL.md` — v šabloně dashboardu (`72-103`) jedna řádka, když `inbox_sembly_pending` > 0: `Sembly inbox: N přepisů (nejstarší X dní)`. Když `oldest_pending_age_days` ≥ 1, doplnit „starší než 24 h“. Zdroj pole: `context` z light, na fail-path z plného `get_context`. Chybějící pole (starý Brain) = řádek vynechat.

### Skill zápisu

Jen `ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md`. Kroky 2–5, GN-1/GN-2, HTML standard, `build_html.py`, Downloads a Krok 1 (kalendář) zůstanou. Žádný odkaz na `rbedu-zapis-ze-schuzky`. Žádný Krok 10b.

- Description (`3-8`): MD do vaultu jde Brain `finalize_meeting`, ne zápisem do klonu.
- „Co skill dělá“ bod 4 a 7: jeden `finalize_meeting` uklidí přepis; `archive_inbox_item.py` se nevolá.
- Krok 6 „MD → vault“: po GN-2 složit `zapis_md` v `/tmp`, HTML pořád do `~/Downloads/`. Pak `finalize_meeting(dry_run=true)` a po něm ostré volání s `expect_oid=transcript_oid` z dry-runu. `source_transcript` a `drive_copies` do markdownu agent nepíše (doplní Brain). `drive_folder` jen když se bude sdílet; u 1:1 a citlivých chybí a není chyba.
- Nový blok „Uzavření přepisu“ hned za Preview: nejdřív třídění zápis vs skip (smoke, empty, duplicate, fragment, other + note). Generický název → název a slug z kalendáře (Krok 1); bez události se zeptat, nevymýšlet. Skip taky až po krátkém ano s důvodem. Po ano na preview: dry-run, pak ostré volání. Teprve potom tasky a nabídka sdílení.
- 1:1 a citlivé (A10): otázku na disk/Slack přeskočit, `drive_urls=[]`. Dva účastníci na pojmenované týmové schůzce otázku nepřeskakují. Sdílet jen když to Lukáš v tom tahu výslovně řekne.
- Krok 8: `create_task` až po úspěšném finalize, `materials:` = wikilink zápisu. Soubor zápisu se znovu neotevírá, `related_tasks` se nedoplňuje, stub v `materials/` se nezakládá (R12). Bod se skriptem archivu pryč.
- Krok 9 až po OK z finalize. „Neposílej“ / odmítnutý disk končí tím, že přepis už v inboxu není. Známý kanál a folder pořád posílají samy, jakmile finalize prošel a nejde o 1:1/citlivé.
- Preview: cílové cesty z dry-runu, řádek „jen vault“ vs „po finalize nabídnu Drive/Slack“, a skip vs zápis.
- Checklist: archiv = `finalize_meeting`; `drive_folder` není univerzálně povinný; odmítnuté sdílení není důvod vracet přepis do inboxu; stub se nezakládá; `related_tasks` se po založení tasku nemění.

`bash scripts/install_agenda_skills.sh` nespouštět, symlink na `ŠABLONY/skills/` už je zdroj.

### RBAC, Alembic, Celery, MCP RB Universe, subnav, qa_gate, Playwright

Netýká se. Auth je dnešní `AuthPrincipal` / MCP session. Tester: bez UI, `rbu-tester` se nevolá.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | `dry_run=true`, platný přepis v `01-INBOX/sembly/` nebo `daily/`, platný `zapis_md` | 200, `zapis_path` + `archive_path` + `transcript_oid`, `commit` null, `would_write` true. Žádný `write_text`/`delete`/`move`. Session `mode=read` | R2, R8 | T1 |
| B2 | Ostré volání, inbox md tracked, zápis ani archiv nejsou | Jeden mutate `with`. Zápis v `zapisy/YYYY-MM/`, archiv s hlavičkou `**ZPRACOVÁNO**` + `Zápis: <path>`, inbox md pryč, přílohy v téže archivní složce. `commit` = nový HEAD, message `brain: finalize_meeting …`. Pracovní strom čistý | R1, R5, R6, R8 | T2, T8 |
| B3 | Druhé volání se stejným `zapis_md`, přepis už v archivu, zápis stejné bajty | OK, `idempotent` true, `commit` null, žádný write. I s původním inbox `expect_oid` | R6, A7 | T3 |
| B4 | Inbox soubor existuje, `expect_oid` jiné než blob oid | 409 `oid_mismatch`, `oid` aktuální. REST `as_dict`. MCP `CallToolResult` `is_error` a `structured_content.oid`. Nic nezapsáno. Platí i pro dry-run | R2 | T4 |
| B5 | `skip_reason=smoke` (a `other` bez note) | Archiv s `skip_reason` v hlavičce, žádný soubor v `zapisy/`. `other` bez `skip_note` = 400 `skip_note_required`. Obojí `zapis_md` i skip = 400. Ani jedno = 400 | R2, R8 | T5 |
| B6 | `zapis_md` bez úvodní fence, `YAMLError` v prvním řezu, nebo chybí pole R4 | 400 `bad_frontmatter` nebo `missing_fields`. `safe_load` neběží nad celým souborem | R4 | T6 |
| B6b | `zapis_md` ve tvaru Finance Sync: první fence zavře frontmatter, v těle jsou další `---` | 200. Po dumpu tělo pořád obsahuje ty fence | R4 | T6 |
| B7 | Cílový `…_zapis.md` existuje a bajty se liší | 409 `zapis_exists` + oid toho souboru. Inbox na místě. Bez sufixu `-2` | R3 | T7 |
| B8 | Zápis už existuje a bajty se rovnají, přepis pořád v inboxu, archiv není | Zápis se nezapisuje znovu. Ve stejném commitu se archivuje přepis. Po návratu inbox prázdný pro ten soubor | R3, R6, A7 | T3 |
| B9 | Vedle `2026-10-13-1000-sync.md` leží tracked `2026-10-13-1000-notes.pdf` | PDF skončí ve stejné archivní složce. Cizí soubor s jiným timestampem zůstane. Untracked PDF = 400 `attachment_untracked`, strom beze změny | R5, A14 | T8 |
| B10 | Druhý zápis v `apply` vyhodí (archiv), zápis už byl `write_text` jako nový soubor | Výjimka ven. `reset --hard` + `git clean -fd`. Nový zápis na disku není, inbox md je zpátky, porcelain prázdný, HEAD stejný | R6 | T9 |
| B11 | `transcript_path` mimo sembly/daily, s `..`, nebo bez date prefixu | 400 `bad_transcript_path` / `bad_inbox_kind` / `inbox_date_unparsed` | A1, R5 | T10 |
| B12 | Není inbox, není archiv a není cílový zápis | 404 `transcript_not_found`. Žádný nový soubor | R6 | T10 |
| B13 | `01-INBOX/daily/YYYY-MM-DD-….md` | Archiv pod `…/inbox-processed/YYYY/MM/daily/`, ne `sembly/` | R5, A1 | T11 |
| B14 | `get_context` warm, rebuild return, a `get_context_light` | Oba objekty `context` mají živý počet a věk z `list_dir`, i když JSON na disku pole nemá. Po „úklidu“ (ve fixture prázdná složka) počet 0 a věk null. Soubor v `.keys` se nepočítá. Složka chybí = 0 / null | R9 | T12 |
| B15 | Light trio je stale | 503 `context_light_stale` jako dnes, počítadlo se nečte | R9 | T12 |
| B16 | `meeting_date` parametr ≠ frontmatter | 400 `meeting_date_mismatch` | A2 | T6 |
| B17 | Měsíc v názvu přepisu ≠ měsíc `meeting_date` | Zápis ve složce podle `meeting_date`, archiv podle názvu, warning `archive_month_differs` | A2 | T2 |
| B18 | URL mimo http(s), nebo víc než 20 | 400 `bad_drive_url`. Platné URL jsou přesně `drive_copies` ve uloženém frontmatteru | A5, R7 | T2 |
| B19 | Archivní cíl existuje s jiným obsahem, nebo příloha v cíli už je | 409 `archive_exists` / `attachment_exists` před prvním zápisem. Existující archiv se nemaže | R3, R6 | T7 |
| B20 | Skill po ano | Nejdřív dry-run, pak ostré `finalize_meeting`, pak `create_task` s `materials` = wikilink zápisu a `detail` = samonosný odstavec, pak Krok 9. Skill neříká doplnit `related_tasks`, nezakládá stub a nechce **Cíl:** / **Kontext ze zápisu:** / `**ID-N**`. 1:1 jen podle A10. `archive_inbox_item.py` v skillu není | R7, R10, R12 | T13 |
| B24 | `create_task` s `materials=["[[…_zapis]]"]` | Ve stejném commitu je frontmatter se quoted wikilinkem, ne `materials: []`. Tělo má `**Detail:**` a nemá `**Cíl:**`. Bez `materials` zůstane `materials: []`. Ne-seznam nebo prázdná položka = 400 `bad_materials`. REST i MCP pole přijmou | R12 | T16 |
| B21 | Inbox soubor není, cílový zápis existuje a bajty se liší | 409 `zapis_exists` + oid. Žádný write | R3 | T3, T7 |
| B22 | Inbox soubor není, archiv existuje a hlavička k tomuto volání nesedí | 409 `archive_exists`. Žádný write | R3, R6 | T7 |
| B23 | Inbox soubor není a sedí jen jedna půlka u volání, které zápis má | 409 `inconsistent_state`. 404 to není | R6 | T7 |

Nerelevantní body checklistu A (soubor `quality-checklists.md` v repu není; obecný průchod):

- Alembic, SQL, RBAC sekce, subnav, hub dlaždice — netýká se, Brain nemá tyhle vrstvy.
- Celery, Allfred, Pipedrive, Fakturoid, Fio, MCP `user-rb-universe` — netýká se.
- Cron, který čte celý vault — netýká se, nástroj ani počítadlo nejsou cron. Počítadlo je jeden `list_dir` ve už otevřené context session.
- Playwright, `qa_gate.mjs`, `rbu-tester` — netýká se, bez UI.
- n8n ingest, `ingest_sembly`, firemní skill, hook 10b, backlog 30 souborů — mimo rozsah, kód se nemění.
- CAS na zápis při create — netýká se, soubor nesmí před během existovat; CAS je na přepisu (`expect_oid`). Existující zápis je `zapis_exists`, ne tichý overwrite.
- Prázdný commit — `commit_if_dirty` při idempotenci nic necommituje (B3).

## Výkonový rozpočet (P)

Nástroj není cron a nečte celý vault. Checklist B z playbooku v repu není; u obou cest stačí strop níž.

`POST /v1/finalize_meeting` a MCP ekvivalent:

1. Cold i warm: jeden `brain_vault` (read pro dry-run, mutate pro ostré). Mutate k tomu má dnešní fetch + případný push, stejně jako `ingest_sembly`. Žádný druhý commit a žádný rebuild `agent-context`.
2. SQL: 0.
3. Čtení: 1× přepis, 1× `list_dir` jeho složky (ne rekurze, oid se nepočítá), 1× existence/čtení cíle zápisu a cíle archivu. Přílohy se jako text nečtou.
4. Zápis: nejvýš jeden nový md zápisu, jeden archivní md, delete zdroje, move N příloh. N je počet sousedů se stejným prefixem, v praxi 0.
5. Payload odpovědi: cesty, oid, sha, krátké `warnings`. Tělo zápisu se nevrací.
6. Cache: žádná. Invalidace context snapshotu se nedělá; počítadlo se lepí při čtení.
7. Cíl: práce navíc proti `ingest_sembly` je parse YAML + pár existencí v jedné složce. Strop ať drží dnešní mutate session (fetch + commit + ff-only push), ne sken vaultu.
8. Idempotentní replay: stejná session, 0 write, `commit_if_dirty` skončí bez commitu a bez push.

`GET /v1/context`, `GET /v1/context/light`, MCP `get_context`:

1. K existujícímu read/rebuild se přidá jeden nerekurzivní `list_dir` `01-INBOX/sembly` s `compute_oid=False` (`git_io.py:538`). Žádné `read_text` po souborech, když název má `YYYY-MM-DD`.
2. Do `agent-context.json` ani light JSON se pole nezapisuje, TTL 15 min ho tedy nezmrazí.
3. Chybějící složka je 0, ne výjimka a ne druhý otevřený vault.
4. Strop: desítky až nízké stovky md v jedné složce. Dnešní backlog je 30 souborů. Celý `02-PROJEKTY/` se kvůli tomu neprochází.

## Testy (T#)

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T1 | pytest, fake vault jako `test_ingest_sembly_collision.py` | gate | `vps/second-brain-brain/tests/test_finalize_meeting.py` | B1 dry-run 0 write, cesty, `transcript_oid` |
| T2 | pytest, fake vault | gate | stejný | B2, B17, B18: hlavička, `drive_copies`, měsíční warning, jeden `brain_vault(mode="mutate")` |
| T3 | pytest, fake vault | gate | stejný | B3 a B8: replay 0 write; stejné bajty zápisu jen archivují |
| T4 | pytest + MCP `build_mcp` jako `test_bulk_oid.py:156` | gate | stejný | B4 REST důvod + MCP `CallToolResult.structured_content.oid` |
| T5 | pytest | gate | stejný | B5: skip archiv obsahuje konkrétní větu z přepisu pod hlavičkou; `skip_note`; obojí/nic |
| T6 | pytest | gate | stejný | B6, B6b, B16. Fixture s `---` v těle (Finance Sync). Assert, že fence v uloženém těle zůstanou. Chybějící úvodní fence = 400 |
| T7 | pytest | gate | stejný | B7, B19 kolize zápisu a archivu, inbox netknutý, archivní soubor se nesmazal |
| T8 | pytest, fake `list_dir` | gate | stejný | B9 příloha se stejným prefixem se přesune, cizí ne; untracked = 400 |
| T9 | pytest, reálný git jako `test_bulk_oid.py:110` a bare origin jako `test_export_tasks.py:306` | gate | stejný | B10: druhý write vyhodí, nový untracked zápis po `clean -fd` není, tracked inbox je zpátky, porcelain prázdný, HEAD beze změny. Druhý test: šťastná cesta commitne message `brain: finalize_meeting` a push na lokální bare |
| T10 | pytest | gate | stejný | B11, B12 špatná cesta a chybějící přepis |
| T11 | pytest | gate | stejný | B13 `daily/` → kind `daily` |
| T12 | pytest, fake vault | gate | `vps/second-brain-brain/tests/test_sembly_pending.py` | B14, B15: overlay na warm `get_context`, na return z rebuildu, na light; JSON fixture pole nemá; `.keys` a chybějící složka; stale light pořád 503 |
| T13 | ruční čtení diffu skillu, ne vault write | gate | `ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md`, `agenda-co-ted/SKILL.md` | B20: `materials` jde do `create_task`; tabulka Samonosný kontext nemá `related_tasks` ani stub; **Cíl:** / checkbox jsou nahrazené `detail`; 1:1 jen podle A10; žádný `archive_inbox_item.py`; žádný odkaz na firemní skill; dashboard řádka počítadla |
| T16 | pytest | gate | `vps/second-brain-brain/tests/test_create_and_bulk.py` | B24: neprázdné `materials` ve vykresleném souboru; bez pole pořád `materials: []`; 400 `bad_materials` nic nezapíše |
| T14 | pytest | gate | `vps/second-brain-hub/tests/test_inbox_archive.py` | `inbox_archive_rel` pro `01-INBOX/sembly/2026-10-13-1000-x.md` a `daily/`; staré testy `archive_inbox_capture` pořád zelené |
| T15 | pytest, reálný `GitVault` | gate | `vps/second-brain-hub/tests/test_git_session_discard.py` (nový) | Samotný `end_session` při výjimce po `write_text` nového souboru: soubor pryč, porcelain prázdný. Successful session `git clean` nevolá |

Ostrý zápis do `second-brain-vault` / Brain na Coolify není T#. Po nasazení image stačí existující `/healthz`. Playwright a `rbu-tester` se nevolají.

Gate: `python3 -m pytest vps/second-brain-hub/tests scripts/tests -q` a `python3 -m pytest vps/second-brain-brain/tests -q`.

## Pořadí implementace

F1 — `inbox_archive_rel` + `attachment_belongs` a T14. `archive_inbox_capture` beze změny chování.

F2 — `git_io` discard `clean -fd` + `commit_message` + `is_tracked`, T15. Bez toho T9 neprojde a nový soubor by po výjimce nechal dirty tree.

F3 — `finalize_meeting.py` + REST + MCP `CallToolResult` + řádek v runbooku. T1–T11, T9 až po F2.

F4 — `sembly_pending.py` a overlay v `get_context` / `get_context_light` bez zápisu snapshotu. T12.

F5 — skill zápisu a řádka v `agenda-co-ted`. T13 (diff).

F6 — gate pytest z bloku Testy. Deploy image `second-brain-brain` (build context `vps/`) až po zeleném F6, v samostatném kroku nasazení. Skill začne ostré volání zvládat až když je nástroj na `https://brain.cyprovi.cz`. Do té doby skill pořád popisuje `finalize_meeting`; lokální pytest nástroj kryje.

Závislosti: F3 potřebuje F1 a F2. F4 je nezávislý na F3 a může běžet po F2. F5 až když sedí kontrakt cest a chyb z F3/F4.

## Rizika a zpětná kompatibilita

1. `git clean -fd` při chybě mění všechny mutate/rebuild session, ne jen finalize. Session smí začít jen na čistém stromu a drží flock, takže má mazat jen to, co sama vytvořila. `-x` se nepoužívá (ignored soubory zůstávají). Úspěšný commit se nečistí.

2. `reset --hard` bez `clean` dnes nechává nové soubory jako `??` a další mutate spadne na `vault_dirty_start`. T9 to hlídá. Tracked úpravy dál vrací `reset --hard` (už dnes, `test_bulk_oid.py`).

3. Untracked příloha by se při move + clean mohla ztratit. Proto 400 `attachment_untracked` před zápisem (A14).

4. `yaml.safe_dump` přepíše styl frontmatteru (uvozovky, pořadí nových klíčů na konec). Tělo za `---` se neformátuje. Idempotence srovnává bajty po tomhle dumpu, ne surový vstup agenta. Druhé volání se stejným vstupem musí vyjít stejně; T3 to drží na frontmatteru s listem `participants` a `projects`.

5. `drive_copies` u nové schůzky budou v commitu prázdné, protože upload je až po finalize (A11). URL souboru na Drive se do vaultu už nedoplní. Složka známá předem žije ve `drive_folder` uvnitř `zapis_md`.

6. Create-only: doplnění `related_tasks` po `create_task` by bylo 409. Skill to přestane dělat (A12). Odkaz task → zápis je na tasku.

7. Skill dnes píše MD do klonu a pak volá `archive_inbox_item.py`, který existující archivní cíl smaže. Po F5 to dělá jen Brain a cíl neničí. Kdo skript pustí ručně, staré chování skriptu zůstane.

8. Počítadlo počítá každé `*.md` v `01-INBOX/sembly/`. Cizí markdown v té složce zvýší počet. `.keys` jsou jiná přípona a leží ve podsložce.

9. Dry-run je read bez fetch. Ostré volání po fetchi může rozhodnout jinak (mezitím archivováno). Skill bere ostré volání jako závazné; dry-run je náhled cest.

10. MCP light endpoint pořád není. Ranní brief bere REST light; fail-path MCP `get_context` má stejný overlay, protože se lepí ve funkci, ne v route.

11. Nasazení: do commitu nástroje patří Brain image. Samotný merge skillu na starém Brainu volání nástroje nenajde. Produkční vault se v testech nezapisuje.

12. `ingest_sembly` a n8n se nemění. `.keys` idempotence ingestu s finalize nesouvisí a finalize do `.keys` nezapisuje.

## Nálezy kritika (kolo r=2)

| C# | Stav | Kde |
|---|---|---|
| C1 | vyřešeno | Řez `FRONTMATTER_RE`, `safe_load` jen group 1, B6b, T6 |
| C2 | vyřešeno | Bez inboxu jiné bajty → 409 `zapis_exists`; jiná hlavička archivu → 409 `archive_exists`; 404 jen když chybí vše (B12, B21, B22) |
| C3 | vyřešeno (kolo 3) | `create_task` zapíše neprázdné `materials` ve svém commitu (B24, T16). Zápis se znovu neotevírá. Skill přestane chtít `related_tasks`, stub, **Cíl:** a checkbox. Tělo tasku zůstává `**Detail:**`. |
| C4 | vyřešeno | A10: 1:1 jen z názvu/kalendáře nebo výslovného pokynu, ne z počtu účastníků |
| C5 | vyřešeno | Skip ukázka má pod hlavičkou původní tělo. T5 |

## Otevřené otázky pro uživatele

1. Mají `drive_copies` u nové schůzky zůstat prázdné, protože upload je až po finalize? Předpoklad A11: ano, prázdné; složka je `drive_folder` ve `zapis_md`. Kdyby měly v commitu být URL kopií, skill musí nahrát na Drive před `finalize_meeting` a předat `drive_urls`. Pořadí „sdílení až potom“ by se otočilo.

2. Má řádek v `agenda-co-ted` patřit do tohoto kroku? Předpoklad A9: ano, jinak ranní brief číslo neukáže. Kdyby ne, F5 tu řádku vynechá a R9 splní jen JSON.

3. Počítat do `inbox_sembly_pending` i dnešní přepisy (věk 0), nebo jen věk ≥ 1? Předpoklad A8: počítat všechny; „starší než 24 h“ je text briefu, když věk ≥ 1. Kdyby počet měl být jen starší než 24 h, pole by po ranním ingestu ukazovalo 0 a acceptační „po úklidu = 0“ by přestalo odlišovat dnešní frontu.

4. `other` bez `skip_note` odmítnout? Předpoklad A4: ano. Kdyby note byla vždy volitelná, zmizí 400 `skip_note_required` a hlavička ponese jen `skip_reason: other`.
