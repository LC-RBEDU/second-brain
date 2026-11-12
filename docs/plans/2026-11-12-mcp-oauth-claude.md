# Plán: MCP OAuth pro Claude

## Osnova rozhodnutí

Uzavřená rozhodnutí uživatele se znovu neotvírají. Kde brief z 11. 11. říká něco jiného (zákaz focus pro stroj, samostatný token per klient, audit starých IP, rotace service tokenu, `set_focus` jen pro člověka), platí věta z konverzace níže. Grill 12. 11. změnil A2 a zavřel A-G1 až A-G10. Druhý grill se nespouští.

### Požadavky

R1 — Org connector v Claude Team bez sdíleného bearer tokenu. Každý se přihlásí sám, Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá. Zdroj: brief, varianta A.

R2 — Allowlist je jen `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní Gmail neprojde. Zdroj: rozhodnutí z konverzace. Dnešní cookie allowlist jsou přesně tyto dvě adresy a `hd` se neposílá.

R3 — Jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Tokeny se nedělí. Audit starých IP se nedělá. Tahle práce service token znovu nerotuje. Zdroj: rozhodnutí z konverzace a mimo rozsah.

R4 — Úložiště tokenů je nový SQLite mimo git vault a mimo `/data/vault`. Druhý Coolify persistent volume. Restart ani deploy nesmí odhlásit Claude, jakmile je volume připojené. Replicas Brainu zůstávají 1. Zdroj: rozhodnutí z konverzace.

R5 — Dnešní cookie OAuth (`/oauth/authorize`, `/oauth/callback`, cookie `sb_brain_session`) zůstává a dál pouští MCP i REST. Claude ho jako MCP OAuth nepoužije. Zdroj: rozhodnutí z konverzace.

R6 — Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi, jiný než `{veřejná URL}/oauth/callback`. Přidání URI do Google konzole je ruční krok člověka. Zdroj: rozhodnutí z konverzace.

R7 — Org connector se do organizace přidá až po testu, že cizí účet z organizace token nedostane. Ten test není pytest a není `rbu-tester`. Zdroj: rozhodnutí z konverzace.

R8 — Focus smí na pokyn člověka Grok, Cursor i Claude. Doslova: „Omezení neplatí - focus můžou na pokyn člověka řešit i Grok / Cursor / Claude.“ `BRAIN_SERVICE_TOKEN` dál smí `apply_focus`. Claude OAuth principal ho smí taky. `allow_focus_write(ServicePrincipal)` se nezakazuje. Pokyn člověka je dnešní tok návrh a pak apply. Nový příznak souhlasu se nezavádí. Zdroj: rozhodnutí uživatele.

R9 — Zamítací HTML není dashboard ani nový shell. Souhlasová stránka taky ne. V DONE auditu `TESTER: přeskočeno (profil SECOND_BRAIN, bez UI)`. `rbu-tester` se nevolá. Vizuální B# a layout probe se nečekají. Zdroj: rozhodnutí z konverzace a grill.

R10 — Souběžný refresh téhož tokenu: jeden z nich vydá tokeny a family nechá živou. Ostatní souběžné pokusy family nezruší a druhou sadu tokenů nevydají. Poražený souběh vrací `invalid_grant`. Pozdější replay starého refreshe, až po návratu prvního, family zruší. `temporarily_unavailable` se pro ten souběh nepoužije. Zdroj: rozhodnutí z konverzace 12. 11. a A-G10.

R11 — Brain MCP je pro Claude OAuth 2.1 resource server. Neautorizovaný požadavek na MCP vrací `401` a `WWW-Authenticate` s odkazem na Protected Resource Metadata. Vedle toho metadata authorization serveru, PKCE S256, granty `authorization_code` a `refresh_token`, Dynamic Client Registration. Povolené redirect URI jen `https://claude.ai/api/mcp/auth_callback` a `https://claude.com/api/mcp/auth_callback`. V konfiguraci connectoru žádný token a žádný client secret (veřejné Client ID smí být). Zdroj: brief, fáze 1 a akceptační bod 1. Dnešní MCP `401` je JSON bez `WWW-Authenticate`.

R12 — Scope oddělí čtení a zápis. Nástroj mimo udělený scope Brain odmítne. Věta briefu „`set_focus` jen pro člověka“ neplatí, nahrazuje ji R8. Zdroj: brief, fáze 1, zúženo R8.

R13 — Odebrání e-mailu z allowlistu nebo odvolání tokenu zastaví další volání toho člověka a nesáhne na service token ani na cookie session ostatních. Každé volání s OAuth access tokenem allowlist znovu ověří. Zdroj: brief, akceptační bod 5.

R14 — U volání nástroje je dohledatelná identita, klient, nástroj, čas a výsledek. Záznam není v git vaultu. U service tokenu je identita `service`, protože jeden token sdílí víc klientů (R3). Zdroj: brief, akceptační bod 4, a zákaz zápisu auditů do git vaultu.

R15 — Žádné odhady effortu. Opuštěný plán z 11. 11. se dál neupravuje. Fáze 0 z briefu (auditní poznámka do vaultu) se do vaultu nezapisuje. Zdroj: zadání pipeline a mimo rozsah.

R16 — Jen hostované plochy: web, Desktop, mobil a Cowork. Loopback se nepřijímá. Claude Code se tímhle OAuth nepřihlásí a dál může jet service tokenem. Claude Code je mimo akceptaci. Registrace hostovaného connectoru nesmí spadnout proto, že CIMD dokument Claude Code uvádí loopback. DCR s redirecty z R11 musí projít. `https://claude.com/api/mcp/auth_callback` v R11 zůstává. Zdroj: Q1, volba hosted.

### Produktová rozhodnutí

Uzavřeno spolu s R1–R16. Další volby, které uživatel doslovně neřekl, jsou v předpokladech A-G1 až A-G10 a v návrhu. Mechanismus souběžného refresh je v návrhu: jeden zámek na hash předloženého tokenu a příznak, jestli volající na zámek čekal. Žádné počítadlo a žádná množina `request_id`.

### Předpoklady

A1 — Veřejná báze je `https://brain.cyprovi.cz` bez koncového lomítka. Člověk v Claude zadá resource s lomítkem. Ověřeno, že MCP dnes visí na `/mcp` a cookie callback je `{báze}/oauth/callback`.

A2 — Hostované plochy (web, Desktop, mobil, Cowork) sdílejí HTTPS callbacky z R11. Claude Code používá loopback a ten se odmítá. Věta, že Claude Code stačí dvě HTTPS URL, je proti dokumentaci Claude a po Q1 neplatí. Claude Code je mimo akceptaci a dál může použít service token.

A3 — Publikovaná identita hostovaného Claude je veřejný klient bez secretu. Když ji Claude nepoužije, stačí DCR se stejnými dvěma redirecty. Důvěrný klient se secretem v connectoru by rozbil R11.

A4 — Jedna sada metadat a jeden authorize/token kód stačí pro specifikace 2025-03-26, 2025-06-18 a 2025-11-25. Druhá implementace protokolu nevzniká. Odlišnosti 2025-11-25 jsou vypsané v návrhu.

A5 — SQLite na jednom volume drží jen proto, že replicas zůstávají 1 a proces je jeden uvicorn bez `--workers`. Druhá replika nebo druhý worker by sdílený soubor a zámek v paměti neměly.

A6 — „Family“ je řetěz refresh tokenů jednoho uděleného loginu. Každý úspěšný login je vlastní family. Replay znamená znovu předložit refresh, který už úspěšná rotace nahradila, a to až když ta rotace volajícímu vrátila nové tokeny.

A-G1 až A-G10 jsou závazné předpoklady z grillu. Nejsou otevřené. Jejich text je v sekci Předpoklady plánu.

### Co by jiná odpověď změnila

Uzavřeno grilllem, jiná odpověď by šla proti rozhodnutí uživatele: R1–R16, A-G1 až A-G10, jeden service token, zákaz auditu starých IP, cookie OAuth ponechané, stejný Google klient, focus pro service i Claude, replicas 1, skip Testera, loopback odmítnutý, poražený refresh je `invalid_grant`.

