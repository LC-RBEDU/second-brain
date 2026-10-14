# Pipeline: Brain append_task_note

Stav: DONE
Plán: docs/plans/2026-10-14-brain-append-task-note.md
Schvalování plánu uživatelem: ne
Architekt: agent ID b5d26299-9469-414b-a4b3-34bd0eb9d446, otevření plánu #1, generace v otevření k=2/3, kolo r=2/3
Šťoural: g=5 agent ID 2641ba9c-06f2-4138-bcba-8fb3a903d8fd · HOTOVÝ GRILL (0 otázek)
Kritik: kolo 5 agent ID d8b5ab8b-49fc-478e-bca2-e0bbfed2c75a · SCHVÁLENO (0 BLOCKER, 0 MAJOR)
Review: agent ID 8e8aa5b2-8878-4b2d-80b8-f04f49bf1a88 · SCHVÁLENO (0 BLOCKER, 0 MAJOR) na 99ad22a
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base (rbu-base, origin/main při vzniku větve): 99c3685c2a76860c6c48d0ff604661c30813f1c5 · Kódový SHA: 99ad22a9b93236a8840f7b79fe7845b81d497385 · Review SCHVÁLENO na: 99ad22a9b93236a8840f7b79fe7845b81d497385 · QA PASS na: 99ad22a9b93236a8840f7b79fe7845b81d497385 · TESTER: přeskočeno (profil SECOND_BRAIN)
Plán schválen uživatelem: nevyžadováno
Goal: complete

## Zadání (doslovně) a rozhodnutí

### Zadání uživatele (doslovně)

Zpráva 1:

Chci upravit funkčnost Brain MCP podle tohoto doporučení Groka:

"Second Brain do GitHubu nezapíše. Má k němu jen čtecí přístup a jeho nástroje umí založit nový úkol a změnit stav nebo termín, ale do textu existujícího úkolu (kroky, log, poznámky) nepřipíše nic.

Nejčistší oprava je přidat do Brainu (repo second-brain, část vps/second-brain-brain) jeden nový nástroj na doplnění poznámky, kroku nebo záznamu do logu úkolu. Hlídal by souběžné změny stejně jako dnešní úpravy stavu. Pak by Second Brain zvládl doplňky rovnou a bez obcházení. Mám na to pustit Cursor agenta? Nasazení na server by pak bylo na tobě, nebo na tom, kdo Brain spravuje."

Je to takto OK a dává smysl?

Zpráva 2:

ještě doplnění druhého agenta: "Nejjednodušší oprava je přidat do Brainu nástroj append_task_note, který připíše odrážku do logu, kroků nebo poznámek úkolu. Pak to půjde hned. Saturnin má ode mě podrobný popis, který můžeš předat agentovi, co Brain staví."

Zpráva 3 (příkaz):

nechej /rbu-pipeline architekta a další doladit zadání této změny

### Rozhodnutí z konverzace

