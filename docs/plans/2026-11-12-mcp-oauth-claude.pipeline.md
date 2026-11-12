# Pipeline: MCP OAuth Claude (nový běh)

Stav: IMPLEMENT
Plán: docs/plans/2026-11-12-mcp-oauth-claude.md
Schvalování plánu uživatelem: ne
Architekt: agent ID 9c40c621-d63a-42f8-8b60-f4bafdfff34f, otevření plánu #1, generace k=2/3, kolo r=1/3
Šťoural: agent ID cca0b716-7574-46ce-88b5-15b6ce1a0693 · jedno kolo hotové, Q1 zodpovězeno
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku větve): c930c5a5157abd5720bb146bbd86b305741b5e77 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: —
Plán schválen uživatelem: nevyžadováno
Goal: aktivní (znovu po „pokračuj“)
Větev: `feat/mcp-oauth-claude`

Předchůdce [docs/plans/2026-11-11-mcp-oauth-claude.pipeline.md](2026-11-11-mcp-oauth-claude.pipeline.md) je ABANDONED. Tenhle běh ho nepřebírá v kole k=3. Necommitnutá revize C15 v `docs/plans/2026-11-11-mcp-oauth-claude.md` je kontext, ne závazek.

## Zadání (doslovně) a rozhodnutí

### Zadání uživatele (doslovně)

> OK, vypadá to, že musím vytvořit nový OAuth způsob autentizace, jinak bude mít k mému Second Brainu přístup každý.
>
> Návrh postupu je v /Users/lukascypra/Downloads/brief-oauth-claude-connector.md
> Projdi si to, doptej se a pak připrav základní plán - po zrušení plan modu budu chtít /rbu-pipeline

Později: `ok, /rbu-pipeline`

Brief (varianta A, schválená jako realizovatelná): org connector v Claude Team bez sdíleného bearer tokenu. Každý člen se autentizuje sám. Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá.

Nový chat 12. 11. 2026 (doslovně): „Vrať se ke konverzaci 7ff51b50-ac6e-4b41-a463-caad0e9726e8 a spusť novou /rbu-pipeline“. Není to `pokračuj` na zablokovaný ledger.

### Rozhodnutí z konverzace

