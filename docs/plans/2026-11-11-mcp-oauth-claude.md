# Plán: MCP OAuth pro Claude connector

## Zadání a požadavky

R1 — Org connector v Claude Team bez sdíleného bearer tokenu. Každý člen se autentizuje sám. Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá. Zdroj: brief varianta A + rozhodnutí „org connector se do Claude organizace přidá až po lidském testu“.

R2 — Allowlist je jen `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní Gmail neprojde. Stejný seznam jako dnešní cookie OAuth. Zdroj: rozhodnutí z konverzace.

R3 — Rozsah je jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Tokeny se nedělí. Audit starých IP se nedělá. Zdroj: rozhodnutí z konverzace.

R4 — Úložiště tokenů je nový SQLite soubor na druhém Coolify persistent volume. Není to vault a nesmí ležet v `/data/vault` (host `/data/second-brain-vault`). Návrh cesty: host `/data/second-brain-oauth`, v kontejneru `/data/oauth`. Google Drive ani Mac disk se nepoužijí. Restart ani deploy nesmí odhlásit Claude. Replicas Brainu zůstávají 1. Zdroj: rozhodnutí z konverzace.

R5 — Dnešní cookie OAuth (`/oauth/authorize`, `/oauth/callback`, cookie `sb_brain_session`) zůstává. Claude ho jako MCP OAuth nepoužije. Zdroj: rozhodnutí z konverzace.

R6 — Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi: `https://brain.cyprovi.cz/oauth/mcp/callback`. Přidání URI do Google konzole je ruční krok člověka, ne skript. Zdroj: rozhodnutí z konverzace.

