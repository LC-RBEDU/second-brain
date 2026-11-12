# Plán: MCP OAuth pro Claude connector

## Zadání a požadavky

R1 — Org connector v Claude Team bez sdíleného bearer tokenu. Každý člen se autentizuje sám. Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá. Zdroj: brief varianta A + rozhodnutí „org connector se do Claude organizace přidá až po lidském testu“.

R2 — Allowlist je jen `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní Gmail neprojde. Stejný seznam jako dnešní cookie OAuth. Zdroj: rozhodnutí z konverzace.

R3 — Rozsah je jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Tokeny se nedělí. Audit starých IP se nedělá. Zdroj: rozhodnutí z konverzace.

R4 — Úložiště tokenů je nový SQLite soubor na druhém Coolify persistent volume. Není to vault a nesmí ležet v `/data/vault` (host `/data/second-brain-vault`). Cesta: host `/data/second-brain-oauth`, v kontejneru `/data/oauth`. Google Drive ani Mac disk se nepoužijí. Restart ani deploy nesmí odhlásit Claude, jakmile je volume skutečně připojené. Replicas Brainu zůstávají 1. Řádek v `local_persistent_volumes` sám mount nevytvoří: compose se skládá až při deploymentu. Po INSERT se queueuje deployment se `restart_only=false`, stejně jako vault ve `setup-coolify.sh:192-207`. Restart už běžícího kontejneru volume ani nový env (pepper) do procesu nedostane. Pepper v Coolify UI musí být uložený před tím deploymentem. Zdroj: rozhodnutí z konverzace + nález NEW-1 (ledger C5).

R5 — Dnešní cookie OAuth (`/oauth/authorize`, `/oauth/callback`, cookie `sb_brain_session`) zůstává. Claude ho jako MCP OAuth nepoužije. Zdroj: rozhodnutí z konverzace.

R6 — Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi: `https://brain.cyprovi.cz/oauth/mcp/callback`. Přidání URI do Google konzole je ruční krok člověka, ne skript. Token POST z MCP callbacku posílá Google právě tuhle `redirect_uri`, ne `{public}/oauth/callback`. Zdroj: rozhodnutí z konverzace + nález C2.

