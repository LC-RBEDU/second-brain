# Plán: Brain `append_task_note`

Kolo 3 doplněné převzetím generace k=2 (agent `b5d26299-9469-414b-a4b3-34bd0eb9d446`). C1–C14 zůstávají. C15–C23 jsou v A32–A40, B50–B57 a T34–T41.

## Zadání a požadavky

| R# | Požadavek | Zdroj |
|---|---|---|
| **R1** | Brain dnes umí založit úkol a změnit stav nebo termín, ale do textu existujícího úkolu (kroky, log, poznámky) nepřipíše nic. Tohle se má opravit. | zpráva 1, citace Groka |
| **R2** | Oprava je jeden nový nástroj v Brainu (`vps/second-brain-brain`), ne zápis do GitHubu / RB Universe. | zpráva 1 + blok Mimo rozsah |
| **R3** | Nástroj doplní poznámku, krok, nebo záznam do logu. Druhý návrh jméno `append_task_note` a odrážku do logu, kroků nebo poznámek. Tvar smí doladit architekt. | zpráva 1 + zpráva 2 + rozhodnutí „tvar předem nezamykat“ |
| **R4** | Souběžné změny hlídat stejně jako dnešní úpravy stavu (`update_task`: volitelný `expect_oid`, 409 `cas_conflict`). | zpráva 1 |
| **R5** | Stejný povrch jako dnešní mutace: MCP i REST. | brief, ověřeno v `mcp_app.py` a `main.py` |
| **R6** | `focus` zůstává `set_focus`. `## Stav (auto)` se nepíše. Obecný přepis těla, mazání sekcí, Slack, Gmail, materials, nové task ID a odškrtnutí existujícího kroku jsou mimo rozsah. | brief Mimo rozsah + bootstrap |
| **R7** | Cronové `body_append` (lepí na konec těla) se nesmí rozbít. Nový nástroj na něj nesmí spoléhat, protože řádek nedostane do sekce. | brief + `task_io.py` |
| **R8** | Po změně tasku platí konvence: bump `updated:`, podkrok `**ID-N**` s dalším číslem, nesplněné kroky první. Snapshot kontextu řešit tombstone jako `create_task` / `set_focus`, ne ručním `build_agent_context.py` v requestu. | `task-operational-steps-vault.mdc`, `second-brain-bootstrap.mdc`, kód tombstone |
| **R9** | Projekt SECOND_BRAIN. Lokální commit na `main` bez push, dokud reviewer neschválí. Commit nesmí zahrnout nesouvisející dirty strom. Tester se nevolá. Ostrý zápis do živého vaultu v testech není. | blok Projekt + Rozhodnutí |

**Mimo rozsah:** zápis do GitHubu aplikace RB Universe; přepis celého těla; mazání sekcí; `focus`; `## Stav (auto)`; Slack; Gmail; materials backlink; `allocate_task_id` / `next_task_id.py`; odškrtnutí `[x]`; změna `status`; úprava `task_io.update_task`; vaultový `boti-prehled.md` (gitignored). Alembic, RBAC Universe, Celery, frontend, `qa_gate.mjs` — netýká se.

## Předpoklady

