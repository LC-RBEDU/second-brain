# Týmové karty CP na wiki + skill

Text níže je plán schválený kritikem r6 (0 nálezů) v chatu `556327f9-40ab-4ae6-b64f-072b63116136`. Implementace ho nemění.

## Jak to chápu

Jedna týmová pravda o 9 aktivních prioritách 2HY/FY2026 na **RB Wiki**. Vault `OBSIDIAN/00-System/Memory/priority/` je **dočasný** vstup do prvního `create`. Až karty žijí, ranking (`company_priorities` → +5) má číst **wiki**, ne kopii ve vaultu.

ICE, ABC, +5 a cesty do Obsidianu **jen ve vaultu**, navázané na `id: CPn` — **ne v kartách**.

## Kritik

- r1 (`98139ff3-ba5b-4de1-82fd-d2daf7dc71f4`) — NEW-1–10 zapracováno
- r2 (`775f6714-7651-40fd-b372-2963242aee36`) — NEW-11 kořen append+sha
- r3 (`55c13b81-73a0-4d90-a2dc-536daa2d249e`) — SCHVÁLENO (invalidováno show/update)
- r4 (`dbd3e345-26d8-4d38-980d-f6c4eded0a7c`) — zapracováno (allowlist + audit kdo)
- r5 (`7670dee4-891d-4af8-bed8-90b772b49a65`) — `### Historie` + T-update DoD blok
- r6 (`4b5d45b9-4d76-441f-8501-d3115c5604a4`) — **SCHVÁLENO** (0 nálezů)
- Rozhodnutí: **kdokoli v Claude Team** smí zapsat allowlist; **v historii musí být vidět kdo** (jméno → commit summary + `### Historie změn`). MCP identitu neověřuje.

## Režimy skillu v Claude Team

Skill + **jedna věta v Team / Project instructions**: věty o firemních prioritách / CP / 2HY dashboard → tento skill + `wiki_manifest` / `wiki_read` / `wiki_write`. Bez načtení skillu **nezobrazovat** priority z hlavy (NEW-4 r4).

### Show

Nic nezapisovat. `wiki_read`, v chatu artefakt.

- „ukaž mi firemní priority“ / dashboard / 2HY → `prehled.md`
- „ukaž … KAM / CP6 …“ → karta; match `id` / `title` / aliasy; nejednoznačné → zeptat se
- **Bez wiki MCP:** žádný obsah karet, žádný vault — hláška „chybí wiki MCP“ (NEW-5 r4)

### Update (a update-status = stejný lock)

**Kdo smí zapsat:** kdokoli v Teamu. Identitu MCP neověřuje.

**Uzavřená allowlist** (jen tohle bez flagu strat. týmu):

- `progress` / text pod `### Stav plnění` (jen z toho, co uživatel řekl)
- milníky (přidat/odškrtnout když zadá text + datum)
- přepočet `nearest_milestone*` + řádek v `prehled.md`
- řádek v `### Historie změn` (pod DoD H2) / audit (viz níž)

**Lock** (stejný flag „DoD/obsah se mění“ / strat. tým): text DoD (cíle), `cp_owner`, seznam 9 CP, sidelined, názvy `##`, **`## Název` / `## Co to konkrétně znamená` / `## Kontext` / tělo `## Owner` / `## Klíčové osoby`** (NEW-2 r4).

Neurčitý „uprav KAM“ → show + otázka, žádný write.

Po úspěšném zápisu: `wiki_read` + **finální verze v chatu**; zmínit draft.

### Audit — kdo zapsal (rozhodnutí uživatele)

Každý `wiki_write` při update:

1. **Autor:** jméno z kontextu Claude Team, pokud je; jinak se skill **zeptá** „Pod jakým jménem to mám zapsat?“ — bez jména **nepíše**.
2. **`summary`** u `wiki_write` (commit): `CP6 progress→riziko — Jan Novák` (id + co + jméno).
3. **Na kartě** append jednoho řádku do `### Historie změn` (vždy H3 pod `## DoD + aktuální stav plnění`, nikdy samostatné `## Historie`): `- YYYY-MM-DD — Jméno — co se změnilo`. Nejnovější nahoře. Při změně jen `prehled.md` stačí commit summary + řádek na příslušné kartě.

### Create

Jednorázové založení (pořadí níž). Bundle fallback jen create → aplikuje agent s `user-wiki`.

## Kam to na wiki

Sekce `strategicke-priority-rb-edu/` (Strategické priority RB EDU).