R7 — Registrace klienta oběma cestami, aby seděl dialog Claude: Dynamic Client Registration (RFC 7591) a Client ID Metadata Document („Use Claude's published identity“). Redirect host jen `claude.ai` a `claude.com`, včetně `https://claude.ai/api/mcp/auth_callback` a `https://claude.com/api/mcp/auth_callback`. V connectoru žádný secret. Zdroj: rozhodnutí z konverzace. Ověřeno v dokumentaci Claude (11. 11. 2026) a na živém CIMD `https://claude.ai/oauth/mcp-oauth-client-metadata`: `client_name` je `Claude`, `token_endpoint_auth_method` je `none`, redirect je jen `https://claude.ai/api/mcp/auth_callback`. Claude CIMD vybere, jen když metadata authorization serveru mají `client_id_metadata_document_supported: true` a v `token_endpoint_auth_methods_supported` je `none`. Jinak padá na DCR. `private_key_jwt` se neinzeruje.

R8 — Brain vydává vlastní neprůhledné tokeny. V úložišti jen hash. Access krátký, refresh delší, obojí odvolatelné. PKCE S256, granty `authorization_code` a `refresh_token`. Token endpoint bere `application/x-www-form-urlencoded` a odpovídá podle RFC 6749 §5.1–5.2: úspěch je HTTP 200 a JSON s klíči `access_token`, `token_type`, `expires_in`, `refresh_token`, `scope`. Chyba je HTTP 400 a JSON s klíčem `error` (`invalid_grant`, `invalid_scope`, `unsupported_grant_type`, `invalid_request`, `invalid_target`). Tělo chyby nemá `detail` ani `error_reason`. Route nesmí házet `HTTPException` (dnešní cookie callback v `oauth_routes.py:102-103` z něj udělá `{"detail": "…"}` a ten tvar se nekopíruje). MCP `401` dál používá `error_reason` (B1). Refresh se rotuje. Dva souběžné refreshe serializuje zámek kolem SQL. Vlákno, které na ten zámek čekalo, dostane `invalid_grant` a family neruší; access z vítězné odpovědi dál platí. Family se zruší až když starý refresh přijde znovu až po uvolnění zámku. Transakce se nedrží přes `await` na Google. Na `refresh_token` parametr `scope`, který v těle chybí, je prázdný, je jen z mezer, nebo po zahození `offline_access` nic neobsahuje, znamená scope uložený u grantu (RFC 6749 §6), ne prázdnou množinu. JSON klíč `scope` i access token nesou kanonický řetězec toho, co access právě dostal (`brain:read`, `brain:write`, nebo `brain:read brain:write`). Zúžení, které klient opravdu pošle a které je podmnožina grantu, platí jen pro nový access. Rotovaný refresh si nechá scope grantu, protože RFC 6749 §6 vyžaduje, aby scope nového refresh tokenu byl stejný jako u tokenu v requestu. `invalid_scope` u ještě platného refreshe nic nezapíše: token se nezrotuje a family se neruší. Každá authorization response na Claude (úspěšný i chybový `302`, a zamítací meta refresh) nese `iss` rovný issueru. Zdroj: rozhodnutí + RFC 6749 §5.1, §6 a RFC 9207 + nález NEW-3 (ledger C7) + C9, C10, C11 a C14.

R9 — Každý požadavek znovu ověří allowlist. Odebrání e-mailu nebo smazání tokenu zastaví další volání. Service token se tím nemění. Zdroj: rozhodnutí z konverzace.

R10 — Scope `brain:read` a `brain:write`. Lukáš dostane oba, když o ně klient požádá nebo scope vynechá. Nástroj mimo scope se odmítne. Mapa scope je totální: každé jméno `@mcp.tool` má klíč a chybějící klíč je odmítnutí, funkce se nespustí. Zdroj: rozhodnutí z konverzace + nález C4.

R11 — Focus smí na pokyn člověka Grok, Cursor i Claude. `BRAIN_SERVICE_TOKEN` dál smí `apply_focus` (`allow_focus_write(ServicePrincipal)` se nezakazuje). Claude OAuth principal smí focus taky, prakticky `OAuthPrincipal` se scope `brain:write`. Samotný `brain:read` focus nezapisuje. Lukáš dostává oba scope, takže Claude na jeho účtu focus zapíše. „Pokyn člověka“ je dnešní tok `propose_focus` a pak `apply_focus`; nový příznak souhlasu se nezavádí. Zdroj: rozhodnutí uživatele „Omezení neplatí - focus můžou na pokyn člověka řešit i Grok / Cursor / Claude.“ (C1, beze změny).

R12 — Audit: jeden JSON řádek na stdout Brainu na každé volání nástroje, na všech cestách ven (`ok`, `error`, `insufficient_scope`). Řádek píše jedna funkce, kterou zavolá každý z 33 wrapperů, včetně pěti, které dnes `_call` míjí (`update_task`, `export_tasks`, `bulk_update`, `finalize_meeting`, `get_task`). Do git vaultu se nezapisuje. Pole: identita, klient z registrace, nástroj, čas, výsledek. U service tokenu je identita přesně `service`, protože jeden token pořád sdílí Cursor, Grok, hub, dashboard a n8n. Zdroj: rozhodnutí z konverzace + nález NEW-2 (ledger C6).

R13 — MCP bez platného tokenu: `401` a `WWW-Authenticate` s odkazem na `/.well-known/oauth-protected-resource`. REST pro cron (hub, n8n) zůstává na dnešním JSON `401` bez nucení OAuth discovery. Pole `resource` se rovná URL, kterou člověk zadá do Claude, včetně lomítka: `https://brain.cyprovi.cz/mcp/`. Zdroj: rozhodnutí z konverzace.

R14 — Po Google loginu e-mail mimo allowlist: stránka „přístup zamítnut“ a redirect do Claude s `access_denied`. Žádný token. Redirect nese `state`, který Claude poslal na authorize, ne `state`, který Google vrátil (to je id transakce). DCR je otevřená, takže `state` volí klient a bere se jako vstup útočníka. URL se skládá jen přes `urllib.parse.urlencode`. Do atributu meta refresh jde až `html.escape(url, quote=True)`. Surový `state` se do HTML neskládá. Zdroj: rozhodnutí z konverzace + nález C2 a C12.

R15 — `get_context` pro OAuth principal s pouhým `brain:read` smí jen warm větev (`brain_vault(mode="read")`, `commit_on_end` je tam false). Když `needs_rebuild` je true, vrátí `BrainClientError` `context_rebuild_requires_write` a `mode="rebuild"` neotevře, tedy 0 commitů. MCP wrapper tu chybu vrátí jako `_error_result`, stejně jako `get_task`. Neprojde `_call`, protože ten z ní udělá `RuntimeError` a klient vidí jen `Error executing tool get_context` (`mcp_app.py:55-63`). Rebuild smí `OAuthPrincipal` s `brain:write` (Lukáš ho má). Service token, cookie session, dev a REST `get_context` rebuildují jako dnes. Zdroj: nález C3 + NEW-4 (ledger C8), kód `get_context.py:45-70`, `vault_deps.py:137-153`, `test_get_task_mcp.py:45-52`.

R16 — Org connector se přidá až po lidském testu: Lukáš v claude.ai dokončí Sign in now a vidí nástroje; druhý účet z organizace mimo allowlist token nedostane. Ten test není pytest a není `rbu-tester`. Zdroj: rozhodnutí z konverzace + profil SECOND_BRAIN.

R17 — Žádné odhady effortu. `P` je výkonový rozpočet v milisekundách a počtu dotazů, ne čas práce. Zdroj: rozhodnutí z konverzace.

R18 — Nové tokeny nesmí záviset na tom, že prázdný `BRAIN_SESSION_SECRET` spadne na `BRAIN_SERVICE_TOKEN`. Cookie serializer se nemění. Zdroj: omezení v briefu pipeline.

Mimo rozsah: dělení a rotace service tokenu; audit historických volání; dashboard OAuth a přechod Groku a Cursoru na OAuth; zápis OAuth secretů nebo auditů do git vaultu; nový project hub; `AGENTS.md`; Enterprise Managed Auth (`jwt-bearer` z CIMD dokumentu); Claude Code loopback (Q1); vizuální gate dashboardu. Alembic, RBAC, subnav, dlaždice, `qa_gate.mjs`, Celery a React se této změny netýkají. Tester se nevolá.

## Předpoklady

A1 — Vlastní tenká vrstva nad stdlib `sqlite3` + stávající `httpx`. Authlib se nepřidává. V `requirements.txt` není a CIMD, hash tokenů a oddělení od cookie session by se v něm stejně psaly ručně.

A2 — Vynechaný `scope` na authorize u allowlist e-mailu znamená oba scope. Požádá-li klient jen o jeden, dostane jen ten. `offline_access` se neinzeruje a když přijde, zahodí se; refresh token se vydá vždy u `authorization_code`. `brain:write` neimplikuje `brain:read`. Vynechání na token endpointu není totéž co vynechání na authorize: neznamená „oba scope“, znamená scope uložený u grantu. Grant jen s `brain:read` se refreshem bez parametru nerozšíří. Prázdný řetězec není podmnožina „nula scope“.

A3 — Cookie session na MCP zůstává a má implicitně oba scope (dnešní plný přístup, včetně rebuildu `get_context` a fokusu). OAuth access token z nového flow se na REST `/v1/*` nepřijímá. REST `get_context` ContextVar nenastavuje, takže se ho brána v R15 netýká.

A4 — Odebrání e-mailu z allowlistu zastaví volání hned, ale řádek grantu se nesmaže. Vrácení e-mailu do kódu allowlistu nepoužitý a neodvolaný grant znovu pustí. Odvolání grantu (CLI) je trvalé do nového loginu. Veřejný revoke endpoint se nedělá.

A5 — Redirect Claude se povolí jen jako přesná shoda s URI z DCR nebo CIMD, a jen když host je přesně `claude.ai` nebo `claude.com`, schéma `https`, bez userinfo, bez fragmentu, bez jiného portu. Jakákoli cizí URI v seznamu shodí celou registraci. `localhost` / `127.0.0.1` se zamítnou. Claude Code tedy tímhle plánem OAuth nedokončí (Q1).

A6 — Publikované `resource` je `{BRAIN_PUBLIC_URL}/mcp/` s koncovým lomítkem. Při srovnání se jedno koncové lomítko ignoruje. Cizí resource se odmítne.

A7 — TTL: authorize transakce 10 min, authorization code 60 s, access 3600 s, refresh 30 dní od vydání (rotace posune jen nový refresh), absolutní strop grantu 90 dní od vytvoření. Časy v UTC. `expires_at <= now` je vypršelé. Pepper je `BRAIN_OAUTH_TOKEN_PEPPER` (HMAC-SHA256). Chybějící pepper nepadá na service token.

A8 — SQLite se neotevírá při importu ani při úspěšném service-token requestu. Chybějící volume neshodí lifespan. Metadata a `401` jedou i bez databáze. Authorize, register a token bez zapsatelné DB nebo pepperu vrací `503`. `503` tohoto stavu je JSON `{"error":"temporarily_unavailable"}` se statusem 503, ne `detail`. Claude ho neplete s `invalid_grant`.

A9 — Re-run celého `setup-coolify.sh` na živé aplikaci se pro tuhle změnu nespouští (kopíruje env a může sáhnout na service token). Volume a následný deployment přidá malý skript. Plný setup skript dostane stejný INSERT jen pro novou instalaci, a protože queue je až na konci souboru, greenfield deploy volume uvidí.

A10 — Produkční počet řádků OAuth DB nejde změřit: soubor ještě neexistuje. Strop na dva roky je jeden člověk, pod 500 DCR klientů, pod 100 grantů. Dotaz po nasazení, není to gate: v kontejneru `sqlite3 /data/oauth/brain-oauth.sqlite 'SELECT COUNT(*) FROM oauth_tokens;'`.

A11 — Stránka zamítnutí je HTTP 200 HTML se statickým textem „Přístup zamítnut.“ a `meta refresh` 0 na Claude `redirect_uri` s `error=access_denied`, uloženým Claude `state` a `iss`. E-mail ani allowlist se na stránku nevypisují. Úspěch je HTTP 302, bez cookie `sb_brain_session`. `iss` v query je přesně issuer (báze z `auth_google.py:30`), na `302` i v meta refresh. `state` je v query procentově kódovaný a v HTML atributu ještě escapovaný.

Focus už není předpoklad. Je to R11, uzavřené rozhodnutím uživatele. Tohle kolo ho nemění.

## Současný stav (ověřeno v kódu)

`vps/second-brain-brain/app/auth_google.py:9-14` — `ALLOWLIST` je přesně ty dva e-maily. `email_allowed` (`45-46`) je case-insensitive. `authorize_url` (`49-67`) posílá `prompt=select_account`, query skládá přes `urlencode` a neposílá `hd`. `oauth_callback_url` (`29-33`) dělá `(brain_public_url or "").strip().rstrip("/")` a z té báze skládá `{báze}/oauth/callback`. `tests/test_auth_b37.py:18-26` hlídá, že `https://brain.example.com/` i varianta bez lomítka dají stejnou callback URL. Issuer pro `iss` je tahle báze, druhá normalizace nevzniká.

`vps/second-brain-brain/app/oauth_routes.py:91-99` — výměna kódu u Google posílá `redirect_uri: cfg.callback_url`, tedy cookie callback `/oauth/callback`. MCP callback, který by tenhle POST zkopíroval, dostane od Google `redirect_uri_mismatch`. Cizí e-mail je HTTP 403 a v těle je vypsaný allowlist (`113-117`). `BRAIN_SESSION_SECRET` při prázdnu padá na `BRAIN_SERVICE_TOKEN` (`25-29`). Route `/oauth/mcp/*` dnes nejsou.

`vps/second-brain-brain/app/oauth_routes.py:102-103` — neúspěch Google token POST je `raise HTTPException(401, "token exchange failed")`. FastAPI z `HTTPException` udělá tělo `{"detail": "token exchange failed"}`, klíč `error` v něm není. `/oauth/mcp/token` tuhle výjimku nepoužije. Cookie callback ji smí nechat, Claude ho jako token endpoint nečte.

`vps/second-brain-brain/app/mcp_auth.py:14-65` — MCP pustí cookie e-mail, nebo Bearer shodný s `BRAIN_SERVICE_TOKEN`, nebo dev bez tokenu. Jinak JSON `401` s `error_reason: client_error`. `WWW-Authenticate` se nenastavuje. Cookie vyhraje nad Bearerem. Tohle tělo MCP `401` zůstává (B1). Není to odpověď token endpointu.

`vps/second-brain-brain/app/auth_deps.py:17-49` — REST je cookie, nebo service Bearer, nebo dev. Cizí Bearer je `401` bez OAuth hlavičky. REST nenastavuje ContextVar principalu.

`vps/second-brain-brain/app/auth_service.py:26-36` — service token je `hmac.compare_digest` proti `BRAIN_SERVICE_TOKEN` a při shodě vrací `ServicePrincipal()` s default `label="service"`. `audit_id` (`17-18`) z toho složí `service:service` a nikde jinde se nečte. Nový auditní řádek použije řetězec `service`.

`vps/second-brain-brain/app/policy.py:15-25` — `allow_focus_write` pouští `ServicePrincipal`, řetězec `oauth:…` i `dev`. Tohle zůstává.

`vps/second-brain-brain/app/tools/set_focus.py:122-136` — bez `via_apply=True` je vždy `403 focus_requires_proposal` a nic se nezapíše. Zápis jde jen přes `apply_focus`.

`vps/second-brain-brain/app/tools/get_context.py:45-70` — nejdřív `brain_vault(mode="read")`. Když `needs_rebuild` je false, vrátí `mode: warm`. Když je true, otevře `brain_vault(mode="rebuild")` a `build_and_write_context_bundle`. Scope principalu nezná.

`vps/second-brain-brain/app/vault_deps.py:137-153` — `mode="read"` má `commit_on_end: False`. `mode="rebuild"` i `mutate` mají `commit_on_end: True` a vždy fetch, dirty check a commit (`196-198`).

`vps/second-brain-brain/app/mcp_app.py:55-63` — `_call` z `BrainClientError` / `BrainVaultError` udělá `RuntimeError`. Komentář na `60-62` říká, že knihovna pak vrátí jen `Error executing tool {name}` a JSON zůstane na `__cause__`. `get_task` proto vrací `_error_result` (`254-258`). `tests/test_get_task_mcp.py:45-52` hlídá, že text nezačíná `Error executing tool` a že `error_reason` je v JSON. `tests/test_export_tasks.py:526-537` ukazuje opačnou cestu: `UnexpectedToolError` s textem přesně `Error executing tool update_task`.

`vps/second-brain-brain/app/mcp_app.py` — 33 nástrojů přes `@mcp.tool`. Pět jich při úspěchu nejde přes `_call` a výsledek vrací přímo: `update_task` (`103-137`), `export_tasks` (`215-229`, chybu navíc hází jako `RuntimeError`), `get_task` (`254-259`), `bulk_update` (`391-417`), `finalize_meeting` (`444-475`). `mailbox_apply` / `external_apply` (`508-532`) principal natvrdo staví jako `ServicePrincipal(label="mcp")`. `gate_brain_apply` pro service vrací 403 a pro řetězec `oauth:` 501 (`auth_apply.py:15-26`).

`vps/second-brain-brain/app/main.py:90-95` a `142-143` — MCP je mount `/mcp` obalený `McpAuthMiddleware`. Cookie router je na appce. Lifespan spadne jen když chybí `GIT_VAULT_PUSH` a není `BRAIN_ALLOW_NO_PUSH`. Dockerfile spouští jeden proces `uvicorn` bez `--workers`. Sync route FastAPI jede v threadpoolu, takže dva refreshe jsou dvě vlákna.

`vps/second-brain-brain/requirements.txt` — fastapi, httpx, itsdangerous, mcp, google-auth-oauthlib. Authlib tam není. `sqlite3` je ve stdlib.

`vps/second-brain-brain/Dockerfile` — jeden proces, user root, žádný volume v image.

`vps/second-brain-brain/deploy/setup-coolify.sh:103-107` — idempotentní INSERT jen pro `mount_path=/data/vault`. Hned potom (`192-207`) queueje řádek do `application_deployment_queues`: `commit=HEAD`, `force_rebuild=true`, `is_webhook=false`, `restart_only=false`, a jen když pro appku není `queued` ani `in_progress`. Skript taky sahá na env. Samotný INSERT volume bez toho queue mount na běžícím kontejneru nezapne.

`docs/brain-api-runbook.md:150-153` — kanonická MCP URL je `https://brain.cyprovi.cz/mcp/` s lomítkem.

Živý CIMD (11. 11. 2026): `client_id` = `https://claude.ai/oauth/mcp-oauth-client-metadata`, granty zahrnují i `urn:ietf:params:oauth:grant-type:jwt-bearer`. Ten grant se neimplementuje.

## Návrh

Netýká se: Alembic, SQLAlchemy, RBAC, Celery, React, `api.ts`, subnav, hub dlaždice, `scripts/qa_gate.mjs`, Allfred, Pipedrive, Fakturoid, Fio. Žádná nová závislost.

### Úložiště

Nový `vps/second-brain-brain/app/oauth_mcp_store.py`. Soubor z `BRAIN_OAUTH_DB`, default `/data/oauth/brain-oauth.sqlite`. Cesta, jejíž `realpath` leží v `GIT_VAULT_ROOT` nebo pod `/data/vault`, se neotevře. Zápisové OAuth route pak vrací `503` s `{"error":"temporarily_unavailable"}` (R4, A8).

Žádné sdílené spojení a žádné `check_same_thread=False`. Každá SQL operace pod `main_lock` otevře vlastní `sqlite3.connect` (default `check_same_thread=True`), nastaví `PRAGMA journal_mode=WAL` a `PRAGMA busy_timeout=5000`, provede `BEGIN IMMEDIATE`, commitne a spojení zavře ještě před návratem z funkce. `counter_lock` je jen na `waiters` a `pardon` a drží se krátce, i když `main_lock` drží někdo jiný, aby šlo `waiters[hash]` zvýšit ještě před čekáním na SQL. Zámek SQL se pouští před každým `await`. Callback tedy: pod `main_lock` načte transakci a spojení zavře, pak teprve `await` na Google token a userinfo, a až potom pod zámkem zapíše kód nebo nic.

Refresh a odvolání family (C10, navazuje na C7; počítadlo je per hash kvůli C13):

- Globální integer `waiters` neexistuje. Jsou dva slovníky v paměti procesu, oba pod `counter_lock`, klíč je HMAC předloženého refresh tokenu: `waiters[hash]` a `pardon[hash]`.
- `refresh` si před čekáním na `main_lock` pod `counter_lock` zvýší `waiters[hash]`. Po získání `main_lock` tu jedničku (vlastní vstup) zase odečte. Nula klíč smaže. `finally` má dvě větve a obě mažou klíč, když hodnota spadne na nulu. Když odečet vlastního vstupu ještě neproběhl, odečte `waiters[hash]`, aby visící jednička příští rotaci neudělila pardon replayi, který nečekal. Když odečet vlastního vstupu už proběhl, tohle volání pardon nezapsalo a ještě ho nespotřebovalo, odečte `pardon[hash]`. To je čekající vlákno, které spadlo až po odečtu sebe a dřív, než větev nahrazeného refreshe pardon snížila. Bez toho by další replay dostal `invalid_grant` a family nechal živou (B34 by jednou neplatilo, B70). Volání, které pardon právě zapsalo (vítěz rotace), `finally` nesníží: ten slot patří čekajícímu vláknu. Volání, které pardon už spotřebovalo, ho nesníží podruhé.
- Držitel, který refresh ještě umí rotovat, ho zrotuje a v okamžiku commitu pod `counter_lock` zapíše `pardon[hash] = waiters[hash]`. To je počet jiných volání `refresh` téhož tokenu, která už vešla a ještě nedrží `main_lock`. Nula klíč nezakládá. Family neruší. Refresh jiného grantu je jiný hash a do toho pardonu se nepočítá.
- Držitel, který už vidí nahrazený refresh a `pardon[hash] > 0`, pardon o jedničku sníží (nulu smaže), vrátí `invalid_grant` a family neruší. To je vlákno, které čekalo na stejnou rotaci.
- Držitel, který vidí nahrazený refresh a `pardon[hash]` je 0 nebo klíč chybí, family odvolá a vrátí `invalid_grant`. To je další request až po uvolnění zámku (B34), ne čekající vlákno téhož tokenu. Souběh jiného grantu tuhle nulu nezvedne (B68).
- Po restartu jsou oba slovníky prázdné, takže replay starého refreshe family zruší. To je přísnější a pořád v souladu s B34.

Access z vítězné odpovědi po souběhu téhož tokenu pořád projde na MCP. Zruší ho až pozdější replay, který v `waiters[hash]` nečekal (u jiného grantu je to každý replay, protože ten hash nezvedl), nebo revoke CLI, nebo vypršení, nebo vyřazení e-mailu z allowlistu.

### Metadata a 401

Nový `vps/second-brain-brain/app/oauth_mcp_metadata.py`, v `main.py` před mountem MCP, bez autentizace:

- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-protected-resource/mcp` — stejné JSON

`resource` = `{public}/mcp/`, `authorization_servers` = jednoprvkový issuer (`BRAIN_PUBLIC_URL` bez koncového lomítka), `scopes_supported` = `brain:read`, `brain:write`, `bearer_methods_supported` = `header`. `offline_access` tam není.

- `GET /.well-known/oauth-authorization-server` — issuer, `authorization_endpoint` `/oauth/mcp/authorize`, `token_endpoint` `/oauth/mcp/token`, `registration_endpoint` `/oauth/mcp/register`, `response_types_supported` `code`, `grant_types_supported` `authorization_code` + `refresh_token`, `code_challenge_methods_supported` `S256`, `token_endpoint_auth_methods_supported` jen `none`, `client_id_metadata_document_supported` true, `authorization_response_iss_parameter_supported` true. Bez `private_key_jwt`. Issuer v tom JSON je stejný řetězec jako `iss` na authorization response (B69): `(BRAIN_PUBLIC_URL or "").strip().rstrip("/")`, báze z `auth_google.py:30`. Příznak `true` bez shody hodnoty test nesplní.

`McpAuthMiddleware`: každý MCP `401` dostane

`WWW-Authenticate: Bearer resource_metadata="{issuer}/.well-known/oauth-protected-resource", scope="brain:read brain:write"`

Tělo JSON zůstává `{"error_reason":"client_error","message":"authentication required"}` (u API key dnešní text). Hlavička není na `200` ani na tool error. REST `HTTPException` hlavičku nedostane. Token endpoint tohle tělo nepoužívá.

Pořadí: `X-API-Key` → cookie (`read_session_email`, principal řetězec `oauth:{email}`, oba scope, bez SQLite) → `hmac` service token (bez SQLite, `ServicePrincipal`) → HMAC access tokenu a jeden SELECT podle PK → dev jako dnes. Selhání SQLite u neznámého Beareru je `401`, ne `500`. Service token při rozbité SQLite projde.

`OAuthPrincipal` v `app/oauth_mcp_principal.py`: `email`, `scopes`, `client_id`, `client_name`. `__str__` vrací `oauth:{email}`. `allow_focus_write` ho pustí, když má `brain:write`, a větev `ServicePrincipal` nechá allowed (R11). `gate_brain_apply` ho pustí stejnou větví jako řetězec `oauth:` → 501.

### DCR, CIMD, authorize, token

Nový router `vps/second-brain-brain/app/oauth_mcp_routes.py`. `auth_google.py` dostane `oauth_mcp_callback_url` = `{public}/oauth/mcp/callback`. Cookie `oauth_callback_url` se nemění a MCP handler ji do Google POST nedá. `authorize_url` se znovupoužije, `hd` se nepřidává.

Redirect URI: `https`, host přesně `claude.ai` nebo `claude.com`, bez userinfo, fragmentu a cizího portu. Jedna špatná URI shodí celou registraci.

`POST /oauth/mcp/register` JSON, max 8 KiB, `201`, `client_id` = `brain_` + `token_urlsafe`, `token_endpoint_auth_method: none`, v odpovědi ani v DB žádný secret. Strop 500 klientů, pak `429`.

CIMD: `client_id` je `https` URL na těch dvou hostech, bez query, fragmentu a userinfo. `httpx` timeout 5 s, `follow_redirects=False`, tělo max 64 KiB. JSON `client_id` se rovná URL. `token_endpoint_auth_method` je `none` nebo chybí. Cache 1 h. Grant `jwt-bearer` v dokumentu klienta neodmítne; na token endpointu je HTTP 400 `{"error":"unsupported_grant_type"}`.

`GET /oauth/mcp/authorize`: `response_type=code`, PKCE jen `S256`, klient z DCR nebo CIMD, `redirect_uri` přesná shoda. Špatná `redirect_uri` → `400` a žádný `Location`. Platná URI a špatné PKCE nebo scope → `302` s `error=invalid_request` nebo `invalid_scope`, `state` = Claude state z query (ne id transakce), plus `iss`. To je redirect prohlížeče, ne tělo token endpointu. Resource se uloží; cizí resource → `invalid_target`. V SQLite vznikne transakce: `id` je nové `token_urlsafe`, `claude_state` je query `state` od Claude. Prohlížeč jde na Google s `redirect_uri={public}/oauth/mcp/callback` a `state={transaction.id}`. Žádná cookie.

`GET /oauth/mcp/callback` nesdílí funkci `oauth_callback`. Pod zámkem načte transakci podle query `state` (to je `transaction.id`) a spojení zavře. Pak teprve Google POST na `https://oauth2.googleapis.com/token` s `redirect_uri` přesně `oauth_mcp_callback_url`, timeout 20 s, a userinfo. Zámek přes ten `await` nedrží. Do žádného redirectu na Claude se query `state` od Google nekopíruje.

Jedna funkce skládá URL na Claude. Vezme registrovanou `redirect_uri` (`urlsplit`), existující query zachová a parametry přidá jen přes `urllib.parse.urlencode`. `state`, `code` ani `error` se do řetězce nedávají f-stringem. `iss` je issuer z B69. `302` tuhle URL dá do `Location` a v hodnotě hlavičky nezůstane surové `\r` ani `\n`. Zamítací stránka je pořád HTTP 200, ne `RedirectResponse`. Meta refresh je `content="0;url=` + `html.escape(url, quote=True)` + `"`. Viditelný text je jen „Přístup zamítnut.“ Surový `state` v těle není. `400` bez `Location` (špatná `redirect_uri`, B22) `iss` nemá, protože to není authorization response. Token endpoint `iss` do JSON nedává.

- Allowlist e-mail → pod zámkem authorization code (v DB jen hash, TTL 60 s) a `302` na Claude `redirect_uri` s `code`, `state` = uložený Claude state, `iss` = issuer.
- E-mail mimo allowlist, `verified_email is false` nebo prázdný e-mail → žádný grant, HTML „Přístup zamítnut.“ a meta refresh na Claude s `error=access_denied`, uloženým Claude state a `iss`. `state` s uvozovkou atribut nerozbije (B67).
- Google 5xx nebo timeout → žádný token; u známé transakce redirect `error=server_error` se stejným uloženým Claude state a `iss`, jinak `400`.

`POST /oauth/mcp/token` jen form body. Odpověď je `JSONResponse`, nikdy `HTTPException`. Úspěch: HTTP 200, `Cache-Control: no-store`, tělo přesně s klíči `access_token`, `token_type` (`Bearer`), `expires_in` (`3600`), `refresh_token`, `scope` (jen `brain:read` / `brain:write`). Chyba: HTTP 400, tělo `{"error":"<kód>"}`. Klíče `detail` a `error_reason` v té odpovědi nejsou. `503` při chybějícím pepperu nebo DB je výjimka z toho 400 a má `error=temporarily_unavailable` (A8).

`authorization_code`: jednorázový kód, shoda `redirect_uri` s tou uloženou (Claude callback, ne Google callback), PKCE S256, resource shodný až na jedno lomítko. Replay spotřebovaného kódu, špatný verifier, jiná `redirect_uri`, vypršelý kód: HTTP 400 `invalid_grant`. `refresh_token`: celá rotace v jednom držení zámku podle pravidel pardonu výše. Allowlist se kontroluje znovu. Vypršelý, odvolaný, nebo grant starší 90 dní, nebo e-mail mimo allowlist: HTTP 400 `invalid_grant`. `client_secret` se ignoruje a úspěch tím nepadá. `client_credentials` a `jwt-bearer`: HTTP 400 `unsupported_grant_type`. Tělo není form (`Content-Type` není `application/x-www-form-urlencoded`): HTTP 400 `invalid_request`, ne 415. Cizí resource: HTTP 400 `invalid_target`.

Scope na obou grantech řeší jedna funkce, až když je předložený refresh pořád aktuální (nebo jde o výměnu kódu). Chybějící parametr, `""`, řetězec z mezer, nebo seznam, ve kterém po zahození `offline_access` nic nezbylo, je vynechání. Neparsuje se jako prázdná množina a neprojde testem „je podmnožina“. Vynechání dá access tokenu scope uložený u grantu: u kódu scope z authorize (A2), u refreshe scope řádku refresh tokenu. Neprázdný seznam smí obsahovat jen `brain:read` a `brain:write` a jen jména, která grant má. Jinak HTTP 400 `{"error":"invalid_scope"}` a u refreshe žádný zápis: rotace neproběhne, family se neruší, stejný refresh zůstane použitelný. `offline_access` se zahodí a samo o sobě není `invalid_scope` ani zúžení na nulu. Vlastní podmnožina zúží jen nový access. Nový refresh při rotaci dostane původní scope grantu, ne zúžený access. JSON `scope` je kanonický řetězec access tokenu v pořadí `brain:read` pak `brain:write`, a test ho srovnává rovností. Rovnost řetězce nestačí: u grantu s write T23 po vynechání, po `""`, po řetězci z mezer i po samotném `offline_access` zavolá `update_task` a vnitřní funkce musí běžet. Jinak JSON ukáže oba scope a access token zůstane prázdný. Když už je refresh nahrazený, scope se nehodnotí: platí pardon a chyba je `invalid_grant`. Prázdný `scope` v JSON po hodinovém refreshi, na který Claude parametr často nepošle, by další hodinu shodil nástroje na `insufficient_scope` (B64, B65).

### Scope, get_context, audit

`app/mcp_scopes.py` — jeden slovník `TOOL_SCOPES`. Žádný default „když klíč chybí, pustit“.

`brain:read` (13): `get_context`, `read_file`, `list_dir`, `export_tasks`, `find_tasks`, `get_task`, `list_children`, `get_tree`, `list_reminders`, `get_triage_candidates`, `slack_live`, `get_meeting_prep`, `allocate_task_id`.

`brain:write` (20): `update_task`, `append_task_note`, `set_focus`, `propose_focus`, `apply_focus`, `edit_task_body`, `toggle_step`, `close_task`, `create_task`, `bulk_update`, `schedule_reminder`, `cancel_reminder`, `finalize_meeting`, `ingest_sembly`, `capture_daily`, `mailbox_propose`, `mailbox_apply`, `external_propose`, `external_apply`, `prepare_meeting`. `dry_run` scope nesnižuje.

Jedna funkce `run_tool(tool_name, fn)` v `mcp_app.py`. Každý z 33 wrapperů vrací jen její výsledek. Audit je uvnitř ní, ne v `_call`. `_call` se pro nové cesty nepoužije: z `BrainClientError` dělá `RuntimeError` (`55-63`) a pět nástrojů ho stejně míjí.

`run_tool` na každé cestě zapíše právě jeden JSON řádek a pak vrátí:

- `OAuthPrincipal` a klíč chybí, nebo v principalu není požadovaný scope: `fn` se nezavolá, řádek `result=denied`, `error_reason=insufficient_scope`, návrat `_error_result`. Service, cookie řetězec `oauth:` a `dev` tuhle větev přeskočí.
- `fn` vrátí obyčejný výsledek: řádek `result=ok`, návrat beze změny (řetězec i `ExportTasksResult`).
- `fn` vrátí `CallToolResult` s `is_error` (dnešní `oid_mismatch` u `update_task` a `bulk_update`): řádek `result=error` a ten objekt. Bez druhého řádku.
- `fn` vyhodí `BrainClientError` nebo `BrainVaultError`: řádek `result=error` s `error_reason` z výjimky, návrat `_error_result`. Žádný `RuntimeError`.
- Jiná výjimka: jeden řádek `result=error` a výjimka letí dál.

`mailbox_apply` a `external_apply` přestanou vyrábět `ServicePrincipal(label="mcp")` a předají `get_brain_principal()`, ale až uvnitř `fn`, tedy po scope kontrole.

`get_context` zůstává v read mapě, aby warm šel bez write. Uvnitř `get_context.py`, až po read sondě a jen když `needs_rebuild` je true: pokud `get_brain_principal()` je `OAuthPrincipal` a nemá `brain:write`, vyhodit `BrainClientError` (`403`, `error_reason: context_rebuild_requires_write`) a neotevírat `mode="rebuild"`. `ServicePrincipal`, řetězec `oauth:`, `dev` a `None` (REST) jdou do dnešního rebuildu. `OAuthPrincipal` s `brain:write` taky. Wrapper je `return run_tool("get_context", get_context_tool.get_context)`, takže MCP `call_tool` dostane `_error_result`: text nezačíná `Error executing tool` a JSON má `error_reason`. Stejný tvar jako `get_task` (`254-258`, `test_get_task_mcp.py:45-52`).

`app/mcp_audit.py` — logger `brain.mcp.audit`, `propagate False`, handler na stdout, formát jen `%(message)s`. JSON: `ts` (UTC), `identity`, `client_id`, `client_name`, `tool`, `result` (`ok`|`error`|`denied`), `error_reason`. Bez argumentů a bez tokenu. U service je `identity` přesně `service` a oba client fieldy null. Volá ji jen `run_tool`.

### Nasazení a docs

`deploy/add-oauth-volume.sh` na coolify-dev: `mkdir -p /data/second-brain-oauth`, `chmod 700`, idempotentní INSERT `local_persistent_volumes` (`mount_path=/data/oauth`, `host_path=/data/second-brain-oauth`). Na env nesahá, secret netiskne, `BRAIN_SERVICE_TOKEN` nemění. Hned po INSERT queueje deployment stejným tvarem jako `setup-coolify.sh:192-207`: `application_deployment_queues`, `commit=HEAD`, `force_rebuild=true`, `is_webhook=false`, `restart_only=false`, a `WHERE NOT EXISTS` pro `queued` / `in_progress`. Když queue přeskočí, skript na stdout napíše, že mount vznikne až dalším během po doběhnutí současného deploymentu, a ať se skript spustí znovu. Restart kontejneru v textu skriptu není.

Do `setup-coolify.sh` stejný INSERT hned za vault volume (před queue na `192`), plus komentář, že živá appka má malý skript, ne celý setup.

`config.example.env` — zakomentované `BRAIN_OAUTH_DB` a `BRAIN_OAUTH_TOKEN_PEPPER`. Pepper jednou v Coolify UI, není odvozený ze service tokenu. Uložení v UI proces neaktualizuje; chytí ho až deployment.

`docs/brain-api-runbook.md` — endpointy, resource URL s lomítkem, Google token POST MCP flow používá `/oauth/mcp/callback`, že `/oauth/mcp/token` vrací RFC 6749 JSON (`error`, ne `detail`), volume, pepper, ruční redirect URI, CLI revoke, repliky 1, connector až po T-H1. Pořadí na živé appce: (1) pepper v Coolify UI, (2) `add-oauth-volume.sh`, (3) počkat na deployment, který skript zařadil (`restart_only=false`); když queue přeskočil, spustit skript znovu až ten běžící deployment skončí, (4) redirect URI v Google konzoli, (5) T-H1, (6) connector. Docker restart mount ani pepper nezapne. SQLite se nesmí založit dřív, než je volume v kontejneru, jinak další deployment soubor ve vrstvě schová a Claude odhlásí. Odstavec o service tokenu zůstane.

## Kontrakt chování (B#)

Checklist A, co tu není samostatný řádek: fiskální rok a měny se netýkají, OAuth nemá částky ani FY. Sync Allfred/Pipedrive se netýká. `backend/app/services/data_consistency.py` se netýká, tohle není RB Universe; invariant je B6, B7 a B52 (service token beze změny, DB mimo vault).

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | `POST /mcp` a `POST /mcp/` bez Authorization | `401`, JSON `error_reason=client_error`, `WWW-Authenticate` obsahuje `resource_metadata` a `scope="brain:read brain:write"`. Hlavička není na `200`. Klíč `error` tu není. Tohle není token endpoint | R13 | T1 |
| B2 | `GET /v1/context` bez cookie a bez Beareru | `401`, `WWW-Authenticate` chybí | R3, R13 | T2 |
| B3 | `GET /healthz` a oba well-known GET bez tokenu | `200` | R13 | T3 |
| B4 | Protected resource metadata | `resource` je `{BRAIN_PUBLIC_URL}/mcp/` včetně lomítka; `authorization_servers` má jediný prvek | R13 | T3 |
| B5 | Authorization server metadata | DCR, CIMD true, `none`, S256, granty code+refresh. Není tam `private_key_jwt` ani `offline_access`. `authorization_response_iss_parameter_supported` je JSON `true`. `issuer` a jediný prvek `authorization_servers` se rovnají `rstrip` veřejné URL (B69). Samotný příznak `true` hodnotu `iss` na redirectu neověří | R7, R8 | T3 |
| B6 | MCP `initialize` s platným service tokenem, SQLite chybí nebo je rozbitá | není `401` ani `500`; SQLite se neotevírá | R3, R9 | T4 |
| B7 | `BRAIN_OAUTH_DB` uvnitř `GIT_VAULT_ROOT` nebo `/data/vault` | zápisové OAuth route `503`, soubor nevznikne | R4 | T5 |
| B8 | Prázdná DB, chybí pepper nebo adresář | metadata `200`; register, authorize a token `503` s `error=temporarily_unavailable`, bez `detail`; lifespan naběhne; service MCP projde | R4, R18 | T5 |
| B9 | DCR s oběma auth_callback URI | `201`, žádný `client_secret` v těle ani v DB | R7 | T6 |
| B10 | DCR s cizím hostem, `http://claude.ai/...`, `www.claude.ai`, userinfo, nebo mix dobré a zlé URI | `400`, 0 nových klientů | R7 | T6 |
| B11 | DCR nebo authorize s `http://localhost/callback` nebo `http://127.0.0.1:<port>/callback` | odmítnuto, kód se nevydá | R7 | T6 |
| B12 | CIMD jako živý dokument (mock), redirect jen claude.ai callback | authorize klienta přijme, fetch bez redirectů | R7 | T7 |
| B13 | CIMD s cizím redirectem, neshodou `client_id`, nebo jiným hostem | `invalid_client` | R7 | T7 |
| B14 | CIMD URL vrátí redirect, timeout nebo 5xx | redirect se nesleduje; klient odmítnut; token není | R7 | T7 |
| B15 | Token request s neprázdným `client_secret` a platným kódem | HTTP 200, klíče `access_token`, `token_type=Bearer`, `expires_in=3600`, `refresh_token`, `scope`. Secret se nekontroluje a neukládá. V těle není `detail` ani `error_reason` | R7, R8 | T8 |
| B16 | Authorize bez PKCE, method `plain`, nebo bez `code_challenge` | redirect `302` s `error=invalid_request` a Claude `state`. Kód v DB není. Není to JSON token endpointu | R8 | T8 |
| B17 | Platné S256, allowlist e-mail, scope vynechaný | HTTP 200 a stejné klíče jako B15, `scope` je přesně `brain:read brain:write` (rovnost, ne „klíč existuje“ a ne „obsahuje“). V DB jen HMAC; raw token v souboru není | R2, R8, R10 | T8 |
| B18 | Špatný `code_verifier` | HTTP 400, tělo `{"error":"invalid_grant"}`. Není `detail`, není `error_reason`, tokeny nejsou | R8 | T8 |
| B19 | Stejný authorization code podruhé | HTTP 400 `error=invalid_grant`, bez `detail`. Druhá sada nevznikne | R8 | T8 |
| B20 | Kód starší než 60 s | token endpoint HTTP 400 `error=invalid_grant`. Transakce starší než 10 min: žádný token; redirect `invalid_request` se uloženým Claude state, pokud URI známe. Redirect není tělo token endpointu | R8 | T9 |
| B21 | Token exchange s jinou `redirect_uri`, než šla na authorize | HTTP 400 `error=invalid_grant`, bez `detail` | R7, R8 | T8 |
| B22 | Authorize s `redirect_uri` mimo registraci klienta | HTTP `400`, `Location` na tu URI neukazuje | R7 | T6 |
| B23 | Oba allowlist e-maily, jiná velikost písmen, scope oba nebo vynechaný | tokeny, scope oba. Google authorize URL nemá `hd`. Úspěch tokenu je B17 | R2, R10 | T10 |
| B24 | Scope jen `brain:read` | v tokenu přesně `brain:read`, HTTP 200. Refresh bez parametru `scope` ten grant nerozšíří (B64) | R10 | T10, T23 |
| B25 | Scope jen `foo` na authorize | redirect `error=invalid_scope` a `iss` = issuer, token není. Když token endpoint dostane neprázdný scope mimo grant: HTTP 400 `{"error":"invalid_scope"}`, bez `detail`. U refreshe se řádek nezapíše (B66) | R10, R8 | T10, T8, T23 |
| B26 | Scope obsahuje `offline_access` a `brain:read` | uložený scope je jen `brain:read`; HTTP 200 a `refresh_token` v těle je | R8, R10 | T10 |
| B27 | Userinfo mimo allowlist | HTTP 200 HTML obsahuje „Přístup zamítnut.“, neobsahuje e-mail ani allowlist; meta refresh má `error=access_denied`; grant ani token v DB není; cookie `sb_brain_session` není. Kódování `state` a rovnost `iss` jsou B67 a B69, ne jen přítomnost slov v HTML | R14 | T11 |
| B28 | `verified_email: false` nebo prázdný e-mail | stejné jako B27 | R2, R14 | T11 |
| B29 | Google token endpoint timeout nebo 5xx | žádný token; u známé transakce redirect `error=server_error` | R8 | T11 |
| B30 | `GET /oauth/callback` cizí e-mail | pořád `403` a dnešní `HTTPException`; MCP token route se nezavolá; Google POST pořád používá `/oauth/callback` | R5 | T12 |
| B31 | `GET /oauth/authorize` | redirect na Google s `/oauth/callback`, ne s `/oauth/mcp/callback` | R5, R6 | T12 |
| B32 | Access s `expires_at <= now` na MCP | `401` + `WWW-Authenticate`, tělo `error_reason`, nástroj neběží. Token endpoint se tu nevolá | R8, R9 | T13 |
| B33 | Grant odvolaný CLI nebo smazaný řádek tokenu | MCP `401` s `error_reason`; refresh HTTP 400 `error=invalid_grant` | R8, R9 | T13 |
| B34 | Platný refresh, a až po návratu obou stran další request se starým refreshem | První odpověď HTTP 200 s klíči z B15, nový refresh. Ten další request (začal až po uvolnění zámku, pardon je 0) je HTTP 400 `error=invalid_grant` a family je odvolaná: access z té první odpovědi pak na MCP neprojde | R8 | T14 |
| B35 | Dva thready zavolají refresh téhož tokenu a oba vejdou do `refresh` dřív, než jeden commitne | Jedna odpověď HTTP 200 s klíči z B15. Druhá HTTP 400 `error=invalid_grant`, bez `detail`. Ani jedna není 500 a nevznikne `sqlite3.InterfaceError`. Family zůstane neodvolaná. Access z vítězné odpovědi na MCP projde (není 401) | R8 | T14 |
| B36 | E-mail zmizel z allowlistu | MCP `401` s `error_reason`; refresh HTTP 400 `error=invalid_grant`; service token funguje | R9 | T15 |
| B37 | E-mail se vrátí, grant nebyl odvolaný a nevypršel | stejný access znovu projde | R9 | T15 |
| B38 | Grant starší než 90 dní | HTTP 400 `error=invalid_grant` | R8 | T13 |
| B39 | Resource `…/mcp` i `…/mcp/` | přijato, úspěch je B17. Jiná URL: HTTP 400 `{"error":"invalid_target"}`, bez `detail` | R13, R8 | T8 |
| B40 | Token endpoint s JSON tělem místo form | HTTP 400 `{"error":"invalid_request"}`. Není 415, není `detail`, token není | R8 | T8 |
| B41 | Grant `client_credentials` nebo jwt-bearer | HTTP 400 `{"error":"unsupported_grant_type"}`, bez `detail` | R8 | T8 |
| B42 | OAuth jen `brain:read`, write nástroj včetně `create_task`, `update_task`, `bulk_update`, `finalize_meeting` | HTTP 200, `isError`, `insufficient_scope`, vnitřní funkce se nezavolá. Není to `401` | R10 | T16 |
| B43 | OAuth jen `brain:write`, read nástroj včetně `read_file` a `export_tasks` | `insufficient_scope`, vnitřní funkce se nezavolá | R10 | T16 |
| B44 | `OAuthPrincipal` s `brain:write` (Lukáš má i read), `apply_focus` | `allow_focus_write` pustí. Zápis do vaultu tenhle test nevolá, jen bránu. `propose_focus` před `apply_focus` zůstává | R11 | T17 |
| B45 | Service token, `apply_focus` i ostatní nástroje | scope mapa se neaplikuje; `allow_focus_write(ServicePrincipal)` zůstává allowed | R3, R11 | T4, T17 |
| B46 | Cookie `sb_brain_session` allowlist e-mailu na MCP | projde jako dnes, oba scope implicitně, focus i rebuild smí | R5, R11, R15 | T18 |
| B47 | OAuth access token na `GET /v1/context` | `401` | R3 | T2 |
| B48 | `str(OAuthPrincipal)` a `mailbox_apply` / `external_apply` | principal `oauth:<email>`; brána → 501. Service → pořád 403. Natvrdo `ServicePrincipal(label="mcp")` zmizí | R10 | T19 |
| B49 | `tools/call` přes `run_tool`, úspěch i denial | právě jeden stdout JSON řádek na cestu. Úspěšný `update_task` (nástroj, který dnes `_call` míjí): `result=ok`. OAuth jen s read na write nástroji: `result=denied`, `error_reason=insufficient_scope`, a vnitřní funkce se nezavolá. OAuth identita `oauth:<email>` a `client_name` z registrace. Service: `identity=service`, client fieldy null. Bez argumentů a bez tokenu. Do vaultu se nezapíše | R12 | T20 |
| B50 | `X-API-Key` na MCP | `401` + `WWW-Authenticate`, tělo `error_reason` | R13 | T1 |
| B51 | Dev bez service tokenu a s `BRAIN_ALLOW_NO_PUSH` | principal `dev`; import testů neotevírá OAuth DB | R3 | T4 |
| B52 | Úspěšný MCP login | nenastaví `sb_brain_session` a hash neleží ve vaultu | R4, R5 | T8, T5 |
| B53 | Stránka zamítnutí | HTML v `/oauth/mcp/callback`, ne dashboard; text „Přístup zamítnut.“ je v těle | R14, R16 | T11 |
| B54 | MCP callback vymění kód u Google | POST `redirect_uri` je přesně `{BRAIN_PUBLIC_URL}/oauth/mcp/callback`. Není to `cfg.callback_url`. Authorize URL na Google má tutéž `redirect_uri` a `state` rovný id transakce, jiné než Claude state. Zámek se přes Google `await` nedrží | R6, R8 | T8, T11 |
| B55 | Úspěšný `302` i zamítací meta refresh na Claude | query `state` je `claude_state` uložený při authorize. Není to query `state` z návratu od Google. Hodnota `iss` je B69 | R14 | T8, T11 |
| B56 | `OAuthPrincipal` jen s `brain:read`, `needs_rebuild` false | odpověď `mode: warm`. `brain_vault` jen `mode="read"`. `mode="rebuild"` se nezavolá | R15 | T21 |
| B57 | `OAuthPrincipal` jen s `brain:read`, `needs_rebuild` true | `BrainClientError` `context_rebuild_requires_write`. `brain_vault(mode="rebuild")` se nezavolá. Commitů 0. Read sonda smí proběhnout (`commit_on_end` false) | R15 | T21 |
| B58 | `needs_rebuild` true a principal je `ServicePrincipal`, řetězec `oauth:`, `dev`, `None`, nebo `OAuthPrincipal` s `brain:write` | dnešní rebuild větev se otevře. REST handler principal nenastavuje, takže se ho B57 netýká | R15 | T21 |
| B59 | `TOOL_SCOPES` a jména `@mcp.tool` po `build_mcp()` | množiny se rovnají (33 jmen, 13 read + 20 write). Neznámé jméno v `run_tool` funkci nespustí a vrátí `insufficient_scope` | R10 | T16 |
| B60 | Každý nástroj s `brain:write` a principal jen `brain:read` | `run_tool` vrátí `insufficient_scope` dřív, než se zavolá vnitřní funkce. Platí i pro `update_task`, `bulk_update` a `finalize_meeting` | R10 | T16 |
| B61 | `add-oauth-volume.sh` po INSERT volume | queue do `application_deployment_queues` má `restart_only=false` a `force_rebuild=true`, stejný `WHERE NOT EXISTS` pro `queued`/`in_progress` jako `setup-coolify.sh:192-207`. Skript neříká, že stačí restart kontejneru. Když queue přeskočí, text řekne spustit skript znovu po doběhnutí běžícího deploymentu. Na `BRAIN_SERVICE_TOKEN` nesahá | R4 | T22 |
| B62 | MCP `call_tool("get_context")` s OAuth jen `brain:read` a `needs_rebuild` true | `is_error`, text nezačíná `Error executing tool`, JSON `error_reason` je `context_rebuild_requires_write`, `structured_content` sedí na ten JSON. Není to `RuntimeError` z `_call` | R15 | T21 |
| B63 | Callback drží řádek transakce a pak čeká na Google | mezi načtením řádku a zápisem kódu zámek není držený. Selhání Google nezanechá otevřenou transakci | R8 | T11 |
| B64 | Refresh, parametr `scope` v těle chybí. Jednou grant s oběma scope, jednou grant jen `brain:read` | HTTP 200. U obou grantů je `scope` přesně řetězec grantu: `brain:read brain:write`, respektive `brain:read`. Nestačí, že klíč v JSON je. Access z grantu s write na `update_task` vnitřní funkci zavolá (není `insufficient_scope`). Access z grantu jen s read ji nezavolá a odpověď je `insufficient_scope`. Prázdná množina by oba případy srazila na `insufficient_scope` na hodinu | R8, R10 | T23 |
| B65 | Refresh grantu s oběma scope. Čtyři vstupy, každý zvlášť: parametr `scope` chybí, je `""`, je jen mezery (`"   "`), nebo je jen `offline_access` | Každý HTTP 200 a `scope` je přesně `brain:read brain:write`. U každého z těch čtyř access tokenů `call_tool("update_task")` vnitřní funkci zavolá. JSON rovnost bez toho hovoru test nesplní. Není `invalid_scope` a není prázdný `scope` v JSON. `offline_access` se zahodí a samo scope nezúží na nulu. Grant jen s `brain:read` a refresh bez parametru dál write funkci nezavolá (B64) | R8, R10 | T23 |
| B66 | Refresh grantu s oběma scope pošle jen `brain:read`. Druhý případ: neprázdný scope mimo grant (`foo`, nebo `brain:write` když grant má jen read) | První případ HTTP 200 a access má přesně `brain:read`. Nový refresh v DB má dál oba scope grantu. Další refresh bez parametru vrátí zase `brain:read brain:write`. Druhý případ HTTP 400 `{"error":"invalid_scope"}`, bez `detail`. Řádek se nezrotuje, `revoked_at` zůstane prázdné. Stejný refresh hned potom bez špatného scope vrátí HTTP 200 a scope grantu | R8, R10 | T23 |
| B67 | Zamítací HTML. `state` je `say "a" & <b>\n` (uvozovka, `&`, `<`, mezera, nový řádek). DCR je otevřená, state volí klient | HTTP 200, tělo obsahuje „Přístup zamítnut.“ a neobsahuje ten surový `state`. URL vznikne `urlencode`, do atributu jde `html.escape(url, quote=True)`. Parser HTML uvidí jeden meta refresh. Po `html.unescape` a `parse_qs` je `state` rovný původnímu a `error` je `access_denied`. Uvozovka ve state atribut `content` nezavře. Stejný builder skládá `Location` úspěšného `302`: `parse_qs` vrátí tentýž `state` a v hodnotě hlavičky není surové `\r` ani `\n` | R14 | T11 |
| B68 | Dva thready, každý zavolá refresh jiného grantu, a oba vejdou do `refresh` dřív, než jeden commitne | Obě odpovědi HTTP 200 a klíče z B15. `pardon[hash]` se rovná `waiters[hash]` v okamžiku commitu, ne globálnímu počtu čekajících refreshů. Hned potom replay starého refreshe prvního grantu: HTTP 400 `error=invalid_grant` a family toho grantu je odvolaná (access z jeho vítězné odpovědi pak na MCP neprojde). Souběh druhého grantu odvolání neoddálí. Dva souběžné refreshe téhož tokenu zůstávají B35: family žije | R8 | T14 |
| B69 | Úspěšný `302`, chybový `302` (`invalid_request`, `invalid_scope`, `server_error`) a zamítací meta refresh. `BRAIN_PUBLIC_URL` je `https://brain.example.com/` s koncovým lomítkem | Query `iss` (u HTML až po unescape) je přesně `https://brain.example.com`. Žádné koncové lomítko, žádná cesta, žádný jiný host. Stejný řetězec je `issuer` v authorization-server metadata. Příznak `authorization_response_iss_parameter_supported: true` sám test nesplní. Token endpoint klíč `iss` v JSON nemá | R8, R14 | T3, T8, T11 |
| B70 | Dva thready vejdou do refresh téhož tokenu dřív, než jeden commitne. Poražený po odečtu vlastního `waiters[hash]` spadne, ještě než sníží `pardon[hash]`. `finally` doběhne | Vítěz HTTP 200, family po pádu pořád neodvolaná, jeho access na MCP není 401. `finally` poraženého sníží `pardon[hash]` (nulu smaže) a nesáhne na pardon, který zapsal vítěz. Až potom replay starého refreshe: HTTP 400 `error=invalid_grant` a family je odvolaná, access vítěze na MCP je 401. Kdyby `finally` pardon nechal, replay family nezruší a B34 jednou neplatí | R8 | T14 |

Prázdná data: B8. Chybějící e-mail a kód: B20, B28. Hranice expirace: B32, B38. Oprávnění: B23–B28, B36, B42–B48, B56–B60, B62. Smazaný grant: B33, B36. Opakování: B19, B34, B35, B68, B70. Cizí služba: B14, B29, B54, B63. Zpětná kompatibilita: B2, B6, B30, B31, B45, B46, B51, B58. Scope na refreshi: B64–B66. HTML `state`: B67. `iss`: B69.

## Výkonový rozpočet (P)

Produkční OAuth tabulky dnes neexistují (A10). Strop za dva roky: pod 500 klientů, pod 100 grantů, pod 200 token řádků, soubor v řádu stovek KiB. Lookup access tokenu je jeden SELECT podle PK. Na cestě MCP nástroje není Google, Allfred ani CIMD. CIMD fetch je jen na authorize, timeout 5 s, pak cache 1 h. Token endpoint Google nevolá. Stránkování a frontend se netýkají. Payload metadat je pod 2 KiB, token odpověď pod 1 KiB (pět klíčů z B15), auditní řádek pod 500 B. Platnost tokenu se v procesu necachuje. Uvicorn zůstává jeden proces. Repliky se nenastavují nad 1.

Zámek serializuje jen SQL. Refresh ho drží po dobu jedné transakce (stále cíl pod 50 ms) a ne přes síť. Callback ho přes Google (timeout 20 s) nedrží, takže jeden pomalý login neblokuje druhý refresh déle než samotný zápis. Pardon je jeden int na hash refresh tokenu, který právě čeká nebo se právě rotoval, další SQL nepřidává a po nule se klíč smaže. Rozlišení vynechaného scope je práce se řetězcem v té samé transakci, nula dotazů navíc. `scope_denial` a audit jsou slovník a jeden zápis na stdout, 0 SQL. `get_context` pro read-only a stale stav udělá jen dnešní read sondu (`mode="read"`, `commit_on_end` false) a rebuild neotevře.

| Endpoint | SQL | Externí volání | Cíl | Měření |
|---|---|---|---|---|
| `GET` obou well-known | 0 | 0 | cold i warm pod 50 ms | T3 a QA curl `time_total` |
| `POST /oauth/mcp/register` | 1 INSERT pod zámkem, nové spojení | 0 | pod 50 ms | T6 |
| `GET /oauth/mcp/authorize` | 1 INSERT, u CIMD navíc 1 SELECT cache | CIMD jen při miss, timeout 5 s, mimo zámek | cache hit pod 50 ms | T7 |
| `GET /oauth/mcp/callback` | načtení a zápis jako dvě krátké transakce | Google token + userinfo mezi nimi, timeout 20 s, zámek puštěný | lokální část pod 50 ms | T8, T11 mock |
| `POST /oauth/mcp/token` včetně refresh | 1 transakce pod zámkem, nejvýš 4 statementy | 0 | cold pod 50 ms, warm pod 20 ms; tělo úspěchu pod 1 KiB | T8, T14 |
| MCP gate pro service token | 0 | 0 | přidaná režie pod 5 ms | T4 |
| MCP gate pro OAuth access + `run_tool` | 1 PK SELECT, pak 0 | 0 | přidaná režie pod 15 ms | T13, T16, T20 |

Anti-patterny checklistu B (Allfred blob, `Model.all()`, live GraphQL) se netýkají. Token se neověřuje načtením celé tabulky.

## Testy (T#)

Primární gate: `python3 -m pytest vps/second-brain-brain/tests -q`. Hub pytest se nespouští. `scripts/qa_*_ui.mjs` a Playwright T6 se nezakládají. `rbu-tester` se nevolá.

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| T1 | pytest | gate | `vps/second-brain-brain/tests/test_mcp_oauth.py` a doplnění `test_mcp_auth.py` | B1, B50. Starý JSON `401` s `error_reason` zůstane, přibude hlavička. Klíč `error` v tom MCP `401` není |
| T2 | pytest | gate | oauth soubor | B2, B47 |
| T3 | pytest | gate | oauth soubor | B3, B4, B5, B69 (jen metadata). `issuer` a `authorization_servers[0]` se rovnají `https://brain.example.com`, když je `BRAIN_PUBLIC_URL` s koncovým lomítkem. `authorization_response_iss_parameter_supported` je `true`. Query `iss` na redirectu T3 nevidí |
| T4 | pytest | gate | `test_mcp_auth.py` + oauth soubor | B6, B45 průchod, B51 |
| T5 | pytest | gate | oauth soubor | B7, B8, B52 cesta. `503` má `error=temporarily_unavailable` a nemá `detail` |
| T6 | pytest | gate | oauth soubor | B9, B10, B11, B22 |
| T7 | pytest | gate | oauth soubor, mock httpx | B12, B13, B14 |
| T8 | pytest | gate | oauth soubor, mock Google | B15–B19, B21, B25 (větev tokenu), B39–B41, B52, B54, B55, B69. Úspěch: status 200 a klíče `access_token`, `token_type`, `expires_in`, `refresh_token`, `scope`; `token_type` je `Bearer`, `expires_in` je 3600; když authorize scope vynechal, `scope` je přesně `brain:read brain:write`. V těle není `detail`, `error_reason` ani `iss`. Chyby tokenu: status 400, klíč `error` je `invalid_grant` / `invalid_scope` / `invalid_request` / `invalid_target` / `unsupported_grant_type` podle řádku, a `detail` ani `error_reason` v JSON nejsou. Mock POST: `redirect_uri` rovna `{public}/oauth/mcp/callback`. Google authorize URL má tutéž `redirect_uri` a `state` = id transakce. `302` na Claude se čte přes `parse_qs`: `state` rovný tomu, co klient poslal na `/oauth/mcp/authorize` (v testu řetězec s `&` a uvozovkou, ne jen `[A-Za-z0-9]`), nerovný id transakce, a `iss` přesně `https://brain.example.com` při veřejné URL s koncovým lomítkem |
| T9 | pytest | gate | oauth soubor | B20. Vypršelý kód: HTTP 400 a `error=invalid_grant` |
| T10 | pytest | gate | oauth soubor | B23, B24, B25 (redirect authorize), B26. Úspěšný token assertuje klíče jako T8 |
| T11 | pytest | gate | oauth soubor | B27, B28, B29, B53, B54, B55, B63, B67, B69. I při zamítnutí allowlistu šel Google POST na `/oauth/mcp/callback`. Meta refresh se nečte jako podřetězec `state=` v HTML. `state` v testu je `say "a" & <b>\n`. Tělo obsahuje „Přístup zamítnut.“ a ten surový `state` neobsahuje. HTML parser najde jeden meta refresh; po `html.unescape` a `parse_qs` se `state` rovná původnímu, `error` je `access_denied` a `iss` je přesně issuer bez koncového lomítka. Redirect `server_error` má v `parse_qs` totéž `iss` a uložený Claude state. Testový double zámku ukáže, že během mockovaného Google volání zámek není držený |
| T12 | pytest | gate | `test_mcp_and_oauth_routes.py`, `test_auth_b37.py` | B30, B31. Cookie `403` smí zůstat `HTTPException` |
| T13 | pytest | gate | oauth soubor | B32, B33, B38. Refresh chyba je HTTP 400 `error=invalid_grant`. MCP `401` zůstává `error_reason` |
| T14 | pytest | gate | oauth soubor | B34, B35, B68, B70. Dva thready, oba zavolají refresh téhož tokenu dřív, než jeden commitne. Vítěz: HTTP 200 a klíče z B15. Poražený: HTTP 400 `error=invalid_grant`, bez `detail`. Žádná není 500 a žádná nevyhodí `sqlite3.InterfaceError`. Po joinu obou: access z vítěze na MCP není 401 a `revoked_at` family je prázdné. Až potom třetí request se starým refreshem: HTTP 400 `error=invalid_grant`, family odvolaná, a ten samý access na MCP už je 401. Zvlášť dva thready na dvou různých grantech, oba vejdou dřív, než jeden commitne: oba HTTP 200. Replay starého refreshe prvního grantu hned potom family odvolá. Kdyby `pardon` byl globální počet čekajících, ten replay by family nechal živou. Zvlášť B70: poražený se po odečtu vlastního `waiters[hash]` vyhodí dřív, než sníží pardon. Po `finally` family ještě žije a access vítěze není 401. Replay starého refreshe až potom family odvolá. Kdyby `finally` pardon nesnížil, ten replay family nechá živou |
| T15 | pytest | gate | oauth soubor | B36, B37. Refresh při vyřazeném e-mailu je HTTP 400 `error=invalid_grant` |
| T16 | pytest | gate | oauth soubor | B42, B43, B59, B60. Jména vezme z nástrojů registrovaných `build_mcp()` a porovná je s `set(TOOL_SCOPES)`. Žádný druhý ruční seznam v testu. Pro každé write jméno nastaví `OAuthPrincipal` jen s `brain:read`, zavolá registrovaný wrapper a assertuje, že monkeypatch vnitřní funkce (`update_task`, `bulk_update`, `finalize_meeting` a zbylé write funkce) nebyl zavolaný. Neznámé jméno v `run_tool` sentinel nezavolá |
| T17 | pytest | gate | `test_set_focus.py` zůstává; oauth soubor | B44, B45. `allow_focus_write(ServicePrincipal)` allowed. `allow_focus_write(OAuthPrincipal` s `brain:write`)` allowed. `OAuthPrincipal` jen s `brain:read` se k `apply_focus` přes wrapper nedostane (T16) |
| T18 | pytest | gate | oauth soubor | B46 |
| T19 | pytest | gate | oauth soubor | B48 |
| T20 | pytest | gate | oauth soubor, capsys | B49. `call_tool("update_task")` při úspěchu (vnitřní funkce namockovaná, nástroj dnes `_call` míjí) vypíše právě jeden JSON s `result=ok`. `call_tool` write nástroje s OAuth jen `brain:read` vypíše právě jeden JSON s `result=denied` a `error_reason=insufficient_scope`. V obou případech žádný druhý řádek |
| T21 | pytest | gate | `vps/second-brain-brain/tests/test_get_context_scope.py` | B56, B57, B58, B62. `needs_rebuild` se namockuje. Spy na `brain_vault`: u read-only a stale není `mode="rebuild"` a není commit. U service, cookie řetězce, `dev`, `None` a OAuth s `brain:write` se rebuild větev otevře. Navíc `asyncio.run(mcp.call_tool("get_context", {}))` s principalem nastaveným na OAuth jen `brain:read` a `needs_rebuild` true: text nezačíná `Error executing tool`, `error_reason` je `context_rebuild_requires_write` |
| T22 | pytest | gate | oauth soubor, čte text skriptu | B61. `deploy/add-oauth-volume.sh` obsahuje INSERT do `application_deployment_queues` s `restart_only` false. Neobsahuje instrukci, že stačí restart kontejneru. Nemění `BRAIN_SERVICE_TOKEN`. Proti Coolify se nespouští |
| T23 | pytest | gate | oauth soubor | B64, B65, B66 a větev B24/B25 na refreshi. Čtyři refreshe grantu s oběma scope, každý zvlášť: parametr `scope` chybí, je `""`, je `"   "` (jen mezery), je jen `offline_access`. U každého je JSON `scope` přesně `brain:read brain:write` a `call_tool("update_task")` s tím access tokenem vnitřní funkci zavolá. Hovor jen u prvního (chybějící parametr) nestačí. Grant jen s `brain:read` a refresh bez parametru: `scope` je přesně `brain:read` a stejný write nástroj funkci nezavolá. Grant s oběma a refresh `scope=brain:read`: access má přesně `brain:read`, v DB má nový refresh pořád oba, a další refresh bez parametru vrátí `brain:read brain:write`. Refresh s `scope=foo` na ještě platném tokenu: HTTP 400 `error=invalid_scope`, `revoked_at` prázdné, a tentýž refresh bez `foo` hned potom HTTP 200. Assert není „klíč `scope` existuje“ |
| T-Q1 | curl proti `https://brain.cyprovi.cz` až po deploymentu, který zařadil volume skript | QA | není nový skript | B1, B3, B4, B5, B6. Žádný zápis do vaultu. Service token z env, do chatu se nekopíruje. Restart bez toho deploymentu důkaz o volume není. MCP `401` má `error_reason`, ne klíč `error` |
| T-H1 | ruční v claude.ai | člověk, ne gate a ne Tester | — | R16. Až po doběhnutí volume deploymentu, pepperu v tom image a Google redirect URI. Po hodině Claude obnoví session přes refresh bez nového loginu a nástroj, který před refreshem fungoval, nezačne vracet `insufficient_scope`. To je symptom B64, když by vynechaný `scope` na refreshi uložil prázdnou množinu |