R7 — Registrace klienta oběma cestami, aby seděl dialog Claude: Dynamic Client Registration (RFC 7591) a Client ID Metadata Document („Use Claude's published identity“). Redirect host jen `claude.ai` a `claude.com`, včetně `https://claude.ai/api/mcp/auth_callback` a `https://claude.com/api/mcp/auth_callback`. V connectoru žádný secret. Zdroj: rozhodnutí z konverzace. Ověřeno v dokumentaci Claude (11. 11. 2026) a na živém CIMD `https://claude.ai/oauth/mcp-oauth-client-metadata`: `client_name` je `Claude`, `token_endpoint_auth_method` je `none`, redirect je jen `https://claude.ai/api/mcp/auth_callback`. Claude CIMD vybere, jen když metadata authorization serveru mají `client_id_metadata_document_supported: true` a v `token_endpoint_auth_methods_supported` je `none`. Jinak padá na DCR. `private_key_jwt` se neinzeruje.

R8 — Brain vydává vlastní neprůhledné tokeny. V úložišti jen hash. Access krátký, refresh delší, obojí odvolatelné. PKCE S256, granty `authorization_code` a `refresh_token`. Token endpoint bere `application/x-www-form-urlencoded`. Neplatný refresh je `invalid_grant` a refresh se rotuje. Zdroj: rozhodnutí + dokumentace Claude (token refresh, latence discovery/token 10 s, refresh 30 s).

R9 — Každý požadavek znovu ověří allowlist. Odebrání e-mailu nebo smazání tokenu zastaví další volání. Service token se tím nemění. Zdroj: rozhodnutí z konverzace.

R10 — Scope `brain:read` a `brain:write`. Lukáš dostane oba, když o ně klient požádá nebo scope vynechá. Nástroj mimo scope se odmítne. `set_focus` zůstane pro lidský principal. Service token se touto změnou na lidský principal nepovýší a jeho dnešní schopnost `allow_focus_write` se nemění (viz Předpoklad A2 a otázka Q1). Zdroj: rozhodnutí z konverzace + kód `policy.py`.

R11 — Audit: jeden JSON řádek na stdout Brainu (identita, klient z registrace, nástroj, čas, výsledek). Do git vaultu se nezapisuje. U service tokenu je identita přesně `service`, protože jeden token pořád sdílí Cursor, Grok, hub, dashboard a n8n. Zdroj: rozhodnutí z konverzace.

R12 — MCP bez platného tokenu: `401` a `WWW-Authenticate` s odkazem na `/.well-known/oauth-protected-resource`. REST pro cron (hub, n8n) zůstává na dnešním JSON `401` bez nucení OAuth discovery. Zdroj: rozhodnutí z konverzace. Pole `resource` v metadatech se musí rovnat URL, kterou člověk zadá do Claude, včetně lomítka: `https://brain.cyprovi.cz/mcp/`.

R13 — Po Google loginu e-mail mimo allowlist: stránka „přístup zamítnut“ a redirect do Claude s `access_denied`. Žádný token. Zdroj: rozhodnutí z konverzace.

R14 — Org connector se přidá až po lidském testu: Lukáš v claude.ai dokončí Sign in now a vidí nástroje; druhý účet z organizace mimo allowlist token nedostane. Ten test není pytest a není `rbu-tester`. Zdroj: rozhodnutí z konverzace + profil SECOND_BRAIN.

R15 — Žádné odhady effortu. `P` je výkonový rozpočet v milisekundách a počtu dotazů, ne čas práce. Zdroj: rozhodnutí z konverzace.

R16 — Nové tokeny nesmí záviset na tom, že prázdný `BRAIN_SESSION_SECRET` spadne na `BRAIN_SERVICE_TOKEN`. Cookie serializer se nemění. Zdroj: omezení v briefu pipeline.

Mimo rozsah: dělení a rotace service tokenu; audit historických volání; dashboard OAuth a přechod Groku a Cursoru na OAuth; zápis OAuth secretů nebo auditů do git vaultu; nový project hub; `AGENTS.md`; Enterprise Managed Auth (`jwt-bearer` z CIMD dokumentu); Claude Code loopback (Q2); vizuální gate dashboardu. Alembic, RBAC, subnav, dlaždice, `qa_gate.mjs`, Celery a React se této změny netýkají.

## Předpoklady

A1 — Vlastní tenká vrstva nad stdlib `sqlite3` + stávající `httpx`. Authlib se nepřidává. Důvody: v `requirements.txt` není; CIMD, hash tokenů, allowlist a oddělení od cookie session by se v Authlibu stejně psaly ručně; cookie flow už umí výměnu kódu u Google přes `httpx`.

A2 — Věta „set_focus zůstane jen pro lidský principal, ne pro service token“ se v téhle změně čte takto: Claude OAuth principal je člověk (`oauth:<email>`) a `set_focus` / `apply_focus` smí jen s `brain:write`. `ServicePrincipal` se na lidský principal nepovýší. `allow_focus_write` pro service token se nemění, protože `policy.py` ho dnes pouští, test `test_b2_service_principal` to hlídá a rozhodnutí říká, že service token se nemění. Kdyby Q1 dopadla opačně, Cursor a Grok přijdou o zápis fokusu, dokud nepřejdou na OAuth, což je mimo rozsah.

A3 — Vynechaný `scope` na authorize u allowlist e-mailu znamená oba scope. Požádá-li klient jen o jeden, dostane jen ten. `offline_access` se neinzeruje a když přijde, zahodí se; refresh token se vydá vždy u `authorization_code`. `brain:write` neimplikuje `brain:read`.

A4 — Cookie session na MCP zůstává a má implicitně oba scope (dnešní plný přístup). OAuth access token z nového flow se na REST `/v1/*` nepřijímá.

A5 — Odebrání e-mailu z allowlistu zastaví volání hned, ale řádek grantu se nesmaže. Vrácení e-mailu do kódu allowlistu nepoužitý a neodvolaný grant znovu pustí. Odvolání grantu (CLI) je trvalé do nového loginu. Veřejný revoke endpoint se nedělá.

A6 — Redirect se povolí jen jako přesná shoda s URI z DCR nebo CIMD, a jen když host je přesně `claude.ai` nebo `claude.com`, schéma `https`, bez userinfo, bez fragmentu, bez jiného portu. Jakákoli cizí URI v seznamu shodí celou registraci. `localhost` / `127.0.0.1` se zamítnou. Claude Code tedy tímhle plánem OAuth nedokončí (Q2). Dialog org connectoru na claude.ai sedí na ověřené CIMD URI.

A7 — Publikované `resource` je `{BRAIN_PUBLIC_URL}/mcp/` s koncovým lomítkem. Při srovnání se jedno koncové lomítko ignoruje, aby neselhal klient, který ho pošle jinak. Cizí resource se odmítne.

A8 — TTL: authorize transakce 10 min, authorization code 60 s, access 3600 s, refresh 30 dní od vydání (rotace posune jen nový refresh), absolutní strop grantu 90 dní od vytvoření. Časy v UTC. `expires_at <= now` je vypršelé. Pepper je `BRAIN_OAUTH_TOKEN_PEPPER` (HMAC-SHA256). Chybějící pepper nepadá na service token.

A9 — SQLite se neotevírá při importu ani při úspěšném service-token requestu. Chybějící volume neshodí lifespan. Metadata a `401` jedou i bez databáze. Authorize, register a token bez zapsatelné DB nebo pepperu vrací `503`.

A10 — Re-run celého `setup-coolify.sh` na živé aplikaci se pro tuhle změnu nespouští. Volume přidá malý idempotentní skript. Plný setup skript dostane stejný INSERT jen pro novou instalaci.

A11 — Produkční počet řádků OAuth DB nejde změřit: soubor ještě neexistuje. Strop na dva roky je jeden člověk, pod 500 DCR klientů, pod 100 grantů. Dotaz po nasazení, není to gate: v kontejneru `sqlite3 /data/oauth/brain-oauth.sqlite 'SELECT COUNT(*) FROM oauth_tokens;'`.

A12 — Stránka zamítnutí je HTTP 200 HTML se statickým textem „Přístup zamítnut.“ a `meta refresh` 0 na Claude `redirect_uri` s `error=access_denied`, `state` a `iss`. E-mail ani allowlist se na stránku nevypisují. Úspěch je HTTP 302, bez cookie `sb_brain_session`.

## Současný stav (ověřeno v kódu)

`vps/second-brain-brain/app/auth_google.py:9-14` — `ALLOWLIST` je přesně ty dva e-maily. `email_allowed` je case-insensitive. `authorize_url` (`49-67`) posílá `prompt=select_account` a neposílá `hd`. Callback URL je `{BRAIN_PUBLIC_URL}/oauth/callback`.

`vps/second-brain-brain/app/oauth_routes.py:25-29` — prázdný `BRAIN_SESSION_SECRET` padá na `BRAIN_SERVICE_TOKEN`, jinak `dev-only-insecure`. Cookie `sb_brain_session` má `max_age` 30 dní. Cizí e-mail na `/oauth/callback` je HTTP 403 a v těle je vypsaný allowlist (`113-117`). To MCP flow nesmí zopakovat. Route `/oauth/mcp/*` dnes nejsou.

`vps/second-brain-brain/app/mcp_auth.py:14-65` — MCP pustí cookie e-mail, nebo Bearer shodný s `BRAIN_SERVICE_TOKEN`, nebo dev bez tokenu. Jinak JSON `401` s `error_reason: client_error`. Hlavička `WWW-Authenticate` se nenastavuje. Pořadí: cookie vyhraje nad Bearerem.

`vps/second-brain-brain/app/auth_deps.py:17-49` — REST je cookie, nebo service Bearer, nebo dev. Cizí Bearer je `401` bez OAuth hlavičky. OAuth access token by dnes na REST neprošel, protože se porovnává jen se service tokenem.

`vps/second-brain-brain/app/auth_service.py:26-36` — service token je `hmac.compare_digest` proti `BRAIN_SERVICE_TOKEN`. `ServicePrincipal.audit_id` vrací `service:service` a nikde jinde se nečte. Nový auditní řádek použije řetězec `service`, tuhle property nemění.

`vps/second-brain-brain/app/policy.py:15-25` — `allow_focus_write` pouští `ServicePrincipal`, řetězec `oauth:…` i `dev`. Plán z 12. 10. 2026 (A1) to tak schválil, protože MCP klienti jedou Bearerem.

`vps/second-brain-brain/app/tools/set_focus.py:122-136` — bez `via_apply=True` je vždy `403 focus_requires_proposal` a nic se nezapíše. Zápis jde jen přes `apply_focus`.

`vps/second-brain-brain/app/mcp_app.py:174-184` a `204-206` — MCP `set_focus` principal nepředává a `via_apply` nechá na false. `apply_focus` principal taky nepředává, takže se vezme ContextVar. `mailbox_apply` / `external_apply` (`508-532`) principal natvrdo staví jako `ServicePrincipal(label="mcp")`, i když už ContextVar existuje. `gate_brain_apply` pak pro service vrací 403 a pro řetězec `oauth:` 501 (`auth_apply.py:15-26`). Nový dataclass bez úpravy téhle brány spadne do 401.

`vps/second-brain-brain/app/main.py:90-95` a `142-143` — MCP je mount `/mcp` obalený `McpAuthMiddleware`. Cookie router je na appce, ne pod mountem. Lifespan spadne jen když chybí `GIT_VAULT_PUSH` a není `BRAIN_ALLOW_NO_PUSH`.

`vps/second-brain-brain/requirements.txt` — fastapi, httpx, itsdangerous, mcp, google-auth-oauthlib. Authlib tam není. `sqlite3` je ve stdlib.

`vps/second-brain-brain/Dockerfile` — jeden proces `uvicorn` bez `--workers`, user root, žádný volume v image. Persistenci dělá jen Coolify mount.

`vps/second-brain-brain/deploy/setup-coolify.sh:103-107` — idempotentní INSERT jen pro `mount_path=/data/vault`, `host_path=/data/second-brain-vault`. Skript taky queueje deploy a sahá na env. Pro živou appku se celý nespouští.

`vps/second-brain-brain/tests/test_mcp_auth.py:30-33` — `POST /mcp` bez tokenu čeká `401` a `error_reason == client_error`. Hlavičku neřeší. Service token na `/mcp/` nesmí být 401.

`docs/brain-api-runbook.md:150-153` — kanonická MCP URL je `https://brain.cyprovi.cz/mcp/` s lomítkem. Browser OAuth je cookie a remote MCP ho nepoužije.

Živý CIMD (staženo 11. 11. 2026): `client_id` = `https://claude.ai/oauth/mcp-oauth-client-metadata`, granty zahrnují i `urn:ietf:params:oauth:grant-type:jwt-bearer`. Ten grant se neimplementuje.

## Návrh

Netýká se: Alembic, SQLAlchemy, RBAC, Celery, React, `api.ts`, subnav, hub dlaždice, `scripts/qa_gate.mjs`, Allfred, Pipedrive, Fakturoid, Fio. Žádná nová závislost v `requirements.txt`.

### Úložiště

Nový modul `vps/second-brain-brain/app/oauth_mcp_store.py`. Soubor z `BRAIN_OAUTH_DB`, default `/data/oauth/brain-oauth.sqlite`. Otevření lazy, WAL, `busy_timeout` 5000, `check_same_thread=False`, zápisy v `BEGIN IMMEDIATE`.

Odmítnout cestu, jejíž `realpath` leží v `GIT_VAULT_ROOT` nebo pod `/data/vault` (R4). Pak jsou OAuth route `503` a do logu jde důvod bez secretů.

Tabulky:

- `oauth_clients` — `client_id` PK, `client_name`, `redirect_uris_json`, `source` (`dcr`|`cimd`), `created_at`. Žádný sloupec pro secret.
- `oauth_transactions` — id (Google `state`), `client_id`, `redirect_uri`, `code_challenge`, `scope`, Claude `state`, `resource`, `auth_code_hash`, expirace, `consumed_at`.
- `oauth_grants` — family id, `client_id`, `client_name`, `email`, `scope`, `resource`, `created_at`, `revoked_at`.
- `oauth_tokens` — `token_hash` PK (HMAC-SHA256 hex pepperem), `grant_id`, `kind` (`access`|`refresh`), `expires_at`, `revoked_at`, `replaced_by_hash`, `created_at`.
- `cimd_cache` — URL, JSON, `fetched_at`. TTL čtení 1 hodina. Na MCP request se nečte.

Funkce `revoke_grants_for_email(email)`. CLI `python -m app.oauth_mcp_revoke <email>` jen nad SQLite, bez HTTP. Odvolá granty a jejich tokeny.

Pepper jen z `BRAIN_OAUTH_TOKEN_PEPPER`. Prázdný pepper: OAuth zápisové route `503`, ne tichý fallback (R16).

### Metadata a 401

Nový `vps/second-brain-brain/app/oauth_mcp_metadata.py`, napojený v `main.py` před mountem MCP. Bez autentizace:

- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-protected-resource/mcp` — stejné JSON

JSON: `resource` = `{public}/mcp/`, `authorization_servers` = jednoprvkový seznam issueru (`BRAIN_PUBLIC_URL` bez koncového lomítka), `scopes_supported` = `brain:read`, `brain:write`, `bearer_methods_supported` = `header`. `offline_access` tam není.

- `GET /.well-known/oauth-authorization-server` — issuer, `authorization_endpoint` `/oauth/mcp/authorize`, `token_endpoint` `/oauth/mcp/token`, `registration_endpoint` `/oauth/mcp/register`, `response_types_supported` `code`, `grant_types_supported` `authorization_code` + `refresh_token`, `code_challenge_methods_supported` `S256`, `token_endpoint_auth_methods_supported` jen `none`, `client_id_metadata_document_supported` true, `authorization_response_iss_parameter_supported` true. Bez `private_key_jwt`.

`McpAuthMiddleware`: každý MCP `401` (chybějící token, špatný Bearer, vypršelý nebo odvolaný access, e-mail mimo allowlist, `X-API-Key`) dostane navíc

`WWW-Authenticate: Bearer resource_metadata="{issuer}/.well-known/oauth-protected-resource", scope="brain:read brain:write"`

Tělo JSON zůstává `{"error_reason":"client_error","message":"authentication required"}` (u API key dnešní text o human API keys). Hlavička se nedává na `200` ani na tool error. REST `HTTPException` v `auth_deps.py` hlavičku nedostane.

Pořadí v middleware: `X-API-Key` → cookie (dnešní `read_session_email`, principal `oauth:{email}`, scope oba, bez SQLite) → `hmac` service token (bez SQLite, `ServicePrincipal`) → HMAC access tokenu a jeden SELECT podle PK → dev jako dnes. Selhání SQLite u neznámého Beareru je `401`, ne `500`. Service token při rozbité SQLite pořád projde.

Nový dataclass `OAuthPrincipal` v `app/oauth_mcp_principal.py`: `email`, `scopes`, `client_id`, `client_name`. `__str__` vrací `oauth:{email}`, aby batch principal nebyl repr dataclassu. `allow_focus_write` ho pustí jako člověka a větev `ServicePrincipal` nechá být (A2). `gate_brain_apply` ho pustí stejnou větví jako řetězec `oauth:` → 501.

### DCR, CIMD, authorize, token

Nový router `vps/second-brain-brain/app/oauth_mcp_routes.py`. `auth_google.py` dostane `oauth_mcp_callback_url` = `{public}/oauth/mcp/callback`. `authorize_url` se znovupoužije, `hd` se nepřidává.

Společná kontrola redirect URI: `https`, host přesně `claude.ai` nebo `claude.com`, bez userinfo, fragmentu a cizího portu. Jedna špatná URI v požadavku nebo v CIMD dokumentu = celé odmítnutí, nic se neuloží.

`POST /oauth/mcp/register` JSON, max 8 KiB, odpověď `201`. `client_id` = `brain_` + `token_urlsafe`. `token_endpoint_auth_method: none`. `client_secret` v odpovědi není, a když ho klient pošle, neukládá se. Strop 500 klientů, pak `429`. Každá registrace je nový `client_id`.

CIMD: `client_id` musí být `https` URL na těch dvou hostech, bez query, fragmentu a userinfo. `httpx` timeout 5 s, `follow_redirects=False`. JSON `client_id` se musí rovnat URL. `token_endpoint_auth_method` musí být `none` nebo chybět. Cache 1 h. Cizí grant `jwt-bearer` v dokumentu klienta neodmítne; odmítne se až použití toho grantu na token endpointu (`unsupported_grant_type`).

`GET /oauth/mcp/authorize`: `response_type=code`, PKCE jen `S256`, klient z DCR nebo CIMD, `redirect_uri` přesná shoda s jeho seznamem. Špatná `redirect_uri` → `400` a žádný `Location` (open redirect). Platná `redirect_uri` a špatné PKCE nebo scope → `302` na ni s `error=invalid_request` nebo `invalid_scope`, plus `state` a `iss`. Resource se uloží; cizí resource → `invalid_target`. V SQLite vznikne transakce. Prohlížeč jde na Google s redirectem na `/oauth/mcp/callback` a `state` = id transakce. Žádná cookie.

`GET /oauth/mcp/callback`: výměna kódu u Google jako dnešní callback (timeout 20 s) a userinfo. `verified_email is False` nebo prázdný e-mail nebo e-mail mimo allowlist → žádný řádek tokenu, HTML „Přístup zamítnut.“ a meta refresh na Claude s `error=access_denied`. Allowlist e-mail → authorization code (v DB jen hash, TTL 60 s) a `302` na Claude s `code`, `state`, `iss`. Cookie `sb_brain_session` se nenastavuje. Google 5xx nebo timeout → žádný token; když transakce existuje, redirect `error=server_error`, jinak `400`.

`POST /oauth/mcp/token` jen form body. `authorization_code`: jednorázový kód, shoda `redirect_uri`, PKCE S256, resource shodný až na jedno lomítko. Replay už spotřebovaného kódu je `invalid_grant` a žádný druhý token. `refresh_token`: rotace v jedné SQLite transakci; starý refresh `replaced_by_hash`; jeho opakované předložení odvolá celou family a vrátí `invalid_grant`. Allowlist se kontroluje znovu. Vypršelý nebo odvolaný grant, nebo věk nad 90 dní, je `invalid_grant`. `client_secret` se ignoruje. `client_credentials` a `jwt-bearer` jsou `unsupported_grant_type`. Odpověď: `token_type=Bearer`, `expires_in=3600`, nový refresh, `scope` jen z `brain:read` / `brain:write`.

### Scope a audit na MCP

`app/mcp_scopes.py` — jeden slovník, jeden požadovaný scope na nástroj.

`brain:read`: `get_context`, `read_file`, `list_dir`, `export_tasks`, `find_tasks`, `get_task`, `list_children`, `get_tree`, `list_reminders`, `get_triage_candidates`, `slack_live`, `get_meeting_prep`, `allocate_task_id` (nic nezapisuje).

`brain:write`: `update_task`, `append_task_note`, `set_focus`, `propose_focus`, `apply_focus`, `edit_task_body`, `toggle_step`, `close_task`, `create_task`, `bulk_update`, `schedule_reminder`, `cancel_reminder`, `finalize_meeting`, `ingest_sembly`, `capture_daily`, `mailbox_propose`, `mailbox_apply`, `external_propose`, `external_apply`, `prepare_meeting`. `dry_run` scope nesnižuje.

`app/mcp_audit.py` — logger `brain.mcp.audit`, `propagate False`, handler na stdout, formát jen `%(message)s`. Jeden JSON objekt: `ts` (UTC), `identity`, `client_id`, `client_name`, `tool`, `result` (`ok`|`error`|`denied`), `error_reason`. Bez argumentů nástroje a bez tokenu.

`mcp_app.py` dostane jeden `guarded_call(tool_name, fn, **kwargs)` a všechny nástroje půjdou přes něj, včetně těch, které dnes vracejí `CallToolResult` přímo. Pro `OAuthPrincipal` bez scope: nástroj se nespustí, výsledek je MCP `isError` s `error_reason: insufficient_scope`, HTTP zůstane 200 (Claude by z `401` znovu otevíral login). Service, cookie a dev scope mapu přeskakují. `tools/list` se nefiltruje; hranice je až volání. `mailbox_apply` a `external_apply` přestanou vyrábět `ServicePrincipal(label="mcp")` a předají `get_brain_principal()`.

### Nasazení a docs

`deploy/add-oauth-volume.sh` (běží na coolify-dev jako ops): `mkdir -p /data/second-brain-oauth`, `chmod 700`, idempotentní INSERT `local_persistent_volumes` (`mount_path=/data/oauth`, `host_path=/data/second-brain-oauth`, `name=second-brain-oauth`). Nesahe na env, netiskne secret, nedeployuje. Na konci text, že mount se chytí až restartem aplikace v Coolify.

Do `setup-coolify.sh` stejný INSERT hned za vault volume, plus komentář, že živá appka má použít malý skript, ne celý setup.

`config.example.env` — zakomentované `BRAIN_OAUTH_DB` a `BRAIN_OAUTH_TOKEN_PEPPER`. Pepper se jednou vloží v Coolify UI (`openssl rand -hex 32`), není odvozený ze service tokenu a do gitu nejde.

`docs/brain-api-runbook.md` — nové endpointy, resource URL s lomítkem, volume, pepper, ruční Google redirect URI, CLI revoke, repliky zůstávají 1, connector se do organizace nepřidává, dokud člověk neudělá T-H1. Service token odstavec zůstane.

Ruční kroky člověka, které kód nedělá: (1) volume skript a restart, (2) pepper v Coolify, (3) redirect URI v Google konzoli, (4) až po T-H1 přidat connector. Pytest a veřejné QA tyto kroky nepotřebují, kromě toho, že bez (1)–(3) Claude login na produkci neprojde.

## Kontrakt chování (B#)

Checklist A, co tu není samostatný řádek: fiskální rok a měny se netýkají, protože OAuth nemá částky ani FY. Sync Allfred/Pipedrive se netýká. `backend/app/services/data_consistency.py` se netýká, protože tohle není RB Universe; invariant je B7, B54 a B6 (service token beze změny, DB mimo vault).

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | `POST /mcp` a `POST /mcp/` bez Authorization | `401`, JSON `error_reason=client_error`, `WWW-Authenticate` obsahuje `resource_metadata` na protected-resource a `scope="brain:read brain:write"`. Hlavička není na žádné `200`. | R12 | T1 |
| B2 | `GET /v1/context` bez cookie a bez Beareru | `401`, hlavička `WWW-Authenticate` chybí | R3, R12 | T2 |
| B3 | `GET /healthz` a oba well-known GET bez tokenu | `200`, bez Authorization | R12 | T3 |
| B4 | Protected resource metadata | `resource` je `{BRAIN_PUBLIC_URL}/mcp/` včetně lomítka; `authorization_servers` má jediný prvek, issuer bez lomítka | R12 | T3 |
| B5 | Authorization server metadata | DCR endpoint, CIMD true, `none`, S256, granty code+refresh. Není tam `private_key_jwt` ani `offline_access` | R7, R8 | T3 |
| B6 | MCP `initialize` s platným service tokenem, SQLite chybí nebo je rozbitá | není `401` ani `500`; SQLite se neotevírá | R3, R9 | T4 |
| B7 | `BRAIN_OAUTH_DB` ukazuje dovnitř `GIT_VAULT_ROOT` nebo `/data/vault` | zápisové OAuth route `503`, soubor se nevytvoří, vault se nemění | R4 | T5 |
| B8 | Prázdná DB, chybí pepper nebo adresář volume | metadata `200`; register, authorize a token `503`; lifespan Brainu naběhne; service MCP projde | R4, R16 | T5 |
| B9 | DCR s oběma auth_callback URI | `201`, `client_id`, žádný `client_secret` v těle ani v DB | R7 | T6 |
| B10 | DCR s `https://evil.example/cb`, `http://claude.ai/...`, `https://www.claude.ai/...`, `https://user@claude.ai/...`, nebo jednou dobrou a jednou zlou URI | `400`, v DB 0 nových klientů | R7 | T6 |
| B11 | DCR nebo authorize s `http://localhost/callback` nebo `http://127.0.0.1:<port>/callback` | odmítnuto, kód se nevydá | R7 | T6 |
| B12 | CIMD `client_id` = živý tvar `https://claude.ai/oauth/mcp-oauth-client-metadata` (mock), redirect jen claude.ai callback | authorize klienta přijme, fetch bez redirectů | R7 | T7 |
| B13 | CIMD dokument obsahuje i cizí redirect, nebo `client_id` v JSON nesedí na URL, nebo host není claude.ai/claude.com | `invalid_client`, dokument se jako klient nepoužije | R7 | T7 |
| B14 | CIMD URL vrátí HTTP redirect, timeout nebo 5xx | redirect se nesleduje; klient odmítnut; žádný token | R7 | T7 |
| B15 | Token request s neprázdným `client_secret` | secret se nekontroluje a neukládá; platný code projde | R7 | T8 |
| B16 | Authorize bez PKCE, method `plain`, nebo bez `code_challenge` | při platné redirect URI `302 error=invalid_request`; kód v DB není | R8 | T8 |
| B17 | Platné S256, allowlist e-mail, scope vynechaný | oba scope, access + refresh, v DB jen HMAC hashe, raw token v souboru není | R2, R8, R10 | T8 |
| B18 | Token exchange se špatným `code_verifier` | `invalid_grant`, tokeny se nevydají | R8 | T8 |
| B19 | Stejný authorization code podruhé | `invalid_grant`, druhá sada tokenů nevznikne | R8 | T8 |
| B20 | Kód starší než 60 s, nebo transakce starší než 10 min | kód: `invalid_grant`. Transakce: žádný token, redirect `invalid_request`, pokud URI známe | R8 | T9 |
| B21 | Token exchange s jinou `redirect_uri`, než byla na authorize | `invalid_grant` | R7 | T8 |
| B22 | Authorize s `redirect_uri`, která není v registraci klienta | HTTP `400`, hlavička `Location` neukazuje na tu URI | R7 | T6 |
| B23 | Authorize pro oba allowlist e-maily, jiná velikost písmen, scope oba nebo vynechaný | tokeny, scope oba. Google URL nemá parametr `hd` | R2, R10 | T10 |
| B24 | Scope jen `brain:read` | v tokenu jen read | R10 | T10 |
| B25 | Scope jen `foo` | `invalid_scope`, token není | R10 | T10 |
| B26 | Scope obsahuje `offline_access` a `brain:read` | uložený scope je jen `brain:read`; refresh token v odpovědi je | R8, R10 | T10 |
| B27 | Google userinfo e-mail mimo allowlist | HTTP 200 HTML obsahuje „Přístup zamítnut.“, neobsahuje e-mail ani seznam allowlistu; meta refresh má `error=access_denied` a host claude.ai nebo claude.com; v DB není grant ani token; cookie `sb_brain_session` není | R13 | T11 |
| B28 | `verified_email: false` nebo prázdný e-mail | stejné jako B27 | R2, R13 | T11 |
| B29 | Google token endpoint timeout nebo 5xx | žádný token; u známé transakce redirect `error=server_error` | R8 | T11 |
| B30 | `GET /oauth/callback` cizí e-mail (starý flow) | pořád `403` jako dnes; MCP route se nezavolá | R5 | T12 |
| B31 | `GET /oauth/authorize` | pořád redirect na Google s `/oauth/callback`, ne s `/oauth/mcp/callback` | R5, R6 | T12 |
| B32 | Access starší než `expires_at` (`<= now`) na MCP | `401` + `WWW-Authenticate`, nástroj neběží | R8, R9 | T13 |
| B33 | Grant odvolaný CLI nebo smazaný řádek tokenu | MCP `401`; refresh `invalid_grant` | R8, R9 | T13 |
| B34 | Platný refresh | nový access i nový refresh; starý refresh pak `invalid_grant` a family je odvolaná | R8 | T14 |
| B35 | Dva souběžné refreshe téhož tokenu | právě jedna úspěšná odpověď; druhá `invalid_grant` | R8 | T14 |
| B36 | Access nebo refresh, e-mail mezitím zmizel z allowlistu | MCP `401`; refresh `invalid_grant`; service token pořád funguje | R9 | T15 |
| B37 | E-mail se do allowlistu vrátí, grant nebyl odvolaný a nevypršel | stejný access znovu projde | R9 | T15 |
| B38 | Grant starší než 90 dní, refresh jinak platný | `invalid_grant` | R8 | T13 |
| B39 | Resource `…/mcp` i `…/mcp/` | přijato. Resource na jiné URL | `invalid_target`, token není | R12 | T8 |
| B40 | Token endpoint s JSON tělem místo form | `400` nebo `415`, token není | R8 | T8 |
| B41 | Grant `client_credentials` nebo jwt-bearer | `unsupported_grant_type` | R8 | T8 |
| B42 | OAuth access jen s `brain:read`, `tools/call create_task` | HTTP 200, `isError`, `insufficient_scope`, nástrojová funkce se nezavolá, vault write 0. Není to `401` | R10 | T16 |
| B43 | OAuth access s `brain:write` bez read, `tools/call read_file` | `insufficient_scope`, read se nezavolá | R10 | T16 |
| B44 | OAuth access s oběma scope, `apply_focus` | principal je člověk, `allow_focus_write` pustí (write samotný testuje bránu, ne vault) | R10 | T17 |
| B45 | Service token, libovolný nástroj včetně `apply_focus` | scope mapa se neaplikuje; `allow_focus_write(ServicePrincipal)` zůstává allowed | R3, R10 | T4, T17 |
| B46 | Cookie `sb_brain_session` allowlist e-mailu na MCP, bez Beareru | projde jako dnes, oba scope implicitně | R5 | T18 |
| B47 | OAuth access token na `GET /v1/context` | `401` (není to service token a není cookie) | R3 | T2 |
| B48 | `str(OAuthPrincipal)` a `mailbox_apply` / `external_apply` | principal je `oauth:<email>`; `gate_brain_apply` → 501 `oauth_brain_apply_post_f3`. Service principal → pořád 403 `human_oauth_required`. Natvrdo `ServicePrincipal(label="mcp")` v MCP zmizí | R10 | T19 |
| B49 | `tools/call` OAuth i service | přesně jeden stdout JSON řádek: u OAuth `identity=oauth:<email>`, `client_name` z registrace (u CIMD `Claude`); u service `identity=service`, `client_id` i `client_name` null. Bez argumentů a bez tokenu. Do vaultu se nezapíše | R11 | T20 |
| B50 | `X-API-Key` na MCP | `401` + `WWW-Authenticate`, nástroj neběží | R12 | T1 |
| B51 | Dev bez `BRAIN_SERVICE_TOKEN` a s `BRAIN_ALLOW_NO_PUSH` | pořád principal `dev`, testy bez OAuth DB nepadají na importu | R3 | T4 |
| B52 | Úspěšný MCP login | nenastaví `sb_brain_session` a nestrčí hash do `/data/vault` | R4, R5 | T8, T5 |
| B53 | Stránka zamítnutí | malé HTML v `/oauth/mcp/callback`, ne šablona dashboardu; text „Přístup zamítnut.“ je vidět bez JS | R13, R14 | T11 |

Prázdná data: B8. Chybějící e-mail a kód: B20, B28. Hranice expirace: B32, B38. Oprávnění: B23–B28, B36, B42–B48. Smazaný grant: B33, B36. Opakování: B19, B34, B35. Cizí služba: B14, B29. Zpětná kompatibilita: B2, B6, B30, B31, B45, B46, B51.

## Výkonový rozpočet (P)

Produkční OAuth tabulky dnes neexistují (A11). Po nasazení porostou s jedním uživatelem, ne s vaultem. Strop za dva roky: pod 500 klientů, pod 100 grantů, pod 200 token řádků. Soubor v řádu stovek KiB. Lookup access tokenu je jeden SELECT podle PK, ne N+1 a neroste s N nástrojů. Do Pythonu se nenačítá vault ani cizí blob. Na cestě MCP nástroje není žádné volání Google, Allfredu ani CIMD. CIMD fetch je jen na authorize, timeout 5 s, pak cache 1 h v SQLite. Token endpoint Google nevolá. Stránkování se netýká (žádný seznam pro UI). Payload metadat je pod 2 KiB, token odpověď pod 1 KiB, auditní řádek pod 500 B. Cache platnosti tokenu v procesu se nedělá, aby odvolání platilo hned. Frontend, React Query a virtualizace se netýkají. Worker: žádný nový task; uvicorn zůstává jeden proces, SQLite zápis je krátký a neblokuje vault push worker déle než jednotky ms. Repliky se nenastavují nad 1, protože SQLite na tomhle volume není sdílená mezi procesy na víc hostech.

| Endpoint | SQL | Externí volání | Cíl | Měření |
|---|---|---|---|---|
| `GET` obou well-known | 0 | 0 | cold i warm pod 50 ms | T3 a QA curl `time_total` |
| `POST /oauth/mcp/register` | 1 INSERT | 0 | pod 50 ms | T6 |
| `GET /oauth/mcp/authorize` | 1 INSERT, u CIMD navíc 1 SELECT cache | CIMD jen při miss, timeout 5 s, pod Claude limit 10 s | cache hit pod 50 ms | T7 |
| `GET /oauth/mcp/callback` | 1 transakce | Google token + userinfo, timeout 20 s (prohlížeč, ne MCP) | lokální část pod 50 ms | T11 mock |
| `POST /oauth/mcp/token` včetně refresh | 1 transakce, nejvýš 4 statementy | 0 | cold pod 50 ms, warm pod 20 ms; Claude dává tokenu 10 s a refreshi 30 s | T8, T14 |
| MCP gate pro service token | 0 | 0 | přidaná režie pod 5 ms | T4 |
| MCP gate pro OAuth access | 1 PK SELECT | 0 | přidaná režie pod 15 ms; nástroj za branou se neměří, vault se nemění | T13, T16 |

Anti-patterny checklistu B (Allfred blob, `Model.all()`, live GraphQL, tři endpointy se stejným kontextem) se netýkají. Jediný zákaz: neověřovat token tak, že se na každý request načte celá tabulka tokenů.

## Testy (T#)

Primární gate: `python3 -m pytest vps/second-brain-brain/tests -q`. Hub pytest se nespouští, hub se nemění. `scripts/qa_*_ui.mjs` a Playwright T6 se nezakládají: profil SECOND_BRAIN, stránka zamítnutí není dashboard. `rbu-tester` se nevolá.

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-brain/tests/test_mcp_oauth.py` | B1, B50. Doplní i `test_mcp_auth.py`, aby starý `401` JSON zůstal a přibyla hlavička |
| T2 | pytest | gate | stejný soubor | B2, B47 |
| T3 | pytest | gate | stejný soubor | B3, B4, B5 |
| T4 | pytest | gate | `test_mcp_auth.py` + oauth soubor | B6, B45 (průchod), B51 |
| T5 | pytest | gate | oauth soubor | B7, B8, B52 cesta |
| T6 | pytest | gate | oauth soubor | B9, B10, B11, B22 |
| T7 | pytest | gate | oauth soubor, mock httpx | B12, B13, B14 |
| T8 | pytest | gate | oauth soubor, mock Google | B15, B16, B17, B18, B19, B21, B39, B40, B41, B52 cookie |
| T9 | pytest | gate | oauth soubor | B20 |
| T10 | pytest | gate | oauth soubor | B23, B24, B25, B26 |
| T11 | pytest | gate | oauth soubor | B27, B28, B29, B53 |
| T12 | pytest | gate | stávající `test_mcp_and_oauth_routes.py`, `test_auth_b37.py` | B30, B31 musí zůstat zelené bez úpravy očekávaného cookie chování |
| T13 | pytest | gate | oauth soubor | B32, B33, B38 |
| T14 | pytest | gate | oauth soubor | B34, B35 |
| T15 | pytest | gate | oauth soubor | B36, B37 |
| T16 | pytest | gate | oauth soubor | B42, B43. Scope brána se testuje na falešném callable, bez vaultu |
| T17 | pytest | gate | `test_set_focus.py` zůstává; oauth soubor přidá `OAuthPrincipal` | B44, B45 `allow_focus_write` |
| T18 | pytest | gate | oauth soubor | B46 |
| T19 | pytest | gate | oauth soubor | B48 |
| T20 | pytest | gate | oauth soubor, capsys stdout | B49 |
| T-Q1 | curl proti `https://brain.cyprovi.cz` po deployi image `second-brain-brain` | QA | není nový skript v repu | B1, B3, B4, B5, B6 na veřejné URL. Žádný zápis do vaultu. Service token z env, do chatu se nekopíruje |
| T-H1 | ruční v claude.ai | člověk, ne gate a ne Tester | — | R14: Lukáš dokončí Sign in now a vidí nástroje; druhý účet organizace mimo allowlist dostane stránku zamítnutí a žádný token. Do té doby se connector do organizace nepřidává. Google redirect URI, volume a pepper musí být hotové, jinak test nejde spustit |

## Pořadí implementace

F1 — `oauth_mcp_store.py`, principal dataclass, pepper, zákaz cesty ve vaultu, CLI revoke. Závisí na ničem.

F2 — metadata route a `WWW-Authenticate` v `mcp_auth.py`. Service větev beze změny a bez SQLite. Závisí na F1 jen pro to, aby se DB neotevírala omylem; metadata DB nepotřebují.

F3 — DCR, CIMD, authorize, callback, token. Závisí na F1 a na `oauth_mcp_callback_url`.

F4 — `OAuthPrincipal` v middleware, scope mapa, `guarded_call`, audit, úprava `allow_focus_write` a `gate_brain_apply`, MCP apply bez natvrdo service principalu. Závisí na F1 a F3 (bez tokenů není co ověřovat, unit scope brány jde mockem už po F1).

F5 — `add-oauth-volume.sh`, INSERT do `setup-coolify.sh`, komentáře v `config.example.env`, runbook. Může běžet souběžně s F4, musí být v tom samém diffu před pushem na `main`.

F6 — pytest T1–T20 a kontrola, že T12 (staré soubory) je pořád zelený. Až po F2–F4.

F7 — člověk: volume + restart, pepper, Google redirect URI. Až pak T-H1. Až pak přidání connectoru do organizace. Tohle není krok implementace v gitu.

Push na `main` spustí Coolify deploy image Brain. Volume a pepper mají být na hostu před restartem, který deploy vyvolá, jinak první běh OAuth route vrací `503` a service token dál žije. Druhý restart po doplnění volume stav srovná. Hub image se nenasazuje.

## Rizika a zpětná kompatibilita

1. První deploy bez volume nebo pepperu: Claude login dostane `503`, Cursor/Grok/hub/n8n jedou dál. Není to tichá díra, je to viditelný `503`.

2. Bez ručního redirect URI v Google konzoli callback na produkci skončí `redirect_uri_mismatch`. Pytest to nevidí, mockuje Google.

3. Claude u custom connectoru defaultně vezme CIMD. Ten dokument zná jen `https://claude.ai/api/mcp/auth_callback`. `claude.com` projde jen přes DCR. Pro org connector na claude.ai to stačí.

4. `resource` bez koncového lomítka v metadatech by rozbilo dialog, protože člověk zadá URL s lomítkem. Publikuje se varianta s lomítkem; srovnání přijme obě.

5. Rotace refreshe při dvou paralelních requestech: druhý dostane `invalid_grant` a může odvolat family. U jednoho uživatele a jedné repliky je to přijatelné; Claude se znovu přihlásí.

6. Ztráta pepperu v Coolify env odhlásí Claude. Volume samotný restart odhlášení nezpůsobí. Pepper se nerotuje jako součást téhle změny.

7. Repliky nad 1 by SQLite rozbily. Runbook to nechá na 1. Kód repliky nenastavuje.

8. Otevřené DCR je omezené hostem redirectu a stropem 500 řádků. Jinak by šlo plnit disk.

9. CIMD SSRF: jen dva hosti, žádné redirecty, timeout 5 s, strop těla 64 KiB.

10. `mailbox_apply` a `external_apply` přestanou předstírat service principal. Dnešní service volání pořád skončí 403. OAuth člověk dostane 501, stejně jako REST cookie. Na produkci teď MCP jiného principala než service nemá, takže se chování současných klientů nemění.

11. `WWW-Authenticate` uvidí jen neautentizovaný MCP request. Grok a Cursor posílají platný Bearer a hlavičku nedostanou. REST ji nedostane, takže hub a n8n discovery nespustí.

12. CIMD obsahuje grant `jwt-bearer`. Neimplementuje se. Enterprise Managed Auth / auto-connect tímhle konektorem nepoběží.

13. Claude Code loopback je schválně zamítnutý (A6). Org connector na claude.ai, Desktopu, mobilu a Coworku používá HTTPS callback, ne loopback.

14. Cookie callback pořád vypisuje allowlist do HTML 403. MCP stránka to nedělá. Stará stránka se v téhle změně nepřepisuje.

15. Vrácení e-mailu do allowlistu oživí neodvolaný grant (A5). Kdo chce tvrdý stop, použije CLI revoke.

16. Auditní řádek neříká, jestli service volal Cursor, Grok, hub, dashboard nebo n8n. To je záměr R11.

17. `tools/list` ukáže i nástroje mimo scope. Odmítnutí je až při volání (B42). Claude může write nástroj zkusit a dostat `insufficient_scope`. Lukáš má oba scope, takže to u něj nenastane.

## Otevřené otázky pro uživatele

Q1 — Má se `allow_focus_write` pro `ServicePrincipal` nově zakázat? Předpoklad A2: ne, dnešní A1 z 12. 10. 2026 a test `test_b2_service_principal` zůstávají, protože service token se nemění. Kdybys řekl ano, Cursor a Grok přijdou o `apply_focus`, dokud nebudou mít vlastní lidský principal, a T17 se přepíše.

Q2 — Má Brain přijmout i Claude Code loopback (`http://localhost` a `http://127.0.0.1` s libovolným portem)? Předpoklad A6: ne, redirect host jen `claude.ai` a `claude.com`. Kdybys řekl ano, přibude port-agnostic výjimka jen pro ty dva loopback hosty a T6 přestane loopback odmítat. Org connector na claude.ai to nepotřebuje.

Q3 — Stačí odvolání grantu přes `python -m app.oauth_mcp_revoke` v kontejneru, bez HTTP endpointu? Předpoklad A5: ano. Kdybys chtěl HTTP, přibude autentizovaná route jen pro service token nebo cookie a nové B#/T#, aby ji nešlo zavolat Claude access tokenem.