| # | Kdyby platilo něco jiného | Co se v plánu změní |
|---|---|---|
| 1 | Jeden scope místo read/write | Zmizí zákaz rebuildu a zápisu pro read. R8 (focus) zůstane. |
| 2 | Vynechaný scope na authorize znamená jen čtení | Proti A-G1. Claude bez explicitního write nezapíše focus ani rebuild. |
| 3 | Jen DCR, bez publikované identity | Pořád splní R11, pokud klient zůstane veřejný a redirecty ty dvě URL. Claude by nesměl vyžadovat obě reklamy najednou. |
| 4 | Claude Code má přece jen projít | Proti R16. Přibyl by loopback a port-agnostické srovnání. Teď se nepřidává. |
| 5 | Resource bez koncového lomítka | Změní se řetězec, který člověk zadá do Claude a který vrací metadata. |
| 6 | Jiné životnosti tokenů | Proti A-G5. Změní se jen čísla. |
| 7 | Jiná cesta volume, pořád mimo vault a mimo `/data/vault` | Změní se jen mount. |
| 8 | Audit jinam než na stdout, pořád mimo git vault | Změní se jen cíl záznamu. |
| 9 | Pepper smí spadnout na service token nebo cookie secret | Odmítnuto. Rotace service tokenu by buď odhlásila Claude, nebo z něj šlo razit OAuth token. |
| 10 | Poražený souběh je `temporarily_unavailable`, nebo replay family neruší | Proti R10 a A-G10. |

## Zadání a požadavky

R1 až R16 jsou v osnově, včetně Q1 jako R16. Tady jen to, co grill upřesnil a co patří do akceptace implementace.

- A-G1: vynechaný scope na authorize u allowlistu znamená `brain:read` i `brain:write`. Na refreshi vynechání znamená scope grantu. Read se na write nerozšíří. `offline_access` se neinzeruje. Když přijde, zahodí se a není `invalid_scope`. Refresh token u `authorization_code` je vždy.
- A-G2: `get_context` s `brain:read` je jen warm čtení. Rebuild chce `brain:write`. Service token a cookie session rebuildují jako dnes.
- A-G3: Access z nového OAuth platí jen na MCP. REST `/v1/*` dál bere cookie nebo service token. `WWW-Authenticate` je jen na MCP `401`, a jen když request nemá platnou cookie, platný service token ani platný OAuth access. Platný service token na SQLite nesahá.
- A-G4: Odvolání jednoho grantu je příkaz v kontejneru, bez HTTP route. Odebrání e-mailu je změna allowlistu v kódu. Každé MCP volání s OAuth tokenem allowlist znovu ověří.
- A-G5: transakce 10 minut, kód 60 sekund, access 1 hodina, refresh 30 dní, absolutní strop grantu 90 dní. Životnost transakce se zapíše jen jako `expires_at` (now + 10 min). Odmítnutí neznámé nebo staré transakce je predikát `expires_at <= now`, včetně rovnosti. „Věk nad 10 minut“ se nepoužívá a není to jiný test. Stejný predikát běží na `POST /oauth/mcp/continue` a znovu na callbacku před výměnou u Google a před vložením kódu. Restart s připojeným volume session neruší.
- A-G6: každý úspěšný login je vlastní family. Rotace v jedné family neodhlásí druhou.
- A-G7: před Google je stránka se jménem klienta, scope a hostname redirectu. Zamítnutí allowlistu allowlist nevypisuje a vrátí `access_denied` se `state` klienta. `state` v HTML je `urlencode` a HTML escape.
- A-G8: Enterprise Managed Auth a `jwt-bearer` se nedělají.
- A-G9: mapa nástrojů je 13× read a 20× write, přesně jména níže. Suchý běh scope nesnižuje. Nástroj mimo mapu se nespustí.
- A-G10: poražený souběžný refresh vrací `invalid_grant` a family nechá živou. `temporarily_unavailable` by Claude po starém refreshi zkusil znovu a z toho by byl replay, který family ruší.

Mimo rozsah: dělení a nová rotace service tokenu, audit historických IP, OAuth pro dashboard, Grok a Cursor, zápis secretů nebo auditů do git vaultu, další úpravy `docs/plans/2026-11-11-mcp-oauth-claude.md`, loopback a Claude Code, Enterprise Managed Auth, `jwt-bearer`, HTTP route na odvolání, vizuální gate, `rbu-tester`, ostrý zápis do vaultu touto změnou, nový deploy hub cronu.

Read (13): `get_context`, `read_file`, `list_dir`, `export_tasks`, `find_tasks`, `get_task`, `list_children`, `get_tree`, `list_reminders`, `get_triage_candidates`, `slack_live`, `get_meeting_prep`, `allocate_task_id`.

Write (20): `update_task`, `append_task_note`, `set_focus`, `propose_focus`, `apply_focus`, `edit_task_body`, `toggle_step`, `close_task`, `create_task`, `bulk_update`, `schedule_reminder`, `cancel_reminder`, `finalize_meeting`, `ingest_sembly`, `capture_daily`, `mailbox_propose`, `mailbox_apply`, `external_propose`, `external_apply`, `prepare_meeting`.

## Předpoklady

A1 až A6 a A-G1 až A-G10 výše. Doplňky bez nové otázky:

A7 — Pepper je env `BRAIN_OAUTH_TOKEN_PEPPER`. Hash tokenu je HMAC-SHA256. Chybějící pepper nepadá na `BRAIN_SERVICE_TOKEN` ani na `BRAIN_SESSION_SECRET`. Cookie serializer v `oauth_routes.py` se nemění.

A8 — Soubor je `BRAIN_OAUTH_DB`, default `/data/oauth/brain-oauth.sqlite`. Host mount `/data/second-brain-oauth`. Cesta, jejíž `realpath` leží v `GIT_VAULT_ROOT` nebo pod `/data/vault`, se neotevře.

A9 — Úložiště dnes na produkci není. Objem po roce jednoho člověka je řádově stovky řádků (loginy a rotace), ne tabulka obchodních dat. Ověření po prvním přihlášení: v kontejneru `sqlite3 /data/oauth/brain-oauth.sqlite 'SELECT COUNT(*) FROM access_tokens;'`. Dotaz před nasazením nemá smysl, soubor ještě není.

A10 — Dokumentace Claude (stránka Authentication for connectors, načtená 12. 11. 2026) říká: Claude bere jen první položku `authorization_servers`; CIMD použije, když metadata mají `client_id_metadata_document_supported: true` a v `token_endpoint_auth_methods_supported` je `none`, jinak spadne na DCR; discovery, registrace a token mají odpovědět do 10 s, refresh do 30 s. Hostovaný CIMD `https://claude.ai/oauth/mcp-oauth-client-metadata` má dnes jediný redirect `https://claude.ai/api/mcp/auth_callback`, `token_endpoint_auth_method` `none` a v `grant_types` i `jwt-bearer`. Dokument Claude Code `https://claude.ai/oauth/claude-code-client-metadata` uvádí loopback. `https://claude.com/api/mcp/auth_callback` v tom hostovaném dokumentu dnes není a zůstává povolený pro DCR (R11, R16).

A11 — Checklisty jsou z RB Universe `docs/agent_playbooks/quality-checklists.md`. V SECOND_BRAIN ten soubor není. Alembic, RBAC, subnav, `qa_gate.mjs`, Celery a frontend se netýkají.

## Současný stav (ověřeno v kódu)

`vps/second-brain-brain/app/auth_google.py:9-14` — `ALLOWLIST` jsou přesně ty dva e-maily. `email_allowed` (`45-46`) je case-insensitive. `authorize_url` (`49-67`) skládá query přes `urlencode`, posílá `prompt=select_account` a neposílá `hd`.

`vps/second-brain-brain/app/oauth_routes.py:21-29` — cookie `sb_brain_session`. Prázdný `BRAIN_SESSION_SECRET` spadne na `BRAIN_SERVICE_TOKEN`. `57-77` je sync `GET /oauth/authorize` a stav drží v HttpOnly cookie `sb_oauth_state`. `80-88` je `async def` callback a kód u Google nevymění, dokud `state` nesedí na tu cookie. `91-111` posílá cookie `redirect_uri`. `113-117` při cizím e-mailu vrací 403 a v textu je allowlist. MCP callback allowlist v textu nekopíruje. Cookie route se v tomhle kole nemění. MCP má vlastní cookie, ne `sb_oauth_state`.