## Pořadí implementace

F1 — `oauth_mcp_store.py`: dvě state pole, `main_lock`, `counter_lock`, `waiters[hash]` a `pardon[hash]` (žádný globální integer), `finally` podle B70 (čekající pád sníží pardon, vítěz který pardon zapsal ho nesníží), nové spojení na operaci, WAL, žádné sdílené spojení, principal dataclass, pepper, zákaz cesty ve vaultu, CLI revoke. Scope grantu leží na řádku refresh tokenu a při rotaci se kopíruje beze změny. Access má vlastní scope.

F2 — metadata a `WWW-Authenticate`. Service větev bez SQLite. MCP `401` zůstává `error_reason`. Issuer je jedna funkce, báze z `auth_google.py:30`, a používá ji metadata i `iss` na redirectu.

F3 — DCR, CIMD, authorize, callback, token. Token route vrací `JSONResponse` podle B15 a B18, ne `HTTPException`. Vynechaný a prázdný `scope` na token requestu jde přes funkci z odstavce Scope (B64–B66), ne přes test „je podmnožina“. Callback načte řádek, zámek pustí, pak teprve Google POST s `oauth_mcp_callback_url`. URL na Claude skládá jeden builder (`urlencode` + u HTML `html.escape`). Redirect na Claude čte jen `claude_state` a `iss` = issuer. Cookie `oauth_routes.oauth_callback` se nevolá. Závisí na F1.

