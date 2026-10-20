# Instalace Cursor rule do RB-Universe

Toto SECOND_BRAIN repo **nemá** write přístup do `RedButtonEDU/RB-Universe`. Rule je připravená zde:

- Zdroj: [`ŠABLONY/cursor-rules/rbu-commit-closes.mdc`](../ŠABLONY/cursor-rules/rbu-commit-closes.mdc)
- Lidská věta: [`ŠABLONY/cursor-rules/rbu-commit-closes-CONTRIBUTING.md`](../ŠABLONY/cursor-rules/rbu-commit-closes-CONTRIBUTING.md)
- Zákaz `/init` AGENTS.md: [`ŠABLONY/cursor-rules/no-agents-md-init.mdc`](../ŠABLONY/cursor-rules/no-agents-md-init.mdc) — v lokálním klonu Universe už zkopírováno (4. 9. 2026); commit/push v RB-Universe zvlášť. Kopie má obsahovat i výjimku: krátká šablona `AGENTS.md` / `CLAUDE.md` na týmovém disku `[EDU] <Tým>` skillem `tymovy-disk` po potvrzení člověkem. Lokální soubor je upravený (6. 10. 2026); commit v RB-Universe pořád zvlášť.

## Kroky (v klonu RB-Universe)

```bash
mkdir -p .cursor/rules
cp /path/to/SECOND_BRAIN/ŠABLONY/cursor-rules/rbu-commit-closes.mdc \
  .cursor/rules/rbu-commit-closes.mdc
# volitelně jednu větu do CONTRIBUTING.md z rbu-commit-closes-CONTRIBUTING.md
git add .cursor/rules/rbu-commit-closes.mdc
git commit -m "chore: Cursor rule — Closes RBU* for Second Brain auto-Done"
git push
```

Bez této rule agent v Cursoru při committech do Universe často vynechá `Closes RBU…` a VPS cron (`lifecycle_github_rbu_closes.py`) nemá co zavřít.