`vps/second-brain-brain/app/mcp_auth.py:34-59` — MCP pustí cookie, nebo Bearer shodný se service tokenem, nebo dev bez tokenu. Jinak JSON `401` s `error_reason: client_error`. `WWW-Authenticate` se nenastavuje. Cookie vyhraje nad Bearerem.

`vps/second-brain-brain/app/auth_deps.py:17-49` — REST je cookie, nebo service Bearer, nebo dev. Cizí Bearer je `401` bez OAuth hlavičky.

`vps/second-brain-brain/app/auth_service.py:26-36` — service token je `hmac.compare_digest` proti `BRAIN_SERVICE_TOKEN`. Shoda vrací `ServicePrincipal()`.

`vps/second-brain-brain/app/policy.py:15-25` — `allow_focus_write` pouští `ServicePrincipal`, řetězec `oauth:…` i `dev`.

`vps/second-brain-brain/app/tools/set_focus.py:122-131` — bez `via_apply=True` je `403 focus_requires_proposal` a nic se nezapíše.

`vps/second-brain-brain/app/tools/get_context.py:45-70` — nejdřív `brain_vault(mode="read")`. Když `needs_rebuild` je false, vrátí warm. Když je true, otevře `mode="rebuild"`. Scope principalu nezná.

`vps/second-brain-brain/app/vault_deps.py:141-153` — `mode="read"` má `commit_on_end: False`. Rebuild commituje.

`vps/second-brain-brain/app/mcp_app.py:55-63` — `_call` z `BrainClientError` udělá `RuntimeError`. Klient pak vidí jen `Error executing tool {name}`. `get_task` (`254-259`) a `finalize_meeting` (`456-474`) vracejí `_error_result` / `CallToolResult`. Úspěch `update_task` (`111-137`), `export_tasks` (`215-229`) a `bulk_update` (`391-417`) nejde přes `_call`. `mailbox_apply` a `external_apply` (`505-532`) natvrdo staví `ServicePrincipal(label="mcp")`, takže i lidský principal dnes skončí jako service a `gate_brain_apply` vrátí 403.

`vps/second-brain-brain/app/auth_apply.py:15-26` — service je 403 `human_oauth_required`, řetězec `oauth:` je 501 `oauth_brain_apply_post_f3`. Apply se nezapíná.

`vps/second-brain-brain/app/main.py:90-95` a `142-143` — MCP je mount `/mcp` obalený `McpAuthMiddleware`. Žádná `/.well-known` route.

`vps/second-brain-brain/Dockerfile:28` — jeden proces `uvicorn` bez `--workers`.

`vps/second-brain-brain/requirements.txt` — fastapi, httpx, itsdangerous, mcp, `google-auth-oauthlib`. Balík Authlib tam není. Cookie OAuth ho nevolá: výměna kódu je `httpx` v `oauth_routes.py:91-101`. MCP OAuth Authlib nepřidává. `sqlite3` je ve stdlib.

`vps/second-brain-brain/deploy/setup-coolify.sh:103-107` — persistent volume jen `/data/vault` → host `/data/second-brain-vault`. `192-207` queueje deployment s `restart_only=false`. Samotný INSERT volume bez deploymentu mount na běžícím kontejneru nezapne. Celý skript se znovu nespouští, sahá na env včetně service tokenu (`165-171`).

V `mcp_app.py` je 33 `@mcp.tool`. Jména sedí na A-G9 (13 read, 20 write).

## Návrh

RB Universe vrstvy se netýkají: žádná Alembic migrace, žádné RBAC, žádný Celery, žádný frontend, žádný subnav, žádné `qa_gate.mjs`. MCP nástrojová plocha zůstává. Přibývá OAuth authorization server na tom samém procesu.

### Úložiště

Nový `vps/second-brain-brain/app/oauth_mcp_store.py`. Otevře SQLite jen když nějaká OAuth cesta token čte nebo píše. Import modulu ani úspěšný service-token request soubor neotevírá. Každé volání má vlastní spojení a na zápis `BEGIN IMMEDIATE`. Sdílené spojení mezi vlákny není: default `check_same_thread` by při dvou family spadl. Spojení se zavře ve `finally`.

Tabulky, vše čas v UTC ISO:

- `clients` — DCR klient: `client_id`, `client_name`, `redirect_uris` (JSON). Jen podmnožina dvou URL z R11. Žádný secret.
- `transactions` — rozpracované přihlášení. Primární klíč je `secrets.token_urlsafe`, ne SQLite `rowid`. Dál: klient, přesný redirect z R11 ověřený při GET, scope po A-G1, PKCE challenge, `state` klienta, resource, `expires_at` (+10 min).
- `codes` — hash kódu, vazba na transakci, e-mail, `expires_at` (+60 s), `used_at`.
- `families` — jeden řádek na úspěšný login: e-mail, klient, scope, `created_at`, `absolute_expires_at` (+90 dní), `revoked_at`.
- `refresh_tokens` — hash, `family_id`, stav `active` nebo `rotated`, hash nástupce, `expires_at`, `rotated_at`.
- `access_tokens` — hash, `family_id`, e-mail, scope, `client_id`, `expires_at`.

Raw token se nezapisuje. Hash je HMAC-SHA256 s pepperem. `expires_at <= now` je vypršelé, včetně rovnosti. Věk v minutách se nepočítá. U transakce ten predikát platí na POST pokračování a znovu na callbacku před vložením kódu (B49), ne jen u refreshe.

Cesta: A8. Když pepper chybí, nebo soubor nejde otevřít, nebo cesta padá do vaultu, zápisové OAuth route vrací HTTP 503 a tělo `{"error":"temporarily_unavailable"}`. Bez klíče `detail` a bez `error_reason`. Metadata a MCP `401` jedou dál. Service token SQLite nevolá.

### Metadata a 401 (jedna implementace pro tři specifikace)

Nový `vps/second-brain-brain/app/oauth_mcp_metadata.py`, route na appce před mountem MCP, bez autentizace.

`GET /.well-known/oauth-protected-resource` a `GET /.well-known/oauth-protected-resource/mcp` vrací totéž. `resource` je `{báze}/mcp/` s lomítkem. `authorization_servers` má jedinou položku, bázi bez lomítka. `scopes_supported` je `brain:read` a `brain:write`. `bearer_methods_supported` je `header`. `offline_access` tam není.

`GET /.well-known/oauth-authorization-server`: issuer = tatáž báze, `authorization_endpoint` `/oauth/mcp/authorize`, `token_endpoint` `/oauth/mcp/token`, `registration_endpoint` `/oauth/mcp/register`, `response_types_supported` `code`, `grant_types_supported` jen `authorization_code` a `refresh_token`, `code_challenge_methods_supported` `S256`, `token_endpoint_auth_methods_supported` jen `none`, `client_id_metadata_document_supported` true. Bez `private_key_jwt`. `/.well-known/openid-configuration` se nezakládá.

MCP `401`, když request nemá platnou cookie, platný service token ani platný OAuth access (`mcp_auth.py`): dosavadní JSON `error_reason: client_error` plus

`WWW-Authenticate: Bearer realm="brain", resource_metadata="{báze}/.well-known/oauth-protected-resource/mcp", scope="brain:read brain:write"`.

REST `401` tuhle hlavičku nedostane. OAuth access na `/v1/*` je `401` bez ní.

Čím se 2025-11-25 liší a jak to sedí do jednoho kódu, ne do druhé implementace:

