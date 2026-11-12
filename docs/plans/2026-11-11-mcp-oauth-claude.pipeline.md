# Pipeline: MCP OAuth Claude

Stav: AWAITING_USER (z: aktualizace rbu-pipeline v jiné konverzaci)
Plán: docs/plans/2026-11-11-mcp-oauth-claude.md
Schvalování plánu uživatelem: ne
Architekt: generace k=1 skončila na r=3/3. Převzetí k=2 se nespustilo (uživatel stop). 9628d3a7 neresumovat.
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku větve): c930c5a5157abd5720bb146bbd86b305741b5e77 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER: přeskočeno (profil SECOND_BRAIN) až v DONE auditu
Plán schválen uživatelem: nevyžadováno
Goal: paused-awaiting-user (12. 11.). Nový skill je načtený. Další krok až po „pokračuj“: architekt k=2, bez Šťourala, kritik nad deltou.

Větev: `feat/mcp-oauth-claude` z `origin/main` (lokální `main` byl 59 commitů pozadu). Push na konci pipeline je na `main` dle profilu SECOND_BRAIN.

## Zadání (doslovně) a rozhodnutí

### Zadání uživatele (doslovně)

> OK, vypadá to, že musím vytvořit nový OAuth způsob autentizace, jinak bude mít k mému Second Brainu přístup každý.
>
> Návrh postupu je v /Users/lukascypra/Downloads/brief-oauth-claude-connector.md
> Projdi si to, doptej se a pak připrav základní plán - po zrušení plan modu budu chtít /rbu-pipeline

Později: `ok, /rbu-pipeline`

Brief (varianta A, schválená jako realizovatelná): org connector v Claude Team bez sdíleného bearer tokenu. Každý člen se autentizuje sám. Brain pustí jen allowlist. Do dokončení se connector v organizaci nepoužívá.

### Rozhodnutí z konverzace

- Allowlist: `lukas@redbuttonedu.cz` a `lukas.cypra@gmail.com`. Bez omezení na doménu Workspace (`hd`), jinak osobní gmail neprojde.
- Rozsah: jen MCP OAuth pro Claude. Jeden `BRAIN_SERVICE_TOKEN` pro Cursor, Grok, hub, dashboard a n8n zůstává. Nedělit tokeny. Nedělat audit starých IP.
- Úložiště tokenů: nový SQLite soubor. Není to vault a není v `/data/vault` (host `/data/second-brain-vault`), protože by šel do gitu. Druhý Coolify persistent volume mimo ten mount. Google Drive ani Mac disk se nepoužijí. Restart/deploy nesmí odhlásit Claude. Replicas Brainu zůstávají 1.
- Dnešní cookie OAuth (`/oauth/callback`, cookie `sb_brain_session`) zůstává. Claude ho jako MCP OAuth nepoužije.
- Google IdP: stávající `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`. Nový redirect URI na tom samém klientovi.
- Org connector se do Claude organizace přidá až po testu, že cizí účet z organizace token nedostane.
- Focus (11. 11., odpověď na C1, doslovně): „Omezení neplatí - focus můžou na pokyn člověka řešit i Grok / Cursor / Claude.“ `BRAIN_SERVICE_TOKEN` dál smí `apply_focus`. Claude OAuth principal ho smí taky. `allow_focus_write(ServicePrincipal)` se nezakazuje.
- Pauza (12. 11., doslovně): „v jiné konverzaci provádím aktualizaci rbu-pipeline. Budu chtít, abys zde pokračoval až bude dokončena - 4 verze architekta tímto směrem nikam moc nevedou a utrácí zbytečně tokeny.“ Převzetí k=2 se nespouští. Další krok až po té aktualizaci a pokynu pokračovat.

### Mimo rozsah

- Dělení service tokenu na klienty, rotace už provedená uživatelem (n8n smoke 11. 11. prošel).
- Audit historických volání starým tokenem.
- Dashboard OAuth, Grok a Cursor na OAuth.
- Zápis OAuth secretů nebo auditů do git vaultu.

## Projekt

SECOND_BRAIN