| A# | Předpoklad | Proč |
|---|---|---|
| **A1** | Jeden nástroj `append_task_note`. Cíle jsou dva: `log` a `step`. `note` je alias `log` a v odpovědi se vrací jen `log` nebo `step`. Samostatná sekce poznámek v šabloně není — poznámka i záznam do logu jdou do `## Poznámky / log`. | šablona řádky 34–39, `create_task.py` 109–114; grill uzavřel otázku 1 |
| **A2** | `target` je povinný (bez defaultu). Porovnání je case-insensitive (`Note`, `STEP`, `log`). | A23; omyl v cíli je horší než 400 |
| **A3** | Jedna řádka, strop 1000 znaků **zbytku po** sundání prefixu (A23). CR/LF v surovém textu → 400. Po sundání prázdný zbytek → 400 `empty_text`. | grill: A3 platí dál |
| **A4** | Log řádek je `- {YYYY-MM-DD}: {text}` s datem Europe/Prague (`TZ`, default Prague). Když text už začíná `YYYY-MM-DD:`, datum se nepřidává podruhé. Datum se skládá až po A23. | šablona řádek 39; A23 |
| **A5** | Nový krok je `- [ ] **{id}-{N}** {text}`. `N` počítá **A26**. Písmenná přípona se negeneruje. `next_task_id.py` se nevolá. | konvence podkroku; C9 |
| **A6** | Vlastní úvodní `**{id}-{číslo}{přípona}**` se při skládání kroku sundá. Cizí úvodní `_SUBTASK_ID_RE` → 400 `text_contains_step_id` u logu i kroku, dřív než idempotence. Zmínka uprostřed věty zůstává. | A23, A27 |
| **A7** | Cesta jen `02-PROJEKTY/<slug>/tasks/<soubor>.md` (stejný regex jako `set_focus`). Archiv, hub, materials → 400 `invalid_task_path`. | `set_focus.py` řádek 44; R6 |
| **A8** | Nahrazeno **A22**. Terminální status krok nezaloží. | grill A22, C1 |
| **A9** | V sekci kroků je `### ` a idempotence nesedla → 400 `step_section_has_subheadings`, bez zápisu. `### ` sekci neukončuje. Shoda idempotence vyhraje nad tímto 400. | grill: A9 platí dál; `operational_steps.py` 7–11 a 135 |
| **A10** | Platí **A24** upřesněné **A25**. Libovolné `**…**` se nesundává. | C4, C8 |
| **A11** | Idempotence logu = přesná složená odrážka (po `strip`) už v sekci logu. Stejný text další den je nový řádek, protože datum je součást řádku. Porovnává se až po A23, takže `- foo` a `foo` téhož dne jsou jedna odrážka. | A4, A23 |
| **A12** | `expect_oid` je volitelný, stejné jako `update_task`. Když přijde, nesoulad při čtení i `DriveConflictError` při zápisu → 409 `cas_conflict`. Když chybí, nástroj upraví soubor, který právě přečetl, a do `write_text` CAS nepředá. | R4; `update_task.py` 50–55 a 86–88; `git_io.py` 389–399 |
| **A13** | Zapisovat smí každý už autentizovaný volající (OAuth, service Bearer, `dev`). Zvláštní policy jako u `focus` není. | grill uzavřel otázku 6 |
| **A14** | Tombstone jen když se opravdu mění bajty, těsně před `write_text`. Před zápisem (idempotence, 400, read-time 409) je `write_text` 0× a tombstone 0×. Write-time 409: `write_text` se zavolá a vyhodí; tombstone se smí zavolat před ním. `git_io` při výjimce dělá `reset --hard HEAD` (`git_io.py` 188–195, `vault_deps.py` 91), takže smazaný tombstone se na disku vrátí, ale počítadlo volání v testu ne. `build_agent_context.py` se z nástroje nespouští. | C26 |
| **A15** | Datum a `updated:` počítá helper v novém modulu (ZoneInfo Prague / `TZ`). Soukromý `_prague_today` ze `set_focus` se neimportuje. | necouplovat nástroje |
| **A16** | Popis od Saturnina v briefu není. Zdroj chování je citace, kód a grill A21–A24. | Rozhodnutí |
| **A17** | Po úspěchu session commitne a pushne jako dnešní mutace (`git_io.py` `end_session` 182–186). Při výjimce se necommituje a `discard_dirty_on_error` dělá `reset --hard HEAD` (`vault_deps.py` 88–91, `git_io.py` 188–197). | existující GitVault |
| **A18** | Zakládá se jen sekce cíle (A32, A41). Log se založí na konci body, i u epicu a u terminálního úkolu. Kroky se založí jen když cíl je step, úkol není epic a status není `Done` ani `Cancelled`. Když log už je, blok kroků se vloží na řádek `## Poznámky / log`: checkbox je hned nad tím nadpisem a prázdné řádky, které nad ním už byly, zůstanou nad novou sekcí. Epic bez hlavičky kroků sekci nezaloží. | A21, A22, A32, A41 |
| **A19** | `sort_operational_steps` se volá jen po skutečném vložení kroku, a jen na body. Log řazení nespouští. | nový `[ ]` by jinak zůstal za `[x]` |
| **A20** | Docs/skill úpravy jsou součást změny, včetně pravidel epic / terminální status / alias `note`. | `docs/claude-project-instructions.md` řádek 13; `mrluc-loader` řádek 12 |
| **A21** | `target=step` a epic (`is_epic`) a v těle není hlavička, kterou pozná `is_operational_header` → 400 `epic_has_no_steps`, bez zápisu a bez tombstone. Tělo včetně `## Definition of done (epic)` se nezmění. Sekce kroků už existuje → krok jako u story (dál platí A9 a A22). Log / `note` na epicu je bez tohoto omezení. | grill; `epic-template.md` 27–39; `hierarchy.py` 58–63 |
| **A22** | Log (`log` / `note`) na `Done` i `Cancelled` v aktivní `tasks/` projde a `status` se nemění. Nový krok na `Done` nebo `Cancelled` → 409 `task_terminal`, bez `write_text` a bez tombstone. Stejný text kroku, který v sekci už je, vyhraje idempotence (200 `already_present`, žádný 409). Status se bere z parsovaného dictu stejně jako `ParsedTask.is_terminal` (`task_io.py` 46–56): `str(fm.get("status") or "Next")`. Ne z řádku souboru. | grill; C1 |
| **A23** | Před složením řádku sundat jednu úvodní značku checkboxu (`- [ ]`, `- [x]`, `- [X]`, mezery jako `-\s+\[[ xX]\]\s*`) a u logu ještě jednu úvodní `- `. Pak teprve datum (A4) a u kroku vlastní id (A6). Po sundání prázdný text → 400 `empty_text`. Cizí `**id-číslo**` na začátku zbytku → 400 `text_contains_step_id` u obou cílů. | grill |
| **A24** | Case-sensitive label. `foo  bar` = `foo bar`. `Foo` ≠ `foo`. `a b` ≠ `ab`. `[x]` i `[X]` jsou checkbox. | C4; regex řádek 27 |
| **A25** | Idempotence kroku jen na řádcích `_CHECKBOX_RE` v první operational sekci. Na obou stranách: `strip`, sbalit opakované obyčejné mezery U+0020 na jednu, sundat jedno úvodní `_SUBTASK_ID_RE` (libovolný base) a mezeru za ním. `**Pozor**` se nesundá. | C8; `operational_steps.py` 27–32 |
| **A26** | `N` = max skupiny `num` z vedoucího `_SUBTASK_ID_RE` na checkboxech první operational sekce, kde `base == task_id` case-sensitive, plus 1. `[x]` i `[X]` se počítají. Přípona číslo nezvedne. Střed řádku, odsazení a log se nepočítají. Žádná shoda → 1. | C9 |
| **A27** | Platné `id` je jen neprázdný string po `strip`. Číslo, bool, list ani dict se na string nepřevádí. `task_id_missing` jen u `step`, až po idempotenci, `epic_has_no_steps` a `task_terminal`, před `### `. Cizí id zůstává 400 dřív. Log `id` nekontroluje. Holý label, který v sekci už je, → 200 i při neplatném `id`. | C10 |
| **A28** | `step_id` je `{base}-{num}{suffix}` bez hvězdiček (`SB-S17-3b`), jinak `null`. Bere se z labelu za checkboxem (A42), ne z toho, jestli celý řádek začíná `**`. `inserted_line` při `already_present` je existující řádek po `rstrip`. `updated` v JSON je vždy `str` `YYYY-MM-DD`, nebo `null`. `yaml.safe_load` z nequoted data udělá `datetime.date` (případně `datetime`); z `date` a `datetime` se bere `isoformat()[:10]`. Řetězec, který už je `YYYY-MM-DD`, se vrací tak. Chybějící klíč, `None` a nečitelná hodnota → `null`. Úspěch i `already_present` vrací ten string, ne objekt data. Po úspěšném zápisu je to dnešní Prague datum jako string. | C11, C25, A42 |
| **A29** | Epic je `is_epic(fm)` = `work_type_of` (`hierarchy.py` 58–63): neprázdné `type` má přednost. `work_type` se čte jen když `type` chybí nebo je prázdné. `type: story` + `work_type: epic` není epic. Samotné `work_type: epic` je epic. | C12 |
| **A30** | Chybějící řádek `updated:` se doplní na konec plotu, stejně jako `set_focus.py` 105–107. `status` a `focus` se nepřidávají. | C13 |
| **A31** | HTML komentář sekci neukončí. Na těle šablony (řádky 38–45) je poslední neprázdný řádek sekce `-->`, takže nová log odrážka skončí až pod ním. Mezi nadpis logu a `<!--` se nevkládá. | C14 |
| **A32** | Zakládá se jen sekce cíle. Step nezaloží `## Poznámky / log`. Log nezaloží `## Operativní kroky`. Nový nadpis a první odrážka jsou sousední řádky, bez prázdného řádku mezi nimi. | C15 |
| **A33** | Odrážka se vkládá za poslední neprázdný řádek sekce. Ukončovací prázdné řádky zůstanou pod ní. | C16 |
| **A34** | Z víc shod se do `inserted_line` a `step_id` bere první řádek shora. | C17 |
| **A35** | `task_id = raw.strip()` a tohle se používá v číslování, v cizím id i v `**{id}-N**`. | C18 |
| **A36** | `N = max(int(num)) + 1`. Textové maximum se nepoužije. Žádná shoda → 1. | C19 |
| **A37** | F2 zahrnuje T1–T16, T18, T22–T42. T17 a T19 až po F3. | C20, A43 |
| **A38** | Stejný `sys.path` bootstrap jako `update_task.py` 9–15 (`/app/lib`, pak `parents[3] / second-brain-hub / lib`) před importem hub modulů. | C21 |
| **A39** | `body, _changed = sort_operational_steps(body)`. Do souboru jde jen `body`. `_changed == False` zápis nezruší. | C22 |
| **A40** | Řádky uvnitř `<!-- -->` se počítají do idempotence logu. Přesná odrážka jen tam → 200 bez zápisu. Nový text se do komentáře nevkládá, jde pod `-->`. | C23 |
| **A41** | A18 platí jen pro sekci cíle. Step log nezaloží, log kroky nezaloží. Nový blok kroků se vkládá na řádek `## Poznámky / log`, bez přidaného prázdného řádku mezi checkboxem a tím nadpisem. | grill g=4 Q1 |
| **A42** | `step_id` se bere z labelu za checkboxem: na textu za `_CHECKBOX_RE` (po `strip`) najít vedoucí `_SUBTASK_ID_RE` a vrátit `{base}-{num}{suffix}` bez hvězdiček. Label bez toho id, a každá log odrážka, má `step_id: null`. Ne z toho, jestli celý řádek začíná `**`. | grill g=4 Q2 |
| **A43** | Soubor končí newline. `rstrip` nesmí sebrat prázdné řádky, které A33 nechává pod odrážkou, včetně případu, kdy je sekce poslední a prázdné řádky jdou až do konce souboru. „Jedno `\n`“ znamená nepsat soubor bez ukončení a nepřidávat druhý newline za už existující. | grill g=4 Q3 |

