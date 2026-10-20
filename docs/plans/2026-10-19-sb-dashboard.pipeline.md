# Pipeline: Second Brain dashboard
Stav: IMPLEMENT
Plán: docs/plans/2026-10-19-sb-dashboard.md
Schvalování plánu uživatelem: ne
Architekt: agent ID 0888cb93-6494-4253-9cd4-3e994cfcca21, otevření plánu #2, generace v otevření k=1/3, kolo r=1/3 (otevření #1 skončilo na k=3/3 r=3/3)
Šťoural: agent ID 1f9e157f-872a-41b2-ad22-29dea2594c54 · kolo grill g=10 (POTŘEBUJE ODPOVĚDI, 2, z toho 0 BLOKUJÍCÍ) · g=9 byl 77162b85-a925-414e-9407-c22d9b7fc9fc
Kritik: agent ID 69a3f66c-b60f-4626-9d19-db0252ccee03 · kolo 3 (SCHVÁLENO, 0 BLOCKER, 0 MAJOR) · kolo 2 byl 7ca065b5-ad2f-4de0-9445-b401fc5851a6
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (origin/main při vzniku): 9e0189e45994a6826708afd7606252936b880940 · Kódový SHA: 5193eef6c5ddee507c14640646a8f4b5b3412180 · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Goal: aktivní

## Zadání (doslovně) a rozhodnutí

Uživatel, 2026-10-19:

Navazuji na předchozí změny a chtěl bych do projektu Second Brain přidat další funkcionalitu, která přidá frontend a možnost práce s úkoly.

Zadání je zde: /Users/lukascypra/Downloads/handoff-cursor,  včetně příkladů, wireframů atd.

Chci, aby sis to prošel, doptal se, a pak na to pustil /rbu-pipeline

Zatím ještě běží aktualizace MCP v jiném agentovi, ale počítám, že pro otázky a přípravu plánu to není blocker? Pokud by byl, počkáme

Uživatel, 2026-10-19, po vyjasnění zápisu:

implementaci nespustím dřív než doběhne druhá pipeline, takže počítej s tím, že druhý agent dodělá to, co má v zadání a pak to bude na téhle pipeline aby se o to postarala, takže s tímto vědomím můžeš připravovat plán

Specifikace (soubory, architect je přečte celé, nic nevynechá):

- `/Users/lukascypra/Downloads/handoff-cursor/00-handoff-dashboard-cursor.md`
- `/Users/lukascypra/Downloads/handoff-cursor/01-spec-dashboard-pravidla.md`
- `/Users/lukascypra/Downloads/handoff-cursor/02-classify.js`
- `/Users/lukascypra/Downloads/handoff-cursor/03-brief-export-tasks.md`
- `/Users/lukascypra/Downloads/handoff-cursor/04-brain-opravy.md`
- `/Users/lukascypra/Downloads/handoff-cursor/wireframy/README.md`
- `/Users/lukascypra/Downloads/handoff-cursor/wireframy-html/` (index a všech 7 obrazovek)

### Rozhodnutí

- „Druhá pipeline“ = rozpracovaný plán [export follow-upy](docs/plans/2026-10-19-export-followups.md) (uživatel: aktualizace MCP v jiném agentovi). `export_tasks` je hotový ([export_tasks](docs/plans/2026-10-19-export-tasks.md), DONE).
- Plán této pipeline vzniká teď. Implementace nezačne, dokud `docs/plans/2026-10-19-export-followups.pipeline.md` není `DONE`. Po SCHVÁLENO kritika tedy ne IMPLEMENT, ale čekání na ten stav.
- Follow-upy se berou jako dodané podle jejich plánu (R1–R8, A1–A8). Tahle pipeline je neopakuje a do jejich souborů teď nesahá.
- Co follow-upy výslovně nedělají a dashboard to potřebuje, dodělá tahle pipeline až po jejich DONE:
  - `bulk_update` vrátí strukturovaně `oid_mismatch` a aktuální oid (u follow-upů je to jen `update_task`, A7). Úklid zapisuje dávkou.
  - `needs_decision` v `get_context` = jen prošlá review date u tasku bez deadlinu (04-brain-opravy bod 5). Follow-upy to nemají.
