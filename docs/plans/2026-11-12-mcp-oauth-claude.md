# Plán: MCP OAuth pro Claude

## Osnova rozhodnutí

Uzavřená rozhodnutí uživatele se znovu neotvírají. Kde brief z 11. 11. říká něco jiného (zákaz focus pro stroj, samostatný token per klient, audit starých IP, rotace service tokenu, `set_focus` jen pro člověka), platí věta z konverzace níže.

### Požadavky

R1 — Org connector v Claude Team bez sdíleného bearer tokenu. Každý se přihlásí sám, Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá. Zdroj: brief, varianta A.

R2 — Allowlist je jen `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní Gmail neprojde. Zdroj: rozhodnutí z konverzace. Dnešní cookie allowlist jsou přesně tyto dvě adresy a `hd` se neposílá.

R3 — Jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Tokeny se nedělí. Audit starých IP se nedělá. Tahle práce service token znovu nerotuje. Zdroj: rozhodnutí z konverzace a mimo rozsah.

R4 — Úložiště tokenů je nový SQLite mimo git vault a mimo `/data/vault`. Druhý Coolify persistent volume. Restart ani deploy nesmí odhlásit Claude, jakmile je volume připojené. Replicas Brainu zůstávají 1. Zdroj: rozhodnutí z konverzace.

R5 — Dnešní cookie OAuth (`/oauth/authorize`, `/oauth/callback`, cookie `sb_brain_session`) zůstává a dál pouští MCP i REST. Claude ho jako MCP OAuth nepoužije. Zdroj: rozhodnutí z konverzace.

R6 — Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi, jiný než `{veřejná URL}/oauth/callback`. Přidání URI do Google konzole je ruční krok člověka. Zdroj: rozhodnutí z konverzace.

R7 — Org connector se do organizace přidá až po testu, že cizí účet z organizace token nedostane. Ten test není pytest a není `rbu-tester`. Zdroj: rozhodnutí z konverzace.

R8 — Focus smí na pokyn člověka Grok, Cursor i Claude. Doslova: „Omezení neplatí - focus můžou na pokyn člověka řešit i Grok / Cursor / Claude.“ `BRAIN_SERVICE_TOKEN` dál smí `apply_focus`. Claude OAuth principal ho smí taky. `allow_focus_write(ServicePrincipal)` se nezakazuje. Pokyn člověka je dnešní tok návrh a pak apply. Nový příznak souhlasu se nezavádí. Zdroj: rozhodnutí uživatele.

R9 — Zamítací HTML není dashboard ani nový shell. V DONE auditu `TESTER: přeskočeno (profil SECOND_BRAIN, bez UI)`. `rbu-tester` se nevolá. Zdroj: rozhodnutí z konverzace.

R10 — Souběžný refresh téhož tokenu: jeden z nich vydá tokeny a family nechá živou. Ostatní souběžné pokusy family nezruší a druhou sadu tokenů nevydají. Pozdější replay starého refreshe, až po návratu prvního, family zruší. Jak se to uloží, tahle osnova nerozhoduje. Zdroj: rozhodnutí z konverzace 12. 11.

R11 — Brain MCP je pro Claude OAuth 2.1 resource server. Neautorizovaný požadavek na MCP vrací `401` a `WWW-Authenticate` s odkazem na Protected Resource Metadata. Vedle toho metadata authorization serveru, PKCE S256, granty `authorization_code` a `refresh_token`, Dynamic Client Registration. Povolené redirect URI jen `https://claude.ai/api/mcp/auth_callback` a `https://claude.com/api/mcp/auth_callback`. V konfiguraci connectoru žádný token a žádný client secret (veřejné Client ID smí být). Zdroj: brief, fáze 1 a akceptační bod 1. Dnešní MCP `401` je JSON bez `WWW-Authenticate`.

R12 — Scope oddělí čtení a zápis. Nástroj mimo udělený scope Brain odmítne. Věta briefu „`set_focus` jen pro člověka“ neplatí, nahrazuje ji R8. Zdroj: brief, fáze 1, zúženo R8.