## Současný stav (ověřeno v kódu)

| Soubor | Fakt |
|---|---|
| `vps/second-brain-brain/app/tools/update_task.py` 27–99 | `brain_vault(mode="mutate")`. `focus` a klíč `stav*` → 403. CAS: `expect_oid` proti `meta.oid`, pak `write_text(..., expect_oid=)`. `DriveConflictError` → 409 `cas_conflict`. Nový text je nový frontmatter + původní body beze změny (řádky 56–59, 84). `updated` sám od sebe nebumpne. Cestu neomezuje. |
| `vps/second-brain-brain/app/tools/create_task.py` 109–114, 135, 159 | Nový soubor má `## Operativní kroky`, checkbox a pak prázdný řádek (111) před `## Poznámky / log`. Při vložení bloku před existující log se ten prázdný řádek nepřebírá (A41). Na začátku session volá `delete_context_tombstone`. |
| `vps/second-brain-brain/app/mcp_app.py` 69–120 | MCP `update_task`, `set_focus`, `create_task`. Append do těla není. |
| `vps/second-brain-brain/app/main.py` 174–224 | REST `PATCH /v1/tasks`, `POST /v1/set_focus`, `POST /v1/tasks`. Mutace berou `AuthPrincipal`. |
| `vps/second-brain-brain/app/policy.py` 28–37 | `deny_focus_write` jen pro `update_task`. `deny_stav_auto_write` pro klíče `stav*`. |
| `vps/second-brain-brain/app/tools/set_focus.py` 44, 158–228 | Regex cesty `^02-PROJEKTY/[^/]+/tasks/[^/]+\.md$`. Chybějící soubor → 404 `not_found`. Patch frontmatteru je řádkový, ne `yaml.safe_dump`. |
| `vps/second-brain-brain/app/tools/read_file.py` 36–40 | Čtení vrací `oid`. |
| `vps/second-brain-brain/app/vault_deps.py` 75–79, 88–91 | Mutate bez `GIT_VAULT_PUSH` → 503. `discard_dirty_on_error=True`. |
| `vps/second-brain-hub/lib/task_io.py` 46–56 | `status` je `frontmatter.get("status") or "Next"`. `is_terminal` je jen `Done` nebo `Cancelled`. |
| `vps/second-brain-hub/lib/task_io.py` 66–71 | `parse_task_text`: `YAMLError`, `None` i ne-dict (list, skalár) spadnou na `{}` a chybu nehlásí. Nástroj tenhle tichý pád nesmí použít jako „frontmatter je v pořádku“. |
| `vps/second-brain-hub/lib/task_io.py` 132–160 | `body_append` lepí na konec body. |
| `vps/second-brain-hub/lib/hierarchy.py` 50–63 | `is_epic` bere `type` i `work_type` přes `normalise_work_type`. Na dictu funguje `_task_get`. |
| `vps/second-brain-hub/lib/operational_steps.py` 27–32 | Checkbox `^-\s+\[([ xX])\]`. Id podkroku `**base-číslo**`. |
| `vps/second-brain-hub/lib/operational_steps.py` 131–136 | Sekce končí na `## `, nebo na `#`, který není `###`. `### ` sekci nekončí. |
| `vps/second-brain-hub/lib/operational_steps.py` 44–48 | `is_operational_header`: `## ` + začátek „operativní kroky“ bez diakritiky. |
| Crony `lifecycle_overdue_flag.py` 67 a ostatní `body_append` | Logují na EOF. Soubory se nemění. |
| `vps/second-brain-hub/lib/context_tombstone.py` 13–32 | Maže trojici kontextu. |
| `vps/second-brain-hub/lib/agent_context_build.py` 154–176 | Snapshot má `updated`, ne text kroků ani logu. |
| `vps/second-brain-hub/lib/git_io.py` 178–197, 381–410 | Commit jen bez výjimky. `expect_oid` se kontroluje jen když není `None`. |
| `vps/second-brain-brain/Dockerfile` 14–24 | Image kopíruje hub `lib/` + brain `app/`. `TZ=Europe/Prague`. |
| `vps/second-brain-hub/README.md` 40–66 | `application_id` 11 je hub cron, ne Brain. |
| `ŠABLONY/obsidian-templates/task-template.md` 34–39 | Story má `## Operativní kroky` a `## Poznámky / log`. |
| `ŠABLONY/obsidian-templates/epic-template.md` 27–39 | Epic má `## Definition of done (epic)` s checkboxem, `## Stories`, `## Poznámky / log`. `## Operativní kroky` tam není. |
| `docs/agent_playbooks/quality-checklists.md` | V tomto repu není. |

`scripts/_apply_hygiene_cleanup.py` `append_log_line` (397–443) se neimportuje a nemění.

## Návrh

### Rozhodnutí

Jeden modul `append_task_note`. Hub lib se needituje. Brain importuje `is_operational_header`, `sort_operational_steps`, `is_epic` a `delete_context_tombstone` z už zkopírované `/app/lib`. Podmínku konce sekce z `operational_steps.py` 135 si nástroj zapíše u sebe (veřejná funkce na to v lib není), hub soubor se nemění.

`update_task` a `task_io.update_task` zůstávají. Hub cron image se kvůli téhle změně nestaví (base hubu je `vps/second-brain-hub`).

### 1. Nový modul `vps/second-brain-brain/app/tools/append_task_note.py` (R1–R8, A21–A24)

```text
append_task_note(*, path, text, target, expect_oid=None, env=None) -> dict
```

Na začátku souboru, před importem z hubu, stejná smyčka jako `update_task.py` 9–15: `Path("/app/lib")`, pak `parents[3] / "second-brain-hub" / "lib"` (A38).

MCP a REST `env` nevystavují. Testy ano.

**Před otevřením vaultu**