Pořadí create:

1. `wiki_section_write` `confirm_create: true`. Intro sekce: synonyma + odkaz na `prehled.md`.
2. Kořen: `wiki_read` cesty **`index.md`** (z manifestu; ne prázdný string u read) → append 1 odstavce → `wiki_section_write` `path: ""` + celé intro + `expected_sha` (NEW-7 r4 / NEW-11).
3. 9 karet + `strategicke-priority-rb-edu/prehled.md` přes `wiki_write`.

Dashboard = `prehled.md`, ne `index.md`. Sidelined = odrážky pod tabulkou, bez `CPn`.

## Frontmatter

Wiki: `type` (konvence wiki, ne `company_priority`), `title`, `description`, `tags`, `owner` = steward (update **nemění**), `status` draft/stable, `generated: true`, `stale_after`.

CP: `id`, `cp_owner`, `period`, `nearest_milestone`, `nearest_milestone_date`, `progress`.

Task YAML: jen `[[CPn — Title]]`.

## Karta — 7× `##` + vnitřní struktura DoD (NEW-3 r4)

1. `## Název`
2. `## Co to konkrétně znamená`
3. `## Kontext`
4. `## Owner`
5. `## Klíčové osoby`
6. `## DoD + aktuální stav plnění`
   - nejdřív **pevný blok DoD** (create doslova; skill nesahe bez flagu)
   - pak `### Stav plnění` (allowlist)
   - pak `### Historie změn` (allowlist append)
7. `## Přehled milníků se zvýrazněním nejbližšího`

DoD create doslova včetně CP4. CP2: sheet + „DoD neuzavřené“; owner Maru; Káťa klíčová.

## Skill: vymýšlení zakázáno

Create: milník/`cp_owner` jen z balíčku; chybí → prázdné / `neznámé`.
Update: nejbližší = min budoucí datum ze seznamu na kartě; nový milník jen když uživatel dodá text+datum.
Bez wiki MCP: show/update žádný obsah, žádný vault.

## B# / T#

- **B1** Create: sekce + 9 karet + `prehled.md` + sidelined.
- **B2** Update allowlist: jen `### Stav plnění` / milník / `### Historie změn` / přehled; pevný blok DoD a `cp_owner` beze změny.
- **B3** Lock: DoD / Kontext / CO / Owner / klíčové osoby bez flagu → 0 write.
- **B4** Create bez milníku → Termín prázdný, `neznámé`.
- **B5** Konflikt `expected_sha` (karta, přehled, kořen) → žádný tichý overwrite.
- **B6** `prehled.md` ano; `wiki_write` na `index.md` ne.
- **B7** Create kořen: staré intro + 1 odstavec; `wiki_read` `index.md` + SHA.
- **B8** Show dashboard / CP6 bez zápisu; obsah ⊆ `wiki_read`.
- **B9** Update: finální `wiki_read` v chatu; commit summary + řádek Historie se jménem; bez jména autora → 0 write.
- **B10** Neurčitý „uprav KAM“ → show + otázka, 0 write.
- **B11** Show/update bez MCP → hláška, žádný vault obsah.

**T#** (checklist, ne Tester):

- T-create: wiki_read 9 karet + přehled + intro sekce + intro kořene; DoD CP4 přítomen; CP2 neuzavřené.
- T-show: prehled + CP6; chat ⊆ wiki; 0 write.
- T-update: `### Stav plnění` změněn; **pevný blok DoD** (řádky před `### Stav plnění`) byte-identical; zbytek H2 mimo Stav/Historie lock; historie + summary se jménem; řádek přehledu; chat = finále.
- T-vague / T-lock: 0 write.
- T-no-mcp: hláška, 0 inventovaný dashboard.

## Ranking cutover (později)

`today_priority.py` mimo toto kolo. Skill neslibuje, že wiki teď řídí +5.

## Co vznikne po schválení

- Create prompt (balíček 9 CP)
- `SKILL.md` + věta do Project instructions
- (volitelně) markdown kopie u tebe mimo vault dependency skillu

## Mimo rozsah

- Kód snapshotu / Coolify na čtení wiki
- Sync ze sheetu Roadmapa EDU
- Sidelined jako karty

## Kde leží implementace

- `ŠABLONY/skills/wiki-firemni-priority/SKILL.md`
- `ŠABLONY/skills/wiki-firemni-priority/create-bundle.md`
- `ŠABLONY/skills/wiki-firemni-priority/project-instructions.md`
