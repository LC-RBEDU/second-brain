# Handoff pro Cowork — nasazení skillu rbedu-grammar-nazi

*Přenos z chatu na claude.ai (7. 10. 2026). V chatu nebyl přístup na lokální disk, proto se dokončení přesouvá do Cowork. Níže je vše potřebné v jednom souboru.*

## Cíl (výsledek)

- Skill **`rbedu-grammar-nazi`** je nasazený v Claude a ověřený. Je to přejmenovaný skill `grammar-nazi`.
- `zapis-ze-schuzky` ho po sestavení draftu MD **sám volá** (směr je `zapis-ze-schuzky` → `rbedu-grammar-nazi`, ne naopak). Ručně se spouští jen na výslovné „rbedu-grammar-nazi".

## Kde co leží

- Původní skill (lokálně): `…/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/ŠABLONY/skills/grammar-nazi/` (`SKILL.md`, `references/meeting-language.md`, `scripts/md_fingerprint.py`, `scripts/fixtures/`, `dist/`).
- Původní zip: `…/grammar-nazi/dist/grammar-nazi-claude.zip` (rozbalená kopie: `dist/grammar-nazi-claude/`).
- Zdroj `zapis-ze-schuzky`: `ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md`.
- Nová složka pro tento skill (tento soubor): `ŠABLONY/skills/rbedu-grammar-nazi/` (Drive ID `1kUZZzJqwTO5tTf-5ohhWRWdP6fkTgD-5`). Zatím obsahuje jen tento handoff.

## Co už je hotové a rozhodnuté

- Verdikt revize: obsah skillu je použitelný, ale nasazení vyžaduje opravy (níže).
- Rozhodnuto: přejmenovat na `rbedu-grammar-nazi`; volání je ve směru `zapis-ze-schuzky` → `rbedu-grammar-nazi`.
- Návrhy jsou v přílohách: nový `SKILL.md`, nový `INSTALL.md`, patch pro `zapis-ze-schuzky`, smoke test `test_fingerprint.sh`.
- Test fingerprintu proběhl **jen na rekonstrukci** skriptu (chat dostal kód jako base64): 8/8 OK. Originál ještě nespuštěn.

## Co je potřeba udělat (pořadí)

