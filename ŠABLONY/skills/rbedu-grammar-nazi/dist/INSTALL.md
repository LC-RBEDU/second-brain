# rbedu-grammar-nazi — instalace do Claude

ZIP: `ŠABLONY/skills/rbedu-grammar-nazi/dist/rbedu-grammar-nazi-claude.zip` (vedle tohoto souboru).

## Obsah ZIP

Vše leží v kořenové složce `rbedu-grammar-nazi/`:

- `SKILL.md` — kdy se spouští, režimy (obecný / zápis), Smí / Nesmí, fingerprint příkazy
- `references/language-rules.md` — obecná jazyková pravidla a blacklist AI frází
- `references/meeting-language.md` — doplněk pro zápisy ze schůzek
- `scripts/md_fingerprint.py` — CLI `capture` / `compare` (exit 0/1/2)
- `scripts/fixtures/` — volitelné testovací MD

## Nasazení v Claude

1. Settings → Skills (název sekce se může lišet) → nahrát ZIP.
2. Fingerprint (jen režim zápis) vyžaduje zapnuté Code execution (Python 3).
3. Skill se spouští automaticky při tvorbě delšího textu (e-mail, dokument, wiki, prezentace, artefakt, zápis). Nespouští se na chat s agentem ani na krátká hesla.
4. Zápisy ze schůzek ho volá skill `agenda-zapis-ze-schuzky` (režim zápis s fingerprintem). Ručně lze spustit výslovným „rbedu-grammar-nazi“.

## Test po nasazení

1. Vezmi `scripts/fixtures/valid-full.md`.
2. `python3 scripts/md_fingerprint.py capture --md valid-full.md --out fp.json` → exit 0.
3. `python3 scripts/md_fingerprint.py compare --before fp.json --md valid-full.md` → exit 0.
4. `broken-highlights.md` musí na `capture` vrátit exit 2.

## Bez Pythonu

Průchod udělej, ale finální soubory nepiš, dokud nejde spustit `compare` (nebo výslovná výjimka uživatele).