- Uživatel nezadal `se schválením`. Po SCHVÁLENO kritika pipeline pokračuje do IMPLEMENT. Plán schválen uživatelem: nevyžadováno.
- Uživatel chce, aby zadání doladil architekt, Šťoural a kritik. Hlavní agent tvar nástroje předem nezamyká.
- Podrobný popis od Saturnina v chatu není. Zdroj zadání = citace výše + kód.
- Projekt: SECOND_BRAIN. Tester: přeskočeno (profil SECOND_BRAIN), `rbu-tester` nevolat.
- Pracovní strom na `main` obsahuje nesouvisející necommitnuté změny. Implementace je nesmí zahrnout.
- Grill kolo 1 (Šťoural `2325a19a-c515-4179-9de9-69548eea5bdf`): 0 BLOKUJÍCÍ. Přijaté předpoklady, plán v1 je ještě nemá — kritik je má chtít v plánu:
  - **A21:** `target=step` a `type: epic` a v těle není `## Operativní kroky` → 400 `epic_has_no_steps`, bez zápisu. Sekce už existuje → krok jako u story. Log / `note` na epicu bez omezení. Checkbox do Definition of done tímto nástrojem nevzniká.
  - **A22:** log (`log` / `note`) na `Done` i `Cancelled` v aktivní `tasks/` povolen, `status` se nemění. Nový krok na `Done` nebo `Cancelled` → 409 `task_terminal`, bez zápisu a bez tombstone. Stejný text, který už v sekci je, vyhraje idempotence (žádný 409, žádný druhý řádek).
  - **A23:** před složením řádku sundat jednu úvodní značku checkboxu (`- [ ]`, `- [x]`, `- [X]`) a u logu jednu úvodní `- `. Pak teprve datum (A4) a vlastní id (A6). Po sundání prázdný text → 400 `empty_text`. Cizí `**id-číslo**` na začátku zbytku → 400 `text_contains_step_id`. `target` bez ohledu na velikost písmen; v odpovědi `log` nebo `step`.
  - **A24:** idempotence kroku = `strip` + vnitřní mezery sbalené na jednu + sundané úvodní `**id-číslo**`. Case-sensitive. `[x]` i `[X]` jsou hotový krok. `a b` a `ab` jsou dva kroky. A10 (stejný text se znovu nezaloží) platí dál.
  - **A9 a A3** platí dál: 400 `step_section_has_subheadings` jen když `### ` je uvnitř `## Operativní kroky` a idempotence nesedla. Strop 1000 znaků, jedna řádka.
  - Otevřené otázky plánu 1 a 6 jsou uzavřené: `note` = alias `log`. Volat smí každý už autentizovaný principal (OAuth, service Bearer, `dev`), stejně jako `update_task` / `create_task`.
  - Grill kolo 2 (0 BLOKUJÍCÍ). Plán v2 tyto body ještě nemá — kritik je má chtít v plánu:
    - **A25:** Idempotence kroku jen na řádcích `_CHECKBOX_RE`. Po `strip` a sbalení obyčejných mezer sundat jedno úvodní `_SUBTASK_ID_RE` (libovolný base). Libovolné `**…**` se nesundává.
    - **A26:** Další `N` = max vedoucího čísla tohoto `task_id` (case-sensitive, skupiny regexu) na checkboxech první operational sekce, plus 1. `[x]` i `[X]` se počítají. Přípona číslo nezvedne. Žádná shoda → 1. Střed řádku, odsazení a log se nepočítají.
    - **A27:** `task_id_missing` až při vkládání, po idempotenci, po `epic_has_no_steps` a po `task_terminal`, před `### `. Jen `step`, jen když `id` není neprázdný string. Číslo, bool, list ani dict nejsou platné `id`. Cizí id zůstává 400 dřív. Log se nekontroluje. Už přítomný holý label → 200, ne 400.
    - **A28:** `step_id` je holé id s příponou, jinak `null`. `inserted_line` je zapsaný řádek, nebo při `already_present` existující řádek po `rstrip`. `updated` v JSON je hodnota ze souboru, nebo `null`, když klíč chybí. Po úspěchu je to dnešek.
    - **A29:** `is_epic` bere `work_type` jen když `type` chybí (`work_type_of`).
    - **A30:** Chybějící řádek `updated:` se doplní, stejně jako `set_focus.py` 105–107.
    - **A31:** Test logu zahrne koncový HTML komentář ze šablony. Sekce jím nekončí; nová odrážka skončí pod ním.
  - Grill kolo 3 (0 BLOKUJÍCÍ). Plán v3 je ještě nemá:
    - **A32:** Zakládá se jen sekce cíle. Step nezaloží log, log nezaloží kroky. Nový nadpis a první odrážka jdou hned pod sebe, bez prázdného řádku mezi nimi.
    - **A33:** Odrážka se vkládá za poslední neprázdný řádek sekce. Ukončovací prázdné řádky zůstanou pod ní.
    - **A34:** Z víc shod se do `inserted_line` a `step_id` bere první řádek shora.
    - **A35:** `task_id = raw.strip()` a tohle se používá v A26, v cizím id i v `**{id}-N**`.
    - **A36:** `N = max(int(num)) + 1`, ne textové maximum (`9` a `10` → 11, ne 10).
    - **A37:** F2 zahrnuje T18 a T27–T33, ne jen testy mimo T17/T19.
    - **A38:** Nový modul má stejný `sys.path` bootstrap na hub `lib/` jako `update_task.py`.
    - **A39:** Z `sort_operational_steps` se bere jen body (`body, _changed = …`). Do souboru nejde celá dvojice.
    - **A40:** Řádky uvnitř `<!-- -->` se do idempotence logu počítají, protože komentář sekci neukončuje.
  - Grill kolo 4 (0 BLOKUJÍCÍ). Zapsáno do plánu v4:
    - **A41:** Zakládá se jen sekce cíle. Step log nezaloží. Nový blok kroků jde na řádek `## Poznámky / log`, checkbox hned nad nadpisem.
    - **A42:** `step_id` se parsuje z labelu za checkboxem, ne z toho, jestli řádek začíná `**`. Log má `step_id: null`.
    - **A43:** Newline na konci souboru nesmaže prázdné řádky pod odrážkou, ani když je sekce poslední.
  - Další poznámky grillu k zapracování, pokud kritik uzná díru: konec sekce sjednotit s `sort_operational_steps` (další `## `, nebo `#`, který není `###`); `parse_task_text` když YAML není dict → 400 i u logu; risk „jeden WC a flock“ grill neověřoval, `expect_oid` zůstává volitelný.