1. `path` po `strip` sedí na `^02-PROJEKTY/[^/]+/tasks/[^/]+\.md$`. Jinak 400 `invalid_task_path`.
2. `target` po `strip` a `casefold`: `log` a `note` → `log`, `step` → `step`. Jinak 400 `invalid_target`.
3. Surový text obsahuje `\n` nebo `\r` → 400 `text_must_be_single_line`.
4. Sundat jednu úvodní značku `^-\s+\[[ xX]\]\s*`. Když je cíl `log`, sundat ještě jednu `^-\s+`.
5. `strip` zbytku. Prázdný → 400 `empty_text`. Délka zbytku > 1000 → 400 `text_too_long`.

**Mutate session, v tomhle pořadí**

1. `with brain_vault(mode="mutate", env=env)`.
2. `read_text`. `DriveNotFoundError` → 404 `not_found`.
3. `expect_oid` nesedí na `meta.oid` → 409 `cas_conflict` před tombstone.
4. Plot chybí (stejný regex jako `update_task`) → 400 `no_frontmatter`.
5. Vlastní `yaml.safe_load` plotu, ne `parse_task_text`. `YAMLError`, nebo výsledek není `dict` a není `None` (list, skalár) → 400 `invalid_frontmatter`, oba cíle, bez tombstone a bez write. `None` (prázdný plot) se bere jako `{}`.
6. `status = str(fm.get("status") or "Next")`. Terminální je jen `Done` a `Cancelled`. `epic = is_epic(fm)` podle A29 (`work_type` jen když `type` chybí). Platné id: `raw = fm.get("id")` jen když `isinstance(raw, str)` a `raw.strip()` není prázdné. Pak `task_id = raw.strip()` (A35). Jinak id neplatné. Žádné `str(fm.get("id") or "")` a žádné použití nestripovaného `raw`.
7. Zbytek textu začíná `_SUBTASK_ID_RE` a `base != task_id` (nebo id není platné, takže každé úvodní id je cizí) → 400 `text_contains_step_id` u logu i kroku, před idempotencí.
8. U kroku, když je id platné a base se rovná `task_id`, sundat to jedno úvodní id a mezeru za ním. Po `strip` prázdné → 400 `empty_text`.
9. Najít sekci. Kroky: první `is_operational_header`. Log: první řádek se `strip()` přesně `## Poznámky / log`. Konec obou: `## `, nebo `#` které není `###`. `### ` ani `<!--` sekci nekončí.
10. Idempotence před 400 epic, před 409, před `task_id_missing` a před `### `. První shoda shora (A34). Řádky uvnitř `<!-- -->` se u logu počítají (A40).
    - Krok, jen řádky `_CHECKBOX_RE` v první operational sekci. Label podle A25. Shoda → 200 `already_present`.
    - Log: každý řádek sekce po `strip` rovný složené odrážce → 200.
11. Krok a idempotence nesedla, v tomhle pořadí, pořád před tombstone:
    - není operational hlavička a `epic` → 400 `epic_has_no_steps` (i když je zároveň `Done`);
    - terminální status → 409 `task_terminal`;
    - id není platný string → 400 `task_id_missing`;
    - v sekci je `### ` → 400 `step_section_has_subheadings`.
12. `N = max(int(num)) + 1` podle A36, nebo 1. Textové `max` se nevolá.
13. Vložení za poslední neprázdný řádek sekce (A33). Zakládá se jen sekce cíle (A32): step nezaloží log, log nezaloží kroky. Nový nadpis a první odrážka jsou sousední řádky. Když log už je, blok kroků se vloží na řádek `## Poznámky / log`: checkbox je hned nad tím nadpisem, bez přidaného prázdného řádku mezi nimi (A41). Prázdné řádky, které už nad logem byly, zůstanou nad `## Operativní kroky`. Prázdný řádek z `create_task.py` 111 se sem nepřebírá.
14. Jen po vložení kroku: `body, _changed = sort_operational_steps(body)` (A39). `_changed == False` zápis nezruší. Do souboru jde jen řetězec `body`. Log sort nevolá.
15. Řádkový patch jen `updated:` na dnešní Prague datum. Klíč, který v plotu není, se doplní na konec (`set_focus.py` 105–107). `status` a `focus` se nepřidají. Soubor končí newline (A43): prázdné řádky pod odrážkou se nesmažou, druhý newline se za už existující nepřidá.
16. Sem jen když se bajty mění. `delete_context_tombstone`, potom `write_text`. `expect_oid` jde do kwargs jen když volající nějaký poslal. Idempotence, 400 a read-time 409 (krok 3 a krok 11) sem nedojdou.
17. `DriveConflictError` z `write_text` → 409 `cas_conflict`. Tombstone v kroku 16 už proběhnout směl. Commit session neudělá; `discard_dirty_on_error` udělá `reset --hard HEAD` (`git_io.py` 188–195).

Nástroj nevolá `task_io.update_task`, nepřepíná cizí checkboxy, nezakládá task ID a nesahá na `## Stav (auto)` ani na `## Definition of done (epic)`.

**Odpověď**

```json
{
  "path": "02-PROJEKTY/<slug>/tasks/<soubor>.md",
  "target": "log",
  "oid": "<blob nebo null>",
  "already_present": false,
  "inserted_line": "- 2026-10-14: text",
  "step_id": null,
  "updated": "2026-10-14"
}
```

`target` v odpovědi je jen `log` nebo `step`. `step_id` se parsuje z labelu za checkboxem (A42): `{base}-{num}{suffix}` (`SB-S17-3b`), nebo `null`, když label vedoucí `_SUBTASK_ID_RE` nemá. Log má `step_id: null`. `inserted_line` při `already_present` je existující řádek po `rstrip`. `updated` je vždy string `YYYY-MM-DD`, nebo `null`. Nequoted datum z `yaml.safe_load` je `datetime.date`; do JSON jde `isoformat()[:10]`, ne objekt data. Chybějící nebo nečitelný klíč je `null`. Při `already_present` je to hodnota ze souboru po tom převodu. Po úspěchu je to dnešní Prague datum jako string. `oid` při idempotenci z čtení.

### 2. MCP — `vps/second-brain-brain/app/mcp_app.py` (R5)

`append_task_note(path, text, target, expect_oid=None)` přes `_call`.

Popis:

> Append one bullet to an existing task file. target=log writes into ## Poznámky / log (target note is an alias; matching is case-insensitive; the result target is log or step). target=step adds the next unchecked **ID-N** checkbox in ## Operativní kroky. A new step on Done or Cancelled returns 409 task_terminal. An epic with no operational-steps section returns 400 epic_has_no_steps. Optional expect_oid is the same CAS as update_task. Does not change status or focus, does not check off existing steps, and does not write ## Stav (auto) or Definition of done.

Server `instructions` v `build_mcp` se nemění.

### 3. REST — `vps/second-brain-brain/app/main.py` (R5)

`POST /v1/tasks/append` s `AuthPrincipal`. Tělo: `path`, `text`, `target`, `expect_oid` optional. Target validuje nástroj (400 `BrainClientError`), ne Pydantic `Literal`. `PATCH /v1/tasks` zůstává frontmatter-only.

### 4. Docs a skill (A20)

