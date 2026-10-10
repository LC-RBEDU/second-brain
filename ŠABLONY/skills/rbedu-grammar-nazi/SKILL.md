---
name: rbedu-grammar-nazi
description: >-
  Jazykový průchod (CS/EN) pro texty, které tým RB EDU vytváří v rámci práce:
  e-maily, Slack příspěvky, dokumenty, wiki stránky, prezentace, artefakty,
  zápisy ze schůzek. Spouští se automaticky při tvorbě takového textu, těsně
  před jeho předáním: opraví gramatiku, skloňování a interpunkci a odstraní
  AI/korporátní fráze, aniž změní fakta, jména, čísla, citáty nebo hlas autora.
  Nepoužívat na chat s agentem ani na krátká hesla, popisky a tlačítka.
  U zápisů ze schůzek běží přísný režim s kontrolou struktury (fingerprint).
---

# rbedu-grammar-nazi — jazykový průchod pro texty týmu RB EDU

Cíl: každý delší text, který tým v práci vytvoří, odejde gramaticky čistý a přirozeně
napsaný, bez AI a korporátní vaty, a přitom se nezmění jeho obsah ani hlas autora.

## Kdy se spouští

Automaticky, jako poslední krok před předáním hotového textu:

- e-maily a jejich drafty, Slack příspěvky (delší sdělení, ne jednořádkové reakce),
- dokumenty, wiki stránky, návody, reporty,
- prezentace a slide copy, nabídky, one-pagery,
- texty v artefaktech (dashboardy, weby, nástroje), včetně popisů a nápovědy,
- zápisy ze schůzek.

Nespouští se na:

- chat mezi uživatelem a agentem,
- krátká hesla, popisky tlačítek, názvy polí a podobné jednoslovné či jednořádkové texty,
- kód, konfigurace, logy a data.

Ručně se spouští i na výslovné „rbedu-grammar-nazi“ nebo „zkontroluj gramatiku“.
Je-li text od uživatele a nevyžádal opravu, nepřepisuj ho — nabídni průchod jednou větou.

## Dva režimy

| Režim | Kdy | Pravidla jazyka | Kontrola struktury |
|---|---|---|---|
| **obecný** (výchozí) | všechny texty výše kromě zápisů | [references/language-rules.md](references/language-rules.md) | pravidla „Nesmí“, bez skriptu |
| **zápis** | zápis ze schůzky ve formátu RB EDU (`## 0. Meta`, `variant: full` / `shared`) | language-rules + [references/meeting-language.md](references/meeting-language.md) | `scripts/md_fingerprint.py` |

Rozpoznání: má-li draft frontmatter s `doc_type: meeting_summary` nebo sekci `## 0. Meta`,
jde o režim zápis. Jinak obecný.

## Priority

1. Gramatika CS/EN: překlepy, skloňování, časování, shoda, interpunkce.
2. Přirozenost: žádný doslovný překlad z angličtiny, žádné AI a korporátní fráze.

## Smí

- Morfologie, překlepy, interpunkce, drobné přeformulování vět **beze změny smyslu**.
- Sjednotit nekonzistentní zápis (např. data, uvozovky, pomlčky) uvnitř jednoho textu.
- EN úseky opravovat v EN, CS v CS; nepřekládat jazyk.
- U dlouhých textů chunkovat po sekcích; u zápisu musí fingerprint běžet na celém MD.

## Nesmí

- Měnit fakta, jména, čísla, data, ceny, rozhodnutí, ownery, smysl úkolů.
- Opravovat text v uvozovkách / citátech (`"…"`, `„…“`, `»…«`).
- Měnit kód, inline code, URL, e-maily, `[[wikilinky]]`, ID úkolů, cesty, YAML klíče a enum hodnoty.
- Přidávat, ubírat nebo slučovat odrážky, řádky tabulek, sekce či slidy.
- Měnit záměrné claimy, nadpisy, názvy produktů a brandové formulace; opravit smí jen gramatiku.
- Měnit tón a hlas autora; není to stylový skill (viz níže).
- V režimu zápis navíc: neměnit `owner` / `key_people` / `status` / hodnoty `- **id:**`
  a tvar `**tasks** — žádné`.

## Vztah k ostatním skillům

- **`rbedu-writing-style`** řeší hlas a obsah nabídek a business dokumentů (claimy,
  nadpisy, struktura slidů). Grammar-nazi běží **po něm** a hlas nepřepisuje: opravuje správnost
  a odstraňuje jen fráze, které jsou na blacklistu. Při rozporu vyhrává `rbedu-writing-style`.
- **Volající skilly** (např. `agenda-zapis-ze-schuzky`) pouští průchod v režimu zápis po sestavení
  draftu MD a před zápisem souborů. Směr je vždy volající skill → `rbedu-grammar-nazi`.

## Výstup

- Při tvorbě textu proběhne průchod tiše a uživatel dostane rovnou opravený text.
  Žádný úvod, diff ani „opravil jsem…“.
- Na výslovnou žádost o kontrolu cizího textu vrať opravený text; seznam změn jen když o něj uživatel požádá.

## Fingerprint (jen režim zápis; spouští volající skill)

Cesty jsou relativní k adresáři tohoto skillu. Potřebuje Python 3.

```bash
python3 scripts/md_fingerprint.py capture --md <draft.md> --out <fp.json>
# exit 0 OK, 2 nevalidní

python3 scripts/md_fingerprint.py compare --before <fp.json> --md <draft.md>
# exit 0 shoda, 1 mismatch, 2 nevalidní after
```

- `capture` / `compare` počítají s formátem zápisu; na jiný MD skončí exit 2.
- Fingerprint hlídá jen **strukturu**. Fakta, čísla ani citáty nekontroluje — ta hlídají pravidla „Nesmí“.
- Exit 1 → opravený draft nepoužít; vrať se k původnímu nebo opravu zopakuj.
- Bez Pythonu / bez compare: průchod udělej, ale finální soubory zápisu nepiš bez výslovné výjimky uživatele.

## Spuštění

Průchod běží in-process: načti tento SKILL a podle režimu příslušné reference, přepiš text a vrať ho.
Nezávisí na žádném konkrétním nástroji ani úložišti.