- Kořen: `~/GitHub/SECOND_BRAIN` (profil ve skillu uvádí starší cestu přes Drive; pracovní kořen je GitHub).
- Větev / base: práce na `feat/mcp-oauth-claude` z `origin/main` `c930c5a5157abd5720bb146bbd86b305741b5e77`. Nasazení: push `main` → Coolify. Změna je v `vps/second-brain-brain/` (image Brain), ne jen hub cron.
- Lokální gate: pytest Brainu (`vps/second-brain-brain/tests`), ne hub gate, pokud se hub nemění.
- QA po nasazení: image `second-brain-brain` na Coolify, ne dry-run hub cronu.
- Tester: vždy `TESTER: přeskočeno (profil SECOND_BRAIN)`. `rbu-tester` nevolat.
- Ostrý zápis do vaultu tahle změna nedělá.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|-----|------|------------|---------|---------------------|--------------------|
| 1 | 2026-11-11 15:14 | PLAN | — | — | — | Ledger založen. CLARIFY hotové v předchozím chatu. Start architekta k=1 r=1. |
| 2 | 2026-11-11 15:40 | PLAN | 9628d3a7-2aca-4985-b99f-a77b13444d46 | plán v1 | — | Otevření #1 kolo 1. Předpoklady A1–A12, otázky Q1–Q3 neblokující. Přechod na kritika. |
| 3 | 2026-11-11 16:05 | CRITIC | 035b611d-d005-4090-bf84-f12186f91b4a | K PŘEPRACOVÁNÍ | 0 BLOCKER, 4 MAJOR, 0 MINOR | C1 blokující (focus a service token). C2–C4 jdou architektovi až po odpovědi. |
| 4 | 2026-11-11 16:20 | AWAITING_USER | — | odpověď | — | C1: omezení neplatí. Focus smí Grok, Cursor i Claude. Service token `apply_focus` zůstává. Nové otevření plánu #2. |
| 5 | 2026-11-11 16:35 | PLAN | 9628d3a7-2aca-4985-b99f-a77b13444d46 | plán v2 | — | Otevření #2. C1–C4 označené jako vyřešené v plánu. Přechod na nového kritika. |
| 6 | 2026-11-11 16:50 | CRITIC | 59c0da30-70f3-459d-a46b-d497edb04f40 | K PŘEPRACOVÁNÍ | 1 BLOCKER, 2 MAJOR, 1 MINOR | Otevření #2 kolo r=1. C1–C4 vyřešené. NEW-1 volume se nespustí restartem. NEW-2 audit mimo `_call`. NEW-3 SQLite bez zámku. NEW-4 MINOR `get_context` error_reason. Zpět architektovi, r=2. |
| 7 | 2026-11-11 17:10 | PLAN | 9628d3a7-2aca-4985-b99f-a77b13444d46 | plán v3 | — | Otevření #2 kolo r=2. NEW-1–NEW-4 označené jako vyřešené. Přechod na nového kritika. |
| 8 | 2026-11-11 17:25 | CRITIC | fa6362d7-f3c6-4f2a-8599-68ec6fc8b7fb | K PŘEPRACOVÁNÍ | 0 BLOCKER, 1 MAJOR, 1 MINOR | Otevření #2 kolo r=2. C1–C4 a C5–C8 potvrzené. C9 token endpoint nemá OAuth JSON `error` / `access_token`. C10 MINOR souběžný refresh nesmí zrušit výherní access. Součet BLOCKER+MAJOR klesl (3→1), architekt zůstává, r=3. |
| 9 | 2026-11-11 17:45 | PLAN | 9628d3a7-2aca-4985-b99f-a77b13444d46 | plán v4 | — | Otevření #2 kolo r=3. C9 a C10 označené jako vyřešené (RFC 6749 JSON, pardon u souběžného refreshe). Přechod na nového kritika. |
| 10 | 2026-11-11 18:05 | CRITIC | d776cdd0-e17c-40f9-965e-3222e215c099 | K PŘEPRACOVÁNÍ | 0 BLOCKER, 2 MAJOR, 2 MINOR | Otevření #2 kolo r=3. C1–C10 potvrzené. C11 vynechaný scope na refreshi. C12 HTML escape state na zamítací stránce. C13 MINOR pardon je globální. C14 MINOR chybí assert `iss`. r=3, další by byl nový architekt k=2. |
| 11 | 2026-11-12 01:07 | AWAITING_USER | — | stop | — | Uživatel: nepokračovat, dokud v jiné konverzaci nedoběhne aktualizace rbu-pipeline. Převzetí k=2 se nespustilo. |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| C1 | MAJOR | PLAN | vyřešen v #6 (kritik potvrdil) | 1 |
| C2 | MAJOR | PLAN | vyřešen v #6 (kritik potvrdil) | 1 |
| C3 | MAJOR | PLAN | vyřešen v #6 (kritik potvrdil) | 1 |
| C4 | MAJOR | PLAN | vyřešen v #6 (kritik potvrdil) | 1 |
| C5 | BLOCKER | PLAN | vyřešen v #8 (kritik značil NEW-1, potvrdil) | 1 |
| C6 | MAJOR | PLAN | vyřešen v #8 (kritik značil NEW-2, potvrdil) | 1 |
| C7 | MAJOR | PLAN | vyřešen v #8 (kritik značil NEW-3, potvrdil) | 1 |
| C8 | MINOR | PLAN | vyřešen v #8 (kritik značil NEW-4, potvrdil) | 1 |
| C9 | MAJOR | PLAN | vyřešen v #10 (kritik potvrdil) | 1 |
| C10 | MINOR | PLAN | vyřešen v #10 (kritik potvrdil) | 1 |
| C11 | MAJOR | PLAN | otevřený (kritik značil NEW-7) | 1 |
| C12 | MAJOR | PLAN | otevřený (kritik značil NEW-8) | 1 |
| C13 | MINOR | PLAN | otevřený (kritik značil NEW-9) | 1 |
| C14 | MINOR | PLAN | otevřený (kritik značil NEW-10) | 1 |