- `docs/brain-api-runbook.md` — jméno, route, `log`/`step`, alias `note`, case-insensitive target, CAS, 409 `task_terminal`, 400 `epic_has_no_steps`, co se nemění (`status`, DoD, focus).
- `docs/claude-project-instructions.md` — do věty o Brain mutate přidat `append_task_note`. Tělo úkolu nejde přes `update_task`.
- `docs/second-brain-architecture.md` řádek 149 — do výčtu nástrojů přidat `append_task_note`.
- `ŠABLONY/skills/mrluc-loader/SKILL.md` řádek 12 — stejný výčet.
- `ŠABLONY/skills/agenda-status-update/SKILL.md` — jedna věta: klient jen s Brainem (Claude / Grok / Saturnin) volá `append_task_note`. Cursor, který soubor edituje na disku, dál patchuje markdown podle skillu.

`scripts/install_agenda_skills.sh` jen když `~/.cursor/skills/...` není symlink na `ŠABLONY/skills/`.

### 5. Nasazení a commit (R9)

`vps/second-brain-hub/**` se nesahá. Commit na `main` bez push, jen:

- `vps/second-brain-brain/app/tools/append_task_note.py`
- `vps/second-brain-brain/app/mcp_app.py`
- `vps/second-brain-brain/app/main.py`
- `vps/second-brain-brain/tests/test_append_task_note.py`
- `docs/brain-api-runbook.md`
- `docs/claude-project-instructions.md`
- `docs/second-brain-architecture.md`
- `ŠABLONY/skills/mrluc-loader/SKILL.md`
- `ŠABLONY/skills/agenda-status-update/SKILL.md`

