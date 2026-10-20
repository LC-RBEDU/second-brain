# Red Button EDU – newest (design system, export 2026-10-20)

Zdroj pravdy: design system artefakt "Red Button EDU - newest" v Claude (export je snapshot, nemodifikuj ručně).

Pořadí čtení pro agenta (Cursor / Grok):
1. guidelines/web-ui.md – pravidla pro web a UI (barvy, typografie, tvary, logo)
2. tokens.css (CSS proměnné) nebo tokens.json (strojově) + api/tokens.md (popis)
3. README.md – kompletní popis systému
4. api/components/*.md – seznam komponent (React komponenty jsou v bundlu v Claude; zde jen popisy)
5. guidelines/slides.md – prezentace; guidelines/brand-manual.cs.md – brand manuál
6. guidelines/accessibility.md – známé slabiny kontrastu

Fonty: Rubik (Google Fonts), Permanent Marker pouze CZ-fix verze v fonts/permanentmarker-regular-czech-fix.otf.
Logo: assets/Logos/logo-light-logo.svg (na světlé pozadí). Tmavé varianty loga a 42 ručně kreslených ikon v balíčku NEJSOU – jsou v asset store artefaktu.
Chybí také: React bundle (components/bundle.js/css), papírová textura, ilustrace.
Pravidlo: používej jen schválené komponenty a assety; chybějící prvek nevymýšlej.