### Mimo rozsah (návrh pro architekta, ověř)

- Zápis do GitHubu / RB Universe repa. Úkoly žijí ve vaultu.
- Obecný přepis celého těla úkolu, mazání sekcí, `focus` (zůstává `set_focus`), `## Stav (auto)`.
- Slack, Gmail, materials backlink, nové task ID.

### Draft hlavního agenta (nepotvrzeno — architekt ověří a smí nahradit)

- `update_task` patchuje jen frontmatter a tělo nemění. `create_task` tělo zapíše jen u nového souboru. Hub `task_io.update_task(..., body_append=)` lepí na konec těla, ne do sekce.
- Šablona úkolu má `## Operativní kroky` a `## Poznámky / log`. Samostatná sekce „poznámky“ v šabloně není.
- CAS dnešního `update_task`: `expect_oid`, 409 `cas_conflict`.
- Nasazení Brainu: Coolify, build context `vps/`, služba `second-brain-brain` (viz `vps/second-brain-brain/README.md`).

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-10-14 | CLARIFY | hlavní | — | — | Nic blokujícího. Uživatel výslovně nechal doladit zadání architektem. |
| 2 | 2026-10-14 | PLAN | 26391434-d835-40f7-a07e-b9adfc204297 | plán v1 | — | Cíle `log`/`step`, `note`=alias logu. Přechod do GRILL. |
| 3 | 2026-10-14 | GRILL | 2325a19a-c515-4179-9de9-69548eea5bdf | POTŘEBUJE ODPOVĚDI | 0 BLOKUJÍCÍ / 6 NEBLOKUJÍCÍ | A21–A24 zapsány. Přechod do CRITIC. |
| 4 | 2026-10-14 | CRITIC | cd8a9c0c-fa65-4f07-b1ca-68860f9934ba | K PŘEPRACOVÁNÍ | 3 BLOCKER, 3 MAJOR, 1 MINOR | C1–C7. Resume architekta, r=2. |
| 5 | 2026-10-14 | PLAN | 26391434-d835-40f7-a07e-b9adfc204297 | plán v2 | — | C1–C7 zapracovány. Přechod do GRILL g=2. |
| 6 | 2026-10-14 | GRILL | aec9eac0-18c9-4a82-a195-1f2723bb4c88 | POTŘEBUJE ODPOVĚDI | 0 BLOKUJÍCÍ / 4 NEBLOKUJÍCÍ | A25–A31. Přechod do CRITIC. |
| 7 | 2026-10-14 | CRITIC | 2b14ef82-8748-4b6f-ad6e-8169bd7a8ca2 | K PŘEPRACOVÁNÍ | 2 BLOCKER, 5 MAJOR | C1–C7 vyřešeny. Nové C8–C14. Resume architekta, r=3. |
| 8 | 2026-10-14 | PLAN | 26391434-d835-40f7-a07e-b9adfc204297 | plán v3 | — | C8–C14 zapracovány (A25–A31, B43–B49, T27–T33). GRILL g=3. |
| 9 | 2026-10-14 | GRILL | 193d6017-dc2f-41c0-b999-dca24dc952a3 | POTŘEBUJE ODPOVĚDI | 0 BLOKUJÍCÍ / 3 NEBLOKUJÍCÍ | A32–A40. Přechod do CRITIC. |
| 10 | 2026-10-14 | CRITIC | 541cc0c0-ec6d-4150-a9e9-e90e6822ddec | K PŘEPRACOVÁNÍ | 1 BLOCKER, 8 MAJOR | C8–C14 vyřešeny. Nové C15–C23. Nový architekt, k=2, r=1. |
| 11 | 2026-10-14 | PLAN | b5d26299-9469-414b-a4b3-34bd0eb9d446 | plán v4 | — | C15–C23 v A32–A40, B50–B57, T34–T41. GRILL g=4. |
| 12 | 2026-10-14 | GRILL | 00f1730b-daa2-4e5b-8234-41421826886b | POTŘEBUJE ODPOVĚDI | 0 BLOKUJÍCÍ | Q1–Q3 → A41–A43. A18, step_id a konec souboru srovnány. B58, T42. |
| 13 | 2026-10-14 | CRITIC | 72b2c45a-912d-4501-925d-5af9040aec93 | K PŘEPRACOVÁNÍ | 0 BLOCKER, 3 MAJOR | C15–C23 vyřešeny. Nové C24–C26. Resume architekta k=2, r=2. |
| 14 | 2026-10-14 | PLAN | b5d26299-9469-414b-a4b3-34bd0eb9d446 | plán v4 doplněn | — | C24–C26: B16/T3, A28 string updated, A14 split 409. GRILL g=5. |
| 15 | 2026-10-14 | GRILL | 2641ba9c-06f2-4138-bcba-8fb3a903d8fd | HOTOVÝ GRILL | 0 | C24–C26 drží. Žádná nová otázka. Přechod do CRITIC. |
| 16 | 2026-10-14 | CRITIC | d8b5ab8b-49fc-478e-bca2-e0bbfed2c75a | SCHVÁLENO | 0 BLOCKER, 0 MAJOR | C24–C26 vyřešeny. Přechod do IMPLEMENT. |
| 17 | 2026-10-14 | IMPLEMENT | hlavní | commit 99ad22a | — | Gate 534 passed. Jen soubory nástroje, docs, skill a plán. Push ne. |
| 18 | 2026-10-14 | REVIEW | 8e8aa5b2-8878-4b2d-80b8-f04f49bf1a88 | SCHVÁLENO | 0 BLOCKER, 0 MAJOR | Na 99ad22a. Push main. |
| 19 | 2026-10-14 | QA | 247e7644-6374-48ff-98c2-d99cfffb5707 | PASS | — | Image `99ad22a` na second-brain-brain (app 18). `GET /healthz` 200. Vault se nezapisoval. |
| 20 | 2026-10-14 | testerGate | hlavní | TESTER: přeskočeno (profil SECOND_BRAIN) | — | rbu-tester se nevolá. |
| 21 | 2026-10-14 | DONE | hlavní | audit | — | Plán SCHVÁLENO, review SCHVÁLENO, QA PASS na 99ad22a, gate 534 passed. |

