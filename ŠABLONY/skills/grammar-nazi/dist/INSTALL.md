# grammar-nazi — Claude / offline install

ZIP SSOT: `ŠABLONY/skills/grammar-nazi/dist/grammar-nazi-claude.zip` (vedle tohoto souboru).

## Obsah ZIP

- `SKILL.md` — role, whitelist, fingerprint příkazy
- `references/meeting-language.md` — thin ToV (anti-AI)
- `scripts/md_fingerprint.py` — CLI `capture` / `compare` (exit 0/1/2)
- `scripts/fixtures/` — volitelné test MD
- `INSTALL.md` — tento návod

## Claude Team

1. Rozbal ZIP nebo čti soubory z GitHubu `SECOND_BRAIN`.
2. Při zápisu ze schůzky (`agenda-zapis-ze-schuzky`): **in-process** language pass
   (načti SKILL + meeting-language, přepiš celý MD, vrať jen MD).
3. Před i po passu preferuj fingerprint CLI (Python 3):

```bash
python3 scripts/md_fingerprint.py capture --md <draft.md> --out <fp.json>
# … GN pass …
python3 scripts/md_fingerprint.py compare --before <fp.json> --md <draft.md>
```

4. Bez Pythonu: udělej GN pass, ale **nepiš** finální soubory, dokud nejde spustit compare
   (nebo explicitní výjimka uživatele). Write path s compare je preferovaný.

## Cursor

`bash scripts/install_agenda_skills.sh` — symlink skill + agent `grammar-nazi`.