F4 — `TOOL_SCOPES` a `run_tool` jako jediný návrat všech 33 wrapperů, včetně `update_task`, `export_tasks`, `bulk_update`, `finalize_meeting` a `get_task`. Audit jen v `run_tool`. `BrainClientError` vrací `_error_result`, ne `RuntimeError`. `allow_focus_write` pro `OAuthPrincipal` s write, větev `ServicePrincipal` zůstává allowed. `gate_brain_apply`. MCP apply bez natvrdo service principalu. Brána rebuildu v `get_context.py` a wrapper přes `run_tool`. Závisí na F1. Tokeny z F3 nejsou podmínka unit testu brány.

F5 — `add-oauth-volume.sh` s queue `restart_only=false`, INSERT v `setup-coolify.sh` před stávající queue, `config.example.env`, runbook s pořadím pepper → skript → počkat na deployment a s větou, že token endpoint mluví klíčem `error`. Souběžně s F4, ve stejném diffu před pushem na `main`.

F6 — pytest T1–T23 a kontrola, že T12 zůstane zelený. Až po F2–F4. T23 patří k token route z F3 a u čtyř vynechaných scope volá `update_task`. T14 patří k pardonu z F1, včetně pádu po odečtu `waiters` (B70).

F7 — člověk, mimo git: nejdřív pepper v Coolify UI, potom `add-oauth-volume.sh`, potom počkat na jeho deployment. Když queue přeskočí, skript spustit znovu až současný deployment skončí. Restart kontejneru se nepočítá. Pak Google redirect URI, T-H1, a teprve potom connector v organizaci. Do té doby se Claude k Brainu nepřihlašuje, aby SQLite nevznikl ve vrstvě kontejneru.