- Širší záměr „všude Google login místo Beareru“ uživatel 11. 11. zrušil („zpět, celé to zruš“). Platí jen MCP OAuth pro Claude.
- Allowlist: `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní gmail neprojde.
- Rozsah: jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Nedělit tokeny. Nedělat audit starých IP.
- Úložiště tokenů: nový SQLite soubor. Není to vault a není v `/data/vault` (host `/data/second-brain-vault`), protože by šel do gitu. Druhý Coolify persistent volume mimo ten mount. Google Drive ani Mac disk se nepoužijí. Restart/deploy nesmí odhlásit Claude. Replicas Brainu zůstávají 1.
- Dnešní cookie OAuth (`/oauth/callback`, cookie `sb_brain_session`) zůstává. Claude ho jako MCP OAuth nepoužije.
- Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi.
- Org connector se do Claude organizace přidá až po testu, že cizí účet z organizace token nedostane.
- Focus (11. 11., odpověď na C1, doslovně): „Omezení neplatí - focus můžou na pokyn člověka řešit i Grok / Cursor / Claude.“ `BRAIN_SERVICE_TOKEN` dál smí `apply_focus`. Claude OAuth principal ho smí taky. `allow_focus_write(ServicePrincipal)` se nezakazuje.
- Tester: bez UI produktu. Zamítací HTML není dashboard ani nový shell. V DONE auditu `TESTER: přeskočeno (profil SECOND_BRAIN, bez UI)`.
- Předchozí běh (11.–12. 11.) se zacyklil na serializaci souběžného refresh (C15) a skončil ABANDONED, když Task `rbu-architect` vrátil chybu. Mechanismus počítadel ani množin `request_id` není rozhodnutí. Nový plán ho smí navrhnout znovu, jednodušeji, pokud pořád splní: jeden ze souběžných refreshů téhož tokenu vydá tokeny, čekající vlákno family nezruší, pozdější replay starého refreshe family zruší.
- Q1 (12. 11., volba hosted): jen web, Desktop, mobil a Cowork. Loopback se nepřijímá. Claude Code se tímhle OAuth nepřihlásí a dál může jet service tokenem.

### Mimo rozsah

- Dělení service tokenu na klienty, rotace už provedená uživatelem (n8n smoke 11. 11. prošel).
- Audit historických volání starým tokenem.
- Dashboard OAuth, Grok a Cursor na OAuth.
- Zápis OAuth secretů nebo auditů do git vaultu.
- Dál ladit opuštěný soubor `docs/plans/2026-11-11-mcp-oauth-claude.md`.

## Projekt

SECOND_BRAIN

- Kořen: `~/GitHub/SECOND_BRAIN` (profil ve skillu uvádí starší cestu přes Drive; pracovní kořen je GitHub).
- Větev / base: `feat/mcp-oauth-claude` z `origin/main` `c930c5a5157abd5720bb146bbd86b305741b5e77`. Nasazení: push `main` → Coolify image `second-brain-brain`. Změna je v `vps/second-brain-brain/`, ne hub cron.
- Lokální gate: `python3 -m pytest vps/second-brain-brain/tests -q` (hub gate jen kdyby se hub měnil).
- QA po nasazení: image Brain na Coolify, ne dry-run hub cronu.
- Tester: `TESTER: přeskočeno (profil SECOND_BRAIN, bez UI)`. `rbu-tester` nevolat.
- Ostrý zápis do vaultu tahle změna nedělá.
- Checklisty: `docs/agent_playbooks/quality-checklists.md`. Žádné odhady effortu.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|-----|------|------------|---------|---------------------|--------------------|
| 1 | 2026-11-12 12:40 | PLAN | — | — | — | Nový běh. CLARIFY bez nové otázky (rozhodnutí jsou v předchozí konverzaci). Start osnovy. |
| 2 | 2026-11-12 12:55 | PLAN | cb53849f-256b-4e2e-b34e-e3a06942fd96 | osnova | — | R1–R15. Přechod na Šťourala, jedno kolo. |
| 3 | 2026-11-12 13:10 | GRILL | cca0b716-7574-46ce-88b5-15b6ce1a0693 | POTŘEBUJE ODPOVĚDI | 1 BLOKUJÍCÍ | Q1 Claude Code a loopback. Neblokující předpoklady A-G1–A-G10 jdou do plánu bez čekání. |
| 4 | 2026-11-12 13:25 | PLAN | — | Q1 hosted | — | Jen hostované plochy. Loopback ne. Claude Code zůstává na service tokenu. Architekt píše celý plán. Druhý grill se nespouští. |
| 5 | 2026-11-12 13:45 | PLAN | cb53849f-256b-4e2e-b34e-e3a06942fd96 | plán v1 | — | R16, A-G1–A-G10, jeden zámek na hash. Přechod na kritika, kolo 1. |
| 6 | 2026-11-12 14:05 | CRITIC | dfbadcc8-3634-49b1-84eb-8a294600ae27 | K PŘEPRACOVÁNÍ | 2 BLOCKER, 4 MAJOR | C1 redirect ve formuláři. C2 zámek na jednom uvicornu family zruší. C3 cookie na Google callback. C4 PKCE a jednorázový kód. C5 escape jména klienta. C6 client_id v DCR. Zpět architektovi, r=2. |
| 7 | 2026-11-12 14:20 | PLAN | cb53849f-256b-4e2e-b34e-e3a06942fd96 | revize r=2 | — | C1–C6 zapsané. Přechod na kritika, kolo 2+ (delta). |
| 8 | 2026-11-12 14:40 | CRITIC | 7ace38ac-ab99-41ad-974b-10cbe962c387 | K PŘEPRACOVÁNÍ | 1 BLOCKER, 0 MAJOR | C2–C6 vyřešené. C1: route při platném id jde na Google, B45 chce u jiného redirectu stop. Součet klesl (6→1). Zpět architektovi, r=3. |
| 9 | 2026-11-12 14:55 | PLAN | cb53849f-256b-4e2e-b34e-e3a06942fd96 | revize r=3 | — | C1: jiné redirect_uri Google nezavolá; stejné nebo chybějící jde dál. Formulář má action bez query. Přechod na kritika, kolo 2+. |
| 10 | 2026-11-12 15:10 | CRITIC | 4833138f-4fb4-4cd8-b630-c8a5c639aa67 | K PŘEPRACOVÁNÍ | 0 BLOCKER, 2 MAJOR, 1 MINOR | C1 vyřešené. C7 test nehlídá produkční POST jen s id ani zákaz přepsat transakci. C8 desetiminutový stop není v kontraktu. C9 MINOR Zrušit spustí Google. r=3, nový architekt k=2. |
| 11 | 2026-11-12 15:25 | BLOCKED | c2897b51-f72d-4461-8a70-aa686ef2e286 | unavailable | — | Task rbu-architect skončil bez zápisu („repeated resume attempts made no progress“). Delta v souboru je pořád C1. C7–C9 zůstávají otevřené. |
| 12 | 2026-11-12 17:20 | PLAN | — | pokračuj | — | Uživatel: další iterace architekta na C7–C9. Šťoural se nespouští. Start převzetí k=2 r=1. |
| 13 | 2026-11-12 17:35 | PLAN | 9c40c621-d63a-42f8-8b60-f4bafdfff34f | revize k=2 | — | C7–C9 zapsané. Přechod na kritika, kolo 2+ (delta). |
| 14 | 2026-11-12 17:50 | CRITIC | b29ed72f-f858-406e-8125-60072a97f091 | SCHVÁLENO | 0 BLOCKER, 0 MAJOR | C7–C9 potvrzené. Schvalování plánu se nečeká. Přechod na implementaci. |
| 15 | 2026-11-12 18:10 | IMPLEMENT | — | lokální commit | — | Pytest `vps/second-brain-brain/tests` 281 passed, 1 skipped. Bez push. Přechod na diff reviewer, první kolo. |

## Grill

Q1 zodpovězeno (hosted). Původně BLOKUJÍCÍ: Claude Code posílá loopback `http://localhost:<port>/callback` a `http://127.0.0.1:<port>/callback`. Osnova v A2 počítá jen se dvěma HTTPS callbacky. Doporučení Šťourala: jen hostované plochy (web, Desktop, mobil, Cowork); Claude Code zůstane na service tokenu.

