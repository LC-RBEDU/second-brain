# Plán: MCP OAuth pro Claude connector

## Zadání a požadavky

R1 — Org connector v Claude Team bez sdíleného bearer tokenu. Každý člen se autentizuje sám. Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá. Zdroj: brief varianta A + rozhodnutí „org connector se do Claude organizace přidá až po lidském testu“.

R2 — Allowlist je jen `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní Gmail neprojde. Stejný seznam jako dnešní cookie OAuth. Zdroj: rozhodnutí z konverzace.

R3 — Rozsah je jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Tokeny se nedělí. Audit starých IP se nedělá. Zdroj: rozhodnutí z konverzace.

R4 — Úložiště tokenů je nový SQLite soubor na druhém Coolify persistent volume. Není to vault a nesmí ležet v `/data/vault` (host `/data/second-brain-vault`). Cesta: host `/data/second-brain-oauth`, v kontejneru `/data/oauth`. Google Drive ani Mac disk se nepoužijí. Restart ani deploy nesmí odhlásit Claude. Replicas Brainu zůstávají 1. Zdroj: rozhodnutí z konverzace.

R5 — Dnešní cookie OAuth (`/oauth/authorize`, `/oauth/callback`, cookie `sb_brain_session`) zůstává. Claude ho jako MCP OAuth nepoužije. Zdroj: rozhodnutí z konverzace.

R6 — Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi: `https://brain.cyprovi.cz/oauth/mcp/callback`. Přidání URI do Google konzole je ruční krok člověka, ne skript. Token POST z MCP callbacku posílá Google právě tuhle `redirect_uri`, ne `{public}/oauth/callback`. Zdroj: rozhodnutí z konverzace + nález C2.