- Discovery smí jít hlavičkou, nebo well-known na kořeni, nebo well-known pod cestou MCP. Děláme všechny tři. Starší klient, který čte jen hlavičku, funguje.
- Klient má posílat `resource` (RFC 8707) na authorize i na token. Když přijde, musí po srovnání sedět na náš resource: scheme a host case-insensitive, jedno koncové lomítko se ignoruje. Když nepřijde, request projde a token je stejně vázaný na náš jediný resource. Neshoda je `invalid_target`.
- `insufficient_scope` ve specifikaci je HTTP 403 na resource request. U nás jeden MCP stream nese read i write. Write mimo scope neshodí session: nástroj se nespustí a vrátí tool error `insufficient_scope` (B42). HTTP 403 celé session by shodil i read na tom samém tokenu.
- CIMD je doporučené až v 2025-11-25. Starší klienti jdou přes DCR. Oba vstupy končí ve stejné authorize/token cestě.
- OpenID Connect Discovery se nedělá. Spec chce aspoň jeden ze dvou discovery mechanismů authorization serveru. Stačí RFC 8414.

### DCR, CIMD, authorize, token

Nový `vps/second-brain-brain/app/oauth_mcp_routes.py`.

DCR `POST /oauth/mcp/register`, JSON. Klient je veřejný: `token_endpoint_auth_method` je `none` nebo chybí. `redirect_uris` je neprázdná podmnožina dvou URL z R11. Jakýkoli jiný redirect, včetně loopbacku, je 400 a klient se neuloží. Samotné dvě URL z R11, i každá zvlášť, projdou (R16). Úspěch je HTTP 201 a JSON s `client_id` (náhodné, ne rowid) a `token_endpoint_auth_method` `none`. Klíč `client_secret` v těle není. Bez `client_id` by Claude neměl čím volat authorize.

CIMD: `client_id` ve tvaru `https://claude.ai/...` nebo `https://claude.com/...` se stáhne (timeout 3 s, bez přesměrování na jiný host, limit velikosti). Jiný host se nestahuje (SSRF). Dokument musí mít `client_id` shodné s URL. Dokument se neodmítne proto, že v `redirect_uris` má loopback, ani proto, že v `grant_types` má `jwt-bearer` (A-G8 a R16). Authorize pak vezme jen requested `redirect_uri`, které je v dokumentu a zároveň je jedna ze dvou URL z R11. Loopback na authorize je odmítnutí bez kódu a bez Google. Cache dokumentu v procesu 5 minut podle této URL. Hostovaný dokument tedy přihlášení na `https://claude.ai/api/mcp/auth_callback` nezablokuje. Claude Code dokument přihlášení loopbackem neotevře.

`GET /oauth/mcp/authorize` na Google ještě nejde. Ověří klienta, redirect (jen dvě URL z R11), `code_challenge_method=S256` (plain a chybějící PKCE jsou `invalid_request`), resource a scope. `offline_access` se zahodí. Vynechaný scope u allowlistovaného toku znamená oba scope. Teprve potom uloží transakci pod náhodné id. HTML souhlasu má jeden formulář: atribut `method="post"` (chybějící method je výchozí GET a na POST route nesedí), `action="/oauth/mcp/continue"` bez query, aby prohlížeč znovu neposlal query z GET. Jediné úspěšné pole je skryté id transakce. Jediný submit je tlačítko Pokračovat. Zrušit je `<a href="/oauth/mcp/cancelled">` mimo ten formulář, bez id a bez `redirect_uri`. `GET /oauth/mcp/cancelled` vrátí 200 a HTML, na SQLite nesáhne, cookie `sb_mcp_oauth_tx` nenastaví, Google nezavolá a kód nezaloží. Není to druhý submit téhož těla: handler by Pokračovat a Zrušit nerozeznal a Zrušit by spustilo Google. Do HTML jdou jméno klienta, scope i `state` jen přes `html.escape(..., quote=True)`. `state` v query navíc přes `urllib.parse.urlencode`.

Pokračování je `POST /oauth/mcp/continue`, sync `def`. Tělo je `application/x-www-form-urlencoded`. Načte transakci podle id. Neznámé id, nebo známé id s `expires_at <= now`: HTTP 400, bez hlavičky `Location`, bez cookie `sb_mcp_oauth_tx`, žádný socket na `accounts.google.com` ani `oauth2.googleapis.com`, řádek transakce se nezmění (neznámé id = žádný INSERT; známé = stejný tuple `SELECT *`), v `codes` nepřibude řádek. Věta „kód se nevydá“ sama nestačí, protože kód vzniká až na callbacku: i tahle větev proto assertuje prázdný přírůstek v `codes`, a callback tu kontrolu opakuje (B49).

`redirect_uri` se z requestu do řádku nikdy nezapíše. POST řádek neaktualizuje ani při úspěchu. Srovnání je po jednom URL-decode, tělo a query zvlášť. Žádné `or`, které vezme první kanál a druhý už nečte:

- parametr v těle chybí a v query chybí → pokračuj (produkční formulář: jen id)
- je jen v jednom kanálu a po decode se rovná uloženému redirectu → pokračuj
- je v obou a po decode se oba rovnají uloženému a sobě navzájem → pokračuj
- cizí hodnota v těle, nebo zvlášť cizí hodnota v query, nebo se tělo a query po decode liší (i když jeden z nich sedí na uložený redirect) → stop. HTTP 400, `Location` chybí (ani Google, ani předané URI), cookie se nenastaví, žádný socket na Google, tuple řádku je stejný jako před requestem, v `codes` nic nepřibude.

Když se pokračuje, nastaví cookie `sb_mcp_oauth_tx` (HttpOnly, SameSite=Lax, Secure podle `_cookie_secure`, max_age 600 s) na to id a teprve pak přesměruje na Google. `Location` vede na `accounts.google.com`. Redirect URI předaný Google je `https://brain.cyprovi.cz/oauth/mcp/callback`, ne cookie callback. Bez `hd`, s `prompt=select_account`. `state` vůči Google je id transakce. Cookie `sb_oauth_state` a `sb_brain_session` se nepřepisují.

`GET /oauth/mcp/callback` je `async def` kvůli Google, stejně jako dnešní cookie callback (`oauth_routes.py:80-88`). Než zavolá Google, srovná query `state` s cookie `sb_mcp_oauth_tx`. Bez shody kód nevydá a na redirect klienta nejde (žádný `Location` na claude.ai ani claude.com). Když cookie sedí, načte transakci znovu. Neznámé id nebo `expires_at <= now`: Google se nezavolá, do `codes` se nevloží řádek, tuple transakce zůstane, odpověď je HTTP 400 bez `Location` (ani Google, ani redirect klienta s `code`). Cookie se na tom stopu nemaže. Jinak výměna kódu u Google používá MCP redirect URI (timeout 20 s). Neúspěch Google nevydá token. E-mail mimo allowlist: HTML „přístup zamítnut“ bez seznamu adres, pak redirect na uložený redirect transakce s `error=access_denied` a se `state` klienta, ne se `state` Google. E-mail na allowlistu: nová family (A-G6), jednorázový kód, redirect s `code` a `state` klienta. Cookie `sb_mcp_oauth_tx` se maže až po tom vyřízení, ne před výměnou u Google.

`POST /oauth/mcp/token` je sync `def`, aby ho Starlette pustil do threadpoolu. Bere `application/x-www-form-urlencoded`. Úspěch je HTTP 200 a JSON `access_token`, `token_type` `Bearer`, `expires_in`, `refresh_token`, `scope`. Chyba je HTTP 400 a JSON s klíčem `error` (`invalid_grant`, `invalid_scope`, `unsupported_grant_type`, `invalid_request`, `invalid_target`, `invalid_client`). Bez `detail` a bez `error_reason`. Route nehází `HTTPException`. Uvnitř zámku není `await`.

`authorization_code` vždy vrátí i refresh (A-G1), ale jen po PKCE. Výměna běží v `BEGIN IMMEDIATE` na vlastním spojení. `S256(code_verifier)` se porovná s uloženou challenge (`compare_digest`). Neshoda je `invalid_grant`, žádný řádek tokenu, `used_at` zůstane prázdné. Shoda udělá `UPDATE … SET used_at=now WHERE used_at IS NULL`. Když se neaktualizuje právě jeden řádek, je to `invalid_grant` a druhý souběh tokeny nezaloží. `refresh_token` rotuje aktivní refresh. Vynechaný scope na refreshi znamená scope grantu. Požadovaný scope musí být podmnožina grantu. Read se na write nerozšíří, jinak `invalid_scope` a family zůstane. `offline_access` se před srovnáním zahodí. `jwt-bearer` a jakýkoli jiný grant je `unsupported_grant_type`. Žádná Enterprise Managed Auth route.