Push na `main` spustí Coolify deploy image Brain podle watch paths. Ten deploy volume neuvidí, pokud řádek v `local_persistent_volumes` ještě není. Skriptový deployment po INSERT ho připojí. Pepper uložený v UI až po startu kontejneru v procesu není, dokud neproběhne další deployment. Hub image se nenasazuje.

## Rizika a zpětná kompatibilita

1. Deploy z pushe na `main` před řádkem volume: kontejner `/data/oauth` nemá. Authorize, register a token vrací `503` s `error=temporarily_unavailable`, service token žije dál. Když se v tom stavu někdo přihlásí a SQLite vznikne ve vrstvě kontejneru, další deployment se správným mountem ten soubor schová a Claude odhlásí. Proto se Claude přihlašuje až po deploymentu ze skriptu. Restart starého kontejneru tohle nespraví.

2. Bez ručního redirect URI v Google konzoli produkční callback skončí `redirect_uri_mismatch`. Pytest to mockuje a hlídá, že POST neposílá `/oauth/callback` (B54).

3. Claude u custom connectoru defaultně vezme CIMD. Ten dokument zná jen `https://claude.ai/api/mcp/auth_callback`. `claude.com` projde přes DCR.

4. `resource` v metadatech musí mít koncové lomítko, protože takovou URL člověk zadá. Srovnání přijme i variantu bez něj.