Base: `99c3685c2a76860c6c48d0ff604661c30813f1c5`. Žádné `git add -A`. Push až po SCHVÁLENO reviewera. Ověření image je app **second-brain-brain**, ne hub `application_id` 11.

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | Test T# |
|---|---|---|---|---|
| **B1** | `POST /v1/tasks/append` bez auth | 401, vault se neotevře | R5 | T17 |
| **B2** | OAuth, service Bearer nebo `dev` | zápis projde; žádná focus-policy | R1, A13 | T18 |
| **B3** | cesta archiv / hub / `..` / materials / prázdná | 400 `invalid_task_path`, žádný write | R6, A7 | T9 |
| **B4** | text prázdný, jen mezery, nebo po A23 prázdný (`- [ ]`, `- `) | 400 `empty_text`, vault se neotevře | A3, A23 | T8, T24 |
| **B5** | surový text obsahuje CR nebo LF | 400 `text_must_be_single_line`, vault se neotevře | A3 | T8 |
| **B6** | zbytek po A23 delší než 1000 znaků | 400 `text_too_long`, vault se neotevře | A3 | T8 |
| **B7** | `note`, `Note`, `LOG` | odpověď `target=log`. `STEP` → `step`. Jiný target → 400 `invalid_target` | A1, A2, A23 | T16, T24 |
| **B8** | soubor neexistuje | 404 `not_found` | R4 | T12 |
| **B9** | bez frontmatteru | 400 `no_frontmatter` | R8 | T13 |
| **B10** | `step` a prázdné `id` v dictu, text nezačíná cizím id | 400 `task_id_missing` | A5 | T14 |
| **B11** | v krocích je `### ` a label tam není | 400 `step_section_has_subheadings`, write ani tombstone | A9 | T5 |
| **B12** | log a za sekcí je další `## ` | odrážka je poslední neprázdný řádek sekce logu | R1, R7 | T1 |
| **B13** | sekce logu chybí | na konci body vznikne `## Poznámky / log` a odrážka | A18 | T2 |
| **B14** | log, zbytek `foo`, Prague 2026-10-14 | `- 2026-10-14: foo`. Text `2026-10-01: starší` zůstane s tím datem | A4 | T1 |
| **B15** | kroky `**SB-S17-1**` a `**SB-S17-3b**`, `id` je `SB-S17` | `- [ ] **SB-S17-4** {text}`. Díra 2 se neobsadí | A5, R8 | T3 |
| **B16** | sekce kroků chybí, `type` není epic, status není terminální, log existuje, nad logem jsou prázdné řádky | `## Operativní kroky` a hned pod ní checkbox. Další řádek je `## Poznámky / log`, bez přidaného prázdného řádku mezi checkboxem a nadpisem. Prázdné řádky, které už nad logem byly, zůstanou nad `## Operativní kroky`. Epic ani `Done`/`Cancelled` tuhle sekci nezaloží | A18, A21, A22, A41 | T3 |
| **B17** | nový otevřený krok by po prostém appendu seděl za `[x]` | po sortu je otevřený krok před hotovými | R8, A19 | T4 |
| **B18** | jen log, kroky jsou schválně nesetříděné | pořadí kroků se nezmění | A19 | T1 |
| **B19** | stejná složená log odrážka už v sekci je; frontmatter má nequoted `updated: 2026-10-01` | 200 `already_present`, write ani tombstone. `updated` v JSON je string `2026-10-01`, ne `datetime.date`. Nečitelná hodnota klíče je `null` | A11, A14, A28 | T6 |
| **B20** | label kroku po A24 sedí na `[x]` nebo `[X]` | `already_present`, `step_id` z řádku, žádný write. `foo  bar` = `foo bar`. `Foo` ≠ `foo`. `a b` ≠ `ab`. `### ` v tom případě 400 nevyvolá | A9, A24 | T7 |
| **B21** | úspěšný zápis story | změní se `updated:` a vložená odrážka. `focus` a `status` zůstanou. `## Stav (auto)` se nezapíše | R6, R8 | T15 |
| **B22** | `expect_oid` ≠ oid z čtení | 409 `cas_conflict` před write a před tombstone | R4, A12 | T10 |
| **B23** | `write_text` vyhodí `DriveConflictError` | 409 `cas_conflict`. `write_text` se zavolal. Tombstone před ním smí být 1×. Test nečeká tombstone 0×. Commit se neudělá | R4, A14 | T11 |
| **B24** | `expect_oid` chybí | zápis právě přečteného souboru, kwargs CAS se nepředají | A12 | T15 |
| **B25** | zápis mění bajty | tombstone jednou před write; `build_agent_context.py` se nespouští | R8, A14 | T6, T15 |
| **B26** | idempotence, 400, nebo 409 ještě před zápisem (CAS při čtení, `task_terminal`) | `write_text` 0× a tombstone 0×. Write-time 409 je B23, ne tenhle řádek. Výjimka po `write_text`: session se necommituje a `reset --hard` vrátí soubory, ne počítadlo volání | A14, A17 | T6, T10, T11, T23 |
| **B27** | úspěch | JSON z návrhu; tělo souboru v odpovědi není; `target` jen `log` nebo `step` | R3 | T1, T3 |
| **B28** | MCP `append_task_note` a `POST /v1/tasks/append` | oba volají stejnou funkci | R5 | T17, T19 |
| **B29** | regrese | `update_task` body nemění; `body_append` zůstává append na EOF | R7 | T20 |
| **B30** | krok i log | existující checkbox se nepřepne na `[x]`; nevznikne nové task ID | R6 | T4, T15 |
| **B31** | `status: Done` v dictu, cíl `log` nebo `note` | odrážka se zapíše, řádek `status` zůstane `Done` | A22 | T23 |
| **B32** | stejný holý text logu další kalendářní den | nová odrážka s novým datem | A11 | T6 |
| **B33** | `status: Cancelled` v dictu, cíl `log` | odrážka se zapíše, `status` zůstane `Cancelled` | A22 | T23 |
| **B34** | `Done`, cíl `step`, label v sekci není | 409 `task_terminal` před tombstone, `write_text` se nezavolá. Sekce kroků, pokud chybí, nevznikne | A22 | T23 |
| **B35** | `Cancelled`, cíl `step`, label v sekci není | 409 `task_terminal`, stejné jako B34 | A22 | T23 |
| **B36** | `Done` nebo `Cancelled`, cíl `step`, label v sekci už je | 200 `already_present`, ne 409 | A22, A24 | T23 |
| **B37** | `type: epic` nebo `work_type: epic`, bez hlavičky `is_operational_header`, cíl `step` | 400 `epic_has_no_steps`. Tělo včetně Definition of done beze změny. Tombstone se nevolá. Epic, který je zároveň `Done` a sekci nemá, vrací tuhle 400, ne 409 | A21 | T22 |
| **B38** | epic a sekce kroků už je, status není terminální | nový krok jako u story (číslo, sort, A9) | A21 | T22 |
| **B39** | epic, cíl `log`, sekce kroků chybí | zápis do `## Poznámky / log`. Definition of done se nezmění | A21 | T22 |
| **B40** | `- [ ] foo` nebo `- foo` jako log; `- [ ] **RBU-S70-1** foo` na úkolu `SB-S17` jako log i jako step | log skončí jako `- {dnes}: foo`. Cizí id na začátku zbytku → 400 `text_contains_step_id` u obou cílů, bez write | A6, A23 | T24 |
| **B41** | mezi kroky a logem je řádek `# …` | nová odrážka zůstane nad tím `#`. Po sortu je pořád v operational sekci. `### ` sekci neukončí | A9, C5 | T25 |
| **B42** | plot je YAML list nebo skalár nebo `YAMLError`, cíl `log` | 400 `invalid_frontmatter`, bez write a bez tombstone. Prázdný plot (`None` → `{}`) tahle 400 není | C6 | T26 |
| **B43** | checkbox `- [ ] **Pozor** foo` a text `**Pozor** foo` | `already_present` navzájem. Text `foo` proti tomu checkboxu nový krok založí. Sundává se jen `_SUBTASK_ID_RE`, ne libovolné `**…**` | A25 | T27 |
| **B44** | čísla jen z vedoucího id na checkboxu první operational sekce, `base == task_id` | `[x]` i `[X]` se počítají. Jiná velikost písmen, id uprostřed řádku, odsazený řádek a zmínka v logu se nepočítají. Žádná shoda → `**ID-1**`. `3b` → další je 4 | A26 | T3, T30 |
| **B45** | `id` je int, `true`, list nebo dict; v sekci je holé `foo` | text `foo` → 200, ne `task_id_missing`. Nový text `bar` u story `Next` → 400 `task_id_missing` až po epic a terminal. `**RBU-S70-1** x` → 400 `text_contains_step_id` dřív | A27 | T28 |
| **B46** | `already_present` na řádku `**SB-S17-3b**` a soubor bez klíče `updated` | `step_id` je `SB-S17-3b`, `inserted_line` je řádek po `rstrip`, `updated` je `null`, soubor beze změny. Po úspěchu je string `2026-10-14`, `isinstance(updated, str)`, ne `datetime.date` | A28 | T29 |
| **B47** | `type: story` a `work_type: epic`, sekce kroků chybí, status `Next` | není epic, sekce kroků se smí založit. Samotné `work_type: epic` bez `type` → 400 `epic_has_no_steps` | A29 | T31 |
| **B48** | ve frontmatteru není řádek `updated:`, zápis projde | řádek se doplní a má dnešní Prague datum. Chybějící `status` a `focus` se nepřidají | A30 | T32 |
| **B49** | log na těle šablony včetně `<!--` … `-->` | komentář sekci neukončí. Nová odrážka je až pod `-->`. Když za `-->` jsou prázdné řádky, odrážka je mezi `-->` a těmi řádky | A31, A33 | T33, T35 |
| **B50** | step bez logu i bez kroků; log bez obou | Step založí jen sousední `## Operativní kroky` a checkbox. Log nezaloží. Log založí jen sousední `## Poznámky / log` a odrážku. Kroky nezaloží | A32 | T34 |
| **B51** | sekce končí dvěma prázdnými řádky a pak dalším `## ` | Odrážka je hned za posledním neprázdným řádkem. Dva prázdné řádky zůstanou pod ní, u logu i u kroku, i když sort přeřadí | A33 | T35 |
| **B52** | dva checkboxy se stejným labelem, první `[x] **SB-S17-4**`, druhý `[ ] **SB-S17-9**` | `already_present`, `step_id` je `SB-S17-4`, ne `SB-S17-9`. Write 0× | A34 | T36 |
| **B53** | `id: " SB-S17 "` | `task_id` je `SB-S17`. Nový řádek je `**SB-S17-2**`, ne s mezerami. Vlastní prefix se sundá. Cizí id je 400 | A35 | T37 |
| **B54** | checkboxy 9 a 10 | nový řádek je `**SB-S17-11**`. Desítka zůstane jednou | A36 | T38 |
| **B55** | čistý `PYTHONPATH` jen na `vps/second-brain-brain` | `import app.tools.append_task_note` v subprocessu skončí 0 díky `parents[3]` | A38 | T39 |
| **B56** | úspěšný step | `write_text` dostane `str`, ne tuple. `changed == False` zápis nezruší | A39 | T40 |
| **B57** | přesná log odrážka jen uvnitř `<!-- -->` | 200 `already_present`, write 0×. Jiný text se zapíše až pod `-->` | A40 | T41 |
| **B58** | sekce je poslední a pod posledním checkboxem nebo pod `-->` jsou dva prázdné řádky až do konce souboru | odrážka je za posledním neprázdným řádkem, oba prázdné řádky zůstanou, soubor končí newline a nepřibude druhý | A43 | T42 |

**Checklist A — netýká se**

- RBAC role Universe, Alembic, frontend, subnav, Celery, Allfred/Pipedrive/Fakturoid — tohle není RB Universe.
- Dávkový partial apply — jeden soubor, jedna odrážka.
- Slack, Gmail, materials backlink — R6.
- Limit focus slotů — to je `set_focus`.
- Generování `## Stav (auto)` — cesta hubu regexem neprojde (B3).
- Odškrtnutí kroku a GitHub `Closes` — cron `github_rbu_closes` se nemění.
- Strop ID projektu — podkrok není `allocate_task_id` (A5).
- `qa_gate.mjs` / Playwright T6 — profil SECOND_BRAIN.

## Výkonový rozpočet (P)

Nástroj nečte celý vault. `iter_active_tasks` se nevolá. `yaml.safe_load` běží na plotu toho jednoho souboru. Checklist „celý vault“ se neuplatní.