### Souběžný refresh

Route tokenu je sync `def`. Starlette ji dá do threadpoolu, takže druhý refresh může běžet, dokud první drží zámek. `async def` na jednom event loopu (`Dockerfile:28`, jeden uvicorn bez `--workers`) by druhý request pustil až po doběhnutí prvního. Poražený by pak viděl `rotated` a `waited=false` a family by zrušil, což je opak R10. Uvnitř drženého zámku není `await`: na tom samém vlákně by to deadlocklo. Google na token route není.

Jeden procesový `threading.Lock` obalí get-or-create zámku na hash předloženého refresh tokenu. Dvě vlákna nemůžou pro stejný hash dostat dva objekty `Lock`. Žádné počítadlo čekajících, žádná množina id requestů.

```text
lock = get_or_create(hash)          # pod jedním zámkem registru
waited = not lock.acquire(blocking=False)
pokud waited: lock.acquire()        # čeká, až vítěz zámek pustí
try:
    vlastní spojení, BEGIN IMMEDIATE:
        token neznámý, family odvolaná, vypršelá, nebo po absolutním stropu
            → invalid_grant, family se znovu neruší, když už revoked je
        stav active
            → rotace, nové tokeny, family zůstává
        stav rotated a waited
            → invalid_grant, family se neruší
        stav rotated a ne waited
            → family.revoked_at = now, invalid_grant
finally:
    lock.release()
    spojení zavřít
```

Čekající vlákno je to, které `acquire(blocking=False)` neudělalo. Po uvolnění zámku je další volání už nové: zámek je volný, `waited` je false, a to je replay, který family zruší. Dva různé tokeny mají dva zámky, takže rotace jedné family nečeká na druhou (A-G6).

Zámek je v paměti. Drží to jen proto, že proces je jeden a replicas jsou 1. Druhý proces by čekajícího neviděl a replay by přišel dřív. Zámek se z dictu nemaže: smazání mezi `acquire(False)` a blokujícím `acquire` by čekajícího nechalo na starém objektu. Počet klíčů je počet předložených refresh tokenů jednoho člověka.

`temporarily_unavailable` je jen chybějící pepper nebo nezapsatelné úložiště, ne výsledek souběhu.

Test (T34 a T35 v jednom testu) volá dvakrát tutéž funkci, kterou volá route, ze dvou vláken. Nevolá zámek bokem. Assert navíc: endpoint není coroutine (`inspect.iscoroutinefunction` je false). Háček, který v produkci nic nedělá, podrží vítěze uvnitř funkce před `release`. Poražený mezitím vstoupí do té samé funkce (`on_wait` nastaví `Event`, bez spánku).

1. Po puštění vítěze poražený vrátí `error == invalid_grant`, ne `temporarily_unavailable`. Nový refresh z vítězné odpovědi pořád funguje a family nemá `revoked_at`. Kdyby čekající family zrušil, tohle selže.
2. Až obě volání skončí, třetí volání té samé funkce se starým refreshem family zruší. Nový refresh z kroku 1 pak nefunguje. Kdyby family zůstala živá, tohle selže.

Háček a `on_wait` nejsou počítadla. Produkční kód je jen get-or-create, `acquire(blocking=False)` a větev `waited`.

### Scope, get_context, focus, apply, audit

Nový `vps/second-brain-brain/app/oauth_mcp_scope.py`: dict jméno nástroje → `read` nebo `write`, přesně A-G9. Test srovná klíče s názvy `@mcp.tool` na `build_mcp()`. Chybějící nebo přebývající jméno test shodí. Suchý běh u `update_task`, `create_task`, `bulk_update`, `finalize_meeting` a `prepare_meeting` write nesnižuje.

Nový principal `OAuthPrincipal(email, scopes, client_name)`. Cookie dál vrací řetězec `oauth:{email}` bez scope. Service token dál `ServicePrincipal`.

`run_tool(name, fn)` v `mcp_app.py` je jediné místo scope a auditu. Každý `@mcp.tool` ho volá, včetně pěti, které dnes `_call` míjí (`update_task`, `export_tasks`, `get_task`, `bulk_update`, `finalize_meeting`). Pořadí: scope, pak `fn`, audit ve `finally`. Nástroj mimo mapu se nespustí. OAuth bez potřebného scope nespustí `fn` a vrátí tool error `insufficient_scope` (stejný tvar jako `_error_result`, ať klient vidí JSON). Service token, cookie a dev scope nemají a mapou neprocházejí jako odmítnutí: dnešní plný přístup zůstává. Existující tvary chyb (`oid_mismatch` jako `CallToolResult`, `ExportTasksResult`) `run_tool` vrací beze změny.

`get_context`: když je principal `OAuthPrincipal` a nemá `brain:write`, nová větev otevře jen `mode="read"`. Když `needs_rebuild` je true, hodí `BrainClientError` `context_rebuild_requires_write` a `mode="rebuild"` neotevře. MCP to vrátí jako `_error_result`, ne přes `_call`. Service, cookie, dev a REST `get_context` volají dnešní funkci včetně rebuildu.

`allow_focus_write`: `ServicePrincipal` zůstává povolený. Řetězec `oauth:` a `dev` taky. `OAuthPrincipal` smí focus jen se scope `brain:write`. Read-only OAuth se k `set_focus` navíc nedostane, protože mapa ho má jako write. `via_apply` se nemění.

`mailbox_apply` a `external_apply` přestanou vyrábět `ServicePrincipal(label="mcp")` a předají `get_brain_principal()`. Service tedy zůstane 403, cookie i Claude OAuth 501. Apply se nezapíná. Scope write znamená, že read token ty nástroje nespustí.

Audit: `vps/second-brain-brain/app/oauth_mcp_audit.py`, jeden JSON řádek na stdout na každé volání nástroje (`ok`, `error`, `insufficient_scope`). Pole: identita, klient, nástroj, čas UTC, výsledek. OAuth: e-mail a `client_name`. Cookie: e-mail a klient `cookie`. Service: identita i klient `service`. Do vaultu se nezapisuje.

### Odvolání a volume

`python -m app.oauth_mcp_revoke --email <adresa>` v kontejneru nastaví `revoked_at` všem family toho e-mailu. `--family <id>` odvolá jednu. Žádná HTTP route. Další MCP volání s access tokenem té family je 401. Jiná family téhož e-mailu při `--family` zůstane. Service token a cookie se nemění.

Volume přidá nový `vps/second-brain-brain/deploy/add-oauth-volume.sh`. Idempotentní INSERT do `local_persistent_volumes`: mount `/data/oauth`, host `/data/second-brain-oauth`, jen když tam ještě není. Pak queue deploymentu se `restart_only=false`, stejně jako podmínka ve `setup-coolify.sh:192-207` (nequeue, když už běží queued nebo in_progress). Skript nekopíruje env a na `BRAIN_SERVICE_TOKEN` nesahá. Pepper musí být v Coolify uložený před tím deploymentem, jinak OAuth po startu vrací 503 a service token dál funguje. `setup-coolify.sh` se na živé aplikaci nespouští. Do něj se stejný INSERT doplní jen jako větev pro úplně novou instalaci, za stejnou podmínkou „jen když řádek není“, a queue nechá tam, kde už je (na konci souboru), aby greenfield deploy volume viděl.