5. Dva paralelní refreshe téhož tokenu: zámek pustí právě jednu rotaci. Čekající vlákno dostane HTTP 400 `invalid_grant` a family nechá živou, takže access z vítěze Claude dál používá (B35). Až další request se starým refreshem, který začal po uvolnění zámku, family odvolá (B34) a Claude se znovu přihlásí. Pardon je `waiters` jen toho hashe. Souběžný refresh jiného grantu počet nezvedne a odvolání family neoddálí (B68). Bez zámku by druhé vlákno dostalo `InterfaceError`. Kdyby čekající vlákno family rušilo hned, vítězný access by umřel ve stejné vteřině a hodinový refresh by vypadal jako odhlášení. Kdyby pardon zůstal globální integer, čekající cizí grant by replay starého tokenu odpustil. Kdyby čekající vlákno spadlo až po odečtu sebe z `waiters` a `finally` pardon nesnížilo, další replay family nezruší (B70). `finally` nesmí snížit pardon, který v témže volání zapsal vítěz.

6. Ztráta pepperu v Coolify env odhlásí Claude, ale až po deploymentu, který ten env načte. Samotné uložení v UI běžící proces nezmění. Volume, které už deployment připojil, restart souboru tokenů nesmaže. Pepper se v téhle změně nerotuje.

