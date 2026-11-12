# Pipeline: MCP OAuth Claude (nový běh)

Stav: GRILL
Plán: docs/plans/2026-11-12-mcp-oauth-claude.md
Schvalování plánu uživatelem: ne
Architekt: agent ID cb53849f-256b-4e2e-b34e-e3a06942fd96, otevření plánu #1, generace k=1/3, kolo r=1/3
Šťoural: běží · právě jedno kolo nad osnovou
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku větve): c930c5a5157abd5720bb146bbd86b305741b5e77 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: —
Plán schválen uživatelem: nevyžadováno
Goal: aktivní
Větev: `feat/mcp-oauth-claude` (beze změny kódu; předchozí běh na ní jen plány)

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
- Předchozí běh (11.–12. 11.) se zacyklil na serializaci souběžného refresh (C15) a skončil ABANDONED, když Task `rbu-architect` vrátil chybu. Mechanismus počítadel ani množin `request_id` není rozhodnutí. Nový plán ho smí navrhnout znovu, jednodušeji, pokud pořád splní: jeden ze souběžných refreshů vydá tokeny, čekající vlákno family nezruší, pozdější replay starého refreshe family zruší.

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

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