README Brainu: člověk přidá v Google konzoli redirect `https://brain.cyprovi.cz/oauth/mcp/callback` na stávajícím klientovi. Bez toho Google výměna kódu selže a token se nevydá. Org connector se do Claude přidá až po ručním testu T60.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| B1 | MCP bez cookie, bez service tokenu a bez OAuth access | `401`, JSON `error_reason=client_error`, `WWW-Authenticate` s `resource_metadata` na `/.well-known/oauth-protected-resource/mcp` a `scope=brain:read brain:write` | R11 | T1 |
| B2 | MCP s platným service tokenem | request projde, 0 otevření SQLite, bez `WWW-Authenticate` | R3, A-G3 | T2 |
| B3 | MCP s platnou cookie allowlistu | principal `oauth:{email}`, 0 otevření SQLite | R5 | T3 |
| B4 | MCP s platným OAuth access, e-mail pořád na allowlistu | `OAuthPrincipal`, nástroj se spustí | R1, R13 | T4 |
| B5 | OAuth access, e-mail už není na allowlistu | `401`, nástroj se nespustí | R13, A-G4 | T5 |
| B6 | OAuth access vypršelý nebo family s `revoked_at` | `401` a hlavička jako B1 | R13, A-G5 | T6 |
| B7 | `GET /v1/context` s OAuth access | `401` bez `WWW-Authenticate` | A-G3 | T7 |
| B8 | REST se service tokenem a s cookie | dnešní chování, beze změny těla `401` | R3, R5 | T8 |
| B9 | `X-API-Key` na MCP | `401`, klíč se nebere jako token | R3 | T9 |
| B10 | oba well-known PRM | stejný `resource` `{báze}/mcp/`, jediný authorization server | R11 | T10 |
| B11 | AS metadata | `registration_endpoint`, CIMD true, auth methods jen `none`, granty jen code a refresh, žádný OIDC dokument | R11, A-G8 | T11 |
| B12 | DCR s oběma URL z R11, nebo s jednou z nich | 201, tělo má `client_id` a `token_endpoint_auth_method=none`, klíč `client_secret` není; s tím `client_id` GET authorize dojde na souhlasovou stránku | R11, R16 | T12 |
| B13 | DCR s loopbackem nebo jiným redirectem | 400, klient se neuloží | R16 | T13 |
| B14 | CIMD dokument jen s `https://claude.ai/api/mcp/auth_callback` a s `jwt-bearer` v grant_types | authorize na ten redirect dojde na souhlasovou stránku, dokument se neodmítne | R16, A-G8, A10 | T14 |
| B15 | CIMD dokument, který navíc uvádí loopback; authorize s loopbackem | klient se načte, kód se nevydá, Google se nezavolá | R16 | T15 |
| B16 | authorize redirect mimo R11, nebo PKCE jiné než S256 | odmítnutí, žádný redirect na Google | R11 | T16 |
| B17 | `resource` sedí i s jinou velikostí písmen hosta nebo jedním lomítkem navíc | přijmout; neshoda je `invalid_target`; chybějící `resource` přijmout | R11 | T17 |
| B18 | authorize bez scope | grant má `brain:read` i `brain:write` | A-G1 | T18 |
| B19 | scope obsahuje `offline_access` | zahodí se, není `invalid_scope`, code grant stejně vrátí refresh | A-G1 | T19 |
| B20 | souhlasová stránka | před Google je jméno klienta, scope a hostname redirectu; formulář má atribut `method="post"`, `action` bez query a posílá jen id; jediný submit je Pokračovat; Zrušit je odkaz na `GET /oauth/mcp/cancelled` a ten request nevolá Google, kód nezaloží a řádek transakce nechá stejný | A-G7, R9 | T20 |
| B21 | `state`, jméno klienta a scope v HTML | vše přes `html.escape(..., quote=True)`; `state` v query navíc `urlencode`; surový `<` ani uvozovka v těle nejsou | A-G7 | T21, T53 |
| B22 | Google userinfo e-mail mimo allowlist | žádný token, HTML bez výpisu allowlistu, redirect `access_denied` se `state` klienta | R2, A-G7 | T22 |
| B23 | Google token endpoint vrátí non-200 | žádný token | R6 | T23 |
| B24 | platný code a platný verifier, podruhé až po prvním návratu | access i refresh, nová family; druhé předložení je `invalid_grant` | A-G1, A-G6, R11 | T24 |
| B25 | refresh bez scope, grant je jen read | zůstane read, write se nepřidá | A-G1 | T25 |
| B26 | refresh chce write a grant je read | `invalid_scope`, family živá | A-G1 | T26 |
| B27 | dva souběžné refreshe téhož tokenu | jeden vrátí tokeny, druhý `invalid_grant` (ne `temporarily_unavailable`), family živá, nový refresh funguje | R10, A-G10 | T34 |
| B28 | třetí předložení starého refreshe až po návratu vítěze | `invalid_grant` a family `revoked_at`; nový refresh z B27 už nefunguje | R10, A-G10 | T35 |
| B29 | rotace nebo replay jedné family | druhá family téhož e-mailu zůstane | A-G6 | T36 |
| B30 | `expires_at == now`, nebo refresh po 90 dnech od vzniku family | `invalid_grant` | A-G5 | T37 |
| B31 | chybí pepper, nebo DB cesta je pod `/data/vault` | metadata a B1 jedou; register, authorize zápis a token vrací 503 `{"error":"temporarily_unavailable"}`; service MCP projde | R4, A7 | T39 |
| B32 | prázdný `BRAIN_SESSION_SECRET` | cookie serializer dál spadne na service token; OAuth hash ne | R5, A7 | T40 |
| B33 | OAuth jen `brain:read` volá write nástroj, včetně `dry_run` | `fn` se nezavolá, tool error `insufficient_scope`, audit řádek | R12, A-G9 | T41 |
| B34 | OAuth `brain:write` volá write nástroj | spustí se | R12, R8 | T42 |
| B35 | mapa vs. `build_mcp()` | přesně 33 jmen, 13 read a 20 write z zadání; jméno mimo mapu se nespustí | A-G9 | T44 |
| B36 | `get_context`, OAuth jen read, `needs_rebuild` true | `context_rebuild_requires_write`, `mode=rebuild` se neotevře | A-G2 | T45 |
| B37 | `get_context`, OAuth write nebo service nebo cookie, `needs_rebuild` true | dnešní rebuild | A-G2, R5 | T46 |
| B38 | `apply_focus` se service tokenem a s OAuth write | focus se zapíše; `set_focus` bez `via_apply` je dál 403; OAuth read focus nezapíše | R8 | T47 |
| B39 | `mailbox_apply` / `external_apply` | service 403, cookie i OAuth 501; read token nástroj nespustí | R5 | T48 |
| B40 | každé volání nástroje | jeden JSON řádek na stdout; service je `service`; do vaultu se nezapíše | R14 | T49 |
| B41 | grant `jwt-bearer` | `unsupported_grant_type`; route Enterprise Managed Auth není | A-G8 | T50 |
| B42 | příkaz revoke `--family` | ta family je `401`, jiná family téhož e-mailu žije; HTTP route na revoke není | A-G4, A-G6 | T51 |
| B43 | prázdná SQLite (soubor bez řádků) | service token funguje; neznámý Bearer je 401 jako B1 | A-G3 | T2 |
| B44 | code starší než 60 s, access starší než 1 h, refresh starší než 30 dní | `invalid_grant` | A-G5 | T37 |
| B45 | POST `/oauth/mcp/continue` | POST jen s id a bez query nastaví cookie `sb_mcp_oauth_tx` a `Location` vede na `accounts.google.com`; stejně i jediný kanál, nebo oba, když po decode sedí na uložený redirect; cizí `redirect_uri` v těle a zvlášť cizí v query nechá řádek byte-shodný (stejný tuple `SELECT *`, žádný UPDATE ani INSERT), žádný socket na Google, HTTP 400 bez `Location` na Google i bez `Location` na předané URI; tělo a query se po decode liší → stop, i když jeden kanál sedí (žádné `or` na první shodě) | R11 | T52 |
| B46 | callback bez cookie `sb_mcp_oauth_tx`, nebo cookie nesedí na `state` | kód se nevydá, odpověď nemá `Location` na redirect klienta | R11 | T54 |
| B47 | výměna kódu se špatným `code_verifier` | `invalid_grant`, žádný access ani refresh, `used_at` zůstane prázdné | R11 | T55 |
| B48 | dvě překrývající se výměny téhož kódu s platným verifierem | právě jedna sada tokenů, druhá `invalid_grant` | R11 | T56 |
| B49 | POST pokračování, nebo callback po shodě cookie a před vydáním kódu; neznámé id nebo `expires_at <= now` | Google se nezavolá, řádek transakce se nezmění, v `codes` nic nepřibude, HTTP 400 bez `Location` na Google a bez `code` na redirect klienta; predikát je `expires_at <= now` včetně rovnosti, ne věk nad 10 minut | A-G5, R11 | T57 |