7. Repliky nad 1 by SQLite rozbily a pardon v paměti by mezi procesy neplatil. Runbook je nechá na 1. Zámek je jen uvnitř jednoho procesu.

8. Otevřené DCR je omezené hostem redirectu a stropem 500 řádků.

9. CIMD SSRF: jen dva hosti, žádné redirecty, timeout 5 s, strop těla 64 KiB.

10. `mailbox_apply` a `external_apply` přestanou předstírat service principal. Service volání pořád skončí 403. OAuth člověk dostane 501, stejně jako REST cookie.

11. `WWW-Authenticate` uvidí jen neautentizovaný MCP. REST ji nedostane. Token endpoint `WWW-Authenticate` na `400` nepřidává, aby Claude nezačal discovery znovu místo čtení `error`.

12. Grant `jwt-bearer` z CIMD se neimplementuje. Enterprise Managed Auth tímhle konektorem nepoběží. Odpověď je HTTP 400 `unsupported_grant_type`.

13. Claude Code loopback je zamítnutý (A5). Org connector na claude.ai loopback nepoužívá.

14. Cookie callback pořád vypisuje allowlist do HTML 403 a pořád používá `HTTPException`. MCP stránka allowlist nevypisuje. Token endpoint `HTTPException` nepoužívá. Stará cookie stránka se nepřepisuje.

