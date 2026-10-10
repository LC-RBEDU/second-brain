# Meeting language (režim zápis)

Doplňuje [language-rules.md](language-rules.md) o pravidla pro zápisy ze schůzek.
**Ne** klientská nabídka / slide copy. Blacklist AI a korporátních frází je v `language-rules.md`.

## Include

- Přirozená čeština a angličtina (ne doslovný překlad z EN do CS).
- Konkrétní slovesa a podstatná jména; krátké, skenovatelné odrážky.
- Humanization: když věta má tři a více abstraktních podstatných jmen, zvaž přepis kolem akce nebo výsledku.

## Exclude

- Claims / headlines ve stylu „2–4 slova jako brand claim“.
- Slide-and-offer / learning-journey / investment copy z `rbedu-writing-style`.
- Registr „ty“ / osobní Slack.

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
