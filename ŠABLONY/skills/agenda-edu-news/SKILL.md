---
name: agenda-edu-news
description: "Připraví návrh témat pro EDU News (~30s firemní video): zpět / dopředu + výjimečné schůzky z kalendáře (ne pravidelné rituály). Use when user says EDU news, OPS2, návrhy témat EDU, připrav EDU news, nebo když je na pořadu OPS2 — Nahrát EDU news. Assist — agent navrhne, člověk schválí před zápisem do OPS2."
---

# agenda-edu-news

> EDU News = krátké video pro tým: **čemu jsem se věnoval** (tento / minulý týden) a **čemu se budu věnovat** (příští). Témata s dopadem pro parťáky — ne technické detaily ani admin maličkosti.

**Vault:** `OBSIDIAN/` — `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`  
**Task:** **OPS2 — Nahrát EDU news ♻️ weekly (čtvrtek)** · `02-PROJEKTY/operations/tasks/OPS2 — *.md` · `agent: assist`

## Kdy spouštět

- „EDU news“ / „připrav EDU news“ / „návrhy témat EDU“ / „OPS2“
- Když `co teď` / práce na Operations ukáže OPS2 s dnešním / blízkým deadline
- **Ne** denní cron — seznam vzniká **jen na zadání** v chatu

## Cíl výstupu

Max **5** headline-ů do ~30s videa, ve **dvou koších**:

1. **Zpět** (2–3) — co se stalo / posunulo a má smysl říct firmě  
2. **Dopředu** (2–3) — kam jdeš příští týden (fokus, silné Next, výsledky z práce — ne „mám schůzku X“)

Kalendář ber jako **doplňkový kontext** pro vault (co se řešilo / bude řešit u ad-hoc setkání). **Nepřidávej do shrnutí pravidelné firemní rituály** — o nich všichni vědí, samotný fakt schůzky není téma EDU news.

Headline = věta do kamery, **ne** surový `title` tasku. Provenance (`ID — title`) drž v závorce / poznámce.

## Workflow

### 1. Načti vault kontext

1. `OBSIDIAN/00-System/agent-context.json` — pokud chybí nebo `generated_at` > 24 h → `python3 scripts/build_agent_context.py`
2. Z snapshotu:
   - `recently_done[]` (lookback od **posledního čtvrtka** včetně, ne jen „7 dní slepě“)
   - `top_priority_today[]` / tasky s `focus` = aktuální ISO týden
   - `top_priority[]` — silné `Doing` / `Next` (ne rituály)
   - `upcoming_deadlines[]` na příští ~7–10 dní
3. Přečti aktuální OPS2 soubor (glob `02-PROJEKTY/operations/tasks/OPS2*.md`) — marker block + log
4. Volitelně: 1× `00-System/Memory/about-me.md` pokud pomůže tónu

**Vyřaď z kandidátů (nepatří do EDU):**
- slug `osobni`, `owners`
- recurring rituály (včetně OPS2 samotného)
- second-brain meta-údržba (ID hygiene, deploy cronu, charter refresh…), pokud nemá firemní dopad
- admin trivia: tabulky účasti, medailonky, přejmenování kanálů, Culture Canvas, zubař, faktura Lukáš→RB, drobné form checky
- nízký dopad / čistě interní tech detaily bez změny pro kolegy

**Preferuj:** strategy, finance, RBU/Universe, sales/BD, firemní procesy, Allfred, Summit, M&A — věci, které mění práci nebo informace ostatních.

### 2. Načti kalendář (povinné)

MCP `user-google-workspace` → `get_events`:

- `user_google_email`: `lukas@redbuttonedu.cz`
- `calendar_id`: `primary` (jiný jen když user řekne)
- `time_min` / `time_max`: od **posledního čtvrtka 00:00** do **příštího čtvrtka 23:59** (Europe/Prague → RFC3339)
- `max_results`: 50
- `detailed`: `true` (attendees pomůžou poznat firemní vs. osobní)

Přeskoč / neber jako téma: `outOfOffice`, `focusTime`, `workingLocation`, celodenní bloky bez lidí, čistě osobní, interní prep bez externího/firemního významu, Reclaim travel/lunch/decompress.

