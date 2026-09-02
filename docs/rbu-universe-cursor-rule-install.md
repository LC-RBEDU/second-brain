# Instalace Cursor rule do RB-Universe

Toto SECOND_BRAIN repo **nemá** write přístup do `RedButtonEDU/RB-Universe`. Rule je připravená zde:

- Zdroj: [`ŠABLONY/cursor-rules/rbu-commit-closes.mdc`](../ŠABLONY/cursor-rules/rbu-commit-closes.mdc)
- Lidská věta: [`ŠABLONY/cursor-rules/rbu-commit-closes-CONTRIBUTING.md`](../ŠABLONY/cursor-rules/rbu-commit-closes-CONTRIBUTING.md)

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