R7 — Registrace klienta oběma cestami, aby seděl dialog Claude: Dynamic Client Registration (RFC 7591) a Client ID Metadata Document („Use Claude's published identity“). Redirect host jen `claude.ai` a `claude.com`, včetně `https://claude.ai/api/mcp/auth_callback` a `https://claude.com/api/mcp/auth_callback`. V connectoru žádný secret. Zdroj: rozhodnutí z konverzace. Ověřeno v dokumentaci Claude (11. 11. 2026) a na živém CIMD `https://claude.ai/oauth/mcp-oauth-client-metadata`: `client_name` je `Claude`, `token_endpoint_auth_method` je `none`, redirect je jen `https://claude.ai/api/mcp/auth_callback`. Claude CIMD vybere, jen když metadata authorization serveru mají `client_id_metadata_document_supported: true` a v `token_endpoint_auth_methods_supported` je `none`. Jinak padá na DCR. `private_key_jwt` se neinzeruje.

R8 — Brain vydává vlastní neprůhledné tokeny. V úložišti jen hash. Access krátký, refresh delší, obojí odvolatelné. PKCE S256, granty `authorization_code` a `refresh_token`. Token endpoint bere `application/x-www-form-urlencoded`. Neplatný refresh je `invalid_grant` a refresh se rotuje. Zdroj: rozhodnutí + dokumentace Claude (token refresh, latence discovery/token 10 s, refresh 30 s).

R9 — Každý požadavek znovu ověří allowlist. Odebrání e-mailu nebo smazání tokenu zastaví další volání. Service token se tím nemění. Zdroj: rozhodnutí z konverzace.

R10 — Scope `brain:read` a `brain:write`. Lukáš dostane oba, když o ně klient požádá nebo scope vynechá. Nástroj mimo scope se odmítne. Mapa scope je totální: každé jméno `@mcp.tool` má klíč a chybějící klíč je odmítnutí, funkce se nespustí. Zdroj: rozhodnutí z konverzace + nález C4.

R11 — Focus smí na pokyn člověka Grok, Cursor i Claude. `BRAIN_SERVICE_TOKEN` dál smí `apply_focus` (`allow_focus_write(ServicePrincipal)` se nezakazuje). Claude OAuth principal smí focus taky, prakticky `OAuthPrincipal` se scope `brain:write`. Samotný `brain:read` focus nezapisuje. Lukáš dostává oba scope, takže Claude na jeho účtu focus zapíše. „Pokyn člověka“ je dnešní tok `propose_focus` a pak `apply_focus`; nový příznak souhlasu se nezavádí. Zdroj: rozhodnutí uživatele „Omezení neplatí - focus můžou na pokyn člověka řešit i Grok / Cursor / Claude.“ (uzavírá C1).

R12 — Audit: jeden JSON řádek na stdout Brainu (identita, klient z registrace, nástroj, čas, výsledek). Do git vaultu se nezapisuje. U service tokenu je identita přesně `service`, protože jeden token pořád sdílí Cursor, Grok, hub, dashboard a n8n. Zdroj: rozhodnutí z konverzace.

R13 — MCP bez platného tokenu: `401` a `WWW-Authenticate` s odkazem na `/.well-known/oauth-protected-resource`. REST pro cron (hub, n8n) zůstává na dnešním JSON `401` bez nucení OAuth discovery. Pole `resource` se rovná URL, kterou člověk zadá do Claude, včetně lomítka: `https://brain.cyprovi.cz/mcp/`. Zdroj: rozhodnutí z konverzace.

R14 — Po Google loginu e-mail mimo allowlist: stránka „přístup zamítnut“ a redirect do Claude s `access_denied`. Žádný token. Redirect nese `state`, který Claude poslal na authorize, ne `state`, který Google vrátil (to je id transakce). Zdroj: rozhodnutí z konverzace + nález C2.

R15 — `get_context` pro OAuth principal s pouhým `brain:read` smí jen warm větev (`brain_vault(mode="read")`, `commit_on_end` je tam false). Když `needs_rebuild` je true, vrátí chybu a `mode="rebuild"` neotevře, tedy 0 commitů. Rebuild smí `OAuthPrincipal`, který má `brain:write` (Lukáš ho má). Service token, cookie session, dev a REST `get_context` rebuildují jako dnes. Zdroj: nález C3, kód `get_context.py:45-70` a `vault_deps.py:137-153`.

R16 — Org connector se přidá až po lidském testu: Lukáš v claude.ai dokončí Sign in now a vidí nástroje; druhý účet z organizace mimo allowlist token nedostane. Ten test není pytest a není `rbu-tester`. Zdroj: rozhodnutí z konverzace + profil SECOND_BRAIN.

R17 — Žádné odhady effortu. `P` je výkonový rozpočet v milisekundách a počtu dotazů, ne čas práce. Zdroj: rozhodnutí z konverzace.

R18 — Nové tokeny nesmí záviset na tom, že prázdný `BRAIN_SESSION_SECRET` spadne na `BRAIN_SERVICE_TOKEN`. Cookie serializer se nemění. Zdroj: omezení v briefu pipeline.

Mimo rozsah: dělení a rotace service tokenu; audit historických volání; dashboard OAuth a přechod Groku a Cursoru na OAuth; zápis OAuth secretů nebo auditů do git vaultu; nový project hub; `AGENTS.md`; Enterprise Managed Auth (`jwt-bearer` z CIMD dokumentu); Claude Code loopback (Q1); vizuální gate dashboardu. Alembic, RBAC, subnav, dlaždice, `qa_gate.mjs`, Celery a React se této změny netýkají.

## Předpoklady

A1 — Vlastní tenká vrstva nad stdlib `sqlite3` + stávající `httpx`. Authlib se nepřidává. V `requirements.txt` není a CIMD, hash tokenů a oddělení od cookie session by se v něm stejně psaly ručně.

A2 — Vynechaný `scope` na authorize u allowlist e-mailu znamená oba scope. Požádá-li klient jen o jeden, dostane jen ten. `offline_access` se neinzeruje a když přijde, zahodí se; refresh token se vydá vždy u `authorization_code`. `brain:write` neimplikuje `brain:read`.

A3 — Cookie session na MCP zůstává a má implicitně oba scope (dnešní plný přístup, včetně rebuildu `get_context` a fokusu). OAuth access token z nového flow se na REST `/v1/*` nepřijímá. REST `get_context` ContextVar nenastavuje, takže se ho brána v R15 netýká.

A4 — Odebrání e-mailu z allowlistu zastaví volání hned, ale řádek grantu se nesmaže. Vrácení e-mailu do kódu allowlistu nepoužitý a neodvolaný grant znovu pustí. Odvolání grantu (CLI) je trvalé do nového loginu. Veřejný revoke endpoint se nedělá.

A5 — Redirect Claude se povolí jen jako přesná shoda s URI z DCR nebo CIMD, a jen když host je přesně `claude.ai` nebo `claude.com`, schéma `https`, bez userinfo, bez fragmentu, bez jiného portu. Jakákoli cizí URI v seznamu shodí celou registraci. `localhost` / `127.0.0.1` se zamítnou. Claude Code tedy tímhle plánem OAuth nedokončí (Q1).

A6 — Publikované `resource` je `{BRAIN_PUBLIC_URL}/mcp/` s koncovým lomítkem. Při srovnání se jedno koncové lomítko ignoruje. Cizí resource se odmítne.

A7 — TTL: authorize transakce 10 min, authorization code 60 s, access 3600 s, refresh 30 dní od vydání (rotace posune jen nový refresh), absolutní strop grantu 90 dní od vytvoření. Časy v UTC. `expires_at <= now` je vypršelé. Pepper je `BRAIN_OAUTH_TOKEN_PEPPER` (HMAC-SHA256). Chybějící pepper nepadá na service token.

A8 — SQLite se neotevírá při importu ani při úspěšném service-token requestu. Chybějící volume neshodí lifespan. Metadata a `401` jedou i bez databáze. Authorize, register a token bez zapsatelné DB nebo pepperu vrací `503`.

A9 — Re-run celého `setup-coolify.sh` na živé aplikaci se pro tuhle změnu nespouští. Volume přidá malý idempotentní skript. Plný setup skript dostane stejný INSERT jen pro novou instalaci.

A10 — Produkční počet řádků OAuth DB nejde změřit: soubor ještě neexistuje. Strop na dva roky je jeden člověk, pod 500 DCR klientů, pod 100 grantů. Dotaz po nasazení, není to gate: v kontejneru `sqlite3 /data/oauth/brain-oauth.sqlite 'SELECT COUNT(*) FROM oauth_tokens;'`.

A11 — Stránka zamítnutí je HTTP 200 HTML se statickým textem „Přístup zamítnut.“ a `meta refresh` 0 na Claude `redirect_uri` s `error=access_denied`, uloženým Claude `state` a `iss`. E-mail ani allowlist se na stránku nevypisují. Úspěch je HTTP 302, bez cookie `sb_brain_session`.

Focus už není předpoklad. Je to R11, uzavřené rozhodnutím uživatele.

## Současný stav (ověřeno v kódu)

`vps/second-brain-brain/app/auth_google.py:9-14` — `ALLOWLIST` je přesně ty dva e-maily. `email_allowed` je case-insensitive. `authorize_url` (`49-67`) posílá `prompt=select_account` a neposílá `hd`. `oauth_callback_url` (`24-33`) je vždy `{BRAIN_PUBLIC_URL}/oauth/callback`.

`vps/second-brain-brain/app/oauth_routes.py:91-99` — výměna kódu u Google posílá `redirect_uri: cfg.callback_url`, tedy cookie callback `/oauth/callback`. MCP callback, který by tenhle POST zkopíroval, dostane od Google `redirect_uri_mismatch`, protože authorize půjde na `/oauth/mcp/callback`. Cizí e-mail je HTTP 403 a v těle je vypsaný allowlist (`113-117`). `BRAIN_SESSION_SECRET` při prázdnu padá na `BRAIN_SERVICE_TOKEN` (`25-29`). Route `/oauth/mcp/*` dnes nejsou.

`vps/second-brain-brain/app/mcp_auth.py:14-65` — MCP pustí cookie e-mail, nebo Bearer shodný s `BRAIN_SERVICE_TOKEN`, nebo dev bez tokenu. Jinak JSON `401` s `error_reason: client_error`. `WWW-Authenticate` se nenastavuje. Cookie vyhraje nad Bearerem.

`vps/second-brain-brain/app/auth_deps.py:17-49` — REST je cookie, nebo service Bearer, nebo dev. Cizí Bearer je `401` bez OAuth hlavičky. REST nenastavuje ContextVar principalu.

`vps/second-brain-brain/app/auth_service.py:26-36` — service token je `hmac.compare_digest` proti `BRAIN_SERVICE_TOKEN`. `ServicePrincipal.audit_id` vrací `service:service` a nikde jinde se nečte. Nový auditní řádek použije řetězec `service`.

`vps/second-brain-brain/app/policy.py:15-25` — `allow_focus_write` pouští `ServicePrincipal`, řetězec `oauth:…` i `dev`. Tohle zůstává.

`vps/second-brain-brain/app/tools/set_focus.py:122-136` — bez `via_apply=True` je vždy `403 focus_requires_proposal` a nic se nezapíše. Zápis jde jen přes `apply_focus`.

`vps/second-brain-brain/app/tools/get_context.py:45-70` — nejdřív `brain_vault(mode="read")`. Když `needs_rebuild` je false, vrátí `mode: warm`. Když je true, otevře `brain_vault(mode="rebuild")` a `build_and_write_context_bundle`. Scope principalu nezná.

`vps/second-brain-brain/app/vault_deps.py:137-153` — `mode="read"` má `commit_on_end: False`. `mode="rebuild"` i `mutate` mají `commit_on_end: True` a vždy fetch, dirty check a commit (`196-198`).

`vps/second-brain-brain/app/mcp_app.py` — 33 nástrojů přes `@mcp.tool`. Čtyři z nich nejdou přes `_call` a vnitřní funkci volají přímo: `update_task` (`110-118`), `export_tasks` (`222-227`), `bulk_update` (`394-398`), `finalize_meeting` (`457-467`). `get_task` (`254-259`) taky vrací `_error_result` mimo `_call`. `mailbox_apply` / `external_apply` (`508-532`) principal natvrdo staví jako `ServicePrincipal(label="mcp")`. `gate_brain_apply` pro service vrací 403 a pro řetězec `oauth:` 501 (`auth_apply.py:15-26`).

`vps/second-brain-brain/app/main.py:90-95` a `142-143` — MCP je mount `/mcp` obalený `McpAuthMiddleware`. Cookie router je na appce. Lifespan spadne jen když chybí `GIT_VAULT_PUSH` a není `BRAIN_ALLOW_NO_PUSH`.

`vps/second-brain-brain/requirements.txt` — fastapi, httpx, itsdangerous, mcp, google-auth-oauthlib. Authlib tam není. `sqlite3` je ve stdlib.

`vps/second-brain-brain/Dockerfile` — jeden proces `uvicorn` bez `--workers`, user root, žádný volume v image.

`vps/second-brain-brain/deploy/setup-coolify.sh:103-107` — idempotentní INSERT jen pro `mount_path=/data/vault`. Skript taky queueje deploy a sahá na env.

`docs/brain-api-runbook.md:150-153` — kanonická MCP URL je `https://brain.cyprovi.cz/mcp/` s lomítkem.

Živý CIMD (11. 11. 2026): `client_id` = `https://claude.ai/oauth/mcp-oauth-client-metadata`, granty zahrnují i `urn:ietf:params:oauth:grant-type:jwt-bearer`. Ten grant se neimplementuje.

## Návrh

Netýká se: Alembic, SQLAlchemy, RBAC, Celery, React, `api.ts`, subnav, hub dlaždice, `scripts/qa_gate.mjs`, Allfred, Pipedrive, Fakturoid, Fio. Žádná nová závislost.

### Úložiště

Nový `vps/second-brain-brain/app/oauth_mcp_store.py`. Soubor z `BRAIN_OAUTH_DB`, default `/data/oauth/brain-oauth.sqlite`. Lazy otevření, WAL, `busy_timeout` 5000, `check_same_thread=False`, zápisy v `BEGIN IMMEDIATE`.

Cesta, jejíž `realpath` leží v `GIT_VAULT_ROOT` nebo pod `/data/vault`, se neotevře. Zápisové OAuth route pak vrací `503` (R4).

Tabulky:

- `oauth_clients` — `client_id` PK, `client_name`, `redirect_uris_json`, `source` (`dcr`|`cimd`), `created_at`. Žádný secret.
- `oauth_transactions` — `id` (tohle jde Google jako `state`), `claude_state` (tohle přišlo od Claude a jen tohle se vrací), `client_id`, `redirect_uri`, `code_challenge`, `scope`, `resource`, `auth_code_hash`, expirace, `consumed_at`. Dva state se nesmí slít do jednoho sloupce.
- `oauth_grants` — family id, `client_id`, `client_name`, `email`, `scope`, `resource`, `created_at`, `revoked_at`.
- `oauth_tokens` — `token_hash` PK (HMAC-SHA256 hex pepperem), `grant_id`, `kind` (`access`|`refresh`), `expires_at`, `revoked_at`, `replaced_by_hash`, `created_at`.
- `cimd_cache` — URL, JSON, `fetched_at`. TTL čtení 1 hodina. Na MCP request se nečte.

`revoke_grants_for_email(email)` a CLI `python -m app.oauth_mcp_revoke <email>` jen nad SQLite, bez HTTP.

Pepper jen z `BRAIN_OAUTH_TOKEN_PEPPER`. Prázdný pepper: OAuth zápisové route `503` (R18).

### Metadata a 401

Nový `vps/second-brain-brain/app/oauth_mcp_metadata.py`, v `main.py` před mountem MCP, bez autentizace:

- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-protected-resource/mcp` — stejné JSON

`resource` = `{public}/mcp/`, `authorization_servers` = jednoprvkový issuer (`BRAIN_PUBLIC_URL` bez koncového lomítka), `scopes_supported` = `brain:read`, `brain:write`, `bearer_methods_supported` = `header`. `offline_access` tam není.

- `GET /.well-known/oauth-authorization-server` — issuer, `authorization_endpoint` `/oauth/mcp/authorize`, `token_endpoint` `/oauth/mcp/token`, `registration_endpoint` `/oauth/mcp/register`, `response_types_supported` `code`, `grant_types_supported` `authorization_code` + `refresh_token`, `code_challenge_methods_supported` `S256`, `token_endpoint_auth_methods_supported` jen `none`, `client_id_metadata_document_supported` true, `authorization_response_iss_parameter_supported` true. Bez `private_key_jwt`.

`McpAuthMiddleware`: každý MCP `401` dostane

`WWW-Authenticate: Bearer resource_metadata="{issuer}/.well-known/oauth-protected-resource", scope="brain:read brain:write"`

Tělo JSON zůstává `{"error_reason":"client_error","message":"authentication required"}` (u API key dnešní text). Hlavička není na `200` ani na tool error. REST `HTTPException` hlavičku nedostane.

Pořadí: `X-API-Key` → cookie (`read_session_email`, principal řetězec `oauth:{email}`, oba scope, bez SQLite) → `hmac` service token (bez SQLite, `ServicePrincipal`) → HMAC access tokenu a jeden SELECT podle PK → dev jako dnes. Selhání SQLite u neznámého Beareru je `401`, ne `500`. Service token při rozbité SQLite projde.

`OAuthPrincipal` v `app/oauth_mcp_principal.py`: `email`, `scopes`, `client_id`, `client_name`. `__str__` vrací `oauth:{email}`. `allow_focus_write` ho pustí, když má `brain:write`, a větev `ServicePrincipal` nechá allowed (R11). `gate_brain_apply` ho pustí stejnou větví jako řetězec `oauth:` → 501.

### DCR, CIMD, authorize, token

Nový router `vps/second-brain-brain/app/oauth_mcp_routes.py`. `auth_google.py` dostane `oauth_mcp_callback_url` = `{public}/oauth/mcp/callback`. Cookie `oauth_callback_url` se nemění a MCP handler ji do Google POST nedá. `authorize_url` se znovupoužije, `hd` se nepřidává.

Redirect URI: `https`, host přesně `claude.ai` nebo `claude.com`, bez userinfo, fragmentu a cizího portu. Jedna špatná URI shodí celou registraci.

`POST /oauth/mcp/register` JSON, max 8 KiB, `201`, `client_id` = `brain_` + `token_urlsafe`, `token_endpoint_auth_method: none`, v odpovědi ani v DB žádný secret. Strop 500 klientů, pak `429`.

CIMD: `client_id` je `https` URL na těch dvou hostech, bez query, fragmentu a userinfo. `httpx` timeout 5 s, `follow_redirects=False`, tělo max 64 KiB. JSON `client_id` se rovná URL. `token_endpoint_auth_method` je `none` nebo chybí. Cache 1 h. Grant `jwt-bearer` v dokumentu klienta neodmítne; na token endpointu je `unsupported_grant_type`.

`GET /oauth/mcp/authorize`: `response_type=code`, PKCE jen `S256`, klient z DCR nebo CIMD, `redirect_uri` přesná shoda. Špatná `redirect_uri` → `400` a žádný `Location`. Platná URI a špatné PKCE nebo scope → `302` s `error=invalid_request` nebo `invalid_scope`, `state` = Claude state z query (ne id transakce), plus `iss`. Resource se uloží; cizí resource → `invalid_target`. V SQLite vznikne transakce: `id` je nové `token_urlsafe`, `claude_state` je query `state` od Claude. Prohlížeč jde na Google s `redirect_uri={public}/oauth/mcp/callback` a `state={transaction.id}`. Žádná cookie.

`GET /oauth/mcp/callback` nesdílí funkci `oauth_callback`. Query `code` a query `state` (to je `transaction.id`) načtou řádek. Google POST na `https://oauth2.googleapis.com/token` má `redirect_uri` přesně `oauth_mcp_callback_url`, timeout 20 s, pak userinfo. Do žádného redirectu na Claude se query `state` od Google nekopíruje.

- Allowlist e-mail → authorization code (v DB jen hash, TTL 60 s) a `302` na Claude `redirect_uri` s `code`, `state={transaction.claude_state}`, `iss`.
- E-mail mimo allowlist, `verified_email is false` nebo prázdný e-mail → žádný grant, HTML „Přístup zamítnut.“ a meta refresh na Claude s `error=access_denied` a `state={transaction.claude_state}`.
- Google 5xx nebo timeout → žádný token; u známé transakce redirect `error=server_error` se stejným uloženým Claude state, jinak `400`.

`POST /oauth/mcp/token` jen form body. `authorization_code`: jednorázový kód, shoda `redirect_uri` s tou uloženou (Claude callback, ne Google callback), PKCE S256, resource shodný až na jedno lomítko. Replay spotřebovaného kódu je `invalid_grant`. `refresh_token`: rotace v jedné transakci; opakované předložení starého refreshe odvolá family a vrátí `invalid_grant`. Allowlist se kontroluje znovu. Vypršelý, odvolaný, nebo grant starší 90 dní je `invalid_grant`. `client_secret` se ignoruje. `client_credentials` a `jwt-bearer` jsou `unsupported_grant_type`. Odpověď: `token_type=Bearer`, `expires_in=3600`, nový refresh, scope jen `brain:read` / `brain:write`.

### Scope, get_context, audit

`app/mcp_scopes.py` — jeden slovník `TOOL_SCOPES`. Žádný default „když klíč chybí, pustit“. `scope_denial(tool_name)` pro `OAuthPrincipal`: klíč chybí, nebo požadovaný scope v principalu není → MCP `isError` s `error_reason: insufficient_scope` a volající funkci nespustí. Service, cookie řetězec `oauth:` a `dev` vrací None (brána je nepustí do mapy).

`brain:read` (13): `get_context`, `read_file`, `list_dir`, `export_tasks`, `find_tasks`, `get_task`, `list_children`, `get_tree`, `list_reminders`, `get_triage_candidates`, `slack_live`, `get_meeting_prep`, `allocate_task_id`.

`brain:write` (20): `update_task`, `append_task_note`, `set_focus`, `propose_focus`, `apply_focus`, `edit_task_body`, `toggle_step`, `close_task`, `create_task`, `bulk_update`, `schedule_reminder`, `cancel_reminder`, `finalize_meeting`, `ingest_sembly`, `capture_daily`, `mailbox_propose`, `mailbox_apply`, `external_propose`, `external_apply`, `prepare_meeting`. `dry_run` scope nesnižuje.

Každý `@mcp.tool` v `mcp_app.py` zavolá `scope_denial` jako první vykonatelný krok, před `json.loads` a před vnitřní funkcí. Týká se i `update_task`, `export_tasks`, `bulk_update`, `finalize_meeting` a `get_task`. `mailbox_apply` a `external_apply` přestanou vyrábět `ServicePrincipal(label="mcp")` a předají `get_brain_principal()`, ale až po `scope_denial`.

`get_context` zůstává v read mapě, aby warm šel bez write. Uvnitř `get_context.py`, až po read sondě a jen když `needs_rebuild` je true: pokud `get_brain_principal()` je `OAuthPrincipal` a nemá `brain:write`, vyhodit `BrainClientError` (`403`, `error_reason: context_rebuild_requires_write`) a neotevírat `mode="rebuild"`. `ServicePrincipal`, řetězec `oauth:`, `dev` a `None` (REST) jdou do dnešního rebuildu. `OAuthPrincipal` s `brain:write` taky. MCP `_call` z té chyby udělá `isError`, HTTP 200, žádný commit.

`app/mcp_audit.py` — logger `brain.mcp.audit`, `propagate False`, handler na stdout, formát jen `%(message)s`. Jeden JSON: `ts` (UTC), `identity`, `client_id`, `client_name`, `tool`, `result` (`ok`|`error`|`denied`), `error_reason`. Bez argumentů a bez tokenu. U service je `identity` přesně `service` a oba client fieldy null.

### Nasazení a docs

`deploy/add-oauth-volume.sh` na coolify-dev: `mkdir -p /data/second-brain-oauth`, `chmod 700`, idempotentní INSERT `local_persistent_volumes` (`mount_path=/data/oauth`, `host_path=/data/second-brain-oauth`). Nesahe na env, netiskne secret, nedeployuje. Mount se chytí restartem aplikace.

Do `setup-coolify.sh` stejný INSERT hned za vault volume a komentář, že živá appka má malý skript.

`config.example.env` — zakomentované `BRAIN_OAUTH_DB` a `BRAIN_OAUTH_TOKEN_PEPPER`. Pepper jednou v Coolify UI, není odvozený ze service tokenu.

`docs/brain-api-runbook.md` — endpointy, resource URL s lomítkem, že Google token POST MCP flow používá `/oauth/mcp/callback`, volume, pepper, ruční redirect URI, CLI revoke, repliky 1, connector až po T-H1. Odstavec o service tokenu zůstane.

Ruční kroky člověka: (1) volume a restart, (2) pepper, (3) redirect URI v Google konzoli, (4) connector až po T-H1.

## Kontrakt chování (B#)

Checklist A, co tu není samostatný řádek: fiskální rok a měny se netýkají, OAuth nemá částky ani FY. Sync Allfred/Pipedrive se netýká. `backend/app/services/data_consistency.py` se netýká, tohle není RB Universe; invariant je B6, B7 a B52 (service token beze změny, DB mimo vault).

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | `POST /mcp` a `POST /mcp/` bez Authorization | `401`, JSON `error_reason=client_error`, `WWW-Authenticate` obsahuje `resource_metadata` a `scope="brain:read brain:write"`. Hlavička není na `200`. | R13 | T1 |
| B2 | `GET /v1/context` bez cookie a bez Beareru | `401`, `WWW-Authenticate` chybí | R3, R13 | T2 |
| B3 | `GET /healthz` a oba well-known GET bez tokenu | `200` | R13 | T3 |
| B4 | Protected resource metadata | `resource` je `{BRAIN_PUBLIC_URL}/mcp/` včetně lomítka; `authorization_servers` má jediný prvek | R13 | T3 |
| B5 | Authorization server metadata | DCR, CIMD true, `none`, S256, granty code+refresh. Není tam `private_key_jwt` ani `offline_access` | R7, R8 | T3 |
| B6 | MCP `initialize` s platným service tokenem, SQLite chybí nebo je rozbitá | není `401` ani `500`; SQLite se neotevírá | R3, R9 | T4 |
| B7 | `BRAIN_OAUTH_DB` uvnitř `GIT_VAULT_ROOT` nebo `/data/vault` | zápisové OAuth route `503`, soubor nevznikne | R4 | T5 |
| B8 | Prázdná DB, chybí pepper nebo adresář | metadata `200`; register, authorize a token `503`; lifespan naběhne; service MCP projde | R4, R18 | T5 |
| B9 | DCR s oběma auth_callback URI | `201`, žádný `client_secret` v těle ani v DB | R7 | T6 |
| B10 | DCR s cizím hostem, `http://claude.ai/...`, `www.claude.ai`, userinfo, nebo mix dobré a zlé URI | `400`, 0 nových klientů | R7 | T6 |
| B11 | DCR nebo authorize s `http://localhost/callback` nebo `http://127.0.0.1:<port>/callback` | odmítnuto, kód se nevydá | R7 | T6 |
| B12 | CIMD jako živý dokument (mock), redirect jen claude.ai callback | authorize klienta přijme, fetch bez redirectů | R7 | T7 |
| B13 | CIMD s cizím redirectem, neshodou `client_id`, nebo jiným hostem | `invalid_client` | R7 | T7 |
| B14 | CIMD URL vrátí redirect, timeout nebo 5xx | redirect se nesleduje; klient odmítnut; token není | R7 | T7 |
| B15 | Token request s neprázdným `client_secret` | secret se nekontroluje a neukládá; platný code projde | R7 | T8 |
| B16 | Authorize bez PKCE, method `plain`, nebo bez `code_challenge` | při platné redirect URI `302 error=invalid_request` a `state` je Claude state; kód v DB není | R8 | T8 |
| B17 | Platné S256, allowlist e-mail, scope vynechaný | oba scope, access + refresh, v DB jen HMAC; raw token v souboru není | R2, R8, R10 | T8 |
| B18 | Špatný `code_verifier` | `invalid_grant`, tokeny nejsou | R8 | T8 |
| B19 | Stejný authorization code podruhé | `invalid_grant`, druhá sada nevznikne | R8 | T8 |
| B20 | Kód starší než 60 s, nebo transakce starší než 10 min | kód: `invalid_grant`. Transakce: žádný token; redirect `invalid_request` se uloženým Claude state, pokud URI známe | R8 | T9 |
| B21 | Token exchange s jinou `redirect_uri`, než šla na authorize | `invalid_grant` | R7 | T8 |
| B22 | Authorize s `redirect_uri` mimo registraci klienta | HTTP `400`, `Location` na tu URI neukazuje | R7 | T6 |
| B23 | Oba allowlist e-maily, jiná velikost písmen, scope oba nebo vynechaný | tokeny, scope oba. Google authorize URL nemá `hd` | R2, R10 | T10 |
| B24 | Scope jen `brain:read` | v tokenu jen read | R10 | T10 |
| B25 | Scope jen `foo` | `invalid_scope`, token není | R10 | T10 |
| B26 | Scope obsahuje `offline_access` a `brain:read` | uložený scope je jen `brain:read`; refresh v odpovědi je | R8, R10 | T10 |
| B27 | Userinfo mimo allowlist | HTTP 200 HTML obsahuje „Přístup zamítnut.“, neobsahuje e-mail ani allowlist; meta refresh má `error=access_denied`; grant ani token v DB není; cookie `sb_brain_session` není | R14 | T11 |
| B28 | `verified_email: false` nebo prázdný e-mail | stejné jako B27 | R2, R14 | T11 |
| B29 | Google token endpoint timeout nebo 5xx | žádný token; u známé transakce redirect `error=server_error` | R8 | T11 |
| B30 | `GET /oauth/callback` cizí e-mail | pořád `403`; MCP route se nezavolá; Google POST pořád používá `/oauth/callback` | R5 | T12 |
| B31 | `GET /oauth/authorize` | redirect na Google s `/oauth/callback`, ne s `/oauth/mcp/callback` | R5, R6 | T12 |
| B32 | Access s `expires_at <= now` na MCP | `401` + `WWW-Authenticate`, nástroj neběží | R8, R9 | T13 |
| B33 | Grant odvolaný CLI nebo smazaný řádek tokenu | MCP `401`; refresh `invalid_grant` | R8, R9 | T13 |
| B34 | Platný refresh | nový access i refresh; starý refresh pak `invalid_grant` a family je odvolaná | R8 | T14 |
| B35 | Dva souběžné refreshe téhož tokenu | právě jedna úspěšná odpověď; druhá `invalid_grant` | R8 | T14 |
| B36 | E-mail zmizel z allowlistu | MCP `401`; refresh `invalid_grant`; service token funguje | R9 | T15 |
| B37 | E-mail se vrátí, grant nebyl odvolaný a nevypršel | stejný access znovu projde | R9 | T15 |
| B38 | Grant starší než 90 dní | `invalid_grant` | R8 | T13 |
| B39 | Resource `…/mcp` i `…/mcp/` | přijato. Jiná URL | `invalid_target` | R13 | T8 |
| B40 | Token endpoint s JSON tělem | `400` nebo `415`, token není | R8 | T8 |
| B41 | Grant `client_credentials` nebo jwt-bearer | `unsupported_grant_type` | R8 | T8 |
| B42 | OAuth jen `brain:read`, write nástroj včetně `create_task`, `update_task`, `bulk_update`, `finalize_meeting` | HTTP 200, `isError`, `insufficient_scope`, vnitřní funkce se nezavolá. Není to `401` | R10 | T16 |
| B43 | OAuth jen `brain:write`, read nástroj včetně `read_file` a `export_tasks` | `insufficient_scope`, vnitřní funkce se nezavolá | R10 | T16 |
| B44 | `OAuthPrincipal` s `brain:write` (Lukáš má i read), `apply_focus` | `allow_focus_write` pustí. Zápis do vaultu tenhle test nevolá, jen bránu. `propose_focus` před `apply_focus` zůstává | R11 | T17 |
| B45 | Service token, `apply_focus` i ostatní nástroje | scope mapa se neaplikuje; `allow_focus_write(ServicePrincipal)` zůstává allowed | R3, R11 | T4, T17 |
| B46 | Cookie `sb_brain_session` allowlist e-mailu na MCP | projde jako dnes, oba scope implicitně, focus i rebuild smí | R5, R11, R15 | T18 |
| B47 | OAuth access token na `GET /v1/context` | `401` | R3 | T2 |
| B48 | `str(OAuthPrincipal)` a `mailbox_apply` / `external_apply` | principal `oauth:<email>`; brána → 501. Service → pořád 403. Natvrdo `ServicePrincipal(label="mcp")` zmizí | R10 | T19 |
| B49 | `tools/call` OAuth i service | jeden stdout JSON řádek. OAuth: `identity=oauth:<email>`, `client_name` z registrace. Service: `identity=service`, client fieldy null. Bez argumentů a bez tokenu. Do vaultu se nezapíše | R12 | T20 |
| B50 | `X-API-Key` na MCP | `401` + `WWW-Authenticate` | R13 | T1 |
| B51 | Dev bez service tokenu a s `BRAIN_ALLOW_NO_PUSH` | principal `dev`; import testů neotevírá OAuth DB | R3 | T4 |
| B52 | Úspěšný MCP login | nenastaví `sb_brain_session` a hash neleží ve vaultu | R4, R5 | T8, T5 |
| B53 | Stránka zamítnutí | HTML v `/oauth/mcp/callback`, ne dashboard; text „Přístup zamítnut.“ je v těle | R14, R16 | T11 |
| B54 | MCP callback vymění kód u Google | POST `redirect_uri` je přesně `{BRAIN_PUBLIC_URL}/oauth/mcp/callback`. Není to `cfg.callback_url`. Authorize URL na Google má tutéž `redirect_uri` a `state` rovný id transakce, jiné než Claude state | R6 | T8, T11 |
| B55 | Úspěšný `302` i zamítací meta refresh na Claude | query `state` je `claude_state` uložený při authorize. Není to query `state` z návratu od Google | R14 | T8, T11 |
| B56 | `OAuthPrincipal` jen s `brain:read`, `needs_rebuild` false | odpověď `mode: warm`. `brain_vault` jen `mode="read"`. `mode="rebuild"` se nezavolá | R15 | T21 |
| B57 | `OAuthPrincipal` jen s `brain:read`, `needs_rebuild` true | `BrainClientError` `context_rebuild_requires_write`. `brain_vault(mode="rebuild")` se nezavolá. Commitů 0. Read sonda smí proběhnout (`commit_on_end` false) | R15 | T21 |
| B58 | `needs_rebuild` true a principal je `ServicePrincipal`, řetězec `oauth:`, `dev`, `None`, nebo `OAuthPrincipal` s `brain:write` | dnešní rebuild větev se otevře. REST handler principal nenastavuje, takže se ho B57 netýká | R15 | T21 |
| B59 | `TOOL_SCOPES` a jména `@mcp.tool` po `build_mcp()` | množiny se rovnají (33 jmen, 13 read + 20 write). `scope_denial("nastroj_ktery_neni")` vrátí `insufficient_scope` a předanou funkci nezavolá | R10 | T16 |
| B60 | Každý nástroj s `brain:write` a principal jen `brain:read` | wrapper vrátí `insufficient_scope` dřív, než se zavolá vnitřní funkce modulu. Stejná brána je první řádek i u `update_task`, `bulk_update` a `finalize_meeting` | R10 | T16 |

Prázdná data: B8. Chybějící e-mail a kód: B20, B28. Hranice expirace: B32, B38. Oprávnění: B23–B28, B36, B42–B48, B56–B60. Smazaný grant: B33, B36. Opakování: B19, B34, B35. Cizí služba: B14, B29, B54. Zpětná kompatibilita: B2, B6, B30, B31, B45, B46, B51, B58.

## Výkonový rozpočet (P)

Produkční OAuth tabulky dnes neexistují (A10). Strop za dva roky: pod 500 klientů, pod 100 grantů, pod 200 token řádků, soubor v řádu stovek KiB. Lookup access tokenu je jeden SELECT podle PK. Na cestě MCP nástroje není Google, Allfred ani CIMD. CIMD fetch je jen na authorize, timeout 5 s, pak cache 1 h. Token endpoint Google nevolá. Stránkování a frontend se netýkají. Payload metadat je pod 2 KiB, token odpověď pod 1 KiB, auditní řádek pod 500 B. Platnost tokenu se v procesu necachuje. Uvicorn zůstává jeden proces. Repliky se nenastavují nad 1.

Brána `scope_denial` je slovník v paměti, 0 SQL. `get_context` pro read-only a stale stav udělá jen dnešní read sondu (`mode="read"`, `commit_on_end` false) a rebuild neotevře, takže oproti dnešku jeden vault open ubude, nepřibude.

| Endpoint | SQL | Externí volání | Cíl | Měření |
|---|---|---|---|---|
| `GET` obou well-known | 0 | 0 | cold i warm pod 50 ms | T3 a QA curl `time_total` |
| `POST /oauth/mcp/register` | 1 INSERT | 0 | pod 50 ms | T6 |
| `GET /oauth/mcp/authorize` | 1 INSERT, u CIMD navíc 1 SELECT cache | CIMD jen při miss, timeout 5 s | cache hit pod 50 ms | T7 |
| `GET /oauth/mcp/callback` | 1 transakce | Google token + userinfo, timeout 20 s | lokální část pod 50 ms | T8, T11 mock |
| `POST /oauth/mcp/token` včetně refresh | 1 transakce, nejvýš 4 statementy | 0 | cold pod 50 ms, warm pod 20 ms | T8, T14 |
| MCP gate pro service token | 0 | 0 | přidaná režie pod 5 ms | T4 |
| MCP gate pro OAuth access + `scope_denial` | 1 PK SELECT, pak 0 | 0 | přidaná režie pod 15 ms | T13, T16 |

Anti-patterny checklistu B (Allfred blob, `Model.all()`, live GraphQL) se netýkají. Token se neověřuje načtením celé tabulky.

## Testy (T#)

Primární gate: `python3 -m pytest vps/second-brain-brain/tests -q`. Hub pytest se nespouští. `scripts/qa_*_ui.mjs` a Playwright T6 se nezakládají. `rbu-tester` se nevolá.

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-brain/tests/test_mcp_oauth.py` a doplnění `test_mcp_auth.py` | B1, B50. Starý JSON `401` zůstane, přibude hlavička |
| T2 | pytest | gate | oauth soubor | B2, B47 |
| T3 | pytest | gate | oauth soubor | B3, B4, B5 |
| T4 | pytest | gate | `test_mcp_auth.py` + oauth soubor | B6, B45 průchod, B51 |
| T5 | pytest | gate | oauth soubor | B7, B8, B52 cesta |
| T6 | pytest | gate | oauth soubor | B9, B10, B11, B22 |
| T7 | pytest | gate | oauth soubor, mock httpx | B12, B13, B14 |
| T8 | pytest | gate | oauth soubor, mock Google | B15–B19, B21, B39–B41, B52, B54, B55. Mock POST: `redirect_uri` rovna `{public}/oauth/mcp/callback`. Google authorize URL má tutéž `redirect_uri` a `state` = id transakce. `302` na Claude má `state` rovný tomu, co klient poslal na `/oauth/mcp/authorize`, a nerovný id transakce |
| T9 | pytest | gate | oauth soubor | B20 |
| T10 | pytest | gate | oauth soubor | B23, B24, B25, B26 |
| T11 | pytest | gate | oauth soubor | B27, B28, B29, B53, B54, B55. I při zamítnutí allowlistu šel Google POST na `/oauth/mcp/callback` a meta refresh nese uložený Claude state |
| T12 | pytest | gate | `test_mcp_and_oauth_routes.py`, `test_auth_b37.py` | B30, B31 |
| T13 | pytest | gate | oauth soubor | B32, B33, B38 |
| T14 | pytest | gate | oauth soubor | B34, B35 |
| T15 | pytest | gate | oauth soubor | B36, B37 |
| T16 | pytest | gate | oauth soubor | B42, B43, B59, B60. Jména vezme z nástrojů registrovaných `build_mcp()` (API, které server po `@mcp.tool` vystaví) a porovná je s `set(TOOL_SCOPES)`. Žádný druhý ruční seznam v testu. Pro každé write jméno nastaví `OAuthPrincipal` jen s `brain:read`, zavolá registrovaný wrapper a assertuje, že monkeypatch vnitřní funkce (`update_task`, `bulk_update`, `finalize_meeting` a zbylé write funkce) nebyl zavolaný. Samostatně `scope_denial` na neznámé jméno se sentinel callable, který se nesmí zavolat |
| T17 | pytest | gate | `test_set_focus.py` zůstává; oauth soubor | B44, B45. `allow_focus_write(ServicePrincipal)` allowed. `allow_focus_write(OAuthPrincipal` s `brain:write`)` allowed. `OAuthPrincipal` jen s `brain:read` se k `apply_focus` přes wrapper nedostane (T16) |
| T18 | pytest | gate | oauth soubor | B46 |
| T19 | pytest | gate | oauth soubor | B48 |
| T20 | pytest | gate | oauth soubor, capsys | B49 |
| T21 | pytest | gate | `vps/second-brain-brain/tests/test_get_context_scope.py` | B56, B57, B58. `needs_rebuild` se namockuje. Spy na `brain_vault`: u read-only a stale není volání `mode="rebuild"` a není commit. U service, cookie řetězce, `dev`, `None` a OAuth s `brain:write` se rebuild větev otevře |
| T-Q1 | curl proti `https://brain.cyprovi.cz` po deployi image `second-brain-brain` | QA | není nový skript | B1, B3, B4, B5, B6. Žádný zápis do vaultu. Service token z env, do chatu se nekopíruje |
| T-H1 | ruční v claude.ai | člověk, ne gate a ne Tester | — | R16. Google redirect URI, volume a pepper musí být hotové |

## Pořadí implementace

F1 — `oauth_mcp_store.py` se dvěma sloupci state, principal dataclass, pepper, zákaz cesty ve vaultu, CLI revoke.

F2 — metadata a `WWW-Authenticate`. Service větev bez SQLite.

F3 — DCR, CIMD, authorize, callback, token. Callback má vlastní Google POST s `oauth_mcp_callback_url`. Redirect na Claude čte jen `claude_state`. Cookie `oauth_routes.oauth_callback` se nevolá. Závisí na F1.

F4 — `TOOL_SCOPES`, `scope_denial` jako první řádek všech 33 nástrojů včetně čtyř, které dnes míjí `_call`, audit, `allow_focus_write` pro `OAuthPrincipal` s write bez zákazu service, `gate_brain_apply`, MCP apply bez natvrdo service principalu, brána rebuildu v `get_context.py`. Závisí na F1. Tokeny z F3 nejsou podmínka unit testu brány.

F5 — `add-oauth-volume.sh`, INSERT v `setup-coolify.sh`, `config.example.env`, runbook. Souběžně s F4, ve stejném diffu před pushem na `main`.

F6 — pytest T1–T21 a kontrola, že T12 zůstane zelený. Až po F2–F4.

F7 — člověk: volume a restart, pepper, Google redirect URI, pak T-H1, pak teprve connector v organizaci. Není to krok v gitu.

Push na `main` spustí Coolify deploy image Brain. Volume a pepper mají být na hostu před tím restartem, jinak OAuth route vrací `503` a service token žije dál. Hub image se nenasazuje.

## Rizika a zpětná kompatibilita

1. První deploy bez volume nebo pepperu: Claude login dostane `503`. Cursor, Grok, hub a n8n jedou dál.

2. Bez ručního redirect URI v Google konzoli produkční callback skončí `redirect_uri_mismatch`. Pytest to mockuje a hlídá, že POST neposílá `/oauth/callback` (B54).

3. Claude u custom connectoru defaultně vezme CIMD. Ten dokument zná jen `https://claude.ai/api/mcp/auth_callback`. `claude.com` projde přes DCR.

4. `resource` v metadatech musí mít koncové lomítko, protože takovou URL člověk zadá. Srovnání přijme i variantu bez něj.

5. Dva paralelní refreshe: druhý dostane `invalid_grant` a může odvolat family. Claude se znovu přihlásí.

6. Ztráta pepperu v Coolify env odhlásí Claude. Restart volume neodhlásí. Pepper se v téhle změně nerotuje.

7. Repliky nad 1 by SQLite rozbily. Runbook je nechá na 1.

8. Otevřené DCR je omezené hostem redirectu a stropem 500 řádků.

9. CIMD SSRF: jen dva hosti, žádné redirecty, timeout 5 s, strop těla 64 KiB.

10. `mailbox_apply` a `external_apply` přestanou předstírat service principal. Service volání pořád skončí 403. OAuth člověk dostane 501, stejně jako REST cookie.

11. `WWW-Authenticate` uvidí jen neautentizovaný MCP. REST ji nedostane.

12. Grant `jwt-bearer` z CIMD se neimplementuje. Enterprise Managed Auth tímhle konektorem nepoběží.

13. Claude Code loopback je zamítnutý (A5). Org connector na claude.ai loopback nepoužívá.

14. Cookie callback pořád vypisuje allowlist do HTML 403. MCP stránka to nedělá. Stará stránka se nepřepisuje.

15. Vrácení e-mailu do allowlistu oživí neodvolaný grant (A4). Tvrdý stop je CLI revoke.

16. Audit neřekne, jestli service volal Cursor, Grok, hub, dashboard nebo n8n. To je R12.

17. `tools/list` ukáže i nástroje mimo scope. Odmítnutí je až při volání (B42, B60). Lukáš má oba scope.

18. OAuth účet jen s `brain:read` při stale snapshotu nedostane kontext a Brain nezapíše rebuild (B57). Service token a Lukášův Claude (oba scope) rebuildují jako dnes (B58). REST se nemění.

19. Kdyby MCP callback znovu použil `cfg.callback_url`, Google na produkci vrátí `redirect_uri_mismatch` a Claude nedostane svůj `state`. B54 a B55 to berou jako regresní assert, ne jako komentář.

## Otevřené otázky pro uživatele

Q1 — Má Brain přijmout i Claude Code loopback (`http://localhost` a `http://127.0.0.1` s libovolným portem)? Předpoklad A5: ne. Kdyby ano, přibude port-agnostic výjimka jen pro ty dva hosty a T6 přestane loopback odmítat. Org connector na claude.ai to nepotřebuje.

Q2 — Stačí odvolání grantu přes `python -m app.oauth_mcp_revoke` v kontejneru, bez HTTP endpointu? Předpoklad A4: ano. Kdyby byl HTTP, přibude route jen pro service token nebo cookie a nové B#/T#, aby ji nešlo zavolat Claude access tokenem.

Focus (bývalá Q1) je uzavřená rozhodnutím v R11. Další otázka k tomu není.

## Vyřešení nálezů

| ID | Stav |
|---|---|
| C1 | vyřešeno (rozhodnutí uživatele). Q1 je pryč. R11, B44 a B45: `allow_focus_write(ServicePrincipal)` se nezakazuje, Grok a Cursor focus smí. `OAuthPrincipal` s `brain:write` focus smí taky. Samotný `brain:read` focus nezapisuje. Lukáš má oba scope. |
| C2 | vyřešeno. B54 a B55, návrh callbacku, T8 a T11. Google POST dostane `{BRAIN_PUBLIC_URL}/oauth/mcp/callback`. Na Claude jde uložený `claude_state`, ne query `state` od Google. Cookie POST v `oauth_routes.py:91-99` se pro MCP nepoužije. |
| C3 | vyřešeno. R15, B56, B57, B58, T21. Read smí warm (`mode="read"`, `commit_on_end` false podle `vault_deps.py:141-145`). Při `needs_rebuild` a OAuth jen s read se `mode="rebuild"` neotevře a commitů je 0. Write, service, cookie, dev a REST rebuildují. |
| C4 | vyřešeno. R10, B59, B60, T16. Mapa je totální vůči jménům z `build_mcp()`. Neznámý klíč je `insufficient_scope` a callable se nespustí. Každý write nástroj, včetně `update_task`, `bulk_update` a `finalize_meeting`, má `scope_denial` před vnitřní funkcí; test s principalem jen `brain:read` ověří, že se vnitřní funkce nezavolala. |
