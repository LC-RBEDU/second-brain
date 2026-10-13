# Fetch notes — 2026-10-13

## Co se povedlo

- Firecrawl scrape veřejné stránky artifactu → plný **markdown** snapshot (`design-system.md`), včetně brand manuálu CS/EN, accessibility, web/UI, slides, social kit, token overview.
- Frame CDN bez loginu: `project/tokens.json`, `project/tokens.css`, `project/components/bundle.css`, `project/components/bundle.js`.

## Co nejde bez Claude loginu (HTTP 403)

- Ikony, loga, fonty, fotky, brush frames, network patterns, většina `guidelines/*.card.html` a souborů z panelu „Files 235“.
- Artifact UI: „Sign in to see this artifact’s data“.

## Ruční doplnění assetů

1. Otevři URL z `../SOURCE.url` přihlášený v Claude.
2. Export / download souborů z artifactu (nebo zip, pokud Claude nabídne).
3. Ulož pod `snapshot/assets/` se stejným relativním stromem jako ve frame (`project/assets/...`).
4. Spusť `python3 scripts/refresh_rb_design_system.py --from-markdown snapshot/design-system.md --force` (případně po úpravě MD), ať se přepočítá `bundle_hash`.

## Frame base (ephemeral)

Aktuální base je v `manifest.json` → `frame_base`. Po republish artifactu se `_f/<id>/` může změnit — refresh skript ho znovu vytáhne z markdown odkazů.