## Otevřené nálezy

| ID (C#/D#/Q#/S#) | Závažnost | Typ IMPL/PLAN/ENV | Stav (otevřený / vyřešen v # / odmítnut) | Kolikrát vznesen |
| --- | --- | --- | --- | --- |
| C1 | BLOCKER | PLAN | vyřešen v kritik kole 2 | 1 |
| C2 | BLOCKER | PLAN | vyřešen v kritik kole 2 | 1 |
| C3 | BLOCKER | PLAN | vyřešen v kritik kole 2 | 1 |
| C4 | MAJOR | PLAN | vyřešen v kritik kole 2 | 1 |
| C5 | MAJOR | PLAN | vyřešen v kritik kole 2 | 1 |
| C6 | MAJOR | PLAN | vyřešen v kritik kole 2 | 1 |
| C7 | MINOR | PLAN | vyřešen v kritik kole 2 | 1 |
| C8 | BLOCKER | PLAN | vyřešen v kritik kole 3 | 1 |
| C9 | MAJOR | PLAN | vyřešen v kritik kole 3 | 1 |
| C10 | BLOCKER | PLAN | vyřešen v kritik kole 3 | 1 |
| C11 | MAJOR | PLAN | vyřešen v kritik kole 3 | 1 |
| C12 | MAJOR | PLAN | vyřešen v kritik kole 3 | 1 |
| C13 | MAJOR | PLAN | vyřešen v kritik kole 3 | 1 |
| C14 | MAJOR | PLAN | vyřešen v kritik kole 3 | 1 |
| C15 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C16 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C17 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C18 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C19 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C20 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C21 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C22 | BLOCKER | PLAN | vyřešen v kritik kole 4 | 1 |
| C23 | MAJOR | PLAN | vyřešen v kritik kole 4 | 1 |
| C24 | MAJOR | PLAN | vyřešen v kritik kole 5 | 1 |
| C25 | MAJOR | PLAN | vyřešen v kritik kole 5 | 1 |
| C26 | MAJOR | PLAN | vyřešen v kritik kole 5 | 1 |