1. **Spustit `test_fingerprint.sh` nad originálním `scripts/md_fingerprint.py` a originálními fixtures.** Očekává se 8× OK. Při FAIL opravit skript nebo fixtures a ukázat diff.
2. Naplnit složku `ŠABLONY/skills/rbedu-grammar-nazi/`: kopie `references/` a `scripts/` z původního skillu + nový `SKILL.md` a `INSTALL.md` z příloh. **Původní složku `grammar-nazi/` nemazat**, dokud nebude nový skill ověřený.
3. Složit zip s kořenovou složkou `rbedu-grammar-nazi/` do `rbedu-grammar-nazi/dist/rbedu-grammar-nazi-claude.zip` (bez složky `dist/` uvnitř zipu).
4. Aplikovat patch na `agenda-zapis-ze-schuzky/SKILL.md` (nový krok 5b, bod v „Co skill dělá", položka checklistu, odkaz na nový skill). **Nejdřív ukázat diff a počkat na potvrzení.**
5. Volitelně: v `md_fingerprint.py` přejmenovat docstring „grammar-nazi gate".
6. Ověřit, jestli upload do Claude (Settings → Skills) vyžaduje kořenovou složku v zipu. *Unverified:* v chatu to ověřeno nebylo.

## Známé nálezy

- Fingerprint hlídá jen **strukturu** (nadpisy, ID, počty odrážek, YAML klíče, owner/status). Změnu čísel, jmen v textu ani citátů nezachytí; ta hlídají pravidla v `SKILL.md`.
- Klíče z `name_aliases` se objevují i v `yaml_keys` (drobnost, bezpečné).
- `capture` / `compare` počítají s formátem zápisu (`## 0. Meta`, u `full` přesně 3 highlights); na jiný MD vrací exit 2.
- V původním `SKILL.md` byly: špatný název volajícího skillu (`agenda-zapis-ze-schuzky` vs. `zapis-ze-schuzky`), vaultová cesta ke skriptu a zbytky z Cursoru (Task agent, `install_agenda_skills.sh`).

## Otevřené otázky pro Lukáše

- Má jazykový průchod běžet i u `variant: shared` (sufix `_tym`), nebo jen u `full`? Dosud nerozhodnuto; patch počítá s oběma.

## Pravidla

- Mazání a úpravy existujících souborů vždy po diffu a výslovném potvrzení Lukáše.
- Odhady a nedohledané věci označovat jako *Inference* / *Unverified*.

---

# PŘÍLOHA A — nový SKILL.md

~~~~markdown
---
name: rbedu-grammar-nazi
description: >-
  Jazykový průchod (CS/EN) pro zápisy ze schůzek RB EDU: gramatika, skloňování,
  interpunkce, přirozená próza bez AI/korporátních frází podle
  references/meeting-language.md. Volá ho skill zapis-ze-schuzky po sestavení
  draftu MD a před zápisem souborů. Ručně jen na výslovné "rbedu-grammar-nazi".
  Nepoužívat na nabídky, slide copy, Slack 1:1 ani běžné texty. Vrací pouze
  opravený celý markdown, bez diff reportu. Neupravuje citáty v uvozovkách.
---

# rbedu-grammar-nazi — jazykový průchod pro zápisy ze schůzek

Volá ho skill `zapis-ze-schuzky` (krok „jazykový průchod“). Ručně se spouští jen na výslovný pokyn.
Není pro nabídky, Slack 1:1, těla úkolů mimo zápisový flow ani pro plný `rbe-writing-style`.

## Vstup / výstup

- **Vstup:** celý MD draft zápisu (frontmatter + body).
- **Výstup:** celý opravený MD. **Žádný** úvod, diff, checklist ani „opravil jsem…“.

## Priority

1. Gramatika CS/EN (překlepy, skloňování, časování, shoda, interpunkce).
2. Přirozenost / anti-AI / anti-korpo podle [references/meeting-language.md](references/meeting-language.md).

## Smí

- Morfologie, překlepy, interpunkce, přeformulování vět **beze změny smyslu**.
- Text **uvnitř** existující odrážky / buňky (title úkolu, Co zaznělo, znění úkolu).
- EN úseky opravovat v EN, CS v CS; nepřekládat jazyk.
- Chunking po `##` sekcích při limitu kontextu — po složení chunků musí `md_fingerprint` běžet na **celém** MD.

## Nesmí

- Měnit fakta, jména, čísla, rozhodnutí, ownery, smysl úkolů.
- Přidat / odebrat / sloučit top-level odrážky (Co zaznělo, tasks, highlights, parkoviště).
- Měnit YAML klíče, enum hodnoty (`discussed` / `Projednáno`…), mapu `name_aliases`, cesty.
- Měnit bitově `owner` / `key_people` / `status` / hodnoty `- **id:**`.
- Opravovat text v uvozovkách / citátech (`"…"`, `„…“`, `»…«`).
- Měnit fenced/inline code, URL, e-maily, `[[wikilinky]]`, tvary task ID.
- Měnit tvar `**tasks** — žádné` (neexpandovat na prázdný seznam).
- Offer / claim / slide voice; registr „ty“ / osobní Slack (`lukas-writing-style`).

## Fingerprint (spouští volající skill, ne tento skill)

Cesty jsou relativní k adresáři tohoto skillu. Potřebuje Python 3.

```bash
python3 scripts/md_fingerprint.py capture --md <draft.md> --out <fp.json>
# exit 0 OK, 2 nevalidní

python3 scripts/md_fingerprint.py compare --before <fp.json> --md <draft.md>
# exit 0 shoda, 1 mismatch, 2 nevalidní after
```

- `capture` / `compare` počítají s formátem zápisu (`## 0. Meta`, u varianty `full` přesně 3 highlights). Na jiný MD skončí exit 2.
- Fingerprint hlídá jen **strukturu**. Fakta, čísla ani citáty nekontroluje — ta hlídají pravidla „Nesmí“.
- Exit 1 → opravený draft nepoužít; vrať se k původnímu nebo opravu zopakuj.
- Bez Pythonu / bez compare: průchod udělej, ale finální soubory nepiš bez výslovné výjimky uživatele.

## Claude (bez Cursor agenta)

Průchod běží in-process: načti tento SKILL + `references/meeting-language.md`, přepiš draft, vrať jen MD.
~~~~

# PŘÍLOHA B — nový INSTALL.md

~~~~markdown
# rbedu-grammar-nazi — instalace do Claude

ZIP: `ŠABLONY/skills/rbedu-grammar-nazi/dist/rbedu-grammar-nazi-claude.zip` (vedle tohoto souboru).

## Obsah ZIP

Vše leží v kořenové složce `rbedu-grammar-nazi/`:

- `SKILL.md` — role, whitelist, fingerprint příkazy
- `references/meeting-language.md` — tenká vrstva tone of voice (anti-AI)
- `scripts/md_fingerprint.py` — CLI `capture` / `compare` (exit 0/1/2)
- `scripts/fixtures/` — volitelné testovací MD

## Nasazení v Claude

1. Settings → Skills (název sekce se může lišet) → nahrát ZIP.
2. Pro fingerprint musí být zapnuté Code execution (Python 3).
3. Skill nespouštěj samostatně. Volá ho `zapis-ze-schuzky` v kroku „jazykový průchod“.
4. Ruční spuštění jen výslovným „rbedu-grammar-nazi“.

## Test po nasazení

1. Vezmi `scripts/fixtures/valid-full.md`.
2. `python3 scripts/md_fingerprint.py capture --md valid-full.md --out fp.json` → exit 0.
3. `python3 scripts/md_fingerprint.py compare --before fp.json --md valid-full.md` → exit 0.
4. `broken-highlights.md` musí na `capture` vrátit exit 2.

## Bez Pythonu

Průchod udělej, ale finální soubory nepiš, dokud nejde spustit `compare` (nebo výslovná výjimka uživatele).
~~~~

# PŘÍLOHA C — patch pro zapis-ze-schuzky

~~~~markdown
# Patch pro zapis-ze-schuzky (zdroj: ŠABLONY/skills/agenda-zapis-ze-schuzky/SKILL.md)

## 1) Do „Co skill dělá“ — nový bod mezi 2 a 3

2a. Jazykový průchod draftu MD přes `rbedu-grammar-nazi` (s fingerprint kontrolou).

## 2) Nový krok mezi „Krok 5 — obsah“ a „Krok 6 — soubory“

## Krok 5b — jazykový průchod (rbedu-grammar-nazi)

Po sestavení celého draftu MD, před zápisem jakéhokoli souboru:

1. Ulož draft do dočasného souboru a spusť `capture` (skript z `rbedu-grammar-nazi`, `scripts/md_fingerprint.py`) → `fp.json`.
2. Načti skill `rbedu-grammar-nazi` a proveď průchod na **celém** MD. Dostaneš zpět jen opravený MD.
3. Spusť `compare --before fp.json --md <opravený.md>`:
   - exit 0 → použij opravený MD;
   - exit 1 → opravený MD zahoď, použij původní draft (nebo průchod zopakuj);
   - exit 2 nebo bez Pythonu → soubory nepiš bez výslovné výjimky uživatele.
4. HTML (`body.html`) i MD generuj z **opraveného** textu, ať se obě verze nerozejdou.
5. Do Preview přidej řádek: „Jazykový průchod: proběhl / přeskočen (důvod)“.

## 3) Do Checklistu

- [ ] Jazykový průchod `rbedu-grammar-nazi` + fingerprint compare = exit 0

## 4) Zdroj pravdy na Drive

Do „Zdroj pravdy obsahu…“ doplnit `ŠABLONY/skills/rbedu-grammar-nazi/` a opravit cesty ke skriptům (viz INSTALL.md).
~~~~

# PŘÍLOHA D — test_fingerprint.sh

~~~~bash
#!/usr/bin/env bash
# Smoke test pro scripts/md_fingerprint.py. Spusť ze složky skillu:
#   bash test_fingerprint.sh
# Očekávané výsledky jsou v závorkách. Vyžaduje Python 3.
set -u
S="scripts/md_fingerprint.py"; F="scripts/fixtures"; T="$(mktemp -d)"
run() { # popis, očekávaný exit, příkaz...
  desc="$1"; want="$2"; shift 2
  "$@" 2>/dev/null; got=$?
  [ "$got" = "$want" ] && echo "OK    $desc (exit $got)" || echo "FAIL  $desc (čekáno $want, je $got)"
}
run "capture valid-full"               0 python3 $S capture --md $F/valid-full.md --out $T/fp.json
run "compare identický"                0 python3 $S compare --before $T/fp.json --md $F/valid-full.md
run "capture broken-highlights"        2 python3 $S capture --md $F/broken-highlights.md --out $T/fp2.json
sed 's/tisíc Kč\./tisíc korun./' $F/valid-full.md > $T/ok.md
run "jazyková úprava uvnitř odrážky"   0 python3 $S compare --before $T/fp.json --md $T/ok.md
grep -v "Termín je konec října" $F/valid-full.md > $T/bullet.md
run "smazaná odrážka Co zaznělo"       1 python3 $S compare --before $T/fp.json --md $T/bullet.md
sed 's/\*\*owner:\*\* Lukáš Cypra/**owner:** Lukas Cypra/' $F/valid-full.md > $T/owner.md
run "změněný owner"                    1 python3 $S compare --before $T/fp.json --md $T/owner.md
sed 's/^variant: full/varianta: full/' $F/valid-full.md > $T/yaml.md
run "přejmenovaný YAML klíč"           1 python3 $S compare --before $T/fp.json --md $T/yaml.md
sed 's/strop 100 tisíc/strop 1000 tisíc/' $F/valid-full.md > $T/num.md
run "změněné číslo (známá limitace)"   0 python3 $S compare --before $T/fp.json --md $T/num.md
~~~~