15. Vrácení e-mailu do allowlistu oživí neodvolaný grant (A4). Tvrdý stop je CLI revoke.

16. Audit neřekne, jestli service volal Cursor, Grok, hub, dashboard nebo n8n. To je R12.

17. `tools/list` ukáže i nástroje mimo scope. Odmítnutí je až při volání (B42, B60). Lukáš má oba scope.

18. OAuth účet jen s `brain:read` při stale snapshotu nedostane kontext a Brain nezapíše rebuild (B57, B62). Service token a Lukášův Claude (oba scope) rebuildují jako dnes (B58). REST se nemění.

19. Kdyby MCP callback znovu použil `cfg.callback_url`, Google na produkci vrátí `redirect_uri_mismatch` a Claude nedostane svůj `state`. B54 a B55 to berou jako regresní assert, ne jako komentář.

20. Kdyby audit zůstal jen v `_call`, úspěch `update_task` a scope denial v logu nebudou. B49 to bere na nástroji, který `_call` míjí, a na denial.

21. Skriptový queue se přeskočí, když už jeden deployment běží. Ten běžící mohl začít před INSERT a volume nemá. Druhé spuštění skriptu po jeho konci queue doplní (B61). Bez toho druhého běhu mount nevznikne.

22. Kdyby token endpoint vrátil `{"detail":"invalid_grant"}` nebo `error_reason`, pytest na slově v textu může projít a Claude po vypršení access tokenu (3600 s) refresh nepoužije. T8 a T14 proto assertují status a klíč `error`, ne podřetězec v `detail`.

23. Kdyby vynechaný, prázdný, mezerový nebo jen `offline_access` scope na refreshi prošel jako prázdná podmnožina, JSON by klíč `scope` měl hodnotu grantu a access by neměl žádný scope. Claude po 3600 s parametr často neposílá. Další hodinu by každý nástroj vrátil `insufficient_scope`. B65 u všech čtyř vstupů srovná řetězec a zavolá `update_task`. Rovnost JSON bez toho hovoru díru nechytí. Grant jen s `brain:read` write funkci nezavolá.

24. Kdyby se `state` vložil do meta refresh jako text, uvozovka v něm zavře atribut `content`. DCR je otevřená, state volí kdokoli, kdo registraci udělá. B67 bere state s uvozovkou, `&` a novým řádkem a čte ho až po parse, ne jako podřetězec HTML.

25. Kdyby `iss` test jen ověřil, že metadata mají `authorization_response_iss_parameter_supported: true`, redirect může `iss` vynechat nebo tam dát URL s lomítkem. Klient ho pak odmítne. B69 srovnává query s bází z `auth_google.py:30`.

## Otevřené otázky pro uživatele

Q1 — Má Brain přijmout i Claude Code loopback (`http://localhost` a `http://127.0.0.1` s libovolným portem)? Předpoklad A5: ne. Kdyby ano, přibude port-agnostic výjimka jen pro ty dva hosty a T6 přestane loopback odmítat. Org connector na claude.ai to nepotřebuje.

Q2 — Stačí odvolání grantu přes `python -m app.oauth_mcp_revoke` v kontejneru, bez HTTP endpointu? Předpoklad A4: ano. Kdyby byl HTTP, přibude route jen pro service token nebo cookie a nové B#/T#, aby ji nešlo zavolat Claude access tokenem.

Focus je uzavřený v R11. `allow_focus_write(ServicePrincipal)` se nezakazuje. Další otázka k tomu není.

## Vyřešení nálezů

Ledger: NEW-1 = C5, NEW-2 = C6, NEW-3 = C7, NEW-4 = C8, NEW-5 = C9, NEW-6 = C10. Kolo r=1 zavřelo C12, C13 a C14. Kolo r=2: C11 (test, ne chování) a C15.

| ID | Stav |
|---|---|
| C1 | vyřešeno (rozhodnutí uživatele, beze změny). R11, B44, B45: service token i `OAuthPrincipal` s `brain:write` smí `apply_focus`. `allow_focus_write(ServicePrincipal)` se nezakazuje. Samotný `brain:read` focus nezapisuje. |
| C2 | vyřešeno. B54, B55, T8, T11. Google POST dostane `/oauth/mcp/callback`. Na Claude jde uložený `claude_state`. |
| C3 | vyřešeno. R15, B56–B58, T21. Read smí jen warm. Při stale a OAuth jen s read se `mode="rebuild"` neotevře. |
| C4 | vyřešeno. R10, B59, B60, T16. Mapa je totální. Neznámý nástroj a každý write nástroj s pouhým `brain:read` vnitřní funkci nespustí. |
| C5 (NEW-1) | vyřešeno. R4, B61, T22, F5, F7, riziko 1 a 21. `add-oauth-volume.sh` po INSERT queueje deployment se `restart_only=false` jako `setup-coolify.sh:192-207`. Pepper se ukládá v UI před tím deploymentem. Restart kontejneru mount ani env nezapne. |
| C6 (NEW-2) | vyřešeno. R12, B49, T20, F4. `run_tool` je jediný východ všech 33 wrapperů a na cestách `ok`, `error` a `denied` píše právě jeden JSON. |
| C7 (NEW-3) | vyřešeno. R8, B54, B63, T11, T14. Nové spojení na operaci, zámek jen kolem SQL, žádné `check_same_thread=False` a žádný zámek přes `await` na Google. Navazující věta kvůli C10: čekající vlákno family neruší; ruší ji až pozdější replay (B34, B35). |
| C8 (NEW-4) | vyřešeno. R15, B62, T21. `get_context` nejde přes `_call` (`mcp_app.py:55-63`). `run_tool` vrátí `_error_result` jako `get_task` (`254-258`). |
| C9 (NEW-5) | vyřešeno. R8, A8, B8, B15, B17–B21, B25, B33, B34, B36, B38–B41, T5, T8, T9, T13, T14, F3, riziko 22. Úspěch token endpointu je HTTP 200 a klíče `access_token`, `token_type`, `expires_in`, `refresh_token`, `scope`. Chyba je HTTP 400 a klíč `error`. `HTTPException` z `oauth_routes.py:102-103` se nekopíruje, takže v těle není `detail` ani `error_reason`. MCP `401` (B1) `error_reason` nechává. |
| C10 (NEW-6) | vyřešeno. R8, B34, B35, T14, riziko 5. Po dvou souběžných refreshech téhož tokenu access z vítěze na MCP projde a family žije. Family se ruší až dalším requestem se starým refreshem, který začne až po uvolnění zámku. Počítadlo od C13 není globální `waiters`, je to `waiters[hash]` / `pardon[hash]`. |
| C11 | vyřešeno. B65, T23, riziko 23. Chování scope se nemění. U grantu s write T23 u chybějícího parametru, `""`, `"   "` i samotného `offline_access` zavolá `update_task` a vnitřní funkce musí běžet. JSON rovnost nestačí. Grant jen s `brain:read` write funkci nezavolá. |
| C12 | vyřešeno. R14, A11, B67, T11, F3, riziko 24. Zamítací URL i `Location` skládá `urlencode`. Do meta atributu jde `html.escape(url, quote=True)`. Test má v `state` uvozovku, `&`, `<` a nový řádek a čte hodnotu až po parse HTML. |
| C13 | vyřešeno. Úložiště, B68, T14, F1, riziko 5. `pardon[hash] = waiters[hash]` v okamžiku commitu. Souběžný refresh jiného grantu pardon prvního nezvedne a replay jeho starého refreshe family odvolá. B35 (dva refreshe téhož tokenu) zůstává. |
| C14 | vyřešeno. R8, A11, B5, B69, T3, T8, T11, riziko 25. `iss` na úspěšném `302`, na chybovém `302` i v meta refresh je přesně `(BRAIN_PUBLIC_URL or "").strip().rstrip("/")`, báze z `auth_google.py:30`. Příznak v metadatech sám nestačí. Token JSON `iss` nemá. |
| C15 | vyřešeno. Úložiště (`finally`), B70, T14, F1, riziko 5. Po odečtu vlastního `waiters[hash]`, když volání pardon nezapsalo a ještě ho nespotřebovalo, `finally` `pardon[hash]` sníží a nulu smaže. Vítěz, který pardon zapsal, ho `finally` nesníží. Pád čekajícího vlákna pak nenechá replay bez odvolání family. |

## Delta tohoto kola

Kolo r=2. C12, C13 a C14 beze změny textu. R11 (focus) beze změny.

- C11: odstavec scope u token endpointu (věta, že JSON rovnost nestačí), B65, T23, F6, riziko 23. Čtyři vstupy (chybí, `""`, `"   "`, jen `offline_access`) každý zavolá `update_task`. Negativní assert u grantu jen s `brain:read` zůstává.
- C15: úložiště, bullet `finally`, nové B70, T14, F1, F6, věta v riziku 5. `finally` sníží pardon jen čekajícímu volání, které ho nezapsalo a nespotřebovalo. Vítěz rotace svůj zápis nesmaže.
