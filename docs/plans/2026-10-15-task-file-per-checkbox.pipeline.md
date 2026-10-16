# Pipeline: task soubor místo checkboxu

Stav: IMPLEMENT
Kritik: SCHVÁLENO · c6b287c7-5e95-47db-af24-543f84525817 · 0 BLOCKER, 0 MAJOR
Plán: docs/plans/2026-10-15-task-file-per-checkbox.md
Schvalování plánu uživatelem: ne
Architekt: resume d3b2bc77-6c50-4b46-a3ac-278dd17c886b · otevření #2 · generace k=1/3 · kolo r=2/3
Šťoural: g=2 HOTOVÝ · 1418a290-3fcc-489c-acc5-e9c88d4a6af7. g=1 eb9a4192 je po deltě r=2 neplatný.
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku): neřešeno (ještě bez implementace) · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: přeskočeno (profil SECOND_BRAIN) až v DONE
Plán schválen uživatelem: nevyžadováno
Goal: aktivní

## Projekt

SECOND_BRAIN. Kořen `~/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN`. Větev `main`. Ostrý zápis do vaultu jen po suchém náhledu a výslovném apply. Tester se nespouští.

## Zadání (doslovně) a rozhodnutí

Uživatel: „Ale ještě než se do toho pustím, tak bych chtěl dotáhnout do konce změnu struktury v tom smyslu, že chci mít pro každý task jeden .MD soubor a ne jen položku v checklistu v rámci jednoho story. … Takže chci, abys připravil tuto strukturální změnu, doptal se na detaily a chybějící informace, připravil plán a pak ji přes /rbu-pipeline také zrealizujeme.“

Volby: tvar = tři soubory (epic → story kontejner → task; status, focus a deadline žijí na tasku). Migrace = jen otevřené checkboxy; hotové `[x]` zůstanou ve story.

Uživatel potom: „ok, napadá mě, jak je to s deadliny - měly by asi existovat závislosti - např. deadline story nedává smysl, aby byla dřív než nejpozdější deadline tasku v tomto story a podobně. tohle a podobné závislosti by se měly dotáhnout.“

A pak: „ok, pošli šťourala.“

### Rozšíření MCP (2026-10-16, doslovně)

Uživatel: „OK, takže zadání na rozšíření plánu o fixaci MCP je zde: /Users/lukascypra/Downloads/2026-10-16-brain-mcp-pozadavky.md. Je tam několik otázek, tak se na ně doptej, odpovím. Stejně tak se doptej k samotnému plánu, resp. na něj můžeš pustit rovnou /rbu-pipeline.“

Odpovědi:
- close_task rodiče jen navrhne, sám story nezavře.
- Focus: bot smí navrhnout (`propose_focus`) a zapsat až po ano (`apply_focus`). Strop 10. Focus na story s otevřeným child taskem se odmítne.
- Alias starého id checkboxu jen 90 dní, pak přestane platit.
- Rozsah: P1, P2 i P3 v jedné změně, pokud to nerozbije migraci ani kontrakt termínů. Když něco rozbije, architekt to oddělí a řekne proč. Default je dodat vše.

### Grill g=1 odpovědi (2026-10-15)