| Položka | Rozpočet |
|---|---|
| Čtení | 1× `read_text` jednoho task `.md` |
| Zápis | 0× `write_text` i tombstone při idempotenci, 400 a read-time 409. Úspěch: 1× `write_text` + až 3× `delete`. Write-time 409: 1× `write_text`, které vyhodí; tombstone před ním smí proběhnout |
| SQL | 0 |
| Externí HTTP v nástroji | 0. Git commit/push je stávající konec mutate session |
| Payload odpovědi | malý JSON bez těla souboru. Zbytek textu strop 1000 znaků |
| Paměť | jeden markdown v paměti |
| Flock | jen po dobu jednoho read/modify/write, ne po dobu rebuildu kontextu |
| Cache | vlastní cache není. Tombstone zneplatní trojici kontextu; další `get_context` rebuilduje jako po `create_task` |
| Cold/warm api_ms | stejný řád jako `PATCH /v1/tasks` (jeden soubor + push session). Zákaz je přidat průchod všech tasků |

Body, které dávají smysl: žádný scan všech úkolů, žádný N+1, odpověď bez celého souboru, žádný rebuild pod flockem, jeden zápis souboru. Stránkování, DB index a cache stampede se netýkají.

## Testy (T#)

Žádný test neotevírá živý `OBSIDIAN/` ani produkční Brain. Vault je `MagicMock`, vzor `tests/test_update_task_cas.py` a `tests/test_set_focus.py`. `_prague_today` vrací `date(2026, 10, 14)`. Fixture kroku, který sekci zakládá, má `type: story` a status `Next`.

| T# | Typ | Owner | Soubor | Co ověřuje (B#) |
|---|---|---|---|---|
| **T1** | pytest | gate | `vps/second-brain-brain/tests/test_append_task_note.py` | B12, B14, B18, B27 — log před další H2; kroky se nepřeřadí |
| **T2** | pytest | gate | stejný | B13 |
| **T3** | pytest | gate | stejný | B15, B16 — `1` + `3b` → `4`; chybějící sekce u story `Next` má checkbox hned nad `## Poznámky / log`. Prázdný řádek, který nad logem byl, zůstane nad `## Operativní kroky`. Mezi checkboxem a logem prázdný řádek nepřibude |
| **T4** | pytest | gate | stejný | B17, B30 — nový `[ ]` skončí před `[x]` |
| **T5** | pytest | gate | stejný | B11 — `### ` je uvnitř sekce, proto 400, ne tiché založení vedle |
| **T6** | pytest | gate | stejný | B19, B25, B26, B32 — `already_present` vrací `updated` jako `str` `YYYY-MM-DD`, i když `yaml.safe_load` z nequoted data udělá `datetime.date`. Nečitelný klíč je `null` |
| **T7** | pytest | gate | stejný | B20 — `foo  bar` = `foo bar`; `Foo` ≠ `foo`; `a b` ≠ `ab`; existující `[X]` → `already_present` |
| **T8** | pytest | gate | stejný | B4, B5, B6 — vault se neotevře, včetně `- [ ]` a `- ` |
| **T9** | pytest | gate | stejný | B3 |
| **T10** | pytest | gate | stejný | B22 |
| **T11** | pytest | gate | stejný | B23 — `write_text` se zavolá a vyhodí `DriveConflictError` → 409 `cas_conflict`. Netvrdí, že tombstone byl 0× |
| **T12** | pytest | gate | stejný | B8 |
| **T13** | pytest | gate | stejný | B9 |
| **T14** | pytest | gate | stejný | B10 |
| **T15** | pytest | gate | stejný | B21, B24, B25, B30 — úspěšný zápis story, `focus`/`status` beze změny, bez `expect_oid` se CAS kwargs nepředají |
| **T16** | pytest | gate | stejný | B7 |
| **T17** | pytest | gate | stejný (TestClient jako `test_auth_rest.py`) | B1, B28 — anonymní POST 401 |
| **T18** | pytest | gate | stejný | B2 — nástroj na `dev` / service principal nevrací 403 |
| **T19** | pytest | gate | stejný | B28 — `build_mcp()` obsahuje `append_task_note` |
| **T20** | pytest | gate | hub tests + brain suite | B29 — `task_io` a `update_task` se nemění |
| **T21** | ruční po deployi | QA | bez zápisu do vaultu | image app `second-brain-brain` = pushnutý SHA; `GET https://brain.cyprovi.cz/healthz` |
| **T22** | pytest | gate | `test_append_task_note.py` | B37, B38, B39 — tělo ze `epic-template.md` (DoD checkbox, bez operational hlavičky): step → 400, DoD beze změny, tombstone ne; `work_type: epic` stejně; epic se sekcí kroků → nový checkbox; log na epicu → odrážka v logu, DoD beze změny |
| **T23** | pytest | gate | stejný | B31, B33, B34, B35, B36 — log na `Done` i `Cancelled` zapíše a status v dictu/řádku zůstane; step na obou → 409, write i tombstone 0×; stejný label na `Done` → `already_present` |
| **T24** | pytest | gate | stejný | B4, B7, B40 — `- [ ] foo` a `- foo` jako log; prázdno po sundání; cizí `**RBU-S70-1**` za checkboxem u logu i stepu; `Note` a `STEP` |
| **T25** | pytest | gate | stejný | B41 — `# …` mezi kroky a logem; odrážka nad ním; po sortu pořád v operational sekci |
| **T26** | pytest | gate | stejný | B42 — YAML list jako plot, cíl `log` → 400 `invalid_frontmatter`, write 0×. Stejný soubor testu ještě skalár a `YAMLError`. Prázdný plot tuhle 400 nedostane |
| **T27** | pytest | gate | stejný | B43 — `**Pozor** foo` je `already_present` samo se sebou a není totéž co `foo` |
| **T28** | pytest | gate | stejný | B45 — int, bool, list, dict; holý label → 200; nový text → 400 až po epic a terminal; cizí id → 400 dřív |
| **T29** | pytest | gate | stejný | B46 — `step_id` `SB-S17-3b`, `inserted_line` po `rstrip`, chybějící `updated` je `null`; po úspěchu je `isinstance(updated, str)` a hodnota `2026-10-14`, ne `datetime.date` |
| **T30** | pytest | gate | stejný | B44 — case `sb-s17` se nepočítá, `[x]`/`[X]` ano, id uprostřed ne, odsazení ne, log ne, žádná shoda → 1 |
| **T31** | pytest | gate | stejný | B47 |
| **T32** | pytest | gate | stejný | B48 |
| **T33** | pytest | gate | stejný | B49 — tělo `task-template.md` 38–45 |
| **T34** | pytest | gate | stejný | B50 — step bez logu log nezaloží; log bez kroků kroky nezaloží; nadpis a odrážka jsou sousední |
| **T35** | pytest | gate | stejný | B51 — dva prázdné řádky zůstanou pod novou odrážkou, u logu i u kroku |
| **T36** | pytest | gate | stejný | B52 — první shoda shora, `step_id` je `SB-S17-4` |
| **T37** | pytest | gate | stejný | B53 — mezery kolem `id` se ořežou |
| **T38** | pytest | gate | stejný | B54 — kroky 9 a 10, další je 11 |
| **T39** | pytest | gate | stejný | B55 — subprocess import s čistým PYTHONPATH |
| **T40** | pytest | gate | stejný | B56 — `write_text` dostane řetězec |
| **T41** | pytest | gate | stejný | B57 — odrážka jen v HTML komentáři je `already_present` |
| **T42** | pytest | gate | stejný | B58 — prázdné řádky na konci souboru zůstanou pod odrážkou |

