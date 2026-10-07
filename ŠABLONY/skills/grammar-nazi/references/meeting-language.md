# Meeting language (thin layer)

Kalibrace pro zápisy ze schůzek. **Ne** klientská nabídka / slide copy.

## Include

- Přirozená čeština a angličtina (ne doslovný překlad z EN do CS).
- Konkrétní slovesa a podstatná jména; krátké, skenovatelné odrážky.
- Anti-korpo a anti-AI cliché (viz blacklist níže).
- Humanization: když věta má tři a více abstraktních podstatných jmen, zvaž přepis kolem akce nebo výsledku.

## Exclude

- Claims / headlines ve stylu „2–4 slova jako brand claim“.
- Slide-and-offer / learning-journey / investment copy z `rbe-writing-style`.
- Registr „ty“ / osobní Slack (`lukas-writing-style`).
- Runtime načítání vaultu `anti-ai-writing-tools.md` — tento soubor je self-contained.

## Blacklist (curated)

Nepoužívej / přepiš:

- „Není to jen X, je to Y“ / „It's not just X, it's Y“
- „Pojďme se ponořit“ / „Let's dive in“ / „Delve into“
- „V dnešní rychle se měnící době…“
- „Je důležité poznamenat, že…“ / „It's worth noting that…“
- „Pamatujte si, že…“ / „Remember that…“
- „Game-changer“, „revolutionary“, „cutting-edge“, „seamless“
- „Navigovat složitosti“ / „Navigate the complexities“
- „Empowering…“, „Unlock your…“, „future-ready“, „journey to excellence“
- „Doufám, že to pomůže!“ / „I hope this helps!“
- „Skvělá otázka!“ jako zahřívací lichotka
- Korporátní výplň: synergie, leverage, deliver value, transformační změna bez konkrétna

## Čeština / English

- Preferuj přirozenou CS před přeloženou EN syntaxí.
- EN úseky: crisp business English, ne conference fluff.
- V jednom artefaktu nestřídej „ty“ a neosobní „účastníci“ — zápis je neosobní meeting prose.

## Whitelist — nesahat

| Smí se opravovat (gramatika/styl uvnitř) | Nesmí se měnit |
|---|---|
| Text v „Co zaznělo“, wording úkolu, title v tabulce | Jména, čísla, data, rozhodnutí |
| Interpunkce, shoda, skloňování | `owner`, `key_people`, `status`, `- **id:**` |
| AI/korpo fráze → neutrální meeting prose | YAML klíče, `name_aliases`, cesty |
| | Počet top-level odrážek / řádků tabulky |
| | Citáty v uvozovkách; code; URL; e-mail; `[[wikilink]]`; task ID |
| | Tvar `**tasks** — žádné` |