- **Q1:** A, a musí to být varování, ať člověk rozhodne, jestli dá deadline dítěte na dřív, nebo si může dovolit posunout deadline rodiče. Obsidian se nepoužívá, vše je v Gitu. Cokoliv souvisejícího s Obsidianem smazat a zlikvidovat, ať to nemate. Přidat na začátek plánu.
- **Q2:** A. Jen `deadline`.
- **Q3:** B. Předek proti všem otevřeným potomkům s deadline.
- **Q4:** B. Jedno otevřené dítě: obě datová pole na task. Víc dětí: datum zůstane na story, dry-run to vypíše.
- **Q5:** předpoklad Šťourala, uživatel neodporoval. Do maxima Doing, Next, Backlog, Waiting s deadline. Done, Cancelled a `[x]` mimo. Rodič se sám neposouvá.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-10-15 | GRILL | 7e0171ef-d61b-48f8-a874-e5dff7bee1d5 | POTŘEBUJE ODPOVĚDI | Q1–Q4 blokující, Q5 ne | g=1 |
| 2 | 2026-10-15 | PLAN | 98ebe203-e076-4313-b974-707bcbb632ed | plán k=1 r=1 | — | kontrakt po Q1–Q5 |
| 3 | 2026-10-15 | GRILL | 1ab503f7-bede-4daa-914a-7251c21a3f02 | POTŘEBUJE ODPOVĚDI | Q6 Q8 Q10 blokující | g=2 |
| 4 | 2026-10-15 | PLAN | 98ebe203-e076-4313-b974-707bcbb632ed | delta r=2 | — | Q6 Q8 Q10 zapracováno |
| 5 | 2026-10-15 | GRILL | 42b82ecb-ec3d-4ef9-a80c-6170115b5bf7 | HOTOVÝ GRILL | 0 | g=3 otevření #1, zrušeno rozšířením MCP |
| 6 | 2026-10-16 | PLAN | d3b2bc77-6c50-4b46-a3ac-278dd17c886b | delta r=1 | — | resume 98ebe203 selhal (instance pryč); P1–P3 v jedné změně |
| 7 | 2026-10-16 | GRILL | eb9a4192-966e-4a0b-a624-6f1baceb2c62 | HOTOVÝ GRILL | 0 | A19–A31 zapsány |
| 8 | 2026-10-16 | CRITIC | 6d95abf8-3b0f-4fea-b1cc-2d99f0247935 | K PŘEPRACOVÁNÍ | 1 BLOCKER, 4 MAJOR | NEW-1 až NEW-5 |
| 9 | 2026-10-16 | PLAN | d3b2bc77-6c50-4b46-a3ac-278dd17c886b | delta r=2 | — | NEW-1 až NEW-5 zavřené v plánu |
| 10 | 2026-10-16 | GRILL | 1418a290-3fcc-489c-acc5-e9c88d4a6af7 | HOTOVÝ GRILL | 0 | A32 a A33 zapsány |
| 11 | 2026-10-16 | CRITIC | c6b287c7-5e95-47db-af24-543f84525817 | SCHVÁLENO | 0 | implementace může začít, F8 apply až po suchém náhledu |
| 12 | 2026-10-16 | IMPLEMENT | hlavní | rozpracováno | — | deadline, alias, fronta, recurring, Closes, focus propose/apply |
| 13 | 2026-10-16 | IMPLEMENT | hlavní | rozpracováno | — | find/get/tree, edit, toggle, close |
| 14 | 2026-10-16 | IMPLEMENT | hlavní | rozpracováno | — | create, bulk, promote gate |
| 15 | 2026-10-16 | IMPLEMENT | hlavní | rozpracováno | — | write_plan |
| 16 | 2026-10-16 | IMPLEMENT | hlavní | rozpracováno | — | Smazané šablony .base, zákaz Obsidianu jako editoru. |
| 17 | 2026-10-16 | IMPLEMENT | hlavní | gate zelený | — | 423 hub + 139 brain. Commit 6fd95f7. |
| 18 | 2026-10-16 | REVIEW | 13ae5ee7 | K OPRAVĚ | 7 BLOCKER, 5 MAJOR | NEW-1 cron Done, NEW-2 append checkbox, NEW-3 toggle okno, NEW-4 create deadline, NEW-5 .base, NEW-6 dry-run, NEW-7 YAML, NEW-8 pole, NEW-9 pozdější rodič, NEW-10 index Closes, NEW-11 log čtení, NEW-12 testy. |
| 19 | 2026-10-16 | IMPLEMENT | hlavní | opraveno | — | NEW-1 až NEW-12. Gate 431 + 142. Commit 906e2a8. NEW-13 byl minor: outside_steps hledá poslední nadpis v celém těle. |
| 20 | 2026-10-16 | REVIEW | c317d4fc | K OPRAVĚ | 1 BLOCKER, 3 MAJOR | NEW-5 embed v tasks/, NEW-10 Closes po dni 91, NEW-14 dry-run epic, NEW-15 append dry_run na MCP/REST. |
| 21 | 2026-10-16 | IMPLEMENT | hlavní | opraveno | — | Embed i v tasks/*.md, expirované checkbox id nezavře story, dry-run nese epic a deadline, append dry_run na MCP i REST. Gate: hub+scripts 434 passed, brain 143 passed. Commit ab92bfc. |
| 22 | 2026-10-16 | REVIEW | 215c3f22 | K OPRAVĚ | 0 BLOCKER, 1 MAJOR | NEW-1: po kotvě Closes ID-N bez promoted_from nic neodškrtne, a po dni 91 už natrvalo. |
| 23 | 2026-10-16 | IMPLEMENT | hlavní | opraveno | — | Expirované id s promoted_from story nezavře. Živý krok na souboru se odškrtne. Chybějící řádek je noop, ne Done story. Hub+scripts 437 passed. |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
| --- | --- | --- | --- | --- | --- |
| Q1 | BLOKUJÍCÍ | PLAN | otevřený | 1 |
| Q2 | BLOKUJÍCÍ | PLAN | otevřený | 1 |
| Q3 | BLOKUJÍCÍ | PLAN | otevřený | 1 |
| Q4 | BLOKUJÍCÍ | PLAN | otevřený | 1 |
| Q5 | NEBLOKUJÍCÍ | PLAN | předpoklad do odpovědi (Doing/Next/Backlog/Waiting s deadline; Done/Cancelled a [x] mimo) | 1 |