Checklist A, co v tabulce není samostatně:

1. Prázdná data — B43 a B31. Prázdný soubor není výpadek.
2. Chybějící hodnoty — B16, B17, B18, B31, B49 (neznámé id). `None` scope a chybějící `resource` mají řádek.
3. Hranice období — fiskální rok se netýká. Hranice TTL je B30, B44 a B49 (`expires_at <= now` včetně rovnosti). Časy UTC. Test B49 sloupec nastaví, nespí 10 minut. `set_focus` dál počítá týden v Europe/Prague, tahle změna to nemění.
4. Měny a DPH — netýká se, žádné peníze.
5. Oprávnění — B2, B4, B5, B33, B38, B39. RBAC RB Universe se netýká.
6. Stav syncu — netýká se, není to sync pipeline. Rebuild kontextu je B36 a B37.
7. Smazané entity — odvolaná family je B6 a B42. Pipedrive merge se netýká.
8. Duplicitní akce — B24 (kód podruhé), B27, B28, B29, B48 (souběh jedné výměny).
9. Chyba externí služby — B23. Timeout Google je 20 s a taky nevydá token (T23 to mockuje jako non-200).
10. Zpětná kompatibilita — B2, B3, B7, B8, B32, B39. Staré URL `/oauth/callback` a `/mcp` zůstávají.
11. Konzistence Pipedrive / Allfred / Universe — netýká se.

Tester: `TESTER: přeskočeno (profil SECOND_BRAIN, bez UI)`. Souhlasová a zamítací HTML nejsou dashboard. Vizuální B# a layout probe se nezakládají. Playwright-T6-full se nezakládá.

## Výkonový rozpočet (P)

Produkční SQLite ještě není (A9). Žádný řádek neroste s vaultem. Cíl všech nových HTTP cest je cold i warm pod 500 ms, kromě Google výměny na callbacku, která je jeden externí POST s timeoutem 20 s a není to MCP request Claude. Claude dává discovery, registraci a tokenu 10 s a refreshi 30 s (A10). Naše cíle jsou pod tím o víc než řád.

Společné pro všechny nové cesty: do Pythonu jdou jen řádky podle primárního klíče, ne celá tabulka. Žádné stránkování, payload metadat pod 2 KB, token odpověď pod 2 KB. Žádný Allfred, Pipedrive ani vault read na authorize/token/metadata. Frontend, React Query a worker chord se netýkají. Jeden uvicorn: zámek drží jen vlákna se stejným refresh tokenem, ostatní requesty jedou.

| Cesta | SQL | Externí | Cache | Cíl |
|---|---|---|---|---|
| P1 oba PRM a AS metadata | 0 | 0 | žádná, dokument je z env | cold/warm < 20 ms |
| P2 MCP auth, service token nebo cookie | 0 | 0 | žádná | přidaná latence < 5 ms |
| P3 MCP auth, OAuth access | 1 SELECT podle hashe access + 1 SELECT family | 0 | žádná | < 20 ms |
| P4 DCR | 1 INSERT | 0 | žádná | < 50 ms |
| P5 CIMD na authorize | 0 SQL při cache hitu | 1 GET jen když `client_id` je URL na `claude.ai` nebo `claude.com`, timeout 3 s | proces, 5 min, klíč je URL dokumentu; pád procesu cache smaže | hit < 20 ms, miss < 3 s a pak chyba klientovi, ne tichý průchod |
| P6 GET authorize uloží transakci; POST pokračování jen SELECT podle id a řádek neaktualizuje | 1 INSERT, pak 1 SELECT | 0, dokud POST neprojde B45 a B49; Google až pak | žádná | < 50 ms |
| P7 callback po B46 a B49 | 1 UPDATE/INSERT family a kódu | 1 POST Google, timeout 20 s, až když transakce existuje a `expires_at > now` | žádná | mimo rozpočet 500 ms; při non-200 žádný token (B23); B49 je 0 POST na Google |
| P8 token, code i refresh bez čekání | 1 transakce, jednotky SELECT/INSERT podle PK | 0 | žádná | < 50 ms |
| P9 refresh, který čeká na zámek | stejná transakce až po vítězi | 0 | žádná | čeká jen na P8 vítěze, pak < 50 ms; není 503 |

Invalidace cache: CIMD cache se neváže na vault. Pepper a báze se čtou z env při requestu, ne při importu. Service token se proti pepperi nikdy neporovnává.

Anti-patterny checklistu B (Allfred blob, `Model.all()`, N+1 přes síť, live GraphQL) se netýkají. N+1 v P3 není: dva dotazy podle PK, ne smyčka.

## Testy (T#)

Pytest v `vps/second-brain-brain/tests/`. Gate: `python3 -m pytest vps/second-brain-brain/tests -q`. Playwright se nezakládá. Owner gate je pytest. Ruční test není Tester.

| T# | Typ | Owner | Soubor | Co ověřuje |
|---|---|---|---|---|
| T1 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B1 |
| T2 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B2, B43; počítadlo otevření SQLite je 0 |
| T3 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B3 |
| T4 | pytest | gate | `tests/test_oauth_mcp_token.py` | B4 |
| T5 | pytest | gate | `tests/test_oauth_mcp_token.py` | B5 |
| T6 | pytest | gate | `tests/test_oauth_mcp_token.py` | B6 |
| T7 | pytest | gate | `tests/test_oauth_mcp_token.py` | B7 |
| T8 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B8, existující REST testy dál procházejí |
| T9 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B9 |
| T10 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B10 |
| T11 | pytest | gate | `tests/test_oauth_mcp_metadata.py` | B11 |
| T12 | pytest | gate | `tests/test_oauth_mcp_register.py` | B12; vrácené `client_id` dojde GET authorize na souhlasovou stránku |
| T13 | pytest | gate | `tests/test_oauth_mcp_register.py` | B13 |
| T14 | pytest | gate | `tests/test_oauth_mcp_register.py` | B14, fixture podle živého hostovaného dokumentu (A10), včetně `jwt-bearer` |
| T15 | pytest | gate | `tests/test_oauth_mcp_register.py` | B15, fixture s loopbackem, žádný socket na Google |
| T16 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B16 |
| T17 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B17 |
| T18 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B18 |
| T19 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B19 |
| T20 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B20; v HTML je atribut `method="post"` (chybějící method nebo `get` test shodí), `action` bez query, uvnitř formuláře jediný submit Pokračovat a jen pole id; aktivace odkazu Zrušit je `GET /oauth/mcp/cancelled`, odpověď bez `Location` na Google, v `codes` žádný řádek, tuple transakce stejný, a ten request není POST na `/oauth/mcp/continue` |
| T21 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B21, `state` s `<` a uvozovkou |
| T22 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B22 |
| T23 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B23 |
| T24 | pytest | gate | `tests/test_oauth_mcp_token.py` | B24 |
| T25 | pytest | gate | `tests/test_oauth_mcp_token.py` | B25 |
| T26 | pytest | gate | `tests/test_oauth_mcp_token.py` | B26 |
| T34 | pytest | gate | `tests/test_oauth_mcp_refresh.py` | B27; dvě překrývající se volání funkce, kterou volá sync route; endpoint není coroutine |
| T35 | pytest | gate | `tests/test_oauth_mcp_refresh.py` | B28, navazuje na T34 v tom samém testu |
| T36 | pytest | gate | `tests/test_oauth_mcp_refresh.py` | B29 |
| T37 | pytest | gate | `tests/test_oauth_mcp_token.py` | B30, B44 |
| T39 | pytest | gate | `tests/test_oauth_mcp_store.py` | B31 |
| T40 | pytest | gate | `tests/test_oauth_mcp_store.py` | B32 |
| T41 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B33 |
| T42 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B34 |
| T44 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B35 |
| T45 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B36, spy že `mode=rebuild` nebyl |
| T46 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B37 |
| T47 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B38 |
| T48 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B39 |
| T49 | pytest | gate | `tests/test_oauth_mcp_scope.py` | B40 |
| T50 | pytest | gate | `tests/test_oauth_mcp_token.py` | B41 |
| T51 | pytest | gate | `tests/test_oauth_mcp_revoke.py` | B42, a že router nemá `/oauth/mcp/revoke` |
| T52 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B45; POST jen s id a bez query nastaví cookie a `Location` je `accounts.google.com`; cizí URI v těle a zvlášť cizí URI v query: řádek byte-shodný, nulový socket na Google, HTTP 400 a žádná `Location` na Google ani na předané URI (nulový socket sám nestačí); tělo a query se liší v obou pořadích (uložené vs. cizí) → stop, ne `or` na první shodě |
| T53 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B21, `client_name` s `<` a uvozovkou je v těle jen jako text |
| T54 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B46 |
| T55 | pytest | gate | `tests/test_oauth_mcp_token.py` | B47 |
| T56 | pytest | gate | `tests/test_oauth_mcp_token.py` | B48, dvě překrývající se volání té samé funkce jako route |
| T57 | pytest | gate | `tests/test_oauth_mcp_authorize.py` | B49; neznámé id (v `transactions` nepřibude řádek) i `expires_at == now` a `expires_at < now` (u existujícího řádku stejný tuple; sloupec se nastaví, test nespí) na POST i na callbacku, kde cookie sedí na `state`: žádný socket na Google, v `codes` žádný nový řádek, HTTP 400 bez `Location` a bez `code` |
| T60 | ruční | člověk, ne Tester | claude.ai web | B20 v prohlížeči: Lukáš dokončí Sign in a vidí nástroje; druhý účet organizace token nedostane. Až potom se connector smí přidat do organizace (R7). Desktop, mobil a Cowork jedou stejným redirectem, samostatný pytest nemají. Claude Code se nezkouší. |