R13 — Odebrání e-mailu z allowlistu nebo odvolání tokenu zastaví další volání toho člověka a nesáhne na service token ani na cookie session ostatních. Každé volání s OAuth access tokenem allowlist znovu ověří. Zdroj: brief, akceptační bod 5.

R14 — U volání nástroje je dohledatelná identita, klient, nástroj, čas a výsledek. Záznam není v git vaultu. U service tokenu je identita `service`, protože jeden token sdílí víc klientů (R3). Zdroj: brief, akceptační bod 4, a zákaz zápisu auditů do git vaultu.

R15 — Žádné odhady effortu. Opuštěný plán z 11. 11. se dál neupravuje. Fáze 0 z briefu (auditní poznámka do vaultu) se do vaultu nezapisuje. Zdroj: zadání pipeline a mimo rozsah.

### Produktová rozhodnutí

Uzavřeno spolu s R1–R10 a R15. Další volby, které uživatel doslovně neřekl:

1. Brain je resource server i authorization server na `https://brain.cyprovi.cz`. Identifikátor resource pro Claude je `https://brain.cyprovi.cz/mcp/` včetně koncového lomítka. Jedno koncové lomítko se při srovnání ignoruje. Cizí resource se odmítne. REST (hub, n8n, dashboard) zůstává na dnešním JSON `401` bez hlavičky, která by nutila OAuth discovery.
2. Klient v connectoru je veřejný: PKCE S256 a autentizace token endpointu `none`. Žádný client secret se nevydává ani neukládá do Claude. Registrace jde Dynamic Client Registration i přes publikovanou identitu Claude (aby šla v UI zvolit bez secretu). Redirect host jen `claude.ai` a `claude.com`, jen ty dvě callback URL. Jiné redirect URI se odmítnou. Jméno klienta, které Claude hlásí, je `Claude`.
3. Nový Google redirect je `https://brain.cyprovi.cz/oauth/mcp/callback`. Token výměna s Google posílá tuhle URI, ne cookie callback. Authorize neposílá `hd` a ponechá `prompt=select_account`, aby šel zvolit osobní Gmail. Stejný Google klient jako cookie OAuth.
4. Brain vydává vlastní neprůhledné access a refresh tokeny. V úložišti jen hash. Obojí jde odvolat. Pepper OAuth tokenů je vlastní tajemství. Když chybí, nesmí se použít `BRAIN_SERVICE_TOKEN` ani tajemství cookie session. Cookie serializer se nemění.
5. Životnosti, dokud je někdo nezmění: transakce přihlášení 10 minut, authorization code 60 sekund, access 1 hodina, refresh 30 dní od vydání (rotace posune okno jen novému refresh tokenu), absolutní strop grantu 90 dní od vzniku. Časy UTC. `expires_at <= now` je vypršelé.
6. Scope jsou `brain:read` a `brain:write`. Allowlistovaný člověk dostane oba, když o ně klient požádá nebo scope vynechá. Samotný read nezapisuje a nesmí spustit rebuild kontextu, protože rebuild do vaultu commituje. Write smí zapisovat i focus (R8) i rebuild. Service token a cookie session rebuildují a focusují jako dnes, bez OAuth scope. Nástroj bez přiřazeného scope se odmítne a nespustí.
7. Service token se pozná dřív než OAuth úložiště. Cesta service tokenu SQLite nepotřebuje. Chybějící volume nebo pepper neshodí metadata ani `401` a neshodí Cursor, Grok, hub, dashboard ani n8n. Vydání a přijetí OAuth tokenu bez zapsatelné databáze nebo pepperu selže zavřeně.
8. E-mail mimo allowlist po Google loginu: žádný token, stránka „přístup zamítnut“ bez výpisu allowlistu, pak návrat do Claude s `access_denied` a se `state`, který poslal klient. Dnešní cookie callback, který allowlist v textu 403 vypisuje, se v tomhle kole nemění.
9. Audit je jeden záznam na stdout Brainu na každé volání nástroje, na úspěchu i na odmítnutí. Pole: identita, klient, nástroj, čas, výsledek. OAuth identita je e-mail. U service tokenu je klient i identita `service`.
10. Apply cesty, které dnes service token odmítnou jako `human_oauth_required` a lidské OAuth jako nedodělané po F3, tahle práce nezapíná. Claude OAuth je na nich stejný lidský principal jako cookie OAuth.
11. Allowlist zůstává jeden seznam v kódu, sdílený s cookie OAuth. Žádná obrazovka na jeho správu. Čtení pro další členy organizace se nezavádí.
12. Volume se poprvé připojí deploymentem, který kontejner znovu vytvoří. Restart už běžícího kontejneru nový mount nezapne a tokeny se do té doby nevydávají. Po připojení přežije SQLite restart i nasazení image. Předpokládaná dvojice cest: host `/data/second-brain-oauth`, v kontejneru `/data/oauth`. Celý stávající setup skript, který umí přepsat env včetně service tokenu, se kvůli tomu znovu nespouští.
13. Výsledek souběžného refresh je jen R10. Tvar chyby pro ten pokus, který tokeny nevydal, a způsob uložení family zvolí až fáze plánu. Podmínka: ten pokus family neruší.