**Pravidelné schůzky — vždy vynechat** (i když jsou v kalendáři): samotná zmínka není headline. Typicky:
- **RB EDU Huddle**, **Strategická schůzka** / Strategy pulse, **Finance Sync**
- pravidelné 1:1 rytmy bez mimořádného obsahu (Lukáš/Luboš, Dominik & Lukáš…) — **jen pokud** z nich vyplyne konkrétní novinka pro firmu, formuluj **výsledek/agendu**, ne „měl jsem schůzku“
- čAI session, owners setkání v rutinním režimu (mimořádná agenda = jinak)

**Schůzka z kalendáře smí být téma jen ad-hoc:** klient / partner, kickoff, offsite, DD, jednorázové rozhodnutí, externí host — něco, co tým **nemusí** znát z rytmu kalendáře.

Kalendář použij k tomu, aby sis u tasků ověřil kontext (např. Summit s Mišou → ES5), ne aby EDU news bylo seznam schůzek.

Když MCP auth selže — řekni to, pokračuj jen z vaultu, v preview uveď „kalendář chybí“.

### 3. Sestav návrh (ússudek agenta, ne skóre)

Nealgoritmický rank. Použij širší kontext chatu + vault (+ kalendář jen pro ad-hoc / kontext u tasků). Slouč příbuzné tasky do **jednoho** headline. Preferuj dopad a srozumitelnost pro parťáky. **Neplň preview sekcí „Schůzky“ pravidelnými meetingy.**

Formát preview v chatu (vždy **`ID — title`** u tasků):

```
═══════════════════════════════════════════════
EDU NEWS — návrh (YYYY-MM-DD) · assist
Období: Čt DD.MM. → Čt DD.MM.
═══════════════════════════════════════════════

### Zpět
1. <headline do kamery>
   ← F42 — Opravit fakturační workflow… | proč zajímá tým: …
2. …

### Dopředu
1. <headline>
   ← S12 — Capacity planning… | …
2. …

### Zahodit (ať víš, že jsem to viděl)
- S22 — Offsite… — admin tabulka, ne headline
- kal: Strategická schůzka / Huddle / Finance Sync — pravidelný rytmus, ne téma
- …

OK zapsat do OPS2? (ano / uprav X / vyhoď Y)
```

### 4. Zápis do OPS2 (jen po potvrzení)

Uprav marker block v body OPS2:

```markdown
<!-- edu-news-topics:start -->
**Návrh EDU news** _(assist YYYY-MM-DD HH:MM)_ — zkontrolováno před nahráním:

### Zpět
- [ ] **<headline>** — _(F42 — krátký title)_
- [ ] …

### Dopředu
- [ ] **<headline>** — _(S12 — …)_
<!-- edu-news-topics:end -->
```

(Sekci **Schůzky** v markeru nepoužívej — EDU news nejsou kalendář. Výjimka: user výslovně chce ad-hoc schůzku jako samostatný checkbox.)

- Zachovej zbytek OPS2 (Operativní kroky, log).
- Po zápisu: `updated:` frontmatter OPS2 = dnes.
- **Nenastavuj** `status: Done` — to až po nahrání videa (`agenda-status-update`).
- Cron `lifecycle_extra_edu_news.py` témata **neplní**; `--reset` jen vyčistí marker po cyklu, pokud ho spustíš.

### 5. Po nahrání (když user řekne hotovo)

Deleguj na `agenda-status-update`: OPS2 → `Done` (recurring rotace). Marker se smaže při rotaci / `--reset`; nová instance má prázdný placeholder dokud znovu nespustíš tento skill.

## Pravidla

- **Assist** — nikdy nezapisuj marker bez „ano“ / explicitního schválení úprav
- V chatu vždy **`ID — title`**, ne holé ID
- Max 5 checkboxů celkem ve výsledném markeru (jen Zpět + Dopředu)
- Žádné odhady effortu v návrzích
- Kalendář = kontext a ad-hoc výjimky; **ne** pravidelné Huddle / Strategy / Finance Sync jako témata
- Legacy `00-System/edu-news-topics.json` **nepoužívej** (mrtvý state)