Neblokující předpoklady (architekt je zapíše jako A#, bez dalšího grilu):

- A-G1: vynechaný scope na authorize u allowlistu = `brain:read` i `brain:write`. Na refreshi vynechání = scope grantu; read se na write nerozšíří. `offline_access` se neinzeruje; když přijde, zahodí se a není `invalid_scope`. Refresh token u `authorization_code` vždy.
- A-G2: `get_context` s `brain:read` jen warm čtení. Rebuild chce `brain:write`. Service token a cookie session rebuildují jako dnes.
- A-G3: Access z nového OAuth platí jen na MCP. REST `/v1/*` dál bere cookie nebo service token. `WWW-Authenticate` jen na MCP 401 bez platné cookie, service tokenu ani OAuth access tokenu. Platný service token na SQLite nesahá.
- A-G4: Odvolání jednoho grantu je příkaz v kontejneru, bez HTTP route. Odebrání e-mailu je změna allowlistu v kódu. Každé MCP volání s OAuth tokenem allowlist znovu ověří.
- A-G5: transakce 10 minut, kód 60 sekund, access 1 hodina, refresh 30 dní, absolutní strop grantu 90 dní. Restart s připojeným volume session neruší.
- A-G6: každý úspěšný login je vlastní family. Rotace v jedné family neodhlásí druhou.
- A-G7: před Google je stránka se jménem klienta, scope a hostname redirectu. Zamítnutí allowlistu allowlist nevypisuje a vrátí `access_denied` se `state`. Není to dashboard.
- A-G8: Enterprise Managed Auth a `jwt-bearer` se nedělají.
- A-G9: mapa nástrojů 13× read / 20× write dle opuštěného plánu. Suchý běh scope nesnižuje. Nástroj mimo mapu se nespustí.
- A-G10: poražený souběžný refresh vrací `invalid_grant` a family nechá živou.

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| C1 | BLOCKER | PLAN | vyřešen v #10 (kritik potvrdil) | 2 |
| C7 | MAJOR | PLAN | vyřešen v #14 (kritik potvrdil) | 1 |
| C8 | MAJOR | PLAN | vyřešen v #14 (kritik potvrdil) | 1 |
| C9 | MINOR | PLAN | vyřešen v #14 (kritik potvrdil) | 1 |
| C2 | BLOCKER | PLAN | vyřešen v #8 (kritik potvrdil) | 1 |
| C3 | MAJOR | PLAN | vyřešen v #8 (kritik potvrdil) | 1 |
| C4 | MAJOR | PLAN | vyřešen v #8 (kritik potvrdil) | 1 |
| C5 | MAJOR | PLAN | vyřešen v #8 (kritik potvrdil) | 1 |
| C6 | MAJOR | PLAN | vyřešen v #8 (kritik potvrdil) | 1 |
