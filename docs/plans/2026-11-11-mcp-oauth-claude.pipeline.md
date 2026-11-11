# Pipeline: MCP OAuth Claude

Stav: CRITIC
Plán: docs/plans/2026-11-11-mcp-oauth-claude.md
Schvalování plánu uživatelem: ne
Architekt: agent ID 9628d3a7-2aca-4985-b99f-a77b13444d46, otevření plánu #1, generace k=1/3, kolo r=1/3
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku větve): c930c5a5157abd5720bb146bbd86b305741b5e77 · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER: přeskočeno (profil SECOND_BRAIN) až v DONE auditu
Plán schválen uživatelem: nevyžadováno
Goal: aktivní

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

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
