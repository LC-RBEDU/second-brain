# Pipeline: Týmové karty CP na wiki + skill

Stav: DONE
Plán: docs/plans/2026-10-04-wiki-cp-dashboard-skill.md
Schvalování plánu uživatelem: ne
Profil: SECOND_BRAIN
Architekt: přeskočen (plán schválen v předchozím chatu, kritik r6)
Kritik: agent ID 4b5d45b9-4d76-441f-8501-d3115c5604a4 (r6 SCHVÁLENO, 0 nálezů); předchozí 98139ff3, 775f6714, 55c13b81, dbd3e345, 7670dee4
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main před pipeline): 7b7f67a24e4afe998dd5ebd6fae7e77f0a42aa11 · Kódový SHA: 195bdaee7acc8f14e79578fde5f66c1da4cfdc00 · Review SCHVÁLENO na: 195bdaee7acc8f14e79578fde5f66c1da4cfdc00 · QA PASS na: 195bdaee7acc8f14e79578fde5f66c1da4cfdc00 · TESTER: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno (uživatel řekl implementovat)
Goal: complete

## Zadání (doslovně) a rozhodnutí

### Zadání uživatele (doslovně, chat 556327f9)

Rád bych vytvořil konkrétní zadání, ze kterých nechám Claude Team vytvořit:
1. konkrétní artefakty — viz níže
2. skill pro jejich tvorbu a aktualizaci

Vše musí být nezávislé na mém vaultu a Second Brain — ten používám jenom já a cílem je, že tento dashboard a karty priorit budou dostupné všem členům týmu

Konkrétně k artefaktům:
1. Přehledový dashboard — řádky = jednotlivé CP, pouze klíčové sloupce
2. Karta každé priority — Název; Co to konkrétně znamená; Kontext; Owner; Klíčové osoby; DoD + aktuální stav plnění; Přehled milníků se zvýrazněním nejbližšího

Doplnění z téhož chatu: až karty budou plně funkční, ranking ve vaultu má běžet vůči informacím z karet na Wiki. Zatím karty nejsou, aktuální podoba ve vaultu je OK.
Sidelined témata v bulleted listu pod tabulkou dashboardu.
ICE/ABC/ranking+5/cesty do Obsidianu jen ve vaultu, navázané na karty, ne v kartách.

Pokyn v tomto chatu (doslovně): Chci, abys navázal na chat: 556327f9-40ab-4ae6-b64f-072b63116136 a začal dle /rbu-pipeline implementovat plán "Týmové karty CP na wiki + skill"

### Rozhodnutí

- Kanál: firemní RB Wiki, sekce „Strategické priority RB EDU“ (`strategicke-priority-rb-edu/`), top-level.
- Dashboard = `prehled.md`, ne `index.md`. Sloupce: ID, Priorita, Owner, Nejbližší milník, Termín, Stav (`v termínu` / `riziko` / `hotovo` / `neznámé`).
- Update: kdokoli v Claude Team smí zapsat allowlist; v historii musí být jméno autora. MCP identitu neověřuje.
- DoD / `cp_owner` / Kontext / CO / Owner / klíčové osoby / seznam 9 CP / sidelined: lock bez flagu „DoD/obsah se mění“ nebo strat. týmu.
- CP2: DoD ze sheetu + značka „DoD neuzavřené“; owner Mária Falterová; Kateřina Bayerová (Káťa) klíčová osoba.
- Create bez milníku v balíčku → prázdný Termín, `progress: neznámé`, žádné vymyšlené datum.
- První create neodkazuje na charter Technařů ani na stránku Summitu.
- Ranking cutover (`today_priority.py`) mimo toto kolo.
- Schvalování plánu: ne. Uživatel řekl implementovat hotový plán.
- TESTER: přeskočeno (profil SECOND_BRAIN) — zapíše se při DONE, ne před QA.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-04 | CRITIC r6 | 4b5d45b9-4d76-441f-8501-d3115c5604a4 | SCHVÁLENO | 0 | předchozí chat; plán beze změny chování |
| 2 | 2026-10-04 | IMPLEMENT | hlavní | hotovo | | skill + balíček; wiki sekce + 9 karet + prehled + odstavec v kořeni. Stránky jsou draft, owner human:lukas. `generated` na wiki je objekt (boolean server odmítá). |
| 3 | 2026-10-04 | REVIEW | 0b830a7b-b94b-45c0-b97f-2c73e080fe19 | SCHVÁLENO | 1 MINOR | NEW-1 → D1: po flagu skill výslovně nezakazuje ICE/ABC na kartě. Push přeskočen: diff nemění `vps/second-brain-hub/`. |
| 4 | 2026-10-04 | QA | 4d149aa7-764c-4e29-accd-6b4656efbc4c | PASS | 0 | pytest 273; wiki_read 9 karet + přehled + kořen. Deploy se netýká. |
| 5 | 2026-10-04 | DONE | hlavní | DONE | D1 MINOR otevřený | TESTER přeskočeno. Vlastní gate pytest 273 exit 0. |

## Otevřené nálezy

| ID | Závažnost | Typ IMPL/PLAN/ENV | Stav | Kolikrát vznesen |
|---|---|---|---|---|
| D1 | MINOR | IMPL | otevřený | 1 |