### Předpoklady

A1 — Veřejná báze je `https://brain.cyprovi.cz` bez koncového lomítka. Člověk v Claude zadá resource s lomítkem podle bodu 1. Ověřeno, že MCP dnes visí na `/mcp` a cookie callback je `{báze}/oauth/callback`.

A2 — Claude Code i claude.ai použijí jen ty dvě HTTPS callback URL. Samostatný localhost redirect pro CLI není potřeba. Mobil nemá další redirect. Brief označuje mobil jako neověřený.

A3 — Publikovaná identita Claude je veřejný klient bez secretu. Když ji Claude nepoužije, stačí DCR se stejnými dvěma redirecty. Důvěrný klient se secretem v connectoru by rozbil R11.

A4 — Jedna sada metadat stačí pro auth specifikace, které brief uvádí (2025-03-26 a 2025-06-18). Dvě implementace protokolu nevznikají.

A5 — SQLite na jednom volume drží jen proto, že replicas zůstávají 1. Druhá replika by sdílený soubor neměla.

A6 — „Family“ je řetěz refresh tokenů jednoho uděleného loginu. Replay znamená znovu předložit refresh, který už úspěšná rotace nahradila, a to až když ta rotace volajícímu vrátila nové tokeny.

### Co by jiná odpověď změnila

Uzavřeno, jiná odpověď by šla proti rozhodnutí uživatele: R1–R10, R15, jeden service token, zákaz auditu starých IP, cookie OAuth ponechané, stejný Google klient, focus pro service i Claude, replicas 1, skip Testera.

| # | Kdyby platilo něco jiného | Co se v plánu změní |
|---|---|---|
| 1 | Jeden scope místo read/write | Zmizí zákaz rebuildu a zápisu pro read. R8 (focus) zůstane. |
| 2 | Vynechaný scope znamená jen čtení | Claude bez explicitního write nezapíše focus ani rebuild, dokud o write nepožádá. |
| 3 | Jen DCR, bez publikované identity | Pořád splní R11, pokud klient zůstane veřejný a redirecty ty dvě URL. |
| 4 | CLI potřebuje localhost redirect | Přibude jen loopback redirect. Otevřené http URL mimo loopback ne. |
| 5 | Resource bez koncového lomítka | Změní se řetězec, který člověk zadá do Claude a který vrací metadata. |
| 6 | Jiné životnosti tokenů | Změní se jen čísla v bodu 5. Odvolatelnost a rotace zůstanou. |
| 7 | Jiná cesta volume, pořád mimo vault a mimo `/data/vault` | Změní se jen mount. Zákaz gitu a přežití restartu zůstávají. |
| 8 | Audit jinam než na stdout, pořád mimo git vault | Změní se jen cíl záznamu. Pole a identita `service` zůstávají. |
| 9 | Pepper smí spadnout na service token nebo cookie secret | Odmítnuto v bodu 4. Jinak rotace service tokenu buď odhlásí Claude, nebo z něj jde razit OAuth token. |
| 10 | Souběžný poražený refresh taky dostane tokeny, nebo replay family neruší | Rozbilo by to R10. Tvar chybové odpovědi poraženého na R10 nic nemění a patří do fáze plánu. |