T34 a T35 jsou jeden test se dvěma asserty a volají funkci route, ne zámek bokem. Když čekající volání family zruší, spadne první assert. Když pozdější replay family nechá živou, spadne druhý. Jiný čítač v produkci k tomu testu není.

## Pořadí implementace

F1 — úložiště, pepper, odmítnutí cesty ve vaultu, schéma. Na něm stojí zápis tokenů.

F2 — metadata a MCP `401` s hlavičkou. Service token a cookie se nemění. Nezávisí na řádku v SQLite.

F3 — DCR a CIMD. Potřebuje F1 jen pro uložení DCR klienta. CIMD se do SQLite neukládá.

F4 — GET uloží transakci s `expires_at` = now + 10 min a souhlasovou stránku (`method="post"`, Zrušit mimo formulář). POST pokračování: tělo jen s id a bez query nastaví cookie a jde na Google; cizí `redirect_uri` v těle, zvlášť v query, nebo neshoda těla s query, stop bez zápisu řádku. Neznámé id a `expires_at <= now` stopnou POST (400, bez Google, bez kódu, řádek se nemění). Stejná kontrola je znovu na callbacku před výměnou u Google a před vložením kódu. Callback bez shody cookie kód nevydá. Potřebuje F1 a F3. T20, T52, T54 a T57 patří sem.

F5 — sync token endpoint, PKCE a podmíněné `used_at` v `BEGIN IMMEDIATE`, zámek refresh s get-or-create a vlastním spojením. Potřebuje F1 a F4. T34, T35, T55 a T56 patří sem, dřív než se gate napojí na MCP.

F6 — MCP přijme OAuth access, REST ho odmítne bez hlavičky. Potřebuje F5.

F7 — mapa scope, `run_tool`, audit, warm `get_context`, `allow_focus_write` pro `OAuthPrincipal`, principal do apply. Potřebuje F6.

F8 — příkaz revoke, `add-oauth-volume.sh`, větev v `setup-coolify.sh` jen pro novou instalaci, README s Google redirectem. Může vedle F7, nesmí sahat na service token.

F9 — celý pytest gate. Nasazení volume a pepperu je až s image Brainu. Hub cron se znovu nenasazuje. Org connector až po T60.

## Rizika a zpětná kompatibilita

1. Zámek je v paměti jednoho procesu a route tokenu musí zůstat sync `def`. `async def` na jednom loopu by čekajícího smazal a family by spadla. `--workers` větší než 1 nebo druhá replika by z čekajícího udělala replay. Dockerfile ani replicas se v tomhle směru nesmí změnit.
2. Když proces umře až po commitu rotace a před odesláním odpovědi, klient nový refresh nedostane. Jeho opakování starého refreshe je replay a family zruší. Platné tokeny, které už klient má, restart s připojeným volume neruší.
3. Cookie callback dál vypisuje allowlist v textu 403. Tahle práce to nemění. MCP zamítnutí ten text nekopíruje.
4. Bez ručně přidaného Google redirectu a bez pepperu OAuth token nevydá. Service token, cookie a REST jedou.
5. INSERT volume bez deploymentu s `restart_only=false` mount nezapne. Do té doby se tokeny nevydávají, takže není koho odhlásit.
6. Hostovaný CIMD dnes neobsahuje `https://claude.com/api/mcp/auth_callback`. Ten redirect projde u DCR klienta, který ho má zaregistrovaný. CIMD klient ho projde jen když ho dokument uvádí.
7. `mailbox_apply` a `external_apply` přestanou předstírat service principal. Lidský MCP volající uvidí 501 místo 403. Apply pořád nic nezapíše. Service volající uvidí dál 403.
8. Existující klienti MCP se service tokenem a cookie se nemění. Nový Bearer, který není service token, už není jen anonymní 401: když má tvar access tokenu, jde do SQLite. Service token se porovnává dřív, takže shoda SQLite neotevře.
9. Opuštěný plán z 11. 11. se needituje. Jeho množiny `request_id` se nepřebírají. Počítadlo čekajících se nepřidává.
10. Cookie `sb_mcp_oauth_tx` je jiná než `sb_oauth_state` a `sb_brain_session`. Dokončení MCP loginu dnešní cookie session nepřepíše a cookie přihlášení neodhlásí.
11. Formulář bez `method` je GET. POST route ho nevezme a test, který čte jen `action`, to nevidí. Markup má `method="post"`. Dva submit buttony se stejným tělem (jen id) by Zrušit pustily na Google. Zrušit proto na `/oauth/mcp/continue` neposílá.
12. Stop „kód se nevydá“ jen na POST kód nezastaví: řádek v `codes` vzniká až na callbacku. Neznámé id a `expires_at <= now` se kontrolují na obou koncích. Predikát „věk nad 10 minut“ by `expires_at == now` pustil dál.

## Otevřené otázky pro uživatele

Žádná. Q1 a A-G1 až A-G10 jsou zavřené. Výchozí předpoklady A7, A8 a A10 jsou v plánu. Jiná cesta volume mimo vault by změnila jen mount (řádek 7 tabulky v osnově). Jiný pepper env název by změnil jen jméno proměnné, ne zákaz spadnout na service token.

## Delta tohoto kola

Kolo převzetí, revize C7–C9. Q1 hosted a focus beze změny. C1–C6 se neotvíraly.

Sekce: A-G5, úložiště (predikát `expires_at`), současný stav (`requirements.txt`), návrh (souhlasový formulář, POST pokračování, callback), kontrakt B20, B45, nový B49, checklist A body 2 a 3, P6, P7, testy T20, T52, nový T57, pořadí F4, rizika 11 a 12.

| ID | Stav |
|---|---|
| C7 | vyřešeno — T52 chce produkční POST jen s id a bez query (cookie a `Location` na Google); cizí URI v těle a zvlášť v query nechá řádek byte-shodný, nulový socket a odpověď bez `Location` na Google i na předané URI; liší-li se tělo a query, stop bez `or` na první shodě; B20/T20 vyžadují `method="post"` |
| C8 | vyřešeno — predikát je `expires_at <= now` včetně rovnosti; B49 a T57 hlídají neznámé id i vypršení na POST a znovu na callbacku před kódem (bez Google, řádek beze změny, kód nevznikne); F4 ten krok jmenuje |
| C9 | vyřešeno — Zrušit je odkaz na `GET /oauth/mcp/cancelled`, ne submit `/oauth/mcp/continue`; T20 ten odkaz aktivuje a čeká žádný redirect na Google a žádný kód |