**Lokální gate (T20):**

```bash
python3 -m pytest vps/second-brain-hub/tests scripts/tests vps/second-brain-brain/tests -q
```

Focused běh: `python3 -m pytest vps/second-brain-brain/tests/test_append_task_note.py -q`.

**TESTER: přeskočeno (profil SECOND_BRAIN).** Playwright-T6-full a `rbu-tester` se nevolají.

## Pořadí implementace

1. **F1** — `append_task_note.py`: A23 před vaultem, yaml dict, pořadí idempotence → epic → terminální → `task_id_missing` → `###` → vložení, konec sekce jako řádek 135, bump `updated`, CAS, tombstone. Hub lib se needituje.
2. **F2** — testy T1–T16, T18 a T22–T42. T17 a T19 až po F3. Závisí na F1.
3. **F3** — `mcp_app.py` a `POST /v1/tasks/append`. Závisí na F1. T17 a T19 až po F3.
4. **F4** — runbook, architecture, claude instructions, `mrluc-loader`, věta v `agenda-status-update`. Závisí na kontraktu F1.
5. **F5** — celý gate T20. Závisí na F1–F4.
6. **F6** — lokální commit na `main` jen seznamem cest, bez push. Závisí na zeleném F5. Push a T21 až po review.

## Rizika a zpětná kompatibilita

1. `PATCH /v1/tasks` a MCP `update_task` / `create_task` / `set_focus` se nemění. Nová route je přidání.
2. Crony dál lepí log na EOF přes `body_append`. Vedle řádku v sekci může později přibýt další řádek na konci souboru. Tahle změna to nesjednocuje.
3. `### ` v krocích nástroj odmítne, dokud nepřibude název skupiny. Krok do takové sekce Brain nezapíše, pokud label ještě není (pak je `already_present`).
4. Stejný label kroku se znovu nezaloží (A24). Nové kolo stejné práce potřebuje jiný text. `Foo` a `foo` jsou dva kroky.
5. Nový krok na `Done` / `Cancelled` je 409 a status se nemění. Log na terminálním úkolu projde. Epic bez sekce kroků je 400, checkbox v Definition of done nevznikne.
6. Číslo podkroku se bere jen z checkboxů v sekci kroků. Smazaný řádek bez stopy v sekci se může číslem vrátit. Log se na čísla neprohledává.
7. Jiný nadpis než přesně `## Poznámky / log` se netrefí a nástroj založí druhou sekci logu.
8. Když řazení kroků musí hýbat pořadím, `sort_operational_steps` zahodí prázdné řádky mezi položkami. Ukončovací prázdné řádky před dalším nadpisem nechá (B51). Když sekce žádný ukončovací prázdný řádek neměla, funkce při přeřazení jeden doplní (`max(trailing, 1)`); T4 ten řádek čeká. A43 platí i když je sekce na konci souboru.
9. HTML komentář sekci neukončí. Odrážka jde až pod `-->` (A31), ne nad komentář.
10. Recurring reset (`lifecycle_recurring.py` 242–246) sekci při rotaci přepíše. Nástroj recurring nijak nezná.
11. Commit vaultu má dál hlášku `hub: vault update …` (`git_io.py` 620).
12. Řádkový patch `updated:` mine klíč, který není samostatný řádek `updated:`. Stejné omezení jako `set_focus`.
13. Špinavý pracovní strom: `git add -A` by do `main` vzal cizí změny. Commit je jen explicitní seznam.
14. Bez `expect_oid` nástroj nezjistí, že klient rozhodoval nad starším čtením. Upraví soubor, který právě přečetl. Stejné jako `update_task`.
15. Push failure a reset tipu je stávající `strict_push` všech mutate nástrojů.
16. Epic `Done` bez sekce kroků vrací 400 `epic_has_no_steps`, ne 409. Důvod: sekce chybí, takže se nesmí založit (A21). 409 je až pro nový krok, když sekce je, nebo když terminální není epic.

## Otevřené otázky pro uživatele

Žádné. Grill uzavřel otázky 1 a 6 (`note` = alias `log`; volat smí každý už autentizovaný principal) a zapsal A21–A24. A3 (strop 1000, jedna řádka) a A9 (`### ` → 400, když idempotence nesedla) platí jako rozhodnutí, ne jako vidlice.

## Nálezy kritika

| C# | Stav | Kde |
|---|---|---|
| **C1–C7** | vyřešeno v kole 2, v3 je nerozbíjí | A21–A24, B31–B42, T22–T26 |
| **C8** | vyřešeno | A25, krok 10, B43, T27. Sundává se jen `_SUBTASK_ID_RE`, ne libovolné `**…**`. |
| **C9** | vyřešeno | A26, B44, T3 a T30. Case-sensitive base, `[x]`/`[X]`, střed řádku, odsazení a log se nepočítají, jinak `N` = 1. |
| **C10** | vyřešeno | A27, kroky 6–7 a 11, B10, B45, T28. Žádné `str()` z čísla, boolu, listu ani dictu. `task_id_missing` až po idempotenci, epic a terminal. |
| **C11** | vyřešeno | A28, B46, T29. |
| **C12** | vyřešeno | A29, B47, T31. `type: story` + `work_type: epic` není epic. |
| **C13** | vyřešeno | A30, krok 15, B48, T32. |
| **C14** | vyřešeno | A31, B49, T33. Odrážka je pod `-->`. |
| **C15** | vyřešeno | A32, B50, T34. Jen sekce cíle. |
| **C16** | vyřešeno | A33, B51, T35. Odrážka za posledním neprázdným řádkem. |
| **C17** | vyřešeno | A34, B52, T36. První shoda shora. |
| **C18** | vyřešeno | A35, B53, T37. `task_id = raw.strip()`. |
| **C19** | vyřešeno | A36, B54, T38. `N = max(int(num)) + 1`. |
| **C20** | vyřešeno | A37, F2 zahrnuje T18 a T22–T42. |
| **C21** | vyřešeno | A38, B55, T39. Bootstrap jako `update_task.py`. |
| **C22** | vyřešeno | A39, B56, T40. Do souboru jen `body`. |
| **C23** | vyřešeno | A40, B57, T41. Odrážka v komentáři je `already_present`. |
| **C24** | vyřešeno | A18 a A41 beze změny. B16, krok 13, T3, věta u `create_task.py` 109–114. Checkbox hned nad logem, prázdný řádek z řádku 111 se nepřebírá. |
| **C25** | vyřešeno | A28, odstavec Odpověď, B19, B46, T6, T29. `updated` je `str` `YYYY-MM-DD` nebo `null`. |
| **C26** | vyřešeno | A14, kroky 16–17, B23, B26, T11, řádek Zápis v P. Read-time 409: write i tombstone 0×. Write-time 409: `write_text` hodí, tombstone před ním smí být. |

