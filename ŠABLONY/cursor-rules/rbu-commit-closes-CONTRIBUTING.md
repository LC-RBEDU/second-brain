# Commit convention — Second Brain Closes (lidská poznámka)

Pro práci krytou úkolem v Second Brain (RB Universe development):

Do commit message nebo PR body (merge do **`dev`**) přidej:

`Closes RBU<N>` nebo `Closes RBU<N>-<krok>` + krátký lidský název.

Příklad: `Closes RBU62-1 — Přidat MCP tools`.

Bez toho se úkol ve vaultu automaticky neuzavře. Epic se přes `Closes` nezavírá.

Agent rule: `.cursor/rules/rbu-commit-closes.mdc`.