- Schvalování plánu uživatelem: ne.
- MVP je celé zadání z handoffu §4 (Radar, Chybně zadané, Mapa, Projekt seznam + kanban, Detail, Nový task, Úklid). Mindmapa a hromadný posun deadlinů mimo Úklid = fáze 2. ICE = mimo.
- `classify.js` se převezme jako klasifikace. Dočasný seznam pěti hierarchických projektů se nepoužije: follow-upy A1 ověřily `hierarchy: true` u všech 17 charterů. Appka bere `projects[].hierarchy` z exportu.
- Prohlížeč Brain nevolá. Zápis s `expect_oid`. Konflikt = dialog, nic se tiše nepřepíše. `focus` jen `propose_focus` → `apply_focus`. Zrušeno = `Cancelled`. V UI vždy „ID — název“.
- `BRAIN_PUBLIC_URL` není dashboard UI (`vps/second-brain-brain/README.md`). Kam appka patří, zvolí architekt jako předpoklad.
- Grill g=1 (69bfa1a3): Q3 NEBLOKUJÍCÍ. Drop na Doing bez deadlinu otevře dialog na deadline; prázdné potvrzení nezapíše. Karta, která deadline už má, jde na Doing bez dalšího data.
- Grill g=1: Q4 NEBLOKUJÍCÍ. Radar, Chybně zadané, Mapa, Projekt i Úklid defaultně bez pauznutých projektů. Jeden přepínač je vrátí.
- Grill g=1: Q5 NEBLOKUJÍCÍ. Dlaždice: Overdue (jen prošlý deadline), K rozhodnutí, Due soon, Bez termínu, Waiting po termínu, Doing, Focus (v čísle sloty, v podtitulku epicy a počet prošlého focusu), Chybně zadané, Stale. Prošlý focus není vlastní dlaždice. Popisek „Overdue = deadline nebo review“ se nepoužije.
- Grill g=1: Q6 NEBLOKUJÍCÍ. Hledání = id, název, slug projektu, parent id. Bez těla, bez MiniSearch/Fuse.
- Grill g=1: Q7 NEBLOKUJÍCÍ. Jeden checkbox. Vypnuto = všechny kalendářní dny v rozsahu. Zapnuto = bez víkendů, bez státních svátků a bez 24.–26. 12.
- Grill g=1: Q8 NEBLOKUJÍCÍ. sslip z setup skriptu, druhé redirect URI na stávajícím Google klientovi, zápis service tokenem, autor commitu Brain. Vlastní doména ani lidský autor commitu do plánu nepatří.
- Q2 (uživatel, 2026-10-19): kanban mění jen status. Parent se mění v detailu. Přetažení na jiný epic parenta nemění.
- Q1 (uživatel, 2026-10-19): prefix zůstane. Řez dávek zůstává. Už zapsaná dávka se nevrací. Po konfliktu se úklid nezavře jako hotový: uložené úkoly jsou označené a zbytek zůstane předvybraný na další klik. Jeden commit na celý klik neplatí.
- Uživatel, 2026-10-19: ve stejném Coolify projektu Second Brain (environment production, uuid projektu `0e0b062b15bfef0bff7f7c45`) může vzniknout třetí aplikace vedle `second-brain-hub` a `second-brain-brain`. Potvrzuje A6.
- Poznámky Šťourala g=1 (zapracované v plánu r=2): jeden task jde přes `PATCH /v1/tasks`; číslo Focus sedí s `count_focus_slots`; Waiting bez `waitUntil` odmítne Brain; vlastní text pro `focus_story_has_open_child` a `focus_limit_exceeded`.
- Grill g=2 (d52874e3): Q1–Q8 z g=1 plán neporušuje. Nové otázky přečíslovány Q9–Q15.
- Q10 NEBLOKUJÍCÍ (g=2 Q2). Doing bez deadlinu a Waiting bez waitUntil UI nezapíše nikde, ne jen na kanbanu. Prázdné potvrzení Brain nevolá. Úprava názvu u existujícího Doing bez deadlinu projde, Hotovo a Zrušit taky. Nový Doing bez deadlinu a nové Waiting bez waitUntil neprojde. Na Novém jsou dvě pole, deadline a review. Vyplněný deadline review do create nepošle. Next a Backlog bez data UI pustí.
- Q11 NEBLOKUJÍCÍ (g=2 Q3). Ponechat jen u řádku bez deadlinu. Hromadný posun deadlinu je fáze 2.
- Q12 NEBLOKUJÍCÍ (g=2 Q4). Existující deadline a review se do obsazenosti dne počítají vždy, druhý checkbox není. Den obsadí otevřený task z kteréhokoli projektu včetně pauznutého. Done a Cancelled se nepočítají. Řádky způsobu A se přičtou, když jejich datum padne do rozsahu.
- Q13 NEBLOKUJÍCÍ (g=2 Q5). Jedno hledání (id, název, slug projektu, parent id) na Radaru, Chybně zadaných, Mapě, seznamu tasků v Projektu a v Úklidu. Výběr projektu v liště hledá projekty. Našeptávač parenta tělo neprohledává.
- Q14 NEBLOKUJÍCÍ (g=2 Q6). Stejný přepínač pauzy filtruje i seznam projektů na Novém a našeptávač parenta. Parent z jiného aktivního projektu v našeptávači zůstává.
- Q15 NEBLOKUJÍCÍ (g=2 Q7). Dlaždice Chybně zadané = počet tasků s aspoň jednou červenou chybou, bez `no_date`. Dlaždice Stale = jen Next nebo Doing s pravidlem `stale` (`updated` starší než 30 dní). `stale_unknown`, dlouhý název a markup v dlaždici Stale nejsou. Obrazovka Chybně zadané dál ukáže červené i žluté včetně `stale_unknown`.
- Q9 (uživatel, 2026-10-19): u jednoho tasku (detail, inline na Radaru, kanban) po konfliktu přijde varování a viditelný rozdíl. Tlačítka: „Přesto uložit“ zapíše uživatelovu úpravu s novým oid; „Upravit“ nezapíše a vrátí ho do formuláře s jeho úpravou. Samo se nezapíše. Úklid tento dialog nepoužívá.
- Poznámky Šťourala g=2 (zapracované v plánu r=3): suchý `bulk_update` vrací stejné 400 a 409 jako ostrý zápis. Parent se statusem Done v okně 7 dní není otevřený parent. `today` dlaždic je den Evropy/Prahy. REST `POST /v1/tasks` předá `detail`. Port slotů bere slug z `task.project` a pauzu odfiltruje dřív než story s otevřeným taskem.
- Grill g=3 (417881cf): Q1–Q15 plán neporušuje. Nové otázky Q16–Q19.
- Q18 NEBLOKUJÍCÍ (g=3 Q3). Náhled Done/Cancelled parenta přidá otevřené potomky z celého exportu, včetně pauznutého projektu, a ukáže je i při vypnutém přepínači. Nejdou odškrtnout. Seznam k procházení je dál filtruje.
- Q19 NEBLOKUJÍCÍ (g=3 Q4). `deadline_order` a `open_child_under_closed_parent` na detailu, inline Radaru a kanbanu ukážou důvod a id. Zápis neproběhne. „Přesto uložit“ se nenabídne. Děti se neposouvají a nezavírají. Rodinu zavírá jen Úklid.
- Q16 (uživatel, 2026-10-19): tři režimy pořadí rozprostření. Výchozí „projekt a epic jako jeden blok“: slug projektu, pak id epicu, uvnitř bloku `updated` vzestupně, chybějící `updated` nakonec, pak id. Druhý režim `priority_score` sestupně, prázdné nakonec, stejný tie-break. Třetí režim jen stáří (`updated`).
- Q17 (uživatel, 2026-10-19): z náhledu se neodešle nic, dokud má každý ponechaný řádek den. Zrušit a Hotovo v tom samém náhledu čekají taky. Max za den je pole, výchozí 8, minimum 1.
- Grill g=4 (c1d3f88b): Q1–Q19 plán neporušuje. Nové otázky Q20–Q23.
- Q22 NEBLOKUJÍCÍ (g=4 NEW-3) → předpoklad A. Mezičlánek v řetězu (story už Hotovo nebo Zrušeno mezi epicem a otevřeným taskem) se použije jen když je ten řádek v exportu, včetně zavřeného v okně 7 dní. Soubor, který export vynechal, hop není. Server vrátí `open_child_under_closed_parent` jen pro dítě, které náhled tímhle chodem umí ukázat.
- Q23 NEBLOKUJÍCÍ (g=4 NEW-4) → předpoklad A. Rodina nad 80 se nezapíše a nerozkrojí. Checkbox potomka zůstane zamčený. Zápis uvolní až odebrání předka z výběru. Obrazovka zůstane otevřená. Ani suchý běh neodejde.
- Poznámky g=4 k zapracování spolu s Q20/Q21 (nečekají na další otázku): u Doing bez deadlinu se Ponechat nenabídne. Rozsah rozprostření Od–Do je oboustranně včetně krajů. Panel pořadí deadlinů bere celý export i při vypnuté pauze; stejný den projde; review do pravidla nevstupuje; uzel bez deadlinu potomka neschová; víc konfliktů se ukáže všech. Nový task při `deadline_order` soubor nezaloží, dialog „Přesto uložit“ se neotevře a ukáže důvod a obě data.
- Q20 (uživatel, 2026-10-19): obsazenost je stav po tomto náhledu. Zavřený řádek (včetně zamčeného potomka) den uvolní. Řádek s novým review se počítá jen v ten nový den. Ostatní otevřené tasky, i z pauznutého projektu, zůstávají. Jeden task přidá v jednom dni nejvýš 1, i když deadline a review padnou na stejný den.
- Q21 (uživatel, 2026-10-19): bližší uzavření vyhraje a v náhledu je vidět před potvrzením. Přímé Hotovo nebo Zrušit na potomkovi je blíž než tah předka. Ponechat na potomkovi ustoupí: přepne se na status bližšího zavíraného předka, checkbox je zamčený, den nepotřebuje. Dva předkové s různým statusem: bližší.
- Grill g=5 (f35f02c9): plán je celý. Nové otázky Q24–Q28.
- Q27 NEBLOKUJÍCÍ (g=5 NEW-4) → předpoklad. Ponechat se u Waiting bez `waitUntil` nenabídne. Zrušit a Hotovo zůstanou, protože výsledný status už Waiting není.
- Q28 NEBLOKUJÍCÍ (g=5 NEW-5) → předpoklad. Víc rodičů v jedné dávce, u každého jiné chybějící dítě: nic se nezapíše. `detail.failures` je seznam `{parent_id, child_ids}` seřazený podle `parent_id`. U jednoho rodiče zůstanou i `detail.parent_id` a `detail.child_ids`.
- Q24 (uživatel, 2026-10-19): vlastní datum na řádku má přednost. Pole pro celý výběr vyplní jen ponechané řádky bez vlastního data a z fronty je vyřadí. Rozprostření dostane jen ponechané bez konkrétního data. Konkrétní datum se nekontroluje proti víkendům, svátkům ani Od–Do; do mapy se počítá i mimo rozsah a den smí překročit max. Od, Do, max a checkbox drží zápis jen když fronta rozprostření není prázdná. Prázdné Od, prázdné Do nebo Od po Do pak neodejde nic. Když je fronta prázdná, tato pole zápis nedrží.
- Q25 (uživatel, 2026-10-19): checkbox zamčeného potomka zůstane zamčený. Řádek nejde vyřadit ani vrátit na Ponechat. Hotovo a Zrušit přepnout jde; jakmile je uživatel změní, je to přímá akce a vyhraje nad předkem. Dokud je nezmění, platí status bližšího zavíraného předka. Do zápisu jde jen ten status, ne review date, které na řádku bylo před ustoupením.
- Q26 (uživatel, 2026-10-19): Done a Cancelled v exportu most pořadí deadlinů netvoří. Most tvoří jen otevřený uzel, i když deadline nemá. Stejný den projde, review do pravidla nevstupuje. Server dál čte svou dnešní množinu. Když vrátí 409, panel se složí z `detail` a druhý patch se neposílá.
- Grill g=6 (21bcf629): plán je celý a končí tabulkou Q24–Q28. Nové otázky Q29 (NEW-1, BLOKUJÍCÍ) a Q30 (NEW-2, NEBLOKUJÍCÍ).
- Q30 NEBLOKUJÍCÍ (g=6 NEW-2) → předpoklad A. Stejné otevřené dítě je v `child_ids` každého zavíraného předka, kterého chod A21 po aplikaci zavíracích patchů pořád vidí. Dítě kryje jen patch, jehož výsledný status je Done nebo Cancelled. Položka, která ho nezavírá, ho neschová. Řazení je podle kódových jednotek id. Jeden rodič si nechá `detail.parent_id` a `detail.child_ids`. Dva a víc mají jen `detail.failures`. HTTP 400, suchý i ostrý běh, nikdo se nezapíše.
- Q29 (uživatel, 2026-10-19): nechat staré review. Vlastní datum na řádku se předvyplní stávajícím `review_deadline`. Pole pro celý výběr začíná prázdné, ten řádek nepřepíše a rozprostření ho nedostane. Review se v náhledu pohne, teprve když uživatel předvyplněné datum smaže. Nejdřív se ptal „proč by šel řádek do úklidu, pokud má review date?“ a po vysvětlení zvolil tuhle variantu (prefill).
- Poznámky g=6 k zapracování spolu s Q29 (nečekají na další otázku): A18 cituje A25, ten předpoklad v plánu není, pravidlo mostu je v A20. B48 u prvního náhledu (OWN + FILL, fronta prázdná, obsazenost `2026-11-08` je 2) má říct, že zápis odejít smí a že `2026-11-12` je v mapě. B50 nejde splnit jako jeden průchod: Done story v exportu (archiv, okno 7 dní) most na serveru netvoří, protože v `iter_active_tasks` není; Done story pořád ve `02-PROJEKTY/<slug>/tasks` v exportu není, server přes ni mostí a 409 složí panel z `detail`. k=2 je na stropu r=3, další plán bere nový architekt.
- Grill g=7 (a3daa43b): plán je celý, B50 není useknuté. Tři NEBLOKUJÍCÍ, žádná BLOKUJÍCÍ. Přechod CRITIC bez čekání.
- Q31 NEBLOKUJÍCÍ (g=7 NEW-1) → předpoklad A. Smazání předvyplnění a ručně napsané vlastní datum platí do zavření náhledu. První přechod řádku na Ponechat v tom náhledu předvyplní neprázdné `review_deadline`, pokud ho uživatel ještě nesmazal. Přepnutí pryč a zpět ani refresh po zapsané dávce datum nevrátí. Nové otevření náhledu předvyplní znovu.
- Q32 NEBLOKUJÍCÍ (g=7 NEW-2) → předpoklad A. Potvrzení předvyplněného dne posílá jen `review_deadline`. `updated` se nemění. Věta v riziku 25 o posunu `updated` neplatí.
- Q33 NEBLOKUJÍCÍ (g=7 NEW-3) → předpoklad A. Po 400 `open_child_under_closed_parent` v Úklidu zůstane obrazovka i nezapsaný výběr. Uživatel vidí id a názvy rodičů a dětí z `detail.failures`, nebo u jednoho rodiče z `detail.parent_id` a `detail.child_ids`. Dialog neshody oid ani „Přesto uložit“ se neukáže.
- Poznámky g=7 k plánu (nečekají na otázku): Do `child_ids` patří jen předek, kterého tahle dávka zavírá a kterého chod pořád vidí. Story už Done v exportu je jen hop, ne položka `failures`. A23: smazání není jediná cesta, ruční přepis data na řádku je vlastní datum (Q24). Po smazání předvyplnění řádek svůj starý den v mapě nedrží, dokud nedostane nové konkrétní datum. B54: pořadí rodičů ve `failures` je podle kódových jednotek a v jednom `child_ids` je id jednou; případ, kdy dítě kryje patch Done, na ostro zapíše. B52: „druhý patch“ je automatický retry po 409; formulář si nechá zadané datum a nové Uložit po úpravě data je nový požadavek.
- Grill g=8 (4f3dd7b7): plán je celý, B48 není useknuté. Q1–Q33 a C1–C8 plán neporušuje. Nové otázky Q34 (NEW-1, BLOKUJÍCÍ), Q35 (NEW-2), Q36 (NEW-3).
- Q35 NEBLOKUJÍCÍ (g=8 NEW-2) → předpoklad. V jednom `bulk_update` se do `detail.failures` seberou všechny neshody `expect_oid`. Pořadí je podle kódových jednotek `id`. `write_text` se nezavolá. Jedna neshoda zůstává seznam o jednom prvku.
- Q36 NEBLOKUJÍCÍ (g=8 NEW-3) → předpoklad. První odpověď Brainu, která není úspěch, zastaví další dávky. Platí i pro 404 `not_found` a 5xx. Už commitnutá dávka se nevrací. Úklid zůstane otevřený a vrátí `written`, `failed`, `pending`.
- Poznámky g=8 k plánu (nečekají na otázku): Task právě přepsaný na Done nebo Cancelled po refreshi v exportu není, dokud ho `archive_done_tasks` nepřesune, a ve sloupci Done se objeví jen když je `updated` v okně 7 dní. `updated` se kvůli tomu nedoplňuje. U `B-E` v B38 chybí `updated` a `priority_score`; na pořadí fronty to nesahá, věta u C8 u toho id ale nesedí.
- Q34 čeká. BLOKUJÍCÍ: řádek s cestou pod `07-ARCHIV/` a drop ze sloupce Done.
- Q34 (uživatel, 2026-10-20): jen číst. Řádek s cestou pod `07-ARCHIV/` je jen ke čtení na všech plochách. Žádný drop, detail, focus ani „Otevřít celý task“. BFF takový PATCH odmítne 400 a Brain se nezavolá. Přesun souboru zpět do `tasks/` do plánu nepatří. Drop tasku, který ve `02-PROJEKTY/<slug>/tasks` pořád leží, na Done zůstává PATCH jen se statusem.
- Grill g=9 (77162b85): plán je celý (A26, B57, riziko 28, tabulka Q34–Q36). Q1–Q33, Q35, Q36 a C1–C8 sedí. Tři NEBLOKUJÍCÍ, žádná BLOKUJÍCÍ. Přechod CRITIC bez čekání. k=3 je na stropu r=3, architekta neresumovat.
- Q37 NEBLOKUJÍCÍ (g=9 NEW-1) → předpoklad A27. Archivní řádek nejde otevřít, ani jen ke čtení. Žádný inline, žádný checkbox Úklidu, žádný drop, focus ani „Otevřít celý task“. R1, A26, B57 a T8 říkají tutéž větu. BFF dál vrací 400 `archive_readonly` a Brain se nezavolá.
- Q38 NEBLOKUJÍCÍ (g=9 NEW-2) → předpoklad A28. Redirect URI nového sslip se přidá na stávajícího Google klienta. Nový klient ani vlastní doména do plánu nepatří.
- Q39 NEBLOKUJÍCÍ (g=9 NEW-3) → předpoklad A29. `failures[].oid` je aktuální oid souboru. Úklid po 409 označí řádky z potvrzených dávek jako uložené. Řádky z neúspěšné dávky i neodeslané zůstanou předvybrané. U neshod se `expect_oid` vymění za aktuální a další požadavek odejde až na nový klik. Sám se nezapíše. Dialog Q9 se neukáže.
- Poznámka g=9 k plánu (nečeká na otázku): úspěšný `bulk_update` předá `expect_oid` i do `write_text`. Dnešní smyčka ho nepředává a `git_io._check_cas` při `expect_oid is None` soubor nehlídá. Závod uprostřed smyčky zůstává B9.
- Uživatel, 2026-10-20, po nekonvergenci (doslovně): „zjednoduš to - archivované / done úkoly do toho přehledu vůbec nezobrazuj a hotovo“. Q40. Nové otevření plánu #2. Archivované úkoly a úkoly se statusem Done se v přehledu dashboardu nezobrazují. C10 (závod uprostřed dávky má být 409, ne 500) zůstává k zapracování. C9 se řeší v tomhle zjednodušení, ne druhým zámkem na vault.
- Grill g=10 (1f9e157f): plán je celý a končí tabulkou C9, C10 a Q40. Dvě NEBLOKUJÍCÍ, žádná BLOKUJÍCÍ. Přechod CRITIC bez čekání.
- Q41 NEBLOKUJÍCÍ (g=10 NEW-1) → předpoklad A31. Po úspěšné dávce se export načte znovu. Done a Cancelled se nikde nevykreslí. `written` je počet a id bez karet. Jako uložený jde označit jen řádek, který v exportu zůstal otevřený. `failed` a `pending`, které v exportu pořád jsou, zůstanou předvybrané a `expect_oid` se u neshod vymění. Náhled se zavře, až když `failed` i `pending` jsou prázdné. Detail právě zavřeného úkolu se zavře a vrátí se na seznam, odkud se otevřel.
- Q42 NEBLOKUJÍCÍ (g=10 NEW-2) → předpoklad A32. Prohlížeč u `parse_errors` přeskočí `parent_closed` stejně jako `parent_not_found`. Jediný červený důvod chybějícího parenta je `parent_missing_or_closed`. Serverový export se nemění. Dlaždice počítá task, ne počet důvodů.
- Poznámka g=10 k plánu (nečeká na otázku): kontrola otevřeného dítěte běží i pro čisté Done nebo Cancelled. `needs_forest` dnes pro samotný status Done vrací false (`parent_link.py` 117–123) a B12 přesto čeká 400.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|---|---|---|---|---|---|
| 1 | 2026-10-19 17:40 | PLAN | 19c17eb7-c57b-4921-9686-c10152ffa67e | plán v odpovědi | — | Hlavní agent zapsal docs/plans/2026-10-19-sb-dashboard.md. Přechod GRILL |
| 2 | 2026-10-19 17:58 | GRILL | 69bfa1a3-af8f-4ba7-9012-4b550e17d3e1 | POTŘEBUJE ODPOVĚDI (8, z toho 2 BLOKUJÍCÍ) | Q1 Q2 BLOKUJÍCÍ | g=1. Q3–Q8 zapsány jako předpoklady. Přechod AWAITING_USER (z: grill) |
| 3 | 2026-10-19 18:20 | PLAN | 19c17eb7-c57b-4921-9686-c10152ffa67e | plán r=2 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md. Přechod GRILL g=2 |
| 4 | 2026-10-19 18:38 | GRILL | d52874e3-1e61-411e-a175-754d02912846 | POTŘEBUJE ODPOVĚDI (7, z toho 1 BLOKUJÍCÍ) | Q9 BLOKUJÍCÍ | g=2. Q10–Q15 zapsány jako předpoklady. Přechod AWAITING_USER (z: grill) |
| 5 | 2026-10-19 19:05 | PLAN | 19c17eb7-c57b-4921-9686-c10152ffa67e | plán r=3 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md. Přechod GRILL g=3 |
| 6 | 2026-10-19 19:00 | GRILL | 417881cf-f4f9-4d71-bc39-2f238c8e0876 | POTŘEBUJE ODPOVĚDI (4, z toho 2 BLOKUJÍCÍ) | Q16 Q17 BLOKUJÍCÍ | g=3. Q18 a Q19 zapsány jako předpoklady. Přechod AWAITING_USER (z: grill) |
| 7 | 2026-10-19 19:40 | PLAN | 6ae65175-e2e7-4338-90ab-85ca7d52766a | start r=1 k=2 | — | Q16 tři režimy, Q17 nic se nezapíše. k=1 má r=3, přebírá nový architekt |
| 8 | 2026-10-19 21:36 | PLAN | 6ae65175-e2e7-4338-90ab-85ca7d52766a | plán k=2 r=1 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (Q16–Q19). Přechod GRILL g=4 |
| 9 | 2026-10-19 21:52 | GRILL | c1d3f88b-1697-497c-871c-e73240bf5ecc | POTŘEBUJE ODPOVĚDI (4, z toho 2 BLOKUJÍCÍ) | Q20 Q21 BLOKUJÍCÍ | g=4. Q22 a Q23 zapsány jako předpoklady. Přechod AWAITING_USER (z: grill) |
| 10 | 2026-10-19 21:55 | PLAN | 6ae65175-e2e7-4338-90ab-85ca7d52766a | start r=2 k=2 | — | Q20 stav po náhledu, Q21 bližší uzavření. Resume stejného architekta |
| 11 | 2026-10-19 22:05 | PLAN | 6ae65175-e2e7-4338-90ab-85ca7d52766a | plán k=2 r=2 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (Q20–Q23). Přechod GRILL g=5 |
| 12 | 2026-10-19 22:22 | GRILL | f35f02c9-d927-48ff-b5cc-ad35eb4170f9 | POTŘEBUJE ODPOVĚDI (5, z toho 3 BLOKUJÍCÍ) | Q24 Q25 Q26 BLOKUJÍCÍ | g=5. Q27 a Q28 zapsány jako předpoklady. Přechod AWAITING_USER (z: grill) |
| 13 | 2026-10-19 22:25 | PLAN | 6ae65175-e2e7-4338-90ab-85ca7d52766a | start r=3 k=2 | — | Q24 vlastní datum, Q25 přepnutí statusu, Q26 zavřený most netvoří. Resume stejného architekta |
| 14 | 2026-10-19 22:40 | PLAN | 6ae65175-e2e7-4338-90ab-85ca7d52766a | plán k=2 r=3 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (Q24–Q28). Přechod GRILL g=6. k=2 je na stropu r=3 |
| 15 | 2026-10-19 23:00 | GRILL | 21bcf629-d578-4ab7-83e4-559d9256f6ff | POTŘEBUJE ODPOVĚDI (2, z toho 1 BLOKUJÍCÍ) | Q29 BLOKUJÍCÍ | g=6. Q30 zapsán jako předpoklad A. Přechod AWAITING_USER (z: grill) |
| 16 | 2026-10-19 23:20 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | start r=1 k=3 | — | Q29 předvyplnit staré review. k=2 má r=3, přebírá nový architekt |
| 17 | 2026-10-19 23:45 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | plán k=3 r=1 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (Q29 předvyplnění, Q30, B50/B52). Přechod GRILL g=7 |
| 18 | 2026-10-19 23:58 | GRILL | a3daa43b-e9e4-4116-b98b-42a9ae4026b2 | POTŘEBUJE ODPOVĚDI (3, z toho 0 BLOKUJÍCÍ) | — | g=7. Q31–Q33 zapsány jako předpoklady. Přechod CRITIC |
| 19 | 2026-10-20 00:16 | CRITIC | 78d1516b-260e-4cd5-8b5f-066c88ed2a6a | K PŘEPRACOVÁNÍ | 2 BLOCKER, 6 MAJOR | C1–C8. Q1–Q30 sedí. Chybí Q31–Q33 a poznámky g=7. Resume architekta, r=2 k=3 |
| 20 | 2026-10-20 00:26 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | plán k=3 r=2 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (C1–C8). Přechod GRILL g=8 |
| 21 | 2026-10-20 00:41 | GRILL | 4f3dd7b7-2c68-4b16-8240-a1b32c8735ca | POTŘEBUJE ODPOVĚDI (3, z toho 1 BLOKUJÍCÍ) | Q34 BLOKUJÍCÍ | g=8. Q35 a Q36 zapsány jako předpoklady. Přechod AWAITING_USER (z: grill) |
| 22 | 2026-10-20 00:45 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | start r=3 k=3 | — | Q34 archiv jen ke čtení. Resume stejného architekta. k=3 je na stropu r |
| 23 | 2026-10-20 00:52 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | plán k=3 r=3 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (Q34–Q36). Přechod GRILL g=9. k=3 je na stropu r=3 |
| 24 | 2026-10-20 01:07 | GRILL | 77162b85-a925-414e-9407-c22d9b7fc9fc | POTŘEBUJE ODPOVĚDI (3, z toho 0 BLOKUJÍCÍ) | — | g=9. Q37–Q39 zapsány jako A27–A29 a doplněny do plánu. Přechod CRITIC kolo 2 |
| 25 | 2026-10-20 01:23 | CRITIC | 7ca065b5-ad2f-4de0-9445-b401fc5851a6 | K PŘEPRACOVÁNÍ (1 BLOCKER, 1 MAJOR) | C9 BLOCKER, C10 MAJOR | C1–C8 ověřeny jako vyřešené. k=3 a r=3 jsou na stropu, další architekt v tomhle otevření nejde. Přechod AWAITING_USER (z: nekonvergence) |
| 26 | 2026-10-20 01:40 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | start otevření #2, k=1, r=1 | — | Uživatel: archivované a Done do přehledu vůbec nezobrazovat. Návrat kvůli odpovědi se do stropu nepočítá |
| 27 | 2026-10-20 01:35 | PLAN | 0888cb93-6494-4253-9cd4-3e994cfcca21 | plán otevření #2 r=1 v odpovědi | — | Hlavní agent přepsal docs/plans/2026-10-19-sb-dashboard.md (Q40, C9, C10). Přechod GRILL g=10 |
| 28 | 2026-10-20 01:51 | GRILL | 1f9e157f-872a-41b2-ad22-29dea2594c54 | POTŘEBUJE ODPOVĚDI (2, z toho 0 BLOKUJÍCÍ) | — | g=10. Q41 a Q42 zapsány jako A31 a A32 a doplněny do plánu. Přechod CRITIC kolo 3 |
| 29 | 2026-10-20 02:03 | CRITIC | 69a3f66c-b60f-4626-9d19-db0252ccee03 | SCHVÁLENO (0 BLOCKER, 0 MAJOR) | — | C1–C10 ověřeny. export-followups je DONE. Schvalování plánu není. Přechod IMPLEMENT, start F1 |
| 30 | 2026-10-20 02:10 | IMPLEMENT | hlavní agent | F1 | — | needs_decision je jen prošlá review bez deadlinu. pytest test_today_priority.py: 13 passed |
| 31 | 2026-10-20 02:20 | IMPLEMENT | hlavní agent | F2 | — | Kontrola dětí přes export na otevřeném vaultu. Bulk oid je 409 se seznamem failures. pytest hierarchy+bulk oid+create+cas: 57 passed |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
|---|---|---|---|---|
| Q1 | BLOKUJÍCÍ | grill | vyřešen v #3 (prefix zůstane) | 1 |
| Q2 | BLOKUJÍCÍ | grill | vyřešen v #3 (jen status) | 1 |
| Q9 | BLOKUJÍCÍ | grill | vyřešen v #5 (varování, rozdíl, Přesto uložit / Upravit) | 1 |
| Q16 | BLOKUJÍCÍ | grill | vyřešen v #7 (tři režimy) | 1 |
| Q17 | BLOKUJÍCÍ | grill | vyřešen v #7 (nezapíše se nic) | 1 |
| Q20 | BLOKUJÍCÍ | grill | vyřešen v #10 (stav po náhledu) | 1 |
| Q21 | BLOKUJÍCÍ | grill | vyřešen v #10 (bližší uzavření) | 1 |
| Q22 | NEBLOKUJÍCÍ | grill | předpoklad A v #9 (hop jen když je v exportu) | 1 |
| Q23 | NEBLOKUJÍCÍ | grill | předpoklad A v #9 (rodina nad 80 se nezapíše) | 1 |
| Q24 | BLOKUJÍCÍ | grill | vyřešen v #13 (vlastní datum má přednost) | 1 |
| Q25 | BLOKUJÍCÍ | grill | vyřešen v #13 (Hotovo/Zrušit u zamčeného jde přepnout) | 1 |
| Q26 | BLOKUJÍCÍ | grill | vyřešen v #13 (zavřený most netvoří) | 1 |
| Q27 | NEBLOKUJÍCÍ | grill | předpoklad v #12 (Ponechat u Waiting bez waitUntil se nenabídne) | 1 |
| Q28 | NEBLOKUJÍCÍ | grill | předpoklad v #12 (víc rodičů: detail.failures, nic se nezapíše) | 1 |
| Q29 | BLOKUJÍCÍ | grill | vyřešen v #16 (předvyplnit staré review) | 1 |
| Q30 | NEBLOKUJÍCÍ | grill | předpoklad A v #15 (stejné dítě u obou zavíraných rodičů) | 1 |
| Q31 | NEBLOKUJÍCÍ | grill | předpoklad A v #18 (smazání drží do zavření náhledu) | 1 |
| Q32 | NEBLOKUJÍCÍ | grill | předpoklad A v #18 (updated se neposune) | 1 |
| Q33 | NEBLOKUJÍCÍ | grill | předpoklad A v #18 (úklid ukáže id a názvy, nic nezapíše) | 1 |
| C1 | BLOCKER | PLAN | ověřeno v #25 | 1 |
| C2 | BLOCKER | PLAN | ověřeno v #25 | 1 |
| C3 | MAJOR | PLAN | ověřeno v #25 | 1 |
| C4 | MAJOR | PLAN | ověřeno v #25 | 1 |
| C5 | MAJOR | PLAN | ověřeno v #25 | 1 |
| C6 | MAJOR | PLAN | ověřeno v #25 | 1 |
| C7 | MAJOR | PLAN | ověřeno v #25 | 1 |
| C8 | MAJOR | PLAN | ověřeno v #25 | 1 |
| C9 | BLOCKER | PLAN | ověřeno v #29 | 1 |
| C10 | MAJOR | PLAN | ověřeno v #29 | 1 |
| Q40 | rozhodnutí uživatele | grill | vyřešen v #26 (archiv a Done se v přehledu nezobrazují) | 1 |
| Q41 | NEBLOKUJÍCÍ | grill | předpoklad A31 v #28 (written bez karet) | 1 |
| Q42 | NEBLOKUJÍCÍ | grill | předpoklad A32 v #28 (přeskočit parent_closed) | 1 |
| Q34 | BLOKUJÍCÍ | grill | vyřešen v #22 (archiv jen ke čtení) | 1 |
| Q35 | NEBLOKUJÍCÍ | grill | předpoklad v #21 (všechny neshody oid v jedné dávce) | 1 |
| Q36 | NEBLOKUJÍCÍ | grill | předpoklad v #21 (jakákoli chyba Brainu zastaví další dávky) | 1 |
| Q37 | NEBLOKUJÍCÍ | grill | předpoklad A27 v #24 (archiv nejde ani otevřít) | 1 |
| Q38 | NEBLOKUJÍCÍ | grill | předpoklad A28 v #24 (druhé redirect URI) | 1 |
| Q39 | NEBLOKUJÍCÍ | grill | předpoklad A29 v #24 (oid po 409 v úklidu) | 1 |
