# Red Button Design System

**Red Button** is a Czech ecosystem/network of business professionals — leaders, lecturers, entrepreneurs, experts and change guides — connecting people for 10+ years. Motto: _"Nejsme vzdělávací agentura. Jsme síť."_ (We are not a training agency. We are a network.) Sub-brand **Red Button EDU** partners with companies on people development ("zlepšujeme společnost skrze rozvoj firem" — we improve society through developing companies). Network of 90+ experts. Sub-brands include Exponential Summit, Network, Shortcut, Kniha měsíce, L&D, Eduteka, Circles, B&B, EDU.

**Primary language of all copy: Czech.** Web: www.redbuttonedu.cz · IG: @red\_button\_edu

## Sources

- **Authoritative:**`guidelines/brand-manual.cs.md` — the **complete** Visualbook export (2026-07-22), including the previously-protected sections (client personas, brand rules, tone of voice). English condensation in `guidelines/brand-manual.en.md`.
- `uploads/Red-Button-brand-public-web-20260714-…/` — earlier public-scope export (superseded).
- No codebase or Figma was provided. UI primitives (forms, feedback) are a standard set styled strictly from the manual (see "Intentional additions").

## CONTENT FUNDAMENTALS

- **Czech first.** Casual-expert Czech, direct address. Voice = **experienced, human, bold partner for change**: expert but understandable, human but not familiar, confident but not arrogant. Carries the 4 values #Zájem · #Růst · #Vášeň · #Souhra. English only for punchy program names.
- **Always start with the client's situation, not with us or the product** ("Neprodáváme produkt, ukazujeme změnu"). The format (workshop/academy) is the answer, not the point. Every output ends with a clear next action.
- **Tone axes:** bold not aggressive · human not familiar · practical not banal · smart not academic · current not trendy-for-effect. Full rules + do/don't examples in `guidelines/tone-of-voice.card.html` and manual §13.
- **Audience (ICP):** Leaders (buy the vision — ROI/results language), L&D Owners (gatekeeper/strategist — co-creation + board ammunition), L&D Operations (time-savings, off-the-shelf, deploy in 48h). See `guidelines/personas.card.html` and manual §6.
- **We-voice** ("pomáháme", "věříme", "propojujeme") speaking to **you/your company**. Numbered tips ("3 tipy z praxe", "#1 Změna mindsetu je základ").
- **Casing:** headlines ALL-CAPS Rubik Black; Permanent Marker renders as small-caps handwriting. Kicker labels are red caps or #Hashtags in marker.
- **No emoji** in brand materials. Hand-drawn icons and arrows play that role.
- CTA buttons are short exclamations: "Jdu do toho!", "CTA action!"

## VISUAL FOUNDATIONS

- **Colors:** off-white `#fafafa` dominates (60%), Wine `#a11834` is the brand surface color (20%), Anthracite `#444444` text + dark surfaces (10%), **Red Button `#e4003a` is THE primary brand red / signal accent (5%)**, greys `#b0b2b6`/`#969696` support. Buttons use the same Red Button `#e4003a` (unified 2026-10-09; the former `#e3043a` is kept only as the alias `rb-button-red`). **Dark-mode only** (e.g. Exponential Summit web): Apple Red `#fe1a3f` accent + Red Black `#262626` surface — never on print/branding/merch. Links use Apple Red `#fe1a3f`. **Never place the color logo on Apple Red**; on Wine/dark use the negative (white) logo.
- **Type:** Rubik everywhere. H1 Rubik Black 64px (hero 128px), ALL-CAPS for display headlines; H2 Rubik Extrabold 42px; H3 Rubik Bold 24px; large ¶ Rubik Medium 21px; ¶ Rubik Regular 18px; buttons Rubik Extrabold 16px. Accent font **Permanent Marker** (Czech-fixed OTF in `assets/fonts/`) for subheadings (24/42px), hashtags, quotes, annotations — always Wine or white, never long text. Fallbacks (open decks only): Arial Black/Arial/Kalam. **Slides exception (decision 2026-10-09):** on slides and in Google Slides, including internal decks such as Town hall, hand-written text containing Czech diacritics (ě š č ř ž ů ť ď ň) is set in Kalam Bold, ALL-CAPS, because Permanent Marker does not render them well; see `guidelines/slides.md`. Web, print, branding and merch always use the Czech-fix Permanent Marker.
- **Backgrounds:** flat off-white or subtle paper grain; Wine or Anthracite full-bleed panels for contrast slides/posts. Photography full-bleed with white or wine overlay panels. No gradients.
- **Buttons:** transparent label wrapped in a real hand-drawn **brush frame SVG** (`assets/frames/` — short 504×148 & long 905×149, in red #E3003A / wine #A11834 / grey #B1B3B6). Solid filled button only as fallback on dark/photo surfaces.
- **Motifs:** the hand-drawn **network pattern** (`assets/patterns/`) decorates dead space, always anchored to a corner, recolorable to brand colors, never over faces. Hand-drawn **brush frames** around buttons/panels, **torn-edge banners** (program tags), hand-drawn arrows/underlines/circles from the icon set, and the scribble **bulb** symbol.
- **Photography:** always B&W (or red/wine-toned duotone), real people in context — conversation, collaboration, reflection; smart casual; never stock-feel. Portraits become **cutouts**: irregular hand-painted silhouette frame — wine frame on light bg, white frame on dark bg.
- **Corners & borders:** radius 6px on cards/buttons; borders either subtle `#e2e2e2` or hand-drawn brush strokes in Wine.
- **Shadows:** essentially flat; soft shadow only for floating UI. Buttons/cards sit flat on the page.
- **Hover/press:** manual defines none; convention here — hover darkens red (`#e4003a` → `#a11834`) or lifts opacity, press scales 0.98. Keep subtle.
- **Animation:** manual defines none; keep to quick fades/slides (150–250ms ease-out) if needed.
- **Layout:** generous whitespace, strong left-aligned typographic hierarchy: red kicker caps → ALL-CAPS black headline → marker subheading → body. Logo top-left or top-right, page number bottom-right, net pattern bottom corner.

## ICONOGRAPHY

- **One system only:** 42 hand-drawn marker-stroke SVGs in Wine (`assets/icons/icon-01.svg` … `icon-42.svg`), 500×500. No icon font, no CDN set, no emoji. Recolor via CSS filter or by editing fill. Icons 01–12 are annotation scribbles (ovals, underlines, arrows) used to mark up text like a whiteboard. Keep annotation scribbles small — never scale the underline (03) to full main-headline width; underlines belong under short marker subtitles only.
- Legend: 01 oval-scribble · 02 arrow-up-left · 03 underline · 04 oval-highlight · 05 arrow-bent-down · 06 arrow-squiggle · 07 arrow-s-curve · 08 double-underline · 09 arrow-down-right · 10 arrow-curve-left · 11 circle-scribble · 12 asterisk · 13 map-pin · 14 phone · 15 mail · 16 arrow-right · 17 arrow-down · 18 check · 19 cross · 20 shield · 21 crown · 22 search · 23 compass · 24 presentation · 25 people-group · 26 idea-bulb (brand bulb) · 27 growth-chart · 28 puzzle · 29 gear · 30 arrows-scatter · 31 instagram · 32 facebook · 33 youtube · 34 linkedin · 35 code · 36 road · 37 arrow-up-right · 38 people-pair · 39 checklist · 40 pen · 41 shapes-transform · 42 ellipse
- **Illustrations:** 7 outline program illustrations in Wine (`assets/illustrations/`): target, Charles-bridge, cloud-gears, grad-cap, puzzle, AI badge, tech-book.
- **Logos** (`assets/logos/`): horizontal logo light/dark bg, vertical (alternativní) light/dark, universal symbol (red dot button). Min height 20px screen. Protection zone 50% of logo height. Never rotate/recolor/shadow/deform. Forbidden on Apple Red.

## Web × slides — one system (2026-10-09)

This system now covers digital outputs and presentations; it replaces the separate systems _RB EDU – Web UI_ and _RB EDU – prezentace_. Decisions: values follow the brand manual (Wine ~20 % surface, Red Button `#e4003a` ~5 % accent, one button red); old slide token names live on as aliases (`rb-crimson` → `rb-wine`, `rb-ink` → `rb-anthracite`, `rb-paper` → `rb-off-white` …); token names stay as in this system and the semantic web tokens (`bg`, `surface`, `text`, `action`, `focus`, … with a dark theme) were added.

- Slides: `guidelines/slides.md`, tokens prefixed `slide-*`, assets in group _Slides_.
- Web and UI: `guidelines/web-ui.md`; contrast and known weaknesses: `guidelines/accessibility.md`.

## Index

- `styles.css` → `tokens/` (fonts, colors, typography, spacing)
- `assets/` — logos, fonts, icons (42), illustrations (7), patterns (net ×2), backgrounds, photos
- `guidelines/` — brand manual (cs authoritative / en), specimen cards incl. colors (core, support, semantic, ratio, dark-mode), type, logos, icons, photography, and **voice cards** (tone-of-voice, brand-rules, personas)
- `components/forms/` — Button, IconButton, Input, Select, Checkbox, Radio, Switch
- `components/display/` — Card, Badge, Tag, Tabs
- `components/feedback/` — Dialog, Toast, Tooltip
- `components/brand/` — Logo, Icon, NetPattern, MarkerNote
- `ui_kits/social/` — Instagram post templates kit (SocialPost, PhotoPost + interactive index.html)
- `templates/pitch-deck/` — 16:9 deck template (PitchDeck.dc.html: title, content+photo, wine divider, bullets, quote)
- `guidelines/slides.md`, `guidelines/web-ui.md`, `guidelines/accessibility.md` — rules for presentations, web/UI and contrast
- `assets/Slides/` — slide-specific drawn elements (paper background, header line, corner arc, dotted divider, emphasis strokes, Wine card, dark circle, dot)
- `SKILL.md` — agent skill entry point

No website/app source was provided, so there is no web/app UI kit — the demonstrated brand surfaces are social posts, presentations and print.

## Intentional additions

The manual's own "components" are graphic (icons, illustrations, net pattern, backgrounds, brush frames) — it defines no interactive UI. Since no codebase/Figma was provided, the UI primitives here (forms, feedback, display) are a standard set styled strictly from the manual's colors/type/motifs; their hover/press states, spacing scale and shadows are inferred (flagged above). Copy tone, personas and brand rules are **no longer inferred** — they now come verbatim from the complete export.

## Starters

In the standalone version, this design system came with 1 starter template(s). Each is a small project of its own, not a part of the design system the page shows; its files are kept in this artifact as they were, under its folder, for a later migration of its own.

- **Prezentace Red Button** — 16:9 deck — title, content+photo, wine divider, bullet and quote slides in the brand layout (4 files, entry `templates/pitch-deck/PitchDeck.dc.html`)

## Migrated from a legacy design system

This system was carried over from the standalone version on 2026-09-17. The part of this README the author wrote predates the move, so any file names in it are the old ones. Where things are now:

- `styles.css`, `tokens/fonts.css`, `tokens/colors.css`, `tokens/typography.css`, `tokens/spacing.css` (the global stylesheets) → `project/components/bundle.css`, with the token declarations moved to `project/tokens.json` (`project/tokens.css` is generated from them)
- `_ds_bundle.js` → `project/components/bundle.js`
- showcase pages, each kept whole as one component’s preview (a page of examples, not an export of the bundle): `components/brand/brand.card.html` → `project/components/Brand/preview.html`; `components/display/display.card.html` → `project/components/Display/preview.html`; `components/feedback/feedback.card.html` → `project/components/Feedback/preview.html`; `components/forms/forms.card.html` → `project/components/Forms/preview.html`; `ui_kits/social/index.html` → `project/components/Index/preview.html`; `guidelines/brand-rules.card.html` → `project/components/BrandRules/preview.html`; `guidelines/personas.card.html` → `project/components/Personas/preview.html`
- the migration report, which lists what did not come across: `project/assets/notes/MIGRATION-REPORT.md`

### Přístupnost – známé slabiny manuálu

guidelines/accessibility.md

# Přístupnost – známé slabiny manuálu

Hodnoty jsou převzaté přesně z brand manuálu. Tyto páry nedosahují WCAG AA (4,5:1 pro text, 3:1 pro okraje a ovládací prvky):

- `rb-spanish-grey` jako text na bílé 2,96:1 (tagy, popisky) – jen pro doplňkové údaje.
- `link` (#fe1a3f) na bílé 3,86:1 – odkazy vždy podtržené.
- Okraje polí `border-control` 2,96:1 na bílé.
- Tmavý režim: bílá na Apple Red 3,86:1, Apple Red na Red Black 3,92:1 – jen velký nebo tučný text.
- `rb-grey` jako text na bílé 2,12:1 – nepoužívat pro text na světlém.
- Slidy: staré aliasy `rb-muted` a `rb-subtle` po sloučení ukazují na Spanish Grey (2,96:1). Původní `rb-muted` (#737373) měl 4,1:1. Používej jen pro nedůležité doplňky ve velkém písmu.

Dobré páry: Anthracite na bílé 9,74:1, Wine na bílé 7,79:1, bílá na Wine 7,79:1, bílá na Red Button 4,82:1.

### Red Button — Brand manuál

guidelines/brand-manual.cs.md

# Red Button — Brand manuál

> Kompletní podklad pro AI agenty. Generováno z Visualbooku dne 2026-07-22. Rozsah: Kompletní obsah včetně chráněných sekcí. Jazyk: cs.

* * *

## Obsah

01. Loga
02. Barvy
03. Písma
04. Design Komponenty
05. Ukázky použití
06. Persony klient
07. Loga subbrandů
08. Práce s grafikou
09. Grafické komponenty
10. Práce s fotografií
11. O Red Button
12. Základní pravidla, jak pracovat se značkou
13. Tone of voice Red Button
14. Design tokeny (design stránka)
15. Přiložené soubory

* * *

## 1\. Loga

### Logo

- **Režim pozadí:** Světlé / Tmavé pozadí
- **Barvy pozadí:** světlé: `#ffffff`, tmavé: `#a11834`

- Logo pro světlé pozadí (SVG): `assets/logos/logo-light-logo.svg`
- Logo pro tmavé pozadí (SVG): `assets/logos/logo-dark-logo.svg`
- CMYK na světlé pozadí (PDF): `assets/logos/rb_horizontalni_full_color_cmyk.pdf`
- CMYK na tmavé pozadí (PDF): `assets/logos/rb_horizontalni_negativ_cmyk.pdf`

- **Minimální velikost:** na výšku — obrazovky: 20 px, tisk: 15 mm
- **Ochranná zóna:** aktivní — 50% z výšky loga

- **Čemu se vyhnout:**
- Logo neotáčejte
- Nepoužívejte stíny
- Nepřebarvujte logo
- Nedeformujte ani neměňte původní proporce loga

- **Logo na barevném pozadí:**
- ✅ Povolené: `#fafafa`, `#a11834`, `#444444`
- ❌ Zakázané: `#5b5b5b`, `#e2e2e2`, `#a11834`, `#fe1a3f`, `#fe1a3f`

- **Logo na obrazovém pozadí:**
- ✅ Povoleno — pozadí: `assets/images/background.png` — logo: `assets/logos/logo-dark-logo.svg` — typ loga: neuvedeno
- ✅ Povoleno — pozadí: `assets/images/background-red.png` — logo: `assets/logos/logo-dark-logo.svg` — typ loga: neuvedeno
- ❌ Zakázáno — pozadí: `assets/images/background-red.png` — logo: `assets/logos/logo-light-logo.svg` — typ loga: neuvedeno
- ❌ Zakázáno — pozadí: `assets/images/background.png` — logo: `assets/logos/logo-light-logo.svg` — typ loga: neuvedeno

### Symbol

- **Režim pozadí:** Univerzální pozadí (`#ffffff`)

- Univerzální logo (SVG): `assets/logos/logo-universal-symbol.svg`
- CMYK pro univerzální pozadí (PDF): `assets/logos/rb_piktogram_full_color_cmyk.pdf`

- **Minimální velikost:** na výšku — obrazovky: 20 px, tisk: 15 mm
- **Ochranná zóna:** aktivní — 50% z výšky loga

- **Čemu se vyhnout:**
- Nepřebarvujte logo
- Nedeformujte ani neměňte původní proporce loga

- **Logo na barevném pozadí:**
- ✅ Povolené: `#ffffff`, `#a11834`, `#444444`
- ❌ Zakázané: `#fe1a3f`

- **Logo na obrazovém pozadí:**
- ✅ Povoleno — pozadí: `assets/images/background.png` — logo: `assets/logos/logo-universal-symbol.svg` — typ loga: neuvedeno
- ✅ Povoleno — pozadí: `assets/images/background-red.png` — logo: `assets/logos/logo-universal-symbol.svg` — typ loga: neuvedeno

### Alternativní

- **Režim pozadí:** Světlé / Tmavé pozadí
- **Barvy pozadí:** světlé: `#ffffff`, tmavé: `#a11834`

- Logo pro světlé pozadí (SVG): `assets/logos/logo-light-alternativni.svg`
- Logo pro tmavé pozadí (SVG): `assets/logos/logo-dark-alternativni.svg`
- CMYK na světlé pozadí (PDF): `assets/logos/rb_vertikalni_full_color_cmyk.pdf`
- CMYK na tmavé pozadí (PDF): `assets/logos/rb_vertikalni_negativ_cmyk.pdf`

- **Minimální velikost:** na výšku — obrazovky: 24 px, tisk: 10 mm
- **Ochranná zóna:** aktivní — 50% z výšky loga

- **Čemu se vyhnout:**
- Nepoužívejte stíny
- Logo neotáčejte
- Nepřebarvujte logo
- Nedeformujte ani neměňte původní proporce loga

- **Logo na barevném pozadí:**
- ✅ Povolené: `#ffffff`, `#a11834`, `#444444`
- ❌ Zakázané: `#666666`, `#fe1a3f`, `#fe1a3f`, `#a11834`

- **Logo na obrazovém pozadí:**
- ✅ Povoleno — pozadí: `assets/images/background.png` — logo: `assets/logos/logo-dark-alternativni.svg` — typ loga: neuvedeno
- ✅ Povoleno — pozadí: `assets/images/background-red.png` — logo: `assets/logos/logo-dark-alternativni.svg` — typ loga: neuvedeno
- ❌ Zakázáno — pozadí: `assets/images/background-red.png` — logo: `assets/logos/logo-light-alternativni.svg` — typ loga: neuvedeno
- ❌ Zakázáno — pozadí: `assets/images/background.png` — logo: `assets/logos/logo-light-alternativni.svg` — typ loga: neuvedeno

## 2\. Barvy

### Primární barvy

**Legenda tabulky:** Řádek = jedna barva. Sloupce HEX / RGB / CMYK / Pantone (C coated, U uncoated) / RAL / NCS popisují stejný odstín různými systémy.

| Název | HEX | RGB | CMYK | Pantone C | Pantone U | RAL | NCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Red Button | #e4003a | 228, 0, 58 | 0-100-75-11 | 192 C | — | — | — |
| Wine | #a11834 | 161, 24, 52 | 25 \| 100 \| 70 \| 20 | 56-8 C | — | — | — |
| Anthracite | #444444 | 68, 68, 68 | 00 \| 00 \| 00 \| 85 | 179-14 C | — | — | — |
| White | #ffffff | 255, 255, 255 | 0 \| 0 \| 0 \| 0 | 000 C | — | — | — |

### Podpůrné barvy

**Legenda tabulky:** Řádek = jedna barva. Sloupce HEX / RGB / CMYK / Pantone (C coated, U uncoated) / RAL / NCS popisují stejný odstín různými systémy.

| Název | HEX | RGB | CMYK | Pantone C | Pantone U | RAL | NCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Grey | #b0b2b6 | 176, 178, 182 | 00 \| 00 \| 00 \| 35 | P174-1 C | — | — | — |
| Spanish Grey | #969696 | 150, 150, 150 | 40 \| 32 \| 33 \| 1 | P 179-7 C | — | — | — |

### Poměry barev

Proporcionální použití barev v rámci vizuálního stylu. Sekce je v novém, vylepšeném designu.

**Typ zobrazení:** jeden univerzální poměr barev **Legenda tabulky:** Podíl (sloupec Zastoupení) vyjadřuje, kolik místa by měla barva v paletě zabírat — typicky v procentech.

| Název barvy | HEX | Zastoupení |
| --- | --- | --- |
| White | #fafafa | 60% |
| Wine | #a11834 | 20% |
| Anthracite | #444444 | 10% |
| Red Button | #e4003a | 5% |
| Spanish Grey | #b0b2b6 | 3% |
| Spanish Grey | #969696 | 2% |

### Úprava barev pro Dark Mode

Pro výjimečné použití dark mode (např. web Exponential Summit) používáme místo Red Button červené jako akcent Apple Red. pro tmavé plochy pak slouží barva Red Black.

**Legenda tabulky:** Řádek = jedna barva. Sloupce HEX / RGB / CMYK / Pantone (C coated, U uncoated) / RAL / NCS popisují stejný odstín různými systémy.

| Název | HEX | RGB | CMYK | Pantone C | Pantone U | RAL | NCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Apple Red | #fe1a3f | 254, 26, 63 | 00 \| 100 \| 70 \| 00 | 1788 C | — | — | — |
| Red Black | #262626 | 38, 38, 38 | — | — | — | — | — |

## 3\. Písma

### Rubik Black

Používáme pro hlavní nadpisy a názvy

- **Stáhnout z Google Fonts:** https://fonts.google.com/specimen/Rubik

**Používané řezy písma:** Black (900)

### Permanent Marker

Používáme pro podnadpisy, nadpisy boxů, přímou řeč a citace.

**Upozornění:** Tento font běžně dostupný na Google Fonts je lokalizovaný do češtiny s několika upravenými speciálními znaky. Vždy stahujte font z tohoto manuálu.

- **Stáhnout Font:**`assets/fonts/permanentmarker-regular-czech-fix.otf`

### Rubik Rergular

Používáme pro běžný odstavcový text. Regular - tagy, popisky apod. v kombinaci se Spanish Grey barvou Medium - běžný body text Bold - tučně zvýrazněný text

- **Stáhnout z Google Fonts:** https://fonts.google.com/specimen/Rubik

**Používané řezy písma:** Medium (500), Medium Italic (500), Bold (700), Bold Italic (700), Regular Italic (400), Regular (400)

### Styly textu

**Obrázek:** !\[\](assets/images/textove-styly.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

### Pravidla pro otevřené prezentace

**Upozornění:** Posíláte otevřenou prezentaci klientovi v Google Slides nebo PPTX? Aplikujte toto pravidlo.

<p>Toto pravidlo se používá jen ve vyjímečných případech zasílání otevřených prezentací klientům. Alternativní písmo nikdy nepoužíváme na oficiálních materiálech - tisk, branding, merch atp. </p>

- Nadpisy: Rubik → Arial Black
- Text: Rubik → Arial
- Akcentové písmo: Permanent Marker → Kalam (Google Slides) / Trebuchet Bold (PowerPoint)

## 4\. Design Komponenty

### Ikony

Tyto ručně kreslené ikonky použijte mimo jejich běžný účel také k upoutání pozornosti k specifické informaci skrze grafické materiály, zvýraznění textu (např. zakroužkování a podtržítka) nebo jako dekoraci do mrtvého prostoru.

\[blocked image: not a data: URI\]

### Ilustrace

Tyto ilustrace jsou vytvořené specificky k představení programů Red Button. Použítí je vhodné na větším formátu než ikony. Mohou uvozovat např. slidy prezentací a nabídek.

\[blocked image: not a data: URI\]

### Vzor sítě

Vzor sítě používáme jako jeden z brand symbolů zvyšující rozpoznatelnost značky. Používáme ho k dekoraci především v mrtvém prostoru.

\[blocked image: not a data: URI\]

### Pozadí

Tyto textury jsou alternativní plochou do všech pozadí. Především v prezentacích, tiskových materiálech nebo grafice pro sociální sítě. Na webu může být vhodnější použít CSS styl.

\[blocked image: not a data: URI\]

### Ostatní elementy

Ostatní elementy použitelné pro různé účely.

\[blocked image: not a data: URI\]

## 5\. Ukázky použití

### Identita v akci

* * *

**Položka** (1/6)

**Obrázek:** !\[\](assets/images/aplikace.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

* * *

**Položka** (2/6)

**Obrázek:** !\[\](assets/images/open-single-catalog-mockup-template-6a064b9f4a726a7a1ff49c43--2x2-800x.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

* * *

**Položka** (3/6)

**Obrázek:** !\[\](assets/images/ig-sablony.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

* * *

**Položka** (4/6)

**Obrázek:** !\[\](assets/images/ig.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

* * *

**Položka** (5/6)

**Obrázek:** !\[\](assets/images/ipad-pro-12.9-inch-mockup-6a0653a34a726a7a1ff49c53--2x.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

* * *

**Položka** (6/6)

**Obrázek:** !\[\](assets/images/image-gigapixel-standard-v2-2x.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

## 6\. Persony klient

### Leaders

\[blocked image: not a data: URI\]

### Kdo to je (Demografie &amp; Role)

<p><strong>Motto:</strong> <em>"Svět se mění, moje firma ne dost rychle. Potřebuji parťáka pro byznys, ne školení pro zaměstnance."</em> 1</p><p><strong>Role:</strong> C-Level (CEO, CFO, COO), majitelé firem, ředitelé divizí/Business Unit Leaders, transformační lídři 2, 3.</p><p><strong>Velikost firmy:</strong> Primárně firmy s obratem <strong>nad 250 mil. Kč</strong> a 250+ zaměstnanci 4, 5.</p><p><strong>Rozhodovací pravomoc:</strong> Mají přímou P&amp;L (Profit &amp; Loss) zodpovědnost. <strong>Mají vlastní budget</strong> a hlavní rozhodovací slovo 6, 7.</p><p><strong>Klíčová charakteristika:</strong> Nejsou z HR/L&amp;D oddělení. Často ani "nechtějí řešit vzdělávání", chtějí řešit <strong>výsledky, efektivitu a změnu</strong> 8.</p>

### Co je budí ze spaní (Pain Points &amp; Psychografie)

<p>Marketing a Sales musí adresovat tyto emoce a bariéry:</p><p><strong>Strategická nejistota &amp; FOMO:</strong> Cítí, že jim ujíždí vlak (AI, technologie, inovace) a nevědí, jak firmu rychle adaptovat. <em>"Nevím si s tím rady, potřebuji data místo dojmů."</em> 1, 9.</p><p><strong>Frustrace z interního HR:</strong> Mají pocit, že jim interní HR/L&amp;D <em>"nosí nesmysly"</em> a postrádá byznysový kontext. Cítí propast mezi strategií boardu a realitou ve firmě 1, 10.</p><p><strong>Osamělost a přetížení:</strong> <em>"Jsem na to sám."</em> Cítí se zahlceni operativou a byrokracií, ztrácejí energii. Hledají rovnocenné parťáky pro diskuzi, které uvnitř firmy nemají 1, 11, 12.</p><p><strong>Potřeba rychlých výsledků:</strong> Nemají čas na roční analýzy. Potřebují <strong>Quick Wins</strong>, aby obhájili změnu před investory nebo centrálou 1, 13.</p>

### Co reálně kupují (Job to be Done)

<p>Nekupují "kurzy". Kupují <strong>řešení problému a klid</strong>.</p><p><strong>Model "Mr. Wolf" (Řešení na klíč):</strong> Chtějí problém pustit z hlavy. <em>"Tady máte zadání (např. naučte nás 3D tisk/AI), vyřešte to, já chci vidět výsledek."</em> 14, 15.</p><p><strong>Transformace mindsetu:</strong> Nechtějí jen naučit lidi "klikat v Excelu", chtějí změnit kulturu a myšlení lidí, aby firma přežila 14, 16.</p><p><strong>Validace &amp; Benchmark:</strong> Chtějí vidět, jak to dělají ti nejlepší na trhu (Best Practices), aby si ověřili, že nejdou špatným směrem 17.</p><p><strong>Exkluzivní komunita:</strong> Kupují vstupenku mezi sobě rovné (Exponential Circles), kde mohou bezpečně sdílet své "fuckupy" bez přítomnosti médií 18, 19.</p>

### Strategie pro Sales (Jak prodávat)

<p><strong>Přístup "Consultative Sales":</strong> Neprodáváme z katalogu. Sales musí vést strategický dialog o byznysu klienta, ne o parametrech školení 7.</p><p><strong>Jazyk:</strong> Mluvit jazykem <strong>výsledků, ROI, efektivity a rizika</strong>. Vyhýbat se "měkkému" HR jazyku 2, 19.</p><p><strong>Dual Target Strategy:</strong> Leaders jsou ti, kdo <em>kupují</em> (drží peníze), ale L&amp;D Owners jsou ti, kdo to <em>procesují</em>. Sales musí získat Leadera pro vizi, ale neodříznout L&amp;D, které to musí exekvovat 20.</p><p><strong>Důvěra přes osobnosti:</strong> Klíčovým prodejním argumentem je <strong>kdo</strong> to bude dělat. Leaders kupují experty z praxe (praktici, ne teoretici), nikoliv bezejmenné lektory 21, 22.</p>

### Zadání pro Marketing (Klíčové message)

<p><strong>Brand Positioning:</strong> Red Button EDU jako <strong>"Hasiči i Stavitelé"</strong>. Umíme vyřešit akutní problém, ale i postavit dlouhodobou architekturu rozvoje 23.</p><p><strong>Hlavní kanál:</strong> <strong>Exponential Circles Summit</strong> a komunita. Toto je "výkladní skříň", kam musíme Leadery dostat, aby zažili "Red Button efekt" 24, 25.</p><p><strong>Argumentace (Reason to Believe):</strong></p><p><strong><em>Ekosystém:</em> "Známe lidi, co znají lidi." (Vyřešíme cokoliv díky síti) 14.</strong></p><p><strong><em>Track Record:</em> Děláme to pro největší hráče (Tatra banka, Škoda, ČEZ) 26.</strong></p><p><strong><em>Autenticita:</em> Žádný korporátní bullshit, jdeme k věci 19.</strong></p><p><strong>Vizuál &amp; Tón:</strong> Prémiový, sebevědomý, byznysový. Odlišení od "barevného a hravého" marketingu pro juniorní HR 27.</p>

### Vstupní produkty (Entry Offers)

<p>Co jim nabídnout jako první krok ke spolupráci:</p><p><strong>Exponential Circles:</strong> Vstup do komunity nebo účast na Summitu 28.</p><p><strong>R(e)BeLeader:</strong> Program pro ně samotné nebo jejich klíčové talenty (B-1) 29.</p><p><strong>Business Case Sprint / Audit:</strong> Rychlá diagnostika problému ve firmě (např. AI readiness, kulturní audit) s návrhem řešení 7.</p><p><strong>Strategická konzultace:</strong> 1:1 setkání s expertem ze sítě (např. Jan Mašek, Luboš Malý) nad konkrétní výzvou 30.</p>

### ⚠️ Red Flags (Co nedělat)

<p><strong>Neposílat katalog školení:</strong> To je urazí nebo to delegují a zapadne to.</p><p><strong>Neřešit operativu:</strong> Nezatěžovat je detaily, jak bude probíhat catering nebo přihlašování účastníků.</p><p><strong>Nenabízet "krabicová řešení":</strong> Vždy musí mít pocit, že je to řešení jejich unikátního problému 14.</p>

### L&D Owners

### L&amp;D OWNERS (Vlastníci agendy &amp; Stratégové)

<p><strong>Motto:</strong> <em>„Potřebuji, aby mě byznys bral vážně. Nechci být jen objednávka školení, chci být architektem změny a potřebuji partnera, který mi pomůže to obhájit před boardem.“</em></p>

### Kdo to je (Demografie &amp; Role)

<p><strong>Role:</strong> Head of L&amp;D, Senior HR Manager, HR Director (v korporacích), Talent Development Manager.</p><p><strong>Velikost firmy:</strong> Velké organizace a korporace (1000+ zaměstnanců), firmy s obratem nad 250 mil. Kč.</p><p><strong>Rozhodovací pravomoc:</strong> <strong>Disponují vlastním rozpočtem</strong> (často v řádech milionů) a mají mandát o něm rozhodovat nebo jej silně ovlivňují (spolurozhodují s Leaders).</p><p><strong>Klíčová charakteristika:</strong> Jsou to experti. Rozumí vzdělávání, znají trendy, mají týmy (L&amp;D Operations). Nechtějí „koupit školení“, chtějí „postavit systém“.</p>

### Co je budí ze spaní (Pain Points &amp; Psychografie)

<p>Marketing a Sales musí adresovat jejich potřebu prestiže a relevance:</p><p><strong>Boj o relevanci (Seat at the table):</strong> Cítí tlak, aby je byznys (Leaders) bral vážně. Bojí se, že budou vnímáni jen jako „podpora“ nebo „sluníčkáři“, co utrácejí peníze bez efektu.</p><p><strong>Tlak na obhajobu budgetu:</strong> Musí každoročně bojovat o peníze. Děsí je otázka CFO: <em>„A co nám to přineslo?“</em> Potřebují data a argumenty, které nemají.</p><p><strong>Osamělost v roli:</strong> Často nemají uvnitř firmy rovnocenného partnera pro odbornou diskuzi o rozvoji. Cítí se izolovaní mezi tlakem shora (výsledky) a tlakem zdola (nespokojení zaměstnanci).</p><p><strong>Strach z chyby:</strong> Nechtějí vybrat dodavatele, který udělá ostudu před boardem (např. trapný lektor). Hledají sázku na jistotu.</p>

### Co reálně kupují (Job to be Done)

<p>Nekupují „kurzy“. Kupují <strong>partnerství, jistotu a svou vlastní reputaci</strong>.</p><p><strong>Strategické partnerství:</strong> Hledají někoho, kdo jim pomůže nadefinovat strategii rozvoje tak, aby dávala smysl byznysu. Chtějí „Capability Building“ – systémový rozvoj, ne jednorázovky.</p><p><strong>Argumentace pro Board (Munice):</strong> Kupují si vaše data (RB Index), vaše jméno a vaši schopnost prodat to interně jejich šéfům. Potřebují, abyste vy (Red Button) byli ti, kdo řekne nepříjemnou pravdu CEO, kterou oni říct nemohou.</p><p><strong>Expertní know-how na klíč:</strong> Potřebují vyřešit komplexní témata (AI adopce, změna kultury, digitální transformace), na která interně nestačí.</p><p><strong>Komunita a inspirace:</strong> Kupují si přístup k <em>L&amp;D komunitě</em>, kde mohou sdílet best-practice s lidmi na stejné úrovni (peer-learning).</p>

### Strategie pro Sales (Jak prodávat)

<p><strong>Přístup „Co-creation“ (Spolutvorba):</strong> L&amp;D Owners jsou experti. Nesmíte je poučovat. Musíte s nimi tvořit řešení. <em>„Pojďme společně nadesignovat, jak to u vás bude fungovat.“</em> </p><p><strong>Role „Buddy &amp; Ally“:</strong> Sales a Delivery (např. Key Account Manager) musí fungovat jako jejich spojenec. Pomáháme jim zazářit před jejich šéfy. <em>„Připravíme vám podklady pro board.“</em></p><p><strong>Jazyk:</strong> Používat terminologii L&amp;D (kompetenční modely, learning pathways, LXP, 70-20-10) pro potvrzení expertízy, ale kombinovat ji s jazykem byznysu (ROI, impact) </p><p><strong>Důkaz kvality:</strong> Ukazovat <em>track record</em> a <em>case studies</em> z podobně velkých firem (Tatra banka, Škoda). Reference jsou pro ně klíčové pro snížení rizika.</p>

### Zadání pro Marketing (Klíčové message)

<p><strong>Brand Positioning:</strong> Red Button EDU jako <strong>„Architekt vzdělávacích ekosystémů“</strong>. Nejsme jen dodavatel, jsme váš strategický partner pro Capability Building.</p><p><strong>Hlavní kanál:</strong> <strong>L&amp;D Komunita</strong> a LinkedIn. Obsah musí být expertní (whitepapery, trendy, data z trhu), ne jen prodejní.</p><p><strong>Argumentace (Reason to Believe):</strong></p><p><em>Komplexita:</em> Umíme vše od A do Z (leadership, digi, kultura) pod jednou střechou.</p><p><em>Měření:</em> Máme RB Index – umíme změřit to, co vy potřebujete vykázat.</p><p><em>Síť:</em> Máme nejlepší experty na trhu (ne teoretiky), kteří to u vás odmakají.</p><p><strong>Vizuál &amp; Tón:</strong> Profesionální, expertní, ale s lidskou tváří (Humanity + Technology). Partner, ne korporát.</p>

### Vstupní produkty (Entry Offers)

<p>Co jim nabídnout jako první krok ke spolupráci:</p><p><strong>L&amp;D Scan / Audit:</strong> Analýza současného stavu vzdělávání ve firmě a doporučení strategie.</p><p><strong>Pilotní akademie (Pilot Track):</strong> Menší program pro vybranou skupinu (např. High Potentials), na kterém si ověří kvalitu a dopad.</p><p><strong>Vstup do L&amp;D Komunity:</strong> Pozvánka na setkání, kde mohou nasát atmosféru a know-how.</p><p><strong>Konzultace strategie:</strong> Workshop s expertem (např. na AI nebo kulturu) pro nadefinování směru.</p>

### ⚠️ Red Flags (Co nedělat)

<p><strong>Neobcházet je (Bypass):</strong> Nikdy nejděte rovnou za CEO, pokud už máte vztah s L&amp;D. Budou se cítit ohroženi a zablokují vás. L&amp;D Owner je váš <em>gatekeeper</em> a musí být na vaší straně.</p><p><strong>Nenabízet „krabice“ bez kontextu:</strong> Pokud jim pošlete jen ceník kurzů, zařadí vás do škatulky „školící agentura“ a nebudou s vámi řešit strategii.</p><p><strong>Nepodceňovat jejich expertízu:</strong> Mnozí z nich jsou velmi zkušení. Sales s nimi musí vést rovnocenný dialog, ne je „školit“.</p>

### L&D Opertions

\[blocked image: not a data: URI\]

<p><strong>Motto:</strong> <em>„Jsem přetížený/á operativou. Potřebuji, aby to hlavně fungovalo, lidi to bavilo (vysoký engagement) a dodavatel udělal většinu administrativy za mě. Potřebuji data, abych to obhájil/a u šéfa.“</em></p>

### Kdo to je (Demografie &amp; Role)

<p><strong>Role:</strong> L&amp;D Specialista, Training Coordinator, HR Generalist (v menších firmách), HR Business Partner (řešící operativu), správce LMS/LXP platformy.</p><p><strong>Velikost firmy:</strong> Průřezově – od HR manažerů v SME (do 250 lidí) po specialisty v korporacích, kteří mají na starosti dílčí agendu (např. digitální školení).</p><p><strong>Rozhodovací pravomoc:</strong> Často <strong>nemají vlastní budget</strong> nebo jen malý na operativní nákupy. Fungují jako <strong>Evaluator</strong> (průzkumník) nebo <strong>Influencer</strong> – dělají předvýběr dodavatelů, připravují podklady pro L&amp;D Ownera/Leadera, ale finálně nepodepisují velké kontrakty.</p><p><strong>Klíčová charakteristika:</strong> Jsou zavaleni administrativou. Nevěnují se lidem individuálně (koučink), ale řeší systémy, logistiku a proces.</p>

### Co je budí ze spaní (Pain Points &amp; Psychografie)

<p>Marketing a Sales musí adresovat jejich přetížení a strach z nezájmu zaměstnanců:</p><p><strong>Overload (Přetížení &amp; Nestíhání):</strong> Mají toho moc, řeší operativu (pozvánky, catering, faktury), chybí jim kapacity. Děsí je představa, že nový dodavatel jim přidá práci navíc.</p><p><strong>Noční můra „Prázdná židle“ (Engagement):</strong> Bojí se, že objednají školení/platformu a <strong>nikdo tam nepřijde</strong> nebo se nepřihlásí. Potřebují „zařídit zázrak“ (Amazon efekt) – aby to lidi bavilo a sami chtěli.</p><p><strong>Technologická frustrace:</strong> Řeší nefunkční LMS, složité integrace, importy uživatelů. Potřebují nástroje, které fungují „na kliknutí“ a ušetří jim ruční práci.</p><p><strong>Tlak na reporting:</strong> Šéf (L&amp;D Owner) po nich chce čísla (kdo to viděl, kolik lidí prošlo). Pokud nemají data na jedno kliknutí, je to pro ně peklo.</p>

### Co reálně kupují (Job to be Done)

<p>Nekupují „transformaci“. Kupují <strong>úsporu času, atraktivní obsah a hotové podklady</strong>.</p><p><strong>Seamless Integration (Bezstarostnost):</strong> Chtějí dodavatele, který udělá práci za ně. <em>„Naimportujte nám lidi, pošlete jim pozvánky, vyřešte techniku.“</em> Kupují si čas a klid.</p><p><strong>Hotové produkty (Off-the-shelf):</strong> <strong>EDUtéka</strong> (900+ videí ihned k dispozici), katalogové workshopy, materiály z vysílání. Nechtějí nic složitě designovat, chtějí to hned nasadit.</p><p><strong>Podklady pro interní prodej:</strong> Potřebují munici (prezentace, data, argumenty), aby to prodali svému šéfovi (L&amp;D Ownerovi). Kupují si jistotu, že před šéfem nebudou vypadat hloupě.</p><p><strong>User Experience (UX):</strong> Kupují věci, které „hezky vypadají“ a jsou jednoduché pro koncové uživatele (zaměstnance), aby nemuseli řešit stížnosti typu „nejde mi se přihlásit“ </p>

### Strategie pro Sales (Jak prodávat)

<p><strong>Přístup „Support &amp; Educate“:</strong> Sales musí fungovat jako jejich asistent. <em>„Tady máte připravený e-mail pro šéfa, tady je PDF srovnání, tady je dashboard.“</em> Usnadněte jim rozhodování.</p><p><strong>Rychlost a jednoduchost:</strong> Zdůrazňovat <strong>nasazení do 48 hodin</strong> (u EDUtéky), žádné složité IT projekty. Ukažte jim, že to nebude bolet.</p><p><strong>Discovery otázky:</strong> Ptejte se na to, jak jim ušetříte práci. <em>„Kolik času trávíte reportováním?“, „Jak řešíte zvaní lidí?“</em>.</p><p><strong>Demo, ne vize:</strong> Ukažte jim konkrétně, jak to vypadá (platforma, video). Nechtějí slyšet o strategii 2030, chtějí vidět, jak se z toho exportuje Excel.</p>

### Zadání pro Marketing (Klíčové message)

<p><strong>Brand Positioning:</strong> Red Button EDU (resp. produkty jako EDUtéka) jako <strong>„Nástroj, který šetří práci HR“</strong>.</p><p><strong>Hlavní claimy:</strong></p><p><em>„6 hodin měsíčně šetříme HR.“</em></p><p><em>„Nasazení do 48 hodin.“</em></p><p><em>„Vše jednoduše na jednom místě. Žádné složité IT projekty.“</em> </p><p><strong>Argumentace (Reason to Believe):</strong></p><p><em>Automation:</em> Automatické notifikace, reporting, importy.</p><p><em>Engagement:</em> „Lidi to baví“ (vysoké NPS 80, 90% retence klientů) – důkaz, že nebudou mít prázdné židle.</p><p><strong>Vizuál &amp; Tón:</strong> Praktický, přehledný, návodný (tutorial style). Méně abstraktní „transformace“, více screenshotů a konkrétních ukázek.</p>

### Vstupní produkty (Entry Offers)

<p>Co jim nabídnout jako první krok (často produkty s fixní cenou, které projdou pod radarem velkých schvalování):</p><p><strong>EDUtéka (Basic/Premium):</strong> Ideální „krabicové“ řešení pro okamžité doplnění vzdělávání.</p><p><strong>Jednorázové workshopy:</strong> Konkrétní téma (např. AI, Feedback) s jasnou cenovkou.</p><p><strong>Odemčené snídaně (Brain&amp;Breakfast):</strong> Obsah zdarma nebo za malý poplatek na vyzkoušení, který mohou poslat lidem.</p><p><strong>Mini akademie / Pilot:</strong> Krátký program (6 týdnů), kde si ověří, že to funguje a lidi to baví, než půjdou za šéfem pro velký budget.</p>

### ⚠️ Red Flags (Co nedělat)

<p><strong>Nezatěžovat je strategií:</strong> Pokud začnete mluvit o „Capability Building“ a transformaci mindsetu, ztratí se. Potřebují vyřešit to, že manažeři neumí dávat zpětnou vazbu, teď hned.</p><p><strong>Nepřidělávat práci:</strong> Pokud implementace vyžaduje týdny nastavování, odmítnou to.</p><p><strong>Nepodceňovat jejich roli gatekeepera:</strong> I když nerozhodují o milionech, mohou vás zablokovat, pokud se jim systém nebude líbit nebo jim bude připadat složitý. Musíte je získat na svou stranu jako „vnitřního ambasadora“.</p>

## 7\. Loga subbrandů

### Exponential Summit

Logo pro Exponential Summit.

\[blocked image: not a data: URI\]

* * *

**Tlačítka pod galerií:**

- **Balíček loga Exponential Summit:**`assets/others/exponential_summit.zip`

### Ostatní

Loga všech subbrandů a aktivit.

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

* * *

**Tlačítka pod galerií:**

- **Balíček log subbrandů:**`assets/others/logo-subbrandy.zip`

## 8\. Práce s grafikou

### Příklad layoutu tiskoviny

**Obrázek:** !\[\](assets/images/layout.webp)

### Příklad layoutu prezentace

**Obrázek:** !\[\](assets/images/snimek-obrazovky-2026-05-15-v9.14.18.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

### Povolené barevné kombinace

**Legenda pravidel** (stav použití položky v galerii):

- **zakázáno** — nevhodný příklad (na webu se zobrazí přeškrtnutí).
- **povoleno** — správný příklad (na webu ikona ✓).
- **bez pravidel** — neutrální zobrazení, bez přeškrtnutí ani ✓.

* * *

**Položka galerie** (1/10)

**Obrázek:** !\[\](assets/images/pozadi-default.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (2/10)

**Obrázek:** !\[\](assets/images/pozadi-default-1.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (3/10)

**Obrázek:** !\[\](assets/images/pozadi-default-2.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (4/10)

**Obrázek:** !\[\](assets/images/pozadi-anthracite.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (5/10)

**Obrázek:** !\[\](assets/images/pozadi-anthracite-1.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (6/10)

**Obrázek:** !\[\](assets/images/pozadi-red.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (7/10)

**Obrázek:** !\[\](assets/images/pozadi-dark-red.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (8/10)

**Obrázek:** !\[\](assets/images/group-1484579124.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (9/10)

**Obrázek:** !\[\](assets/images/group-1484579126.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

* * *

**Položka galerie** (10/10)

**Obrázek:** !\[\](assets/images/group-1484579125.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** povoleno

### Zakázané barevné kombinace

**Legenda pravidel** (stav použití položky v galerii):

- **zakázáno** — nevhodný příklad (na webu se zobrazí přeškrtnutí).
- **povoleno** — správný příklad (na webu ikona ✓).
- **bez pravidel** — neutrální zobrazení, bez přeškrtnutí ani ✓.

* * *

**Položka galerie** (1/6)

**Obrázek:** !\[\](assets/images/prace-s-grafikou/pozadi-default.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** zakázáno

* * *

**Položka galerie** (2/6)

**Obrázek:** !\[\](assets/images/prace-s-grafikou/pozadi-anthracite.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** zakázáno

* * *

**Položka galerie** (3/6)

**Obrázek:** !\[\](assets/images/prace-s-grafikou/pozadi-red.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** zakázáno

* * *

**Položka galerie** (4/6)

**Obrázek:** !\[\](assets/images/pozadi-red-1.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** zakázáno

* * *

**Položka galerie** (5/6)

**Obrázek:** !\[\](assets/images/prace-s-grafikou/pozadi-dark-red.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** zakázáno

* * *

**Položka galerie** (6/6)

**Obrázek:** !\[\](assets/images/pozadi-dark-red-1.webp) **Popisek tohoto obrázku:** _(bez textového popisku)_ **Pravidlo:** zakázáno

## 9\. Grafické komponenty

### Ikony

Stáhněte si ikonky v požadované barvě

**Tip:** Ikonky můžete přebarvovat dle bradnových barev.

**Legenda:** Seznam ikon v manuálu — tučný text je název souboru, zpětné apostrofy obsahují relativní cestu v exportu.

- **rb-500x500\_tucne-01-4.svg:**`assets/images/rb-500x500_tucne-01-4.svg`
- **rb-500x500\_tucne-02-4.svg:**`assets/images/rb-500x500_tucne-02-4.svg`
- **rb-500x500\_tucne-03-4.svg:**`assets/images/rb-500x500_tucne-03-4.svg`
- **rb-500x500\_tucne-04-4.svg:**`assets/images/rb-500x500_tucne-04-4.svg`
- **rb-500x500\_tucne-05-4.svg:**`assets/images/rb-500x500_tucne-05-4.svg`
- **rb-500x500\_tucne-06-4.svg:**`assets/images/rb-500x500_tucne-06-4.svg`
- **rb-500x500\_tucne-07-4.svg:**`assets/images/rb-500x500_tucne-07-4.svg`
- **rb-500x500\_tucne-08-4.svg:**`assets/images/rb-500x500_tucne-08-4.svg`
- **rb-500x500\_tucne-09-4.svg:**`assets/images/rb-500x500_tucne-09-4.svg`
- **rb-500x500\_tucne-10-4.svg:**`assets/images/rb-500x500_tucne-10-4.svg`
- **rb-500x500\_tucne-11-4.svg:**`assets/images/rb-500x500_tucne-11-4.svg`
- **rb-500x500\_tucne-12-4.svg:**`assets/images/rb-500x500_tucne-12-4.svg`
- **rb-500x500\_tucne-13-4.svg:**`assets/images/rb-500x500_tucne-13-4.svg`
- **rb-500x500\_tucne-14-4.svg:**`assets/images/rb-500x500_tucne-14-4.svg`
- **rb-500x500\_tucne-15-4.svg:**`assets/images/rb-500x500_tucne-15-4.svg`
- **rb-500x500\_tucne-16-4.svg:**`assets/images/rb-500x500_tucne-16-4.svg`
- **rb-500x500\_tucne-17-4.svg:**`assets/images/rb-500x500_tucne-17-4.svg`
- **rb-500x500\_tucne-18-4.svg:**`assets/images/rb-500x500_tucne-18-4.svg`
- **rb-500x500\_tucne-19-4.svg:**`assets/images/rb-500x500_tucne-19-4.svg`
- **rb-500x500\_tucne-20-4.svg:**`assets/images/rb-500x500_tucne-20-4.svg`
- **rb-500x500\_tucne-21-4.svg:**`assets/images/rb-500x500_tucne-21-4.svg`
- **rb-500x500\_tucne-22-4.svg:**`assets/images/rb-500x500_tucne-22-4.svg`
- **rb-500x500\_tucne-23-4.svg:**`assets/images/rb-500x500_tucne-23-4.svg`
- **rb-500x500\_tucne-24-4.svg:**`assets/images/rb-500x500_tucne-24-4.svg`
- **rb-500x500\_tucne-25-4.svg:**`assets/images/rb-500x500_tucne-25-4.svg`
- **rb-500x500\_tucne-26-4.svg:**`assets/images/rb-500x500_tucne-26-4.svg`
- **rb-500x500\_tucne-27-4.svg:**`assets/images/rb-500x500_tucne-27-4.svg`
- **rb-500x500\_tucne-28-4.svg:**`assets/images/rb-500x500_tucne-28-4.svg`
- **rb-500x500\_tucne-29-4.svg:**`assets/images/rb-500x500_tucne-29-4.svg`
- **rb-500x500\_tucne-30-4.svg:**`assets/images/rb-500x500_tucne-30-4.svg`
- **rb-500x500\_tucne-31-4.svg:**`assets/images/rb-500x500_tucne-31-4.svg`
- **rb-500x500\_tucne-32-4.svg:**`assets/images/rb-500x500_tucne-32-4.svg`
- **rb-500x500\_tucne-33-4.svg:**`assets/images/rb-500x500_tucne-33-4.svg`
- **rb-500x500\_tucne-34-4.svg:**`assets/images/rb-500x500_tucne-34-4.svg`
- **rb-500x500\_tucne-35-4.svg:**`assets/images/rb-500x500_tucne-35-4.svg`
- **rb-500x500\_tucne-36-4.svg:**`assets/images/rb-500x500_tucne-36-4.svg`
- **rb-500x500\_tucne-37-4.svg:**`assets/images/rb-500x500_tucne-37-4.svg`
- **rb-500x500\_tucne-38-4.svg:**`assets/images/rb-500x500_tucne-38-4.svg`
- **rb-500x500\_tucne-39-4.svg:**`assets/images/rb-500x500_tucne-39-4.svg`
- **rb-500x500\_tucne-40-4.svg:**`assets/images/rb-500x500_tucne-40-4.svg`
- **rb-500x500\_tucne-41-4.svg:**`assets/images/rb-500x500_tucne-41-4.svg`
- **rb-500x500\_tucne-42-4.svg:**`assets/images/rb-500x500_tucne-42-4.svg`

### Ilustrace

**Tip:** Ilustrace můžete přebarvovat dle bradnových barev.

**Legenda:** Seznam ikon v manuálu — tučný text je název souboru, zpětné apostrofy obsahují relativní cestu v exportu.

- **ilustrace-27.svg:**`assets/images/ilustrace-27.svg`
- **ilustrace-31.svg:**`assets/images/ilustrace-31.svg`
- **ilustrace-47.svg:**`assets/images/ilustrace-47.svg`
- **ilustrace-46.svg:**`assets/images/ilustrace-46.svg`
- **ilustrace-49.svg:**`assets/images/ilustrace-49.svg`
- **ilustrace-50.svg:**`assets/images/ilustrace-50.svg`
- **ilustrace-48.svg:**`assets/images/ilustrace-48.svg`

### Vzor sítě

**Tip:** Vzor sítě můžete přebarvovat dle bradnových barev.

**Legenda:** Seznam ikon v manuálu — tučný text je název souboru, zpětné apostrofy obsahují relativní cestu v exportu.

- **zakladni-sit.svg:**`assets/images/zakladni-sit.svg`
- **sit-1.svg:**`assets/images/sit-1.svg`

### Ostatní komponenty

Balíček dalších grafických komponent, které se mohou hodit.

**Obrázek:** !\[\](assets/images/komponenty.webp)

* * *

**Tlačítka pod obrázkem:**

- **Balíček komponent:**`assets/others/komponenty.zip`

## 10\. Práce s fotografií

### Obecná filosofie

<p>Fotografie Red Button zobrazují lidi v kontextu — při rozhovoru, spolupráci nebo reflexi. Nikdy nejde o výplňové stockové záběry. <strong>Každá fotografie nese emoci a autenticitu:</strong> skutečné výrazy, přirozené prostředí, inteligentní neformálnost. </p><p><strong>Oblečení vždy v úrovni smart casual</strong> — žádné saka ani trika s potiskem. </p><p>Fotografie jsou vždy <strong>černobílé</strong>, případně <strong>tónované do červené.</strong></p>

### Vizuální styl

* * *

**Položka** (1/2)

**Obrázek:** !\[\](assets/images/frame-40083.webp) **Text pod obrázkem:** KATEGORIE 1: Situační fotografie Zachycují interakci dvou nebo více lidí — rozhovor, workshop, koučovací sezení. Jde o hlavní fotografický formát pro komunikaci značky. Pravidla výběru: vždy alespoň dva lidé v přímé interakci přirozené, teplé výrazy — žádné přepjaté úsměvy neformální byznysové prostředí (kavárna, kancelář, stůl) viditelné rekvizity prostředí jsou v pořádku (káva, zápisník, laptop) Stylizace: černobílá s lehkým filmovým zrnem — základní varianta celoplošné tónování do červené — pro velkoformátové použití (hero bannery, fullscreen pozadí)

* * *

**Položka** (2/2)

**Obrázek:** !\[\](assets/images/image-layer-6a064baa4a726a7a1ff49c45--2x.webp) **Text pod obrázkem:** KATEGORIE 2: Portréty Používají se pro prezentaci konkrétní osoby — lektora, speakera nebo klienta v referenci. Vždy jde o jednoho člověka a vždy jsou graficky zpracované do cutout formátu. Pravidla výběru: přirozený, sebevědomý výraz — přátelský, ne pódiový neutrální nebo přirozené pozadí (v originálu — ořez ho eliminuje) smart casual oblečení, žádné rušivé prvky

### Fotografický filtr

Jemný šum přidávající taktilnost fotografiím.

**Obrázek „Před":** !\[\](assets/images/beforeimage-0-image-201.webp) **Obrázek „Po":** !\[\](assets/images/afterimage-0-image-200.webp)

### Brevná úprava fotografií

Povolené varianty barevné úpravy. Čenobílá s vyšším kontrastem a červené tónování (použitá barva "Wine").

**Obrázek:** !\[\](assets/images/tonovani.webp) **Text pod obrázkem:** _(bez textu pod obrázkem)_

### Grafické zpracování "Cutout"

**Obrázek:** !\[\](assets/images/cutout-in.webp) **Text pod obrázkem:** Portrét je oříznutý, bez pozadí a zarámovaný zdánlivě geometrickýcm tvarem — připomíná ručně malovanou siluetu, ne přesný geometrický výřez. Tvar cutoutu je nepravidelný, který ladí s rukodělným charakterem stylu značky. Varianty: - světlé pozadí → cutout rám ve vínové - tmavé pozadí → cutout rám v bílé Takto upravený portrét je přenositelný do jakéhokoli grafického layoutu — slide deck, web, tiskový materiál.

### Umístění sítě do fotografie

Síť umisťujeme vždycky jako dekoraci do rohu formátu.

**Upozornění:** Nikdy by síť neměla překrývat obličej nebo jiný důležitý motiv fotografie.

* * *

**Obrázek v karuselu:** (1/3) !\[\](assets/images/frame-40083.webp)

* * *

**Obrázek v karuselu:** (2/3) !\[\](assets/images/frame-40085.webp)

* * *

**Obrázek v karuselu:** (3/3) !\[\](assets/images/frame-40084b.webp)

## 11\. O Red Button

### Kdo jsme

<p>Red Button je ekosystém lidí, kteří věří, že byznys má zásadní vliv na to, jak se daří společnosti. Už více než 10 let spojujeme profesionály napříč obory: lídry, lektory, podnikatele, experty i průvodce změnou.</p><p>Sdílíme zkušenosti z praxe a vytváříme prostor, kde vznikají partnerství, projekty a konkrétní změny. Věříme, že firmy mohou generovat zdravý zisk a zároveň být pozitivní hybnou silou společnosti. Že leadership není jen o výkonu, ale i o odpovědnosti. A že rozvoj lidí má smysl tehdy, když má skutečný dopad na byznys i okolí.</p><p>Nejsme vzdělávací agentura.</p><p><strong>Jsme síť, která propojuje lidi, zkušenosti a kompetence budoucnosti.</strong></p><p><strong>Poslání Red Button:</strong> zlepšujeme společnost skrze rozvoj firem a podnikatelského prostředí.</p>

### Role Red Button EDU

<p>Red Button EDU je partner firem na cestě ke změně skrze rozvoj lidí. Pomáháme firmám růst tím, že systematicky budujeme kompetence firem pro 21. století. Vzdělávání vnímáme jako živý proces – propojený s realitou firmy, strategií i technologickou změnou.</p><p>Neučíme podle šablon. Díky síti více než 90 odborníků kombinujeme know-how z byznysu, technologií, koučinku i kreativity. Vzniká tak prostředí, kde se učení nestává povinností, ale nástrojem skutečného dopadu.</p><p><strong>Ambice Red Button EDU:</strong> jsme první volba při provázení firem skutečnou změnou.</p><p><strong>Prakticky to znamená:</strong></p>

- neprodáváme instantní školení, ale hledáme řešení, které sedne kontextu klienta,
- rozvoj lidí chápeme jako cestu k lepšímu fungování firem, ne jako aktivitu bez dopadu,
- propojujeme expertizu, facilitaci, byznysový kontext a lidský přístup,
- zajímá nás skutečná změna v chování lidí, týmů a organizací,
- stojíme na síti lidí, kteří si navzájem přinášejí know-how, vztahy, energii a odvahu dělat věci jinak.

### Naše hodnoty

<p><strong>Co nás vede při práci v týmu i s klienty</strong></p><p><strong>#Zájem:</strong> Nefalšovaný a opravdový<br>O sebe, spolupracovníky, klienty, dodavatele, trh a zbytek kolem nás.</p><p><strong>#Růst: </strong>Raketový<br>Učíme se od nejlepších, sdílíme know-how, věříme, co podporujeme, a neustále testujeme.</p><p><strong>#Vášeň:</strong> Neutuchající. Jsme rebelové a trendsetteři, máme odvahu tvořit a vždy dodáme něco navíc - děláme akce 11 z 10.</p><p><strong>#Souhra:</strong> Efektivní<br>Žijeme ve světě 100% vlastnictví, máme podnikatelský mindset a dotahujeme věci do konce.</p><p><strong>Zájem nám dává lidskost. Růst nás drží v pohybu. Vášeň přidává energii a podpis. Souhra zajišťuje, že z nápadů vznikají skutečné výsledky.</strong></p>

## 12\. Základní pravidla, jak pracovat se značkou

### Red Button jako značka

<p>Red Button je značka pro chvíle, kdy firma nechce jen mluvit o změně, ale opravdu ji rozhýbat.</p><p>Pomáháme leaderům, týmům a organizacím rozvíjet kompetence, měnit způsob práce a zvládat svět, ve kterém se technologie, lidé i byznys mění rychleji než dřív.</p><p>Nejsme školící katalog. Jsme partner pro rozvoj, který má dopad v praxi.</p><p>Red Button EDU propojuje rozvoj lidí s tím, co firma reálně potřebuje zvládnout. Stavíme vzdělávací a rozvojové programy, které nejsou jen inspirací na jeden den, ale vedou ke změně chování, lepší spolupráci a byznysovému dopadu.</p>

### Jak chceme a nechceme působit

- odvážně X ne agresivně
- lidsky X ne familiárně za každou cenu
- prakticky X ne banálně
- chytře X ne akademicky těžce
- energicky X ne chaoticky
- důvěryhodně X ne korporátně sterilně
- současně X ne trendově jen proto, že je něco nové
- systémově X ne složitě
- profesionálně X ne neosobně nebo studeně
- hravě X ne infantilně

### Jak se hodnoty promítají do značky

### Zájem → značka, která je opravdově přítomná

<p>Zájem znamená, že nejdeme po povrchu. Ptáme se, posloucháme, chceme pochopit kontext a hledáme řešení, které dává smysl pro konkrétní lidi a firmu.</p><p>V komunikaci se projevuje tak, že:</p>

- nezačínáme sebou, ale klientovou situací,
- mluvíme lidsky a pozorně,
- nehodnotíme, nesoudíme, nepovyšujeme se,
- ukazujeme, že rozumíme realitě lidí ve firmách.

<p><strong>Brandově působíme:</strong> partnersky, všímavě, lidsky a důvěryhodně.</p>

### Růst → značka, která se pořád učí a posouvá

<p>Růst znamená, že nestojíme na místě. Přinášíme trendy, testujeme nové přístupy, učíme se od nejlepších a pomáháme růst i ostatním.</p><p>V komunikaci se projevuje tak, že:</p>

- ukazujeme vývoj, nové pohledy a inspiraci ze světa,
- nepoužíváme trendy jako dekoraci, ale překládáme je do praxe,
- mluvíme o posunu, učení, odvaze zkoušet a měnit návyky,
- propojujeme rozvoj lidí s budoucností práce a byznysu.

<p><strong>Brandově působíme:</strong> současně, progresivně, zvídavě a ambiciózně.</p>

### Vášeň → značka, která má energii a podpis

<p>Vášeň znamená, že věci neděláme jen „správně“, ale s energií, nápadem a chutí dodat něco navíc. Rozvoj má být zážitek, který lidi probudí, ne jen další položka v kalendáři.</p><p>V komunikaci se projevuje tak, že:</p>

- píšeme živě, s tahem a jasnou pointou,
- nebojíme se výraznějších formulací,
- umíme překvapit, zaujmout a „vystřelit ze sandálů“,
- držíme vysokou kvalitu a vlastní podpis.

<p><strong>Brandově působíme:</strong> energicky, odvážně, výrazně a zapamatovatelně.</p>

### Souhra → značka, která umí spojovat a dotahovat

<p>Souhra znamená, že nejsme jednotlivci hrající každý za sebe. Jsme síť, která umí propojit správné lidi, kompetence a know-how kolem konkrétní výzvy.</p><p>V komunikaci se projevuje tak, že:</p>

- mluvíme o spolupráci, propojení a společném tahu,
- ukazujeme sílu ekosystému, ne jen jednotlivých expertů,
- držíme jasnost, spolehlivost a návaznost,
- neslibujeme jen inspiraci, ale cestu k výsledku.

<p><strong>Brandově působíme:</strong> sehraně, kompetentně, odpovědně a prakticky.</p>

### Základní pravidla práce se značkou

<p>Tato pravidla pomáhají značku používat v praxi. Nejsou dogma, ale brandový kompas: návod, jak tvořit výstupy, které jsou rozpoznatelně Red Button.</p>

### Pravidlo 1: Identita a jasnost

<p>Každý materiál musí být na první pohled rozpoznatelný jako Red Button a do pár vteřin odpovědět:</p>

- Je to Red Button?
- Pro koho to je?
- Jaký problém to řeší?
- Proč je to důležité právě teď?
- Co si má člověk odnést?
- Co má udělat dál?

<p>Příklady: </p><p><strong>Méně vhodně:</strong><br>„Komplexní rozvojový program pro podporu kompetencí manažerů.“</p><p><strong>Lépe:</strong><br>„Pomůžeme vašim manažerům převést změnu z prezentací do každodenní praxe.“</p>

### Pravidlo 2: Vizuál nese energii, není jen dekorací

<p>Vizuální styl Red Button stojí na výrazné červené, kontrastu, ručně kreslených prvcích, síti, texturách a specifické práci s fotografiemi.Každý grafický prvek má mít roli. Buď zvýrazňuje důležitou myšlenku, pomáhá orientaci, dodává lidskost, nebo posiluje rozpoznatelnost značky. Pokud jen vyplňuje prostor, raději ho vynecháme.</p>

### Pravidlo 3: Červená je signál, ne tapeta

- Barvy mají v brandu jasnou roli:Apple Red používáme jako energii, výzvu k akci, důraz a „tlačítko“.
- Wine přináší hlubší, klidnější a serióznější tón.
- Anthracite tvoří profesionální základ.
- White dává prostoru dech.Červenou nepoužíváme proto, aby byl každý výstup hlasitý. Používáme ji tam, kde má člověk zbystřit nebo udělat akci: u hlavního sdělení, důležitého detailu, CTA, navigace nebo momentu změny.</li></ul>

### Pravidlo 4: Ruční prvky přidávají lidskost

<p>Markerové písmo, ruční ikony, podtržení a zakroužkování používáme jako lidskou poznámku do jinak profesionálního systému.Nejsou to ozdoby. Jsou to momenty, kdy značka „vezme fixu do ruky“ a ukáže na to podstatné.</p>

### Pravidlo 5: Fotky jsou pravé a pravdivé

<p>Fotografie mají působit skutečně, lidsky a současně. Vyhýbáme se generickým fotobankovým scénám typu „šťastný tým u skleněné tabule“.</p><p>Hledáme napětí, autenticitu, soustředění, energii, rozhovor, práci a pohyb.</p><p>Prakticky:</p>

- na webech a v materiálech využíváme primárně černobílé fotky,
- barevné fotky využíváme hlavně na sociálních sítích a ve sdílených fotoalbech,
- můžeme využít jemný fotografický filtr / šum pro větší taktilnost,
- síť používáme jako doplňkový prvek, ideálně v rohu,
- síť nikdy nepřekrývá obličej ani důležitý motiv.

### Pravidlo 6: Neprodáváme produkt, ukazujeme změnu

<p>V komunikaci nezačínáme formátem, produktem ani službou. Neříkáme primárně „workshop“, „akademie“, „webinář“ nebo „trénink“. Začínáme změnou, kterou klient potřebuje udělat.</p><p>Formát je odpověď. Ne pointa.</p><p><strong>Méně vhodně:</strong><br>„Nabízíme dvoudenní workshop change managementu.“</p><p><strong>Lépe:</strong><br>„Pomůžeme vašim leaderům vést změnu tak, aby nezůstala jen ve slidu z board meetingu.“</p>

### Pravidlo 7: Každý výstup má jasnou akci

<p>U sales materiálů, webu, newsletteru i LinkedInu musí být jasné, co dál.</p><p>Příklady CTA:</p>

- Pojďme zmapovat, kde se změna ve vaší firmě zasekává.
- Domluvme si krátkou diagnostiku rozvojových priorit.
- Ukážeme vám, jak může vypadat akademie s měřitelným dopadem.
- Pošleme vám ukázku programu pro vaše leadery.
- Přijďte se potkat s lidmi, kteří řeší podobné výzvy.

### Brand checklist pro tým

- Je do 5 vteřin jasné, že jde o Red Button?
- Je výsledek tvořený v souladu s aktuálním brand manuálem a využíváš jen aktuální prvky brandu?
- Je zřejmé, o co nám jde a komu to pomáhá?
- Mluvíme o problému klienta, ne jen o sobě?
- Je tam konkrétní přínos?
- Je tam důkaz, příklad nebo praktický výstup?
- Je jazyk lidský, ale pořád profesionální?
- Používáme červenou jako důraz, ne jako výplň?
- Má každý ruční prvek jasný účel?
- Není výstup přeplácaný?
- Je jasné, co má člověk udělat dál?

## 13\. Tone of voice Red Button

### Tone of voice

### Hlas značky Red Button

### Co má náš tón vyjadřovat

<p><strong>Red Button mluví jako zkušený, lidský a odvážný parťák pro změnu.</strong> Má za sebou praxi, rozumí realitě firem a nebojí se říct věci na rovinu. Zároveň nepoučuje, nesoudí a nestaví se nad klienta. Mluvíme odborně, ale srozumitelně. Lidsky, ale ne familiárně. Sebevědomě, ale ne nafoukaně.</p><p>Náš hlas má nést to, co je pro Red Button typické:</p><p><strong>zájem</strong> — rozumíme lidem, kontextu a realitě klienta,</p><p><strong>růst</strong> — přinášíme nový pohled, trendy a chuť posouvat věci dál,</p><p><strong>vášeň</strong> — máme energii, tah a vlastní podpis,</p><p><strong>souhru</strong> — propojujeme lidi, kompetence a kroky do výsledku.</p>

### Základní pravidla tone of voice

### Mluvíme na rovinu, ne tvrdě

<p>Umíme pojmenovat problém, ale nevytváříme pocit viny.</p><p><strong>Méně vhodně:</strong><br>„Vaše vzdělávání nefunguje.“</p><p><strong>Lépe:</strong><br>„Samotné školení většinou změnu neudělá. Potřebuje návaznost, praxi a jasný systém.“</p>

### Jsme experti z praxe, ne akademici

<p>Máme hloubku, ale nepíšeme složitě jen proto, abychom působili chytře.</p><p><strong>Méně vhodně:</strong><br>„Implementujeme komplexní learning journey zaměřenou na rozvoj transformačních kompetencí.“</p><p><strong>Lépe:</strong><br>„Navrhujeme rozvojovou cestu, která pomáhá lidem měnit konkrétní pracovní návyky.“</p><p></p>

### Jsme lidští, ne familiární

<p>Mluvíme přirozeně, ale ne roztomile, interně ani přehnaně kamarádsky.</p><p><strong>Méně vhodně:</strong><br>„Tak jsme se na to mrkli a chce to vaše leadery trochu nakopnout. 😊“</p><p><strong>Lépe:</strong><br>„Z rozhovorů vidíme, že vaši leadeři potřebují hlavně větší oporu v každodenním vedení změny.</p>

### Jsme odvážní, ne útoční

<p>Můžeme být výrazní, ale nesmíme klienta shazovat.</p><p><strong>Méně vhodně:</strong><br>„Firmy často vůbec netuší, jak změnu řídit.“</p><p><strong>Lépe:</strong><br>„Mnoho firem má strategii změny dobře popsanou, ale naráží ve chvíli, kdy se má propsat do každodenní práce týmů.“</p>

### Jsme praktičtí, ne povrchní

<p>Nezůstáváme u inspirace. Vždy ukazujeme, co se má změnit v praxi.</p><p><strong>Méně vhodně:</strong><br>„Přineseme vám inspiraci pro budoucnost leadershipu.“</p><p><strong>Lépe:</strong><br>„Pomůžeme vašim leaderům zvládnout konkrétní situace: prioritizaci, komunikaci změny, práci s odporem a rozhodování pod tlakem.“</p>

### Jsme hraví, ne infantilní

<p>Umíme tvořit zážitek, ale nesmí zmizet hloubka, kvalita a dopad.</p><p><strong>Méně vhodně:</strong><br>„Uděláme z vašeho leadershipu jízdu, na kterou nikdo nezapomene.“</p><p><strong>Lépe:</strong><br>„Navrhneme rozvoj jako zážitek, který lidi vtáhne, probudí a zároveň povede ke konkrétní změně chování.“</p>

### Jsme současní, ne trendoví za každou cenu

<p>Mluvíme o AI, změně a budoucnosti práce, ale ne jako o módní nálepce.</p><p><strong>Méně vhodně:</strong><br>„Pomůžeme vám být future-ready díky AI mindsetu.“</p><p><strong>Lépe:</strong><br>„Pomůžeme lidem pochopit, kde jim AI může reálně změnit práci — a jak si kolem toho nastavit nové návyky.“</p>

### Jsme sebevědomí, ne nafoukaní

<p>Umíme říct, v čem jsme silní, ale nejsme spasitelé.</p><p><strong>Méně vhodně:</strong><br>„Jsme nejlepší partner pro transformaci vaší firmy.“</p><p><strong>Lépe:</strong><br>„Přinášíme síť zkušených lidí, kteří už podobné změny zažili — a pomohou vám je převést do praxe.“</p>

### Jak psát / jak nepsat

<p><strong>V komunikaci nezačínáme tím, co prodáváme. Začínáme tím, co klient řeší.</strong></p><p>Méně vhodně: Nabízíme workshopy a akademie na míru.</p><p>Lépe: Pomáháme firmám měnit způsob práce skrze rozvoj lidí.</p><p>Méně vhodné: Rozvíjíme soft skills manažerů.</p><p>Lépe: Pomáháme leaderům zvládat změnu, komunikovat jasněji a vést týmy v nejistotě.</p><p>Méně vhodné: Připravíme školení podle vašich potřeb.</p><p>Lépe: Společně navrhneme rozvoj, který sedne vaší realitě, lidem i byznysovým prioritám.</p><p>Méně vhodné: Naše řešení je interaktivní a inovativní.Lidé si věci jen neposlechnou. </p><p>Lépe: Zkouší je, vztahují ke své práci a odcházejí s konkrétním dalším krokem.</p><p>Méně vhodné: Pomáháme s implementací změny.</p><p>Lépe: Pomáháme dostat změnu z prezentací do porad, rozhodování, priorit a každodenních návyků.</p><p>Méně vhodné: Máme širokou síť expertů.</p><p>Lépe: Skládáme pro klienty tým lidí, kteří rozumí jejich výzvě z různých stran - byznysu, leadershipu, technologií i práce s lidmi.</p>

### Krizová a náročná komunikace

- Základní pravidlo: V náročných situacích nejsme ani měkcí, ani ostří. Jsme klidní, přesní a féroví. Pojmenujeme situaci, její dopad a další krok.
- Když je problém na straně klienta, držíme hranice.
- Když je problém na naší straně, přebíráme odpovědnost a rychle ukazujeme nápravu.

### Situace 1: Klient nedodal podklady

<p><strong>Méně vhodně:</strong><br>„Stále jsme od vás nedostali podklady, bez kterých nemůžeme pokračovat.“</p><p><strong>Lépe:</strong><br>„Abychom mohli držet kvalitu i původně navržený harmonogram, potřebujeme od vás ještě doplnit \[konkrétní podklady\]. Bez těchto vstupů bychom museli pracovat s předpoklady, což by mohlo ovlivnit přesnost návrhu.“</p><p><strong>Další krok:</strong><br>„Pokud nám podklady pošlete do \[datum\], zvládneme navázat podle plánu. Pokud to není reálné, upravíme společně harmonogram.“</p>

### Situace 2: Klient nezaplatil fakturu včas

<p><strong>Méně vhodně:</strong><br>„Vaše faktura je po splatnosti. Žádáme o okamžitou úhradu.“</p><p><strong>Lépe — první připomenutí:</strong><br>„Krátce připomínáme fakturu č. \[číslo\], která měla splatnost \[datum\]. Možná se jen ztratila v běžném provozu, proto ji posíláme znovu a budeme rádi za informaci, jestli je u vás v procesu schvalování.“</p><p><strong>Lépe — pevnější varianta:</strong><br>„Vracíme se k faktuře č. \[číslo\], která je po splatnosti od \[datum\]. Potřebujeme prosím vědět, kdy bude platba odeslána, abychom mohli férově nastavit další kroky spolupráce.“</p>

### Situace 3: My jsme něco nedodali dobře

<p><strong>Méně vhodně:</strong><br>„Mrzí nás vzniklá situace, ale bylo to způsobeno kombinací více faktorů.“</p><p><strong>Lépe:</strong><br>„Máte pravdu, v tomto kroku jsme nedodali výstup v podobě, na které jsme se domluvili. Bereme to na sebe a navrhujeme následující nápravu: \[konkrétní krok, termín, odpovědná osoba\].“</p><p><strong>Další krok:</strong><br>„Pošleme upravenou verzi do \[čas/datum\] a vyznačíme, co se změnilo. Zároveň jsme si interně nastavili kontrolu, aby se stejná věc neopakovala.“</p>

### Situace 4: Klient mění zadání v průběhu projektu

<p><strong>Méně vhodně:</strong><br>„Tohle nebylo součástí původní dohody.“</p><p><strong>Lépe:</strong><br>„Rozumíme, že se situace posunula. Pojďme se podívat, co změna zadání znamená pro rozsah, harmonogram a rozpočet, abychom nastavili další postup férově pro obě strany.“</p>

### Situace 5: Musíme říct ne

<p><strong>Méně vhodně:</strong><br>„To bohužel nejde.“</p><p><strong>Lépe:</strong><br>„V této podobě bychom nedokázali garantovat kvalitu, kterou chceme držet. Navrhujeme proto jinou cestu: \[varianta A\] nebo \[varianta B\].“</p>

### Rychlý checklist tone of voice

<p><strong>Před odesláním textu si projdi:</strong></p>

- Začínáme situací klienta, ne sebou?
- Je hlavní sdělení jasné do pár vteřin?
- Zní text lidsky, ale pořád profesionálně?
- Je konkrétní, nebo jen obecný?
- Ukazuje změnu v praxi?
- Vyhýbá se buzzwordům bez významu?
- Není přehnaně familiární?
- Není útočný, hodnotící nebo povýšený?
- Má energii, pointu a tah?
- Je jasné, co má člověk udělat dál?

### AI prompt pro psaní v duchu Red Button

### Piš jako Red Button.

<p>Mluv jako zkušený, lidský a odvážný parťák pro změnu. <br>Buď srozumitelný, konkrétní a praktický. Nepiš jako školící katalog, akademický text ani korporátní konzultant plný buzzwordů.<br><br>Značka má působit:<br>- odvážně, ale ne útočně,<br>- lidsky, ale ne familiárně,<br>- expertně, ale ne složitě,<br>- prakticky, ale ne banálně,<br>- energicky, ale ne chaoticky,<br>- současně, ale ne trendově jen na efekt.<br><br>Vždy ukaž:<br>- jaký problém klient řeší,<br>- co se má změnit v praxi,<br>- proč na tom záleží,<br>- jaký je konkrétní přínos,<br>- co je další krok.<br><br>Vyhýbej se generickým formulacím jako:<br>„komplexní řešení“, „inovativní workshop“, „soft skills training“, „transformační journey“, pokud nejsou vysvětlené konkrétně.<br><br>Text má být v češtině, přirozený, živý, byznysově srozumitelný a vhodný pro firmy, leadery, HR/L&amp;D a partnery Red Button.</p>

### Krizová a náročná komunikace

<p>Kdy použít: Když klient nedodá podklady, nezaplatí fakturu, mění zadání, ruší termín, nebo když jsme něco pokazili my.</p><p>Pomoz mi napsat zprávu v duchu Red Button pro náročnou situaci.<br><br>Situace: \[popiš, co se stalo\]<br>Kdo je příjemce: \[klient / partner / dodavatel / interní tým\]<br>Vztah s příjemcem: \[nový klient / dlouhodobý klient / strategický partner\]<br>Co potřebujeme dosáhnout: \[např. získat podklady / připomenout platbu / navrhnout nápravu / posunout termín / říct ne\]<br>Jaký je dopad situace: \[doplň\]<br>Jaký další krok navrhujeme: \[doplň\]<br>Tón: klidný, přesný, férový, partnerský.<br><br>Pravidla:<br>- neútoč,<br>- nevymlouvej se,<br>- nepoučuj,<br>- nepoužívej pasivně-agresivní formulace,<br>- pojmenuj situaci věcně,<br>- ukaž dopad,<br>- navrhni konkrétní další krok,<br>- drž vztah i hranice.<br><br>Když je problém na straně klienta, buď pevný, ale partnerský.<br>Když je problém na naší straně, převezmi odpovědnost a navrhni nápravu.<br><br>Vytvoř:<br>1. jemnější verzi zprávy,<br>2. pevnější verzi zprávy,<br>3. velmi krátkou verzi do e-mailu nebo chatu,<br>4. seznam formulací, kterým se vyhnout,<br>5. doporučení, co si před odesláním zkontrolovat.</p>

### LinkedIn post v duchu Red Button

<p><strong>Kdy použít:</strong><br>Pro firemní LinkedIn, osobní profily expertů, pozvánky na akce, case studies, názory nebo shrnutí článků.</p><p><strong>Prompt:</strong></p><p><code>Napiš LinkedIn post v duchu Red Button.<br><br>Téma: \[doplň\]<br>Autor / hlas: \[Red Button EDU / konkrétní osoba / expert / leadership\]<br>Cílová skupina: \[doplň\]<br>Cíl postu: \[otevřít téma / pozvat na akci / sdílet insight / prodat službu / ukázat case study\]<br>Hlavní sdělení: \[doplň\]<br>Povinné informace: \[doplň\]<br>CTA: \[doplň\]<br><br>Post má být:<br>- názorový,<br>- živý,<br>- lidský,<br>- konkrétní,<br>- s jasným háčkem na začátku,<br>- bez korporátní omáčky,<br>- bez prázdných motivačních frází.<br><br>Vytvoř 3 varianty:<br>1. věcnou a byznysovou,<br>2. odvážnější a názorovější,<br>3. lidštější a osobnější.<br><br>Každá varianta musí mít:<br>- silný první řádek,<br>- jasné napětí nebo problém,<br>- konkrétní pohled Red Button,<br>- praktický vhled,<br>- závěr s CTA.<br><br>Nepoužívej přehnaně mnoho emoji. Nepiš jako školící katalog. Nezačínej tím, co nabízíme, ale tím, co lidé ve firmách reálně řeší.</code></p>

### Kontrola výstupu, že je v brandu Red Button

<p>Kdy vyuužít: pro <strong>kontrolu jakéhokoliv výstupu</strong> - textu, prezentace, e-mailu, webu, postu, nabídky i vizuálu.</p><p><code>Zkontroluj následující výstup podle brandu Red Button a našeho tone of voice.<br><br>Typ výstupu:<br>\[doplň: prezentace / e-mail / LinkedIn post / webová stránka / nabídka / sales deck / one-pager / pozvánka / vizuál / jiný\]<br><br>Cílová skupina:<br>\[doplň: klient / CEO / HR / L&amp;D / interní tým / partner / veřejnost / účastníci akce\]<br><br>Účel výstupu:<br>\[doplň: informovat / prodat / vysvětlit / pozvat / navázat spolupráci / řešit problém / inspirovat / aktivovat\]<br><br>Výstup ke kontrole:<br>\[vlož text, popis vizuálu, strukturu slidů nebo screenshot\]<br><br>Hodnoť výstup podle toho, jestli působí jako Red Button:<br>- profesionálně a moderně, ne garážově nebo amatérsky,<br>- lidsky a opravdově, ne studeně, strojově nebo genericky,<br>- odvážně, ne agresivně,<br>- hravě a zážitkově, ne infantilně,<br>- prakticky, ne povrchně,<br>- expertně z praxe, ne akademicky těžce,<br>- partnersky, ne mentorsky shora,<br>- současně a vizionářsky, ne trendově jen na efekt.<br><br>Zkontroluj také, jestli výstup odpovídá hodnotám Red Button:<br>- Zájem: je v něm vidět opravdové porozumění člověku, klientovi nebo situaci?<br>- Růst: přináší nový pohled, posun nebo chuť věci zlepšovat?<br>- Vášeň: má energii, tah a vlastní podpis?<br>- Souhra: propojuje lidi, kompetence, kroky a směřuje k výsledku?<br><br>Zkontroluj tone of voice:<br>- Začíná výstup potřebou, problémem nebo situací příjemce, ne námi?<br>- Je jasné, co se má změnit v praxi?<br>- Je zřejmý konkrétní přínos?<br>- Je jazyk lidský, ale pořád profesionální?<br>- Není text příliš korporátní, obecný nebo plný buzzwordů?<br>- Není příliš familiární, roztomilý nebo interní?<br>- Není útočný, hodnotící nebo povýšený?<br>- Má výstup jasnou pointu a další krok?<br><br>Pokud jde o vizuál, zkontroluj:<br>- Je na první pohled rozpoznatelné, že jde o Red Button?<br>- Je červená použitá jako signál, ne jako tapeta?<br>- Mají ruční prvky jasný účel?<br>- Působí fotky autenticky a lidsky?<br>- Není výstup přeplácaný?<br>- Nepůsobí genericky, šablonově nebo „AI hladce“?<br><br>Výstup vrať v této struktuře:<br><br>1. Rychlé hodnocení:<br>Napiš skóre 1–10, jak moc je výstup v souladu s brandem Red Button, a krátce vysvětli proč.<br><br>2. Co funguje:<br>Vypiš konkrétní věci, které jsou v souladu se značkou.<br><br>3. Co nesedí:<br>Vypiš konkrétní místa, která působí mimo brand nebo mimo tone of voice.<br><br>4. Co upravit prioritně:<br>Vyber maximálně 5 nejdůležitějších úprav.<br><br>5. Navržená úprava:<br>Přepiš nebo navrhni lepší verzi tak, aby více odpovídala Red Button stylu.<br><br>6. Checklist před odesláním:<br>Vrať krátký finální checklist, podle kterého si můžu výstup ještě jednou projít.</code></p>

## 14\. Design tokeny

_Poznámka: Jde o tokeny použité pro stylizaci online brand manuálu (webové rozhraní manuálu)._

| Token | Hodnota |
| --- | --- |
| Barva záhlaví | #fafafa |
| H1 titulek | #444444 |
| Nadpisy H2–H6 | #444444 |
| Text | #444444 |
| Odkazy | #fe1a3f |
| Primární tlačítka | #e3043a |
| Zaoblení karet | 6 |

## 15\. Přiložené soubory

Tento export obsahuje následující soubory v archivu:

| Soubor | Typ | Popis |
| --- | --- | --- |
| `assets/logos/logo-light-logo.svg` | logo | Logo pro světlé pozadí — „Logo" |
| `assets/logos/logo-dark-logo.svg` | logo | Logo pro tmavé pozadí — „Logo" |
| `assets/logos/rb_horizontalni_full_color_cmyk.pdf` | logo | CMYK na světlé pozadí (PDF) — „Logo" |
| `assets/logos/rb_horizontalni_negativ_cmyk.pdf` | logo | CMYK na tmavé pozadí (PDF) — „Logo" |
| `assets/images/background.png` | image | Obrázek pozadí (logo na obrázku) — „Logo" — povoleno |
| `assets/logos/logo-dark-logo.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Logo" — povoleno |
| `assets/images/background-red.png` | image | Obrázek pozadí (logo na obrázku) — „Logo" — povoleno |
| `assets/logos/logo-dark-logo.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Logo" — povoleno |
| `assets/images/background-red.png` | image | Obrázek pozadí (logo na obrázku) — „Logo" — zakázáno |
| `assets/logos/logo-light-logo.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Logo" — zakázáno |
| `assets/images/background.png` | image | Obrázek pozadí (logo na obrázku) — „Logo" — zakázáno |
| `assets/logos/logo-light-logo.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Logo" — zakázáno |
| `assets/logos/logo-universal-symbol.svg` | logo | Univerzální logo — „Symbol" |
| `assets/logos/rb_piktogram_full_color_cmyk.pdf` | logo | CMYK pro univerzální pozadí (PDF) — „Symbol" |
| `assets/images/background.png` | image | Obrázek pozadí (logo na obrázku) — „Symbol" — povoleno |
| `assets/logos/logo-universal-symbol.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Symbol" — povoleno |
| `assets/images/background-red.png` | image | Obrázek pozadí (logo na obrázku) — „Symbol" — povoleno |
| `assets/logos/logo-universal-symbol.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Symbol" — povoleno |
| `assets/logos/logo-light-alternativni.svg` | logo | Logo pro světlé pozadí — „Alternativní" |
| `assets/logos/logo-dark-alternativni.svg` | logo | Logo pro tmavé pozadí — „Alternativní" |
| `assets/logos/rb_vertikalni_full_color_cmyk.pdf` | logo | CMYK na světlé pozadí (PDF) — „Alternativní" |
| `assets/logos/rb_vertikalni_negativ_cmyk.pdf` | logo | CMYK na tmavé pozadí (PDF) — „Alternativní" |
| `assets/images/background.png` | image | Obrázek pozadí (logo na obrázku) — „Alternativní" — povoleno |
| `assets/logos/logo-dark-alternativni.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Alternativní" — povoleno |
| `assets/images/background-red.png` | image | Obrázek pozadí (logo na obrázku) — „Alternativní" — povoleno |
| `assets/logos/logo-dark-alternativni.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Alternativní" — povoleno |
| `assets/images/background-red.png` | image | Obrázek pozadí (logo na obrázku) — „Alternativní" — zakázáno |
| `assets/logos/logo-light-alternativni.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Alternativní" — zakázáno |
| `assets/images/background.png` | image | Obrázek pozadí (logo na obrázku) — „Alternativní" — zakázáno |
| `assets/logos/logo-light-alternativni.svg` | logo | Soubor loga v ukázce na obrazovém pozadí — „Alternativní" — zakázáno |
| `assets/fonts/permanentmarker-regular-czech-fix.otf` | download | Stažení písma — „Permanent Marker“ — Stáhnout Font |
| `assets/images/textove-styly.webp` | image | Obrázek a text — „Styly textu“ |
| `assets/images/ikony-cover.webp` | image | Velká galerie — „Ikony“ |
| `assets/images/ilustrace-cover.webp` | image | Velká galerie — „Ilustrace“ |
| `assets/images/net-cover.webp` | image | Velká galerie — „Vzor sítě“ |
| `assets/images/snimek-obrazovky-2026-05-14-v22.31.56.webp` | image | Velká galerie — „Pozadí“ |
| `assets/images/elementy-cover.webp` | image | Velká galerie — „Ostatní elementy“ |
| `assets/images/aplikace.webp` | image | Obrázek a text — „Identita v akci“ |
| `assets/images/open-single-catalog-mockup-template-6a064b9f4a726a7a1ff49c43--2x2-800x.webp` | image | Obrázek a text — „Identita v akci“ |
| `assets/images/ig-sablony.webp` | image | Obrázek a text — „Identita v akci“ |
| `assets/images/ig.webp` | image | Obrázek a text — „Identita v akci“ |
| `assets/images/ipad-pro-12.9-inch-mockup-6a0653a34a726a7a1ff49c53--2x.webp` | image | Obrázek a text — „Identita v akci“ |
| `assets/images/image-gigapixel-standard-v2-2x.webp` | image | Obrázek a text — „Identita v akci“ |
| `assets/images/image-197-kopie.png` | image | Obrázek v textu (blok) — modul „Leaders“ |
| `assets/images/image-197-kopie.png` | image | Obrázek v textu (blok) — modul „L&D Opertions“ |
| `assets/images/pozitiv_exponential_summit_by_rb.webp` | image | Velká galerie — „Exponential Summit“ |
| `assets/others/exponential_summit.zip` | download | Balíček loga Exponential Summit |
| `assets/images/rb_pozitiv_network.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_shortcut.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_kniha_mesice.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_l-d.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_eduteka.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_circles.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_b-b.webp` | image | Velká galerie — „Ostatní“ |
| `assets/images/rb_pozitiv_edu.webp` | image | Velká galerie — „Ostatní“ |
| `assets/others/logo-subbrandy.zip` | download | Balíček log subbrandů |
| `assets/images/layout.webp` | image | Obrázek a text — „Příklad layoutu tiskoviny“ |
| `assets/images/snimek-obrazovky-2026-05-15-v9.14.18.webp` | image | Obrázek a text — „Příklad layoutu prezentace“ |
| `assets/images/pozadi-default.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/pozadi-default-1.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/pozadi-default-2.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/pozadi-anthracite.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/pozadi-anthracite-1.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/pozadi-red.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/pozadi-dark-red.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/group-1484579124.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/group-1484579126.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/group-1484579125.webp` | image | Galerie (logo na obrázku) — „Povolené barevné kombinace“ — použití: povoleno (ikona check) |
| `assets/images/prace-s-grafikou/pozadi-default.webp` | image | Galerie (logo na obrázku) — „Zakázané barevné kombinace“ — použití: zakázáno (přeškrtnutí) |
| `assets/images/prace-s-grafikou/pozadi-anthracite.webp` | image | Galerie (logo na obrázku) — „Zakázané barevné kombinace“ — použití: zakázáno (přeškrtnutí) |
| `assets/images/prace-s-grafikou/pozadi-red.webp` | image | Galerie (logo na obrázku) — „Zakázané barevné kombinace“ — použití: zakázáno (přeškrtnutí) |
| `assets/images/pozadi-red-1.webp` | image | Galerie (logo na obrázku) — „Zakázané barevné kombinace“ — použití: zakázáno (přeškrtnutí) |
| `assets/images/prace-s-grafikou/pozadi-dark-red.webp` | image | Galerie (logo na obrázku) — „Zakázané barevné kombinace“ — použití: zakázáno (přeškrtnutí) |
| `assets/images/pozadi-dark-red-1.webp` | image | Galerie (logo na obrázku) — „Zakázané barevné kombinace“ — použití: zakázáno (přeškrtnutí) |
| `assets/images/rb-500x500_tucne-01-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-02-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-03-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-04-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-05-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-06-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-07-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-08-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-09-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-10-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-11-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-12-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-13-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-14-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-15-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-16-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-17-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-18-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-19-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-20-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-21-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-22-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-23-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-24-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-25-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-26-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-27-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-28-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-29-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-30-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-31-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-32-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-33-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-34-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-35-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-36-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-37-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-38-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-39-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-40-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-41-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/rb-500x500_tucne-42-4.svg` | icon | Ikona — „Ikony“ |
| `assets/images/ilustrace-27.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/ilustrace-31.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/ilustrace-47.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/ilustrace-46.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/ilustrace-49.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/ilustrace-50.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/ilustrace-48.svg` | icon | Ikona — „Ilustrace“ |
| `assets/images/zakladni-sit.svg` | icon | Ikona — „Vzor sítě“ |
| `assets/images/sit-1.svg` | icon | Ikona — „Vzor sítě“ |
| `assets/images/komponenty.webp` | image | Obrázek a text — „Ostatní komponenty“ |
| `assets/others/komponenty.zip` | download | Balíček komponent |
| `assets/images/frame-40083.webp` | image | Obrázek a text — „Vizuální styl“ |
| `assets/images/image-layer-6a064baa4a726a7a1ff49c45--2x.webp` | image | Obrázek a text — „Vizuální styl“ |
| `assets/images/beforeimage-0-image-201.webp` | image | Před (before–after) — „Fotografický filtr“ |
| `assets/images/afterimage-0-image-200.webp` | image | Po (before–after) — „Fotografický filtr“ |
| `assets/images/tonovani.webp` | image | Obrázek a text — „Brevná úprava fotografií“ |
| `assets/images/cutout-in.webp` | image | Obrázek a text — „Grafické zpracování "Cutout"“ |
| `assets/images/frame-40083.webp` | image | Karusel — „Umístění sítě do fotografie“ |
| `assets/images/frame-40085.webp` | image | Karusel — „Umístění sítě do fotografie“ |
| `assets/images/frame-40084b.webp` | image | Karusel — „Umístění sítě do fotografie“ |

### Red Button — Brand manuál

guidelines/brand-manual.en.md

# Red Button — Brand manuál

> Complete brief for AI agents. Generated from Visualbook on 2026-07-22. Scope: Complete content, including previously protected sections. Language: en.

* * *

## Contents

01. Logos
02. Colors
03. Typography
04. Design Komponenty
05. Ukázky použití
06. Client personas (ICP)
07. Loga subbrandů
08. Práce s grafikou
09. Grafické komponenty
10. Práce s fotografií
11. O Red Button
12. Brand rules — how to work with the brand
13. Tone of voice Red Button
14. Design tokens (design page)
15. Attached files

* * *

## 1\. Logos

### Logo

- **Background mode:** Light / Dark background
- **Background colors:** light: `#ffffff`, dark: `#a11834`

- Logo for light background (SVG): `assets/logos/logo-light-logo.svg`
- Logo for dark background (SVG): `assets/logos/logo-dark-logo.svg`
- CMYK for light background (PDF): `assets/logos/rb_horizontalni_full_color_cmyk.pdf`
- CMYK for dark background (PDF): `assets/logos/rb_horizontalni_negativ_cmyk.pdf`

- **Minimum size:** height-based — screen: 20 px, print: 15 mm
- **Protection zone:** active — 50% of logo height

- **Things to avoid:**
- Do not rotate the logo
- Do not use shadows
- Do not recolor the logo
- Do not deform or change the original proportions of the logo

- **Logo on colored backgrounds:**
- ✅ Allowed: `#fafafa`, `#a11834`, `#444444`
- ❌ Forbidden: `#5b5b5b`, `#e2e2e2`, `#a11834`, `#fe1a3f`, `#fe1a3f`

- **Logo on image backgrounds:**
- ✅ Allowed — background: `assets/images/background.png` — logo: `assets/logos/logo-dark-logo.svg` — logo type: not specified
- ✅ Allowed — background: `assets/images/background-red.png` — logo: `assets/logos/logo-dark-logo.svg` — logo type: not specified
- ❌ Forbidden — background: `assets/images/background-red.png` — logo: `assets/logos/logo-light-logo.svg` — logo type: not specified
- ❌ Forbidden — background: `assets/images/background.png` — logo: `assets/logos/logo-light-logo.svg` — logo type: not specified

### Symbol

- **Background mode:** Universal background (`#ffffff`)

- Universal logo (SVG): `assets/logos/logo-universal-symbol.svg`
- CMYK for universal background (PDF): `assets/logos/rb_piktogram_full_color_cmyk.pdf`

- **Minimum size:** height-based — screen: 20 px, print: 15 mm
- **Protection zone:** active — 50% of logo height

- **Things to avoid:**
- Do not recolor the logo
- Do not deform or change the original proportions of the logo

- **Logo on colored backgrounds:**
- ✅ Allowed: `#ffffff`, `#a11834`, `#444444`
- ❌ Forbidden: `#fe1a3f`

- **Logo on image backgrounds:**
- ✅ Allowed — background: `assets/images/background.png` — logo: `assets/logos/logo-universal-symbol.svg` — logo type: not specified
- ✅ Allowed — background: `assets/images/background-red.png` — logo: `assets/logos/logo-universal-symbol.svg` — logo type: not specified

### Alternativní

- **Background mode:** Light / Dark background
- **Background colors:** light: `#ffffff`, dark: `#a11834`

- Logo for light background (SVG): `assets/logos/logo-light-alternativni.svg`
- Logo for dark background (SVG): `assets/logos/logo-dark-alternativni.svg`
- CMYK for light background (PDF): `assets/logos/rb_vertikalni_full_color_cmyk.pdf`
- CMYK for dark background (PDF): `assets/logos/rb_vertikalni_negativ_cmyk.pdf`

- **Minimum size:** height-based — screen: 24 px, print: 10 mm
- **Protection zone:** active — 50% of logo height

- **Things to avoid:**
- Do not use shadows
- Do not rotate the logo
- Do not recolor the logo
- Do not deform or change the original proportions of the logo

- **Logo on colored backgrounds:**
- ✅ Allowed: `#ffffff`, `#a11834`, `#444444`
- ❌ Forbidden: `#666666`, `#fe1a3f`, `#fe1a3f`, `#a11834`

- **Logo on image backgrounds:**
- ✅ Allowed — background: `assets/images/background.png` — logo: `assets/logos/logo-dark-alternativni.svg` — logo type: not specified
- ✅ Allowed — background: `assets/images/background-red.png` — logo: `assets/logos/logo-dark-alternativni.svg` — logo type: not specified
- ❌ Forbidden — background: `assets/images/background-red.png` — logo: `assets/logos/logo-light-alternativni.svg` — logo type: not specified
- ❌ Forbidden — background: `assets/images/background.png` — logo: `assets/logos/logo-light-alternativni.svg` — logo type: not specified

## 2\. Colors

### Střední vzorník barev

Colours used in the application environment (UI - User Interface) and on the web.

**Table legend:** Each row is one color. Columns HEX / RGB / CMYK / Pantone (C coated, U uncoated) / RAL / NCS describe the same hue in different systems.

| Name | HEX | RGB | CMYK | Pantone C | Pantone U | RAL | NCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Red Button | #e4003a | 228, 0, 58 | 0-100-75-11 | 192 C | — | — | — |
| Wine | #a11834 | 161, 24, 52 | 25 \| 100 \| 70 \| 20 | 56-8 C | — | — | — |
| Anthracite | #444444 | 68, 68, 68 | 00 \| 00 \| 00 \| 85 | 179-14 C | — | — | — |
| White | #ffffff | 255, 255, 255 | 0 \| 0 \| 0 \| 0 | 000 C | — | — | — |

> **Note (full-export correction):** the primary brand red is **Red Button `#e4003a`**. **Apple Red `#fe1a3f`** is a **Dark-Mode-only** accent (see below), not the light-mode primary. `#e3043a` is the digital primary-button fill.

### Podpůrné barvy

Colours used in the application environment (UI - User Interface) and on the web.

**Table legend:** Each row is one color. Columns HEX / RGB / CMYK / Pantone (C coated, U uncoated) / RAL / NCS describe the same hue in different systems.

| Name | HEX | RGB | CMYK | Pantone C | Pantone U | RAL | NCS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Grey | #b0b2b6 | 176, 178, 182 | 00 \| 00 \| 00 \| 35 | P174-1 C | — | — | — |
| Spanish Grey | #969696 | 150, 150, 150 | 40 \| 32 \| 33 \| 1 | P 179-7 C | — | — | — |

### Colour ratios

Proportional use of colour within the visual style. The section is in a new, improved design.

**Display type:** one universal color ratio **Table legend:** The Share column indicates how much space that color should take in the palette — usually as a percentage.

| Color name | HEX | Share |
| --- | --- | --- |
| White | #fafafa | 60% |
| Wine | #a11834 | 20% |
| Anthracite | #444444 | 10% |
| Red Button | #e4003a | 5% |
| Grey | #b0b2b6 | 3% |
| Spanish Grey | #969696 | 2% |

### Dark Mode

For exceptional dark-mode use (e.g. the Exponential Summit website) **Apple Red** replaces Red Button as the accent, and **Red Black** serves as the dark surface. Never on print, branding or merch.

| Name | HEX | RGB | Pantone C |
| --- | --- | --- | --- |
| Apple Red | #fe1a3f | 254, 26, 63 | 1788 C |
| Red Black | #262626 | 38, 38, 38 | — |

## 3\. Typography

### Rubik Black

Here is a place for your font label. It will make it easier for users to use this font.

**Tip:** You can insert a note or notification here.

- **Stáhnout z Google Fonts:** https://fonts.google.com/specimen/Rubik

**Used font styles:** Black (900)

### Permanent Marker

- **Stáhnout Font:**`assets/fonts/permanentmarker-regular-czech-fix.otf`

### Rubik Rergular

Používáme pro běžný odstavcový text.

- **Stáhnout z Google Fonts:** https://fonts.google.com/specimen/Rubik

**Used font styles:** Medium (500), Medium Italic (500), Bold (700), Bold Italic (700), Regular Italic (400), Regular (400)

### Styly textu

**Image:** !\[\](assets/images/textove-styly.webp) **Text under the image:** _(no text under the image)_

### Pravidla pro alternativní písmo užívané v otevřených prezentacích

### Pravidla pro alternativní písmo užívané v otevřených prezentacích

<p>Toto pravidlo se používá jen v extrémních případech zasílání otevřených prezentací klientům. Alternativní font nikdy nepoužíváme na oficiálních materiálech - tisk, branding, merch atp. </p><p>Nadpisy: Rubik → Arial Black<br>Text: Rubik → Arial<br>Akcentové písmo: Permanent Marker → Kalam (Google Slides) / Trebuchet Bold (PowerPoint)</p>

## 4\. Design Komponenty

### Ikony

\[blocked image: not a data: URI\]

### Ilustrace

Stáhněte si cover ilustrace programů.

\[blocked image: not a data: URI\]

### Vzor sítě

Vzor sítě používáme jako jeden z brand symbolů zvyšující rozpoznatelnost značky. Používáme ho k dekoraci především v mrtvém prostoru.

\[blocked image: not a data: URI\]

### Pozadí

Stáhněte si balíček texturovaných pozadí.

\[blocked image: not a data: URI\]

### Ostatní elementy

\[blocked image: not a data: URI\]

## 5\. Ukázky použití

### Slidy prezentace

* * *

**Item** (1/6)

**Image:** !\[\](assets/images/aplikace.webp) **Text under the image:** _(no text under the image)_

* * *

**Item** (2/6)

**Image:** !\[\](assets/images/open-single-catalog-mockup-template-6a064b9f4a726a7a1ff49c43--2x2-800x.webp) **Text under the image:** _(no text under the image)_

* * *

**Item** (3/6)

**Image:** !\[\](assets/images/ig-sablony.webp) **Text under the image:** _(no text under the image)_

* * *

**Item** (4/6)

**Image:** !\[\](assets/images/ig.webp) **Text under the image:** _(no text under the image)_

* * *

**Item** (5/6)

**Image:** !\[\](assets/images/ipad-pro-12.9-inch-mockup-6a0653a34a726a7a1ff49c53--2x.webp) **Text under the image:** _(no text under the image)_

* * *

**Item** (6/6)

**Image:** !\[\](assets/images/image-gigapixel-standard-v2-2x.webp) **Text under the image:** _(no text under the image)_

## 6\. Client personas (ICP)

Three buyer personas. All copy is Czech; write to the situation, never from a product catalogue.

### Leaders — _buy the vision_

- **Motto:** "The world is changing, my company isn't fast enough. I need a partner for the business, not training for employees."
- **Who:** C-level, owners, division/BU leaders, transformation leaders. Firms 250 mil. Kč+ turnover, 250+ staff. Own P&L, own budget, final say. Not HR/L&D — they want results, efficiency and change.
- **Pain:** strategic uncertainty & FOMO (AI, tech); frustration with internal HR; loneliness/overload; need quick wins.
- **They buy:** turnkey solutions ("Mr. Wolf"), mindset transformation, benchmark/best practice, exclusive community (Exponential Circles).
- **Sell:** consultative, not from a catalogue. Speak results, ROI, efficiency, risk — avoid soft HR language. Trust via named practitioner experts. Dual-target: win the Leader's vision without cutting out L&D who execute.
- **Entry offers:** Exponential Circles/Summit, R(e)BeLeader, Business Case Sprint / audit, 1:1 strategic consult.
- **Red flags:** don't send a training catalogue, don't drown them in operations, no boxed solutions.

### L&D Owners — _gatekeeper & strategist_

- **Motto:** "I want the business to take me seriously. I want to be the architect of change, and a partner who helps me defend it to the board."
- **Who:** Head of L&D, Senior HR Manager, HR Director. Large orgs (1000+). Own or strongly influence a budget (millions). Experts — want to build a system, not buy a course.
- **Pain:** fight for relevance ("seat at the table"); pressure to justify budget to the CFO; loneliness in role; fear of picking a supplier who embarrasses them.
- **They buy:** strategic partnership, certainty, their own reputation; ammunition for the board (RB Index, data); expert know-how (AI adoption, culture, digital); peer community.
- **Sell:** co-creation, not lecturing. Be their buddy/ally who prepares board materials. Use L&D terminology (competency models, learning pathways, 70-20-10) + business impact. Track record & case studies (Tatra banka, Škoda).
- **Entry offers:** L&D scan/audit, pilot track for high-potentials, L&D community invite, strategy consult.
- **Red flags:** never bypass them to the CEO; don't send a bare price list; never underestimate their expertise.

### L&D Operations — _evaluator & influencer_

- **Motto:** "I'm overloaded with operations. I need it to work, people to enjoy it (high engagement), and the supplier to do most of the admin. And I need data to defend it to my boss."
- **Who:** L&D specialist, training coordinator, HR generalist/HRBP, LMS/LXP admin. Cross-section of company sizes. Often no/small budget — they do pre-selection and prep for the Owner/Leader.
- **Pain:** overload; the "empty-chair" nightmare (no engagement); tech frustration (LMS, imports); reporting pressure.
- **They buy:** time savings & peace of mind; off-the-shelf products (EDUtéka — 900+ videos, catalogue workshops); ammunition for internal selling; good UX for end users.
- **Sell:** support & educate — be their assistant (ready email for the boss, PDF comparison, dashboard). Speed & simplicity: deploy in 48 h, no IT project. Demo, not vision.
- **Claims:** "6 hours a month saved for HR," "deploy in 48 hours," "everything in one place." Proof: automation, engagement (NPS 80, 90% retention).
- **Entry offers:** EDUtéka (Basic/Premium), one-off workshops, unlocked Brain&Breakfast, 6-week mini-academy/pilot.
- **Red flags:** don't burden with strategy/transformation talk; don't add work; don't underestimate their gatekeeper power.

## 7\. Loga subbrandů

### Exponential Summit

\[blocked image: not a data: URI\]

* * *

**Tlačítka pod galerií:**

- **Balíček loga Exponential Summit:**`assets/others/exponential_summit.zip`

### Exponential Summit

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

\[blocked image: not a data: URI\]

* * *

**Tlačítka pod galerií:**

- **Stáhnout balíček log subbrandů.:**`assets/others/logo-subbrandy.zip`

## 8\. Práce s grafikou

### Příklad layoutu tiskoviny

**Obrázek:** !\[\](assets/images/layout.webp)

### Příklad layoutu prezentace

**Image:** !\[\](assets/images/snimek-obrazovky-2026-05-15-v9.14.18.webp) **Text under the image:** _(no text under the image)_

### Barevné kombinace

**Rule legend** (usage state of a gallery item):

- **forbidden** — incorrect example (strike-through on the site).
- **allowed** — correct example (checkmark ✓ on the site).
- **neutral** — neutral display, no strike-through or checkmark.

* * *

**Gallery item** (1/10)

**Image:** !\[\](assets/images/pozadi-default.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (2/10)

**Image:** !\[\](assets/images/pozadi-default-1.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (3/10)

**Image:** !\[\](assets/images/pozadi-default-2.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (4/10)

**Image:** !\[\](assets/images/pozadi-anthracite.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (5/10)

**Image:** !\[\](assets/images/pozadi-anthracite-1.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (6/10)

**Image:** !\[\](assets/images/pozadi-red.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (7/10)

**Image:** !\[\](assets/images/pozadi-dark-red.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (8/10)

**Image:** !\[\](assets/images/group-1484579124.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (9/10)

**Image:** !\[\](assets/images/group-1484579126.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

* * *

**Gallery item** (10/10)

**Image:** !\[\](assets/images/group-1484579125.webp) **Caption for this image:** _(no caption text)_ **Rule:** allowed

### Zakázané barevné kombinace

**Rule legend** (usage state of a gallery item):

- **forbidden** — incorrect example (strike-through on the site).
- **allowed** — correct example (checkmark ✓ on the site).
- **neutral** — neutral display, no strike-through or checkmark.

* * *

**Gallery item** (1/6)

**Image:** !\[\](assets/images/prace-s-grafikou/pozadi-default.webp) **Caption for this image:** _(no caption text)_ **Rule:** forbidden

* * *

**Gallery item** (2/6)

**Image:** !\[\](assets/images/prace-s-grafikou/pozadi-anthracite.webp) **Caption for this image:** _(no caption text)_ **Rule:** forbidden

* * *

**Gallery item** (3/6)

**Image:** !\[\](assets/images/prace-s-grafikou/pozadi-red.webp) **Caption for this image:** _(no caption text)_ **Rule:** forbidden

* * *

**Gallery item** (4/6)

**Image:** !\[\](assets/images/pozadi-red-1.webp) **Caption for this image:** _(no caption text)_ **Rule:** forbidden

* * *

**Gallery item** (5/6)

**Image:** !\[\](assets/images/prace-s-grafikou/pozadi-dark-red.webp) **Caption for this image:** _(no caption text)_ **Rule:** forbidden

* * *

**Gallery item** (6/6)

**Image:** !\[\](assets/images/pozadi-dark-red-1.webp) **Caption for this image:** _(no caption text)_ **Rule:** forbidden

## 9\. Grafické komponenty

### Ikony

**Legend:** Icons from the manual — bold text is the filename, backticks hold the relative export path.

- **rb-500x500\_tucne-01-4.svg:**`assets/images/rb-500x500_tucne-01-4.svg`
- **rb-500x500\_tucne-02-4.svg:**`assets/images/rb-500x500_tucne-02-4.svg`
- **rb-500x500\_tucne-03-4.svg:**`assets/images/rb-500x500_tucne-03-4.svg`
- **rb-500x500\_tucne-04-4.svg:**`assets/images/rb-500x500_tucne-04-4.svg`
- **rb-500x500\_tucne-05-4.svg:**`assets/images/rb-500x500_tucne-05-4.svg`
- **rb-500x500\_tucne-06-4.svg:**`assets/images/rb-500x500_tucne-06-4.svg`
- **rb-500x500\_tucne-07-4.svg:**`assets/images/rb-500x500_tucne-07-4.svg`
- **rb-500x500\_tucne-08-4.svg:**`assets/images/rb-500x500_tucne-08-4.svg`
- **rb-500x500\_tucne-09-4.svg:**`assets/images/rb-500x500_tucne-09-4.svg`
- **rb-500x500\_tucne-10-4.svg:**`assets/images/rb-500x500_tucne-10-4.svg`
- **rb-500x500\_tucne-11-4.svg:**`assets/images/rb-500x500_tucne-11-4.svg`
- **rb-500x500\_tucne-12-4.svg:**`assets/images/rb-500x500_tucne-12-4.svg`
- **rb-500x500\_tucne-13-4.svg:**`assets/images/rb-500x500_tucne-13-4.svg`
- **rb-500x500\_tucne-14-4.svg:**`assets/images/rb-500x500_tucne-14-4.svg`
- **rb-500x500\_tucne-15-4.svg:**`assets/images/rb-500x500_tucne-15-4.svg`
- **rb-500x500\_tucne-16-4.svg:**`assets/images/rb-500x500_tucne-16-4.svg`
- **rb-500x500\_tucne-17-4.svg:**`assets/images/rb-500x500_tucne-17-4.svg`
- **rb-500x500\_tucne-18-4.svg:**`assets/images/rb-500x500_tucne-18-4.svg`
- **rb-500x500\_tucne-19-4.svg:**`assets/images/rb-500x500_tucne-19-4.svg`
- **rb-500x500\_tucne-20-4.svg:**`assets/images/rb-500x500_tucne-20-4.svg`
- **rb-500x500\_tucne-21-4.svg:**`assets/images/rb-500x500_tucne-21-4.svg`
- **rb-500x500\_tucne-22-4.svg:**`assets/images/rb-500x500_tucne-22-4.svg`
- **rb-500x500\_tucne-23-4.svg:**`assets/images/rb-500x500_tucne-23-4.svg`
- **rb-500x500\_tucne-24-4.svg:**`assets/images/rb-500x500_tucne-24-4.svg`
- **rb-500x500\_tucne-25-4.svg:**`assets/images/rb-500x500_tucne-25-4.svg`
- **rb-500x500\_tucne-26-4.svg:**`assets/images/rb-500x500_tucne-26-4.svg`
- **rb-500x500\_tucne-27-4.svg:**`assets/images/rb-500x500_tucne-27-4.svg`
- **rb-500x500\_tucne-28-4.svg:**`assets/images/rb-500x500_tucne-28-4.svg`
- **rb-500x500\_tucne-29-4.svg:**`assets/images/rb-500x500_tucne-29-4.svg`
- **rb-500x500\_tucne-30-4.svg:**`assets/images/rb-500x500_tucne-30-4.svg`
- **rb-500x500\_tucne-31-4.svg:**`assets/images/rb-500x500_tucne-31-4.svg`
- **rb-500x500\_tucne-32-4.svg:**`assets/images/rb-500x500_tucne-32-4.svg`
- **rb-500x500\_tucne-33-4.svg:**`assets/images/rb-500x500_tucne-33-4.svg`
- **rb-500x500\_tucne-34-4.svg:**`assets/images/rb-500x500_tucne-34-4.svg`
- **rb-500x500\_tucne-35-4.svg:**`assets/images/rb-500x500_tucne-35-4.svg`
- **rb-500x500\_tucne-36-4.svg:**`assets/images/rb-500x500_tucne-36-4.svg`
- **rb-500x500\_tucne-37-4.svg:**`assets/images/rb-500x500_tucne-37-4.svg`
- **rb-500x500\_tucne-38-4.svg:**`assets/images/rb-500x500_tucne-38-4.svg`
- **rb-500x500\_tucne-39-4.svg:**`assets/images/rb-500x500_tucne-39-4.svg`
- **rb-500x500\_tucne-40-4.svg:**`assets/images/rb-500x500_tucne-40-4.svg`
- **rb-500x500\_tucne-41-4.svg:**`assets/images/rb-500x500_tucne-41-4.svg`
- **rb-500x500\_tucne-42-4.svg:**`assets/images/rb-500x500_tucne-42-4.svg`

### Ilustrace

**Legend:** Icons from the manual — bold text is the filename, backticks hold the relative export path.

- **ilustrace-27.svg:**`assets/images/ilustrace-27.svg`
- **ilustrace-31.svg:**`assets/images/ilustrace-31.svg`
- **ilustrace-47.svg:**`assets/images/ilustrace-47.svg`
- **ilustrace-46.svg:**`assets/images/ilustrace-46.svg`
- **ilustrace-49.svg:**`assets/images/ilustrace-49.svg`
- **ilustrace-50.svg:**`assets/images/ilustrace-50.svg`
- **ilustrace-48.svg:**`assets/images/ilustrace-48.svg`

### Vzor sítě

**Tip:** Vzor sítě můžete přebarvovat dle bradnových barev.

**Legend:** Icons from the manual — bold text is the filename, backticks hold the relative export path.

- **zakladni-sit.svg:**`assets/images/zakladni-sit.svg`
- **sit-1.svg:**`assets/images/sit-1.svg`

### Ostatní komponenty

Balíček dalších grafických komponent, které se mohou hodit.

**Obrázek:** !\[\](assets/images/komponenty.webp)

* * *

**Tlačítka pod obrázkem:**

- **Balíček komponent:**`assets/others/komponenty.zip`

## 10\. Práce s fotografií

### Obecná filosofie

<p>Fotografie Red Button zobrazují lidi v kontextu — při rozhovoru, spolupráci nebo reflexi. Nikdy nejde o výplňové stockové záběry. Každá fotografie nese emoci a autenticitu: skutečné výrazy, přirozené prostředí, inteligentní neformálnost. Oblečení vždy v úrovni smart casual — žádné saka ani trika s potiskem. Fotografie jsou vždy černobílé, případně tónované do červené.</p>

### Vizuální styl

Fotografie Red Button zobrazují lidi v kontextu — při rozhovoru, spolupráci nebo reflexi. Nikdy nejde o výplňové stockové záběry. Každá fotografie nese emoci a autenticitu: skutečné výrazy, přirozené prostředí, inteligentní neformálnost. Oblečení vždy v úrovni smart casual — žádné saka ani trika s potiskem. Fotografie jsou vždy černobílé, případně tónované do červené.

* * *

**Item** (1/2)

**Image:** !\[\](assets/images/frame-40083.webp) **Text under the image:** _(no text under the image)_

* * *

**Item** (2/2)

**Image:** !\[\](assets/images/image-layer-6a064baa4a726a7a1ff49c45--2x.webp) **Text under the image:** KATEGORIE 2: Portréty Používají se pro prezentaci konkrétní osoby — lektora, speakera nebo klienta v referenci. Vždy jde o jednoho člověka a vždy jsou graficky zpracované do cutout formátu. Pravidla výběru: přirozený, sebevědomý výraz — přátelský, ne pódiový neutrální nebo přirozené pozadí (v originálu — ořez ho eliminuje) smart casual oblečení, žádné rušivé prvky

### Fotografický filtr

**"Before" image:** !\[\](assets/images/beforeimage-0-image-201.webp) **"After" image:** !\[\](assets/images/afterimage-0-image-200.webp)

### Brevná úprava fotografií

**Image:** !\[\](assets/images/tonovani.webp) **Text under the image:** _(no text under the image)_

### Grafické zpracování: Cutout

**Image:** !\[\](assets/images/cutout-in.webp) **Text under the image:** Portrét je oříznutý, bez pozadí a zarámovaný zdánlivě geometrickýcm tvarem — připomíná ručně malovanou siluetu, ne přesný geometrický výřez. Tvar cutoutu je nepravidelný, který ladí s rukodělným charakterem stylu značky. Varianty: - světlé pozadí → cutout rám ve vínové - tmavé pozadí → cutout rám v bílé Takto upravený portrét je přenositelný do jakéhokoli grafického layoutu — slide deck, web, tiskový materiál.

### Umístění sítě do fotografie

Síť umisťujeme vždycky jako dekoraci do rohu formátu.

**Warning:** Nikdy by síť neměla překrývat obličej nebo jiný důležitý motiv fotografie.

* * *

**Image in carousel:** (1/3) !\[\](assets/images/frame-40083.webp)

* * *

**Image in carousel:** (2/3) !\[\](assets/images/frame-40085.webp)

* * *

**Image in carousel:** (3/3) !\[\](assets/images/frame-40084b.webp)

## 11\. O Red Button

### Red Button

### O Red Button

<p>Red Button je ekosystém lidí, kteří věří, že byznys má zásadní vliv na to, jak se daří společnosti. Už více než 10 let spojujeme profesionály napříč obory: lídry, lektory, podnikatele, experty i průvodce změnou.<br></p><p>Sdílíme zkušenosti z praxe a vytváříme prostor, kde vznikají partnerství, projekty a konkrétní změny. Věříme, že firmy mohou generovat zdravý zisk a zároveň být pozitivní hybnou silou společnosti. Že leadership není jen o výkonu, ale i o odpovědnosti. A že rozvoj lidí má smysl tehdy, když má skutečný dopad na byznys i okolí.</p><p>Nejsme vzdělávací agentura.</p><p>Jsme síť, která propojuje lidi, zkušenosti a kompetence budoucnosti.</p>

### Role Red Button EDU

<p>Red Button EDU je partner firem na cestě ke změně skrze rozvoj lidí. Pomáháme firmám růst tím, že systematicky budujeme kompetence firem pro 21. století. Vzdělávání vnímáme jako živý proces – propojený s realitou firmy, strategií i technologickou změnou.</p><p>Neučíme podle šablon. Díky síti více než 90 odborníků kombinujeme know-how z byznysu, technologií, koučinku i kreativity. Vzniká tak prostředí, kde se učení nestává povinností, ale nástrojem skutečného dopadu.</p><p><strong>Naše poslání:</strong> zlepšujeme společnost skrze rozvoj firem a podnikatelského prostředí.</p><p><strong>Naše ambice:</strong> jsme první volba při provázení firem skutečnou změnou.</p><p><strong>Prakticky to znamená:</strong></p>

- neprodáváme instantní školení, ale hledáme řešení, které sedne kontextu klienta,
- rozvoj lidí chápeme jako cestu k lepšímu fungování firem, ne jako aktivitu bez dopadu,
- propojujeme expertizu, facilitaci, byznysový kontext a lidský přístup,
- zajímá nás skutečná změna v chování lidí, týmů a organizací,
- stojíme na síti lidí, kteří si navzájem přinášejí know-how, vztahy, energii a odvahu dělat věci jinak.

## 12\. Brand rules — how to work with the brand

### Red Button as a brand

Red Button is the brand for the moment a company doesn't just want to talk about change but actually set it in motion. Not a training catalogue — a development partner with real-world impact. Red Button EDU connects people development with what the company actually needs to master.

### How we want / don't want to come across

- **bold** × not aggressive
- **human** × not familiar at all costs
- **practical** × not banal
- **smart** × not academically heavy
- **energetic** × not chaotic
- **trustworthy** × not corporately sterile
- **current** × not trendy just because it's new
- **systemic** × not complicated
- **professional** × not impersonal or cold
- **playful** × not infantile

### How the values show up in the brand

- **Interest (Zájem) → a brand that is genuinely present:** start with the client's situation, not ourselves; speak humanly and attentively; don't judge or condescend.
- **Growth (Růst) → a brand that keeps learning:** show development, new angles, inspiration; translate trends into practice, not decoration.
- **Passion (Vášeň) → a brand with energy and a signature:** write vividly with a clear point; dare stronger phrasing; keep high quality.
- **Synergy (Souhra) → a brand that connects and delivers:** talk about collaboration and the ecosystem; be clear, reliable and follow-through; promise a path to results, not just inspiration.

### The 7 rules

1. **Identity & clarity.** Every material is recognisably Red Button within seconds and answers: Is it Red Button? For whom? What problem does it solve? Why now? What to take away? What to do next. _(Better: "We'll help your managers move change from slides into everyday practice," not "A complex development programme to support managerial competencies.")_
2. **The visual carries energy, it isn't decoration.** Every graphic element has a role — highlight, orient, add humanity, or reinforce recognition. If it only fills space, drop it.
3. **Red is a signal, not wallpaper.** Red Button red = energy, call to action, emphasis, the "button." Wine = deeper, calmer, serious. Anthracite = professional base. White = breathing room. Use red where a person should pay attention or act.
4. **Hand-drawn elements add humanity.** Marker type, hand icons, underlines and circles are a human note in a professional system — moments where the brand "picks up the pen." Not ornaments.
5. **Photos are real and truthful.** No generic stock ("happy team at a glass whiteboard"). Seek tension, authenticity, focus, conversation, work. Web primarily B&W; colour mainly on social. Net used sparingly, in a corner, never over a face.
6. **We don't sell a product, we show change.** Don't lead with "workshop / academy / webinar / training." Start with the change the client needs. The format is the answer, not the point.
7. **Every output has a clear action.** Web, newsletter, LinkedIn — make the next step obvious (e.g. "Let's map where change stalls in your firm," "Let's book a short diagnostic of development priorities.")

### Team checklist

Clear within 5 s it's Red Button? · Built with current brand elements only? · Clear what we're about and whom it helps? · About the client's problem, not just us? · Concrete benefit? · Proof/example/practical output? · Human but still professional? · Red as emphasis, not filler? · Every hand-drawn element has a purpose? · Not cluttered? · Clear what to do next?

## 13\. Tone of voice Red Button

### Voice of the brand

Red Button speaks like an **experienced, human and bold partner for change.** Real-world practice, understands the reality of companies, says things straight — without lecturing, judging or standing above the client. Expert but understandable. Human but not familiar. Confident but not arrogant. The voice carries the four values: **interest, growth, passion, synergy.**

### Core rules (with examples)

- **Straight, not harsh.** _Worse:_ "Your training doesn't work." _Better:_ "Training alone usually won't create change. It needs continuity, practice and a clear system."
- **Practitioners, not academics.** _Worse:_ "We implement a complex learning journey for transformational competencies." _Better:_ "We design a development path that helps people change specific work habits."
- **Human, not familiar.** _Worse:_ "So we took a look and your leaders need a kick 😊" _Better:_ "From the interviews we see your leaders mainly need more support in leading change day to day."
- **Bold, not attacking.** _Worse:_ "Companies often have no idea how to manage change." _Better:_ "Many firms have the change strategy well described, but hit a wall when it must reach teams' daily work."
- **Practical, not shallow.** _Worse:_ "We'll bring you inspiration for the future of leadership." _Better:_ "We'll help your leaders handle concrete situations: prioritisation, communicating change, working with resistance, deciding under pressure."
- **Playful, not infantile.** _Worse:_ "We'll make your leadership a ride no one forgets." _Better:_ "We'll design development as an experience that draws people in and leads to a concrete change in behaviour."
- **Current, not trendy for effect.** _Worse:_ "We'll make you future-ready with an AI mindset." _Better:_ "We'll help people see where AI can really change their work — and set new habits around it."
- **Confident, not arrogant.** _Worse:_ "We're the best partner for transforming your company." _Better:_ "We bring a network of experienced people who've lived through similar changes — and will help you put them into practice."

### How to write / not write

Never open with what we sell — open with what the client is solving. _Worse:_ "We offer tailored workshops and academies." _Better:_ "We help companies change the way they work through people development."

### Crisis & difficult communication

Neither soft nor sharp — calm, precise and fair. Name the situation, its impact and the next step. When the problem is the client's, hold the line; when it's ours, take responsibility and show the fix fast. (Covers: missing inputs, overdue invoice, our own miss, mid-project scope change, saying no.)

### Pre-send checklist

Start with the client's situation, not us? · Main message clear in seconds? · Human but professional? · Concrete, not generic? · Shows change in practice? · Avoids empty buzzwords? · Not over-familiar? · Not attacking/judging/condescending? · Has energy, point and drive? · Clear what to do next?

### AI prompt — write like Red Button

The full manual carries ready-made Czech prompts for writing in-brand, crisis messages, LinkedIn posts and a brand-compliance review — see `brand-manual.cs.md` § 13.

## 14\. Design tokens

_Note: These tokens are used to style the online brand manual (the manual’s web UI)._

| Token | Value |
| --- | --- |
| Header | #fafafa |
| H1 title | #444444 |
| Headings H2–H6 | #444444 |
| Text | #444444 |
| Links | #fe1a3f |
| Primary buttons | #e3043a |
| Card border radius | 6 |

## 15\. Attached files

This export includes the following files in the archive:

| File | Type | Description |
| --- | --- | --- |
| `assets/logos/logo-light-logo.svg` | logo | Logo for light background — "Logo" |
| `assets/logos/logo-dark-logo.svg` | logo | Logo for dark background — "Logo" |
| `assets/logos/rb_horizontalni_full_color_cmyk.pdf` | logo | CMYK for light background (PDF) — "Logo" |
| `assets/logos/rb_horizontalni_negativ_cmyk.pdf` | logo | CMYK for dark background (PDF) — "Logo" |
| `assets/images/background.png` | image | Background image (logo on image) — "Logo" — allowed |
| `assets/logos/logo-dark-logo.svg` | logo | Logo file in image-background example — "Logo" — allowed |
| `assets/images/background-red.png` | image | Background image (logo on image) — "Logo" — allowed |
| `assets/logos/logo-dark-logo.svg` | logo | Logo file in image-background example — "Logo" — allowed |
| `assets/images/background-red.png` | image | Background image (logo on image) — "Logo" — forbidden |
| `assets/logos/logo-light-logo.svg` | logo | Logo file in image-background example — "Logo" — forbidden |
| `assets/images/background.png` | image | Background image (logo on image) — "Logo" — forbidden |
| `assets/logos/logo-light-logo.svg` | logo | Logo file in image-background example — "Logo" — forbidden |
| `assets/logos/logo-universal-symbol.svg` | logo | Universal logo — "Symbol" |
| `assets/logos/rb_piktogram_full_color_cmyk.pdf` | logo | CMYK for universal background (PDF) — "Symbol" |
| `assets/images/background.png` | image | Background image (logo on image) — "Symbol" — allowed |
| `assets/logos/logo-universal-symbol.svg` | logo | Logo file in image-background example — "Symbol" — allowed |
| `assets/images/background-red.png` | image | Background image (logo on image) — "Symbol" — allowed |
| `assets/logos/logo-universal-symbol.svg` | logo | Logo file in image-background example — "Symbol" — allowed |
| `assets/logos/logo-light-alternativni.svg` | logo | Logo for light background — "Alternativní" |
| `assets/logos/logo-dark-alternativni.svg` | logo | Logo for dark background — "Alternativní" |
| `assets/logos/rb_vertikalni_full_color_cmyk.pdf` | logo | CMYK for light background (PDF) — "Alternativní" |
| `assets/logos/rb_vertikalni_negativ_cmyk.pdf` | logo | CMYK for dark background (PDF) — "Alternativní" |
| `assets/images/background.png` | image | Background image (logo on image) — "Alternativní" — allowed |
| `assets/logos/logo-dark-alternativni.svg` | logo | Logo file in image-background example — "Alternativní" — allowed |
| `assets/images/background-red.png` | image | Background image (logo on image) — "Alternativní" — allowed |
| `assets/logos/logo-dark-alternativni.svg` | logo | Logo file in image-background example — "Alternativní" — allowed |
| `assets/images/background-red.png` | image | Background image (logo on image) — "Alternativní" — forbidden |
| `assets/logos/logo-light-alternativni.svg` | logo | Logo file in image-background example — "Alternativní" — forbidden |
| `assets/images/background.png` | image | Background image (logo on image) — "Alternativní" — forbidden |
| `assets/logos/logo-light-alternativni.svg` | logo | Logo file in image-background example — "Alternativní" — forbidden |
| `assets/fonts/permanentmarker-regular-czech-fix.otf` | download | Font download — “Permanent Marker” — Stáhnout Font |
| `assets/images/textove-styly.webp` | image | Image and text — “Styly textu” |
| `assets/images/ikony-cover.webp` | image | Large gallery — “Ikony” |
| `assets/images/ilustrace-cover.webp` | image | Large gallery — “Ilustrace” |
| `assets/images/net-cover.webp` | image | Large gallery — “Vzor sítě” |
| `assets/images/snimek-obrazovky-2026-05-14-v22.31.56.webp` | image | Large gallery — “Pozadí” |
| `assets/images/elementy-cover.webp` | image | Large gallery — “Ostatní elementy” |
| `assets/images/aplikace.webp` | image | Image and text — “Slidy prezentace” |
| `assets/images/open-single-catalog-mockup-template-6a064b9f4a726a7a1ff49c43--2x2-800x.webp` | image | Image and text — “Slidy prezentace” |
| `assets/images/ig-sablony.webp` | image | Image and text — “Slidy prezentace” |
| `assets/images/ig.webp` | image | Image and text — “Slidy prezentace” |
| `assets/images/ipad-pro-12.9-inch-mockup-6a0653a34a726a7a1ff49c53--2x.webp` | image | Image and text — “Slidy prezentace” |
| `assets/images/image-gigapixel-standard-v2-2x.webp` | image | Image and text — “Slidy prezentace” |
| `assets/images/pozitiv_exponential_summit_by_rb.webp` | image | Large gallery — “Exponential Summit” |
| `assets/others/exponential_summit.zip` | download | Balíček loga Exponential Summit |
| `assets/images/rb_pozitiv_network.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_shortcut.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_kniha_mesice.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_l-d.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_eduteka.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_circles.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_b-b.webp` | image | Large gallery — “Exponential Summit” |
| `assets/images/rb_pozitiv_edu.webp` | image | Large gallery — “Exponential Summit” |
| `assets/others/logo-subbrandy.zip` | download | Stáhnout balíček log subbrandů. |
| `assets/images/layout.webp` | image | Image and text — “Příklad layoutu tiskoviny” |
| `assets/images/snimek-obrazovky-2026-05-15-v9.14.18.webp` | image | Image and text — “Příklad layoutu prezentace” |
| `assets/images/pozadi-default.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/pozadi-default-1.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/pozadi-default-2.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/pozadi-anthracite.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/pozadi-anthracite-1.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/pozadi-red.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/pozadi-dark-red.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/group-1484579124.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/group-1484579126.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/group-1484579125.webp` | image | Gallery (logo on image) — “Barevné kombinace” — usage: allowed (check icon) |
| `assets/images/prace-s-grafikou/pozadi-default.webp` | image | Gallery (logo on image) — “Zakázané barevné kombinace” — usage: forbidden (strike-through) |
| `assets/images/prace-s-grafikou/pozadi-anthracite.webp` | image | Gallery (logo on image) — “Zakázané barevné kombinace” — usage: forbidden (strike-through) |
| `assets/images/prace-s-grafikou/pozadi-red.webp` | image | Gallery (logo on image) — “Zakázané barevné kombinace” — usage: forbidden (strike-through) |
| `assets/images/pozadi-red-1.webp` | image | Gallery (logo on image) — “Zakázané barevné kombinace” — usage: forbidden (strike-through) |
| `assets/images/prace-s-grafikou/pozadi-dark-red.webp` | image | Gallery (logo on image) — “Zakázané barevné kombinace” — usage: forbidden (strike-through) |
| `assets/images/pozadi-dark-red-1.webp` | image | Gallery (logo on image) — “Zakázané barevné kombinace” — usage: forbidden (strike-through) |
| `assets/images/rb-500x500_tucne-01-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-02-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-03-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-04-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-05-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-06-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-07-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-08-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-09-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-10-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-11-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-12-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-13-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-14-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-15-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-16-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-17-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-18-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-19-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-20-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-21-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-22-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-23-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-24-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-25-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-26-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-27-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-28-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-29-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-30-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-31-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-32-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-33-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-34-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-35-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-36-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-37-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-38-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-39-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-40-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-41-4.svg` | icon | Icon — “Ikony” |
| `assets/images/rb-500x500_tucne-42-4.svg` | icon | Icon — “Ikony” |
| `assets/images/ilustrace-27.svg` | icon | Icon — “Ilustrace” |
| `assets/images/ilustrace-31.svg` | icon | Icon — “Ilustrace” |
| `assets/images/ilustrace-47.svg` | icon | Icon — “Ilustrace” |
| `assets/images/ilustrace-46.svg` | icon | Icon — “Ilustrace” |
| `assets/images/ilustrace-49.svg` | icon | Icon — “Ilustrace” |
| `assets/images/ilustrace-50.svg` | icon | Icon — “Ilustrace” |
| `assets/images/ilustrace-48.svg` | icon | Icon — “Ilustrace” |
| `assets/images/zakladni-sit.svg` | icon | Icon — “Vzor sítě” |
| `assets/images/sit-1.svg` | icon | Icon — “Vzor sítě” |
| `assets/images/komponenty.webp` | image | Image and text — “Ostatní komponenty” |
| `assets/others/komponenty.zip` | download | Balíček komponent |
| `assets/images/frame-40083.webp` | image | Image and text — “Vizuální styl” |
| `assets/images/image-layer-6a064baa4a726a7a1ff49c45--2x.webp` | image | Image and text — “Vizuální styl” |
| `assets/images/beforeimage-0-image-201.webp` | image | Before (before/after) — “Fotografický filtr” |
| `assets/images/afterimage-0-image-200.webp` | image | After (before/after) — “Fotografický filtr” |
| `assets/images/tonovani.webp` | image | Image and text — “Brevná úprava fotografií” |
| `assets/images/cutout-in.webp` | image | Image and text — “Grafické zpracování: Cutout” |
| `assets/images/frame-40083.webp` | image | Carousel — “Umístění sítě do fotografie” |
| `assets/images/frame-40085.webp` | image | Carousel — “Umístění sítě do fotografie” |
| `assets/images/frame-40084b.webp` | image | Carousel — “Umístění sítě do fotografie” |

### Prezentace (slidy, Google Slides, tiskové jednostránky)

guidelines/slides.md

# Prezentace (slidy, Google Slides, tiskové jednostránky)

Vizuální jazyk prezentací Red Button EDU: světlé pozadí, antracitové verzálky Rubik Black, Wine jako hlavní barva značky, ručně kreslené prvky (rámečky, kruhy, šipky) a ruční písmo. Působí lidsky a „rukodělně“, ne korporátně. Zdroj: firemní šablona _Šablona RB prezentace_ (41 slidů, 1920 × 1080 px) sladěná s brand manuálem (rozhodnutí Lukáše Cypry, 9. 10. 2026). Pravidla pro web: `web-ui.md`.

## Principy

1. **Papír, ne bílá.** Obsahové slidy mají papírovou texturu `assets/Slides/pozadi-papir.png` (náhrada, když textura nejde vložit: plná barva `rb-off-white` #fafafa). Plné červené pozadí jen titul a předěly ve Wine (`surface-brand`). Čistě bílé pozadí obsahového slidu nepoužívej.
2. **Wine je hlavní barva.** Akcent v nadpisu, štítek, linka hlavičky, karty, čísla. Ostatní je Anthracite a šedé.
3. **Red Button `#e4003a` je jen akcent, ~5 % plochy.** Nejvýš jedno zvýraznění na slide (klíčové číslo, CTA, zakroužkování). Ne v nadpisu, na štítku, na ploše karet ani v textu odstavců. Nikdy červený text na Wine ploše.
4. **Ruka + systém.** Strukturu nesou Rubik verzálky a mřížka, lidskost dodávají kreslené rámečky, kruhy, šipky a ruční písmo. Na jednom slidu nejvýš 2–3 kreslené prvky.
5. **Dvoubarevný nadpis.** Nadpis verzálkami v Anthracite, klíčová část (2–3 slova) ve Wine: „CÍLE PROGRAMU ANEB **KAM MÍŘÍME**“.
6. **Každý obsahový slide má stejnou hlavičku:** hashtag štítek vlevo, Wine linka, logo Red Button vpravo, číslo strany vpravo dole.
7. **Málo textu, velké písmo.** Text min. 24 px na plátně 1920; odstavce max. 4–5 řádků; detail patří do poznámek řečníka.

## Barvy (hodnoty z manuálu)

- **Wine**`rb-wine` #a11834 – hlavní akcent a plné plochy. Bílý text 7,79:1.
- **Anthracite**`rb-anthracite` #444444 – nadpisy, text, tmavé karty a kroužky.
- **Red Button**`rb-red-button` #e4003a – akcent ≤ 5 %.
- **Grey**`rb-grey` #b0b2b6 – oddělovače, šedé rámečky. **Spanish Grey**`rb-spanish-grey` #969696 – jen nedůležité doplňky (2,96:1, pod AA).
- Slidové odchylky ze šablony byly sloučeny: #3f3f3f → Anthracite, #babbbd → Grey, #f2f2f2 → #fafafa, #9f1b3c a #a01d38 → Wine, #e3003a → Red Button. Staré názvy (`rb-crimson`, `rb-ink`, `rb-paper`…) zůstávají jako aliasy.
- Kombinace: bílý text na Wine nebo Anthracite; Wine nebo Anthracite text na světlém. Nikdy Red Button text na Wine.

## Typografie

- **Rubik Black (900)** – nadpisy, vždy VERZÁLKAMI: `slide-cover-title` 107 px, `slide-title` 56 px.
- **Rubik (400/500/700)** – text: `slide-body` 28 px, `slide-lead` 24 px, `slide-card-text` 20 px na kartách.
- **Permanent Marker** – štítky (`slide-section-tag` „#Design“), tagline, názvy kroků a uzlů (`slide-accent` 32 px), velká čísla a ceny (`slide-big-figure` 48 px). Nikdy na odstavce.
- **Čeština v ručním písmu (rozhodnutí 9. 10. 2026):** Permanent Marker nemá v prezentacích a v Google Slides dobře české znaky ě š č ř ž ů ť ď ň (a jejich verzálky). Každý ruční text, který některý z nich obsahuje, sázej CELÝ v **Kalam Bold** (700), styl `slide-accent-cz`, nikdy nemíchej písma v jednom slově. Platí pro všechny slidy včetně interních decků (Town hall apod.). Texty v Kalam VŽDY VERZÁLKAMI (Permanent Marker má velká písmena v sobě, Kalam ne): „ANEB TECHNAŘI“, „#ZMĚNA“, „LUKÁŠ CYPRA“. V rámci jedné komponenty drž jednotu: když jedno jméno v řadě karet potřebuje Kalam, dostanou ho všechna. Načítej Kalam vždy spolu s Permanent Marker.
- Tohle je firemní rozšíření pravidla z manuálu, který Kalam připouští jen pro otevřené prezentace klientům. Na webu, v tisku, brandingu a merchi se Kalam nepoužívá, tam platí CZ-fix Permanent Marker.
- Fonty jsou z Google Fonts (Rubik, Permanent Marker, Kalam). Alternativy pro materiály k další úpravě, když příjemce nemůže font nainstalovat: Rubik nadpisy → Arial Black, Rubik text → Arial, Permanent Marker → Kalam (Google Slides) / Trebuchet MS Bold (PPTX). Nikdy na tisk a merch.

## Anatomie obsahového slidu (1920 × 1080)

| prvek | poloha | styl |
| --- | --- | --- |
| štítek `#Téma` | vlevo nahoře, x 106, y 28 (řádek 34 px) – svisle na středu linky hlavičky; VŽDY na jednom řádku | `slide-section-tag`, Wine |
| linka hlavičky | y 38, výška 14 (střed y 45); začíná 24 px za koncem štítku (u „#Design“ ≈ x 236) a končí ~20 px před logem (x ≈ 1626) | `assets/Slides/linka-hlavicky.png` roztažená |
| logo | vpravo nahoře, ~210 × 58 | logo Red Button (skupina _Logos_) |
| nadpis | x 106, y 112 | `slide-title`, dvoubarevný |
| podtitul / lead | y ≈ 210 | `slide-lead` |
| obsah | od y ≈ 300, okraje 106 | 2–4 sloupce, mezera 64 |
| číslo strany | vpravo dole (right 64, bottom 64) | `slide-page-number`; za ním `assets/Slides/oblouk-roh.png` ~520 × 520 px s levým horním rohem na x 1700, y 850 – do slidu zasahuje jen levá horní čtvrtina kruhu |

Poloha a rozměry pocházejí ze šablony, v manuálu je jen ukázkový obrázek layoutu.

## Typy slidů ze šablony

- **Titul** – logo klienta vlevo nahoře (pokud je), logo RB vpravo, tagline (marker), NÁZEV PROGRAMU, datum dole, velká kreslená ilustrace vpravo. Varianta na Wine pozadí s bílým textem a negativním logem.
- **Kde jsme a kam směřujeme** – seznam s fajfkami vlevo, kreslený diagram (rámečky + šipky) vpravo, pointa se žárovkou.
- **Citace** – fotka osoby ořízlá do cutoutu, citace v kreslené bublině, citace i jméno v Kalam Bold verzálkami (`slide-accent-cz`).
- **Cesta / moduly** – 4–5 číslovaných kroků na lince, pod každým název (verzálky), podtitul a 2–3 položky.
- **Cíle** – 5 cílů s velkými markerovými čísly 1.–5. ve Wine.
- **Tabulka „Dnes vs. po programu“** – 3 sloupce (Oblast / Dnes / Po programu), tečkované oddělovače (`linka-teckovana.png`), diagonální šipky.
- **Roadmapa** – 4 karty (Wine, Anthracite nebo obrysové) s kroužkem a bílou ikonou nahoře; nebo časová osa fází 01–04.
- **Lektor / průvodce, Reference, Cena a rozsah, O nás, Další krok / kontakt, Text + fotka** – layouty podle šablony _Šablona RB prezentace_.

## Obrázky a ilustrace

- **Fotky vždy černobílé** (nebo tónované do Wine), lidé často vystřižení z pozadí v cutoutu.
- **Ilustrace a ikony jsou ručně kreslené:** Wine na světlém, bílé na Wine nebo tmavé ploše (v kroužku `kruh-tmavy.png`). Neskládej je s plochými ikonami z knihoven. Ikony, ilustrace, rámečky a vzor sítě jsou ve skupinách _icons_, _Images_ a _frames_.
- Skupina _Slides_ obsahuje papírové pozadí `pozadi-papir` a kreslené prvky specifické pro slidy: `linka-hlavicky`, `linka-teckovana`, `oblouk-roh`, `tahy-zdurazneni`, `plocha-cervena`, `kruh-tmavy`, `skvrna`. Barvy přenesených kreslených prvků jsem změřil: Wine (`#a11834`), Anthracite, Grey a Spanish Grey. Red Button v nich není.
- Loga klientů jen na titulním a referenčním slidu.

## Obsah a jazyk

- Česky (angličtina jen pro anglické klienty), tón přímý a lidský, lehce hravý („aneb“, „aka“).
- Nadpisy jako tvrzení nebo otázka, ne jen téma: „JAK POZNÁME, ŽE JSME USPĚLI:“.
- Datum na titulu „květen 2026“; částky „390.000 Kč bez DPH“.
- Emoji nepoužívej.

## Nedělej

- Gradienty, stíny, zaoblené CSS karty, modré a fialové barvy.
- Red Button na plochy nebo do nadpisů; víc než jedno zvýraznění Red Buttonem na slide.
- Permanent Marker na delší text; nadpisy malými písmeny.
- Obsahový slide bez hlavičky se štítkem a logem.

### Web a UI

guidelines/web-ui.md

# Web a UI

Pravidla pro digitální výstupy Red Button EDU (web, aplikace, dashboardy). Vychází z brand manuálu; co manuál neurčuje, je v tokenech označené jako „odvozeno“ nebo „MIMO manuál“.

## Barvy a témata

- Světlý režim je standard: `bg` (#fafafa), `surface` (bílá), `text` (Anthracite), `accent-text` a `accent-display` (Wine), `action` (Red Button) pro primární CTA.
- Tmavý režim jen výjimečně (např. web Exponential Summit): `data-theme="dark"` na `<html>`; akcent Apple Red, plochy Red Black. Nikdy v tisku a oficiálních materiálech.
- Odkazy `link` (#fe1a3f) jsou vždy podtržené.
- Stavové barvy `success-*` a `warning-*` manuál nemá, jsou doplněné pro UI. Chyby jsou v barvě značky (`error-text`).

## Typografie

- Rubik pro nadpisy i text, Permanent Marker jen pro podnadpisy, nadpisy boxů, přímou řeč a citace, vždy v `accent-display`. Vždy CZ-fix verze `fonts/permanentmarker-regular-czech-fix.otf`; Kalam se na webu nepoužívá.
- Styly: `h1-hero`, `h1`, `h2`, `h3`, `lead`, `body`, `button`, `eyebrow`, `caption`; `ui` a `ui-small` jsou doplněk pro rozhraní.

## Rozvržení a tvary

- Zaoblení karet a boxů 6 px (`radius-card`); tabulky a plné pásy bez zaoblení (`radius-none`). Stíny jen u překryvných prvků a hoveru karet.
- Mezery ve škále `space-*`, max. šířka obsahu `container-max` (1200 px), hlavička `header-height` (72 px) – odvozené hodnoty, manuál je neurčuje.
- Focus: 2px plná linka v barvě `focus`, odsazení 2 px.

## Logo

- Na světlé pozadí `logo-light-logo.svg`, na tmavé a Wine pozadí `logo-dark-logo.svg`. Min. výška na obrazovce 20 px (alternativní 24 px), ochranná zóna 50 % výšky loga.
- Logo na barevném pozadí jen na #fafafa, #a11834 nebo #444444. Nikdy na Apple Red. Neotáčet, bez stínů, nepřebarvovat, nedeformovat.

## Implementace

- Načti `tokens.css`, Rubik z Google Fonts, `@font-face` pro Permanent Marker CZ (z `fonts/`) a `components/bundle.css`. Pak používej komponenty a třídy z návodů komponent.

### Social UI kit

ui\_kits/social/README.md

# Social UI kit

Recreation of the brand's demonstrated Instagram templates (source: manual "Ukázky použití" — ig.webp, ig-sablony.webp).

- **SocialPost** — text template in the three demonstrated variants: light / wine / anthracite.
- **PhotoPost** — B&W photo post with torn wine banner headline and URL footer.

No website or app source was provided in the manual, so no web/app kit exists — these social surfaces and the deck template (templates/pitch-deck) are the brand's demonstrated surfaces.

# Colors

Palette

NameSvětlý (standard)Tmavý (výjimečný)

bgrb-off-whiterb-red-black

linkrb-apple-redrb-apple-red

focusrb-red-buttonrb-white

overlayrgba(38,38,38,0.6)rgba(38,38,38,0.6)

rb

NameSvětlý (standard)Tmavý (výjimečný)

rb-red-button#e4003a#e4003a

rb-wine#a11834#a11834

rb-anthracite#444444#444444

rb-white#ffffff#ffffff

rb-off-white#fafafa#fafafa

rb-grey#b0b2b6#b0b2b6

rb-spanish-grey#969696#969696

rb-button-redrb-red-buttonrb-red-button

rb-apple-red#fe1a3f#fe1a3f

rb-red-black#262626#262626

rb-crimsonrb-winerb-wine

rb-crimson-deeprb-winerb-wine

rb-crimson-paperrb-winerb-wine

rb-logo-redrb-red-buttonrb-red-button

rb-ink-strongrb-anthraciterb-anthracite

rb-inkrb-anthraciterb-anthracite

rb-blackrb-anthraciterb-anthracite

rb-mutedrb-spanish-greyrb-spanish-grey

rb-subtlerb-spanish-greyrb-spanish-grey

rb-linerb-greyrb-grey

rb-paperrb-off-whiterb-off-white

rb-paper-lightrb-off-whiterb-off-white

logo

NameSvětlý (standard)Tmavý (výjimečný)

logo-red-deep#a31834#a31834

logo-ink#4a4a49#4a4a49

logo-gray-light#ededed#ededed

logo-gray#bdbcbc#bdbcbc

surface

NameSvětlý (standard)Tmavý (výjimečný)

surface-pagerb-off-whiterb-off-white

surface-cardrb-whiterb-white

surface-brandrb-winerb-wine

surface-darkrb-anthraciterb-anthracite

surface-darkmoderb-red-blackrb-red-black

surfacerb-whiterb-anthracite

surface-sunkenrb-off-whiterb-red-black

text

NameSvětlý (standard)Tmavý (výjimečný)

text-headingrb-anthracite9.3:1Good contrast, 9.3 to 1 on bg (Světlý (standard)); 4 more grounds passrb-anthracite1.0:1Poor contrast, 1.0 to 1 on surface (Tmavý (výjimečný)), below 4.5 to 1; also below 4.5 to 1 on bg (Tmavý (výjimečný)) and surface-sunken (Tmavý (výjimečný)); 2 more grounds passhard to read onsurface

text-bodyrb-anthracite9.3:1Good contrast, 9.3 to 1 on bg (Světlý (standard)); 4 more grounds passrb-anthracite1.0:1Poor contrast, 1.0 to 1 on surface (Tmavý (výjimečný)), below 4.5 to 1; also below 4.5 to 1 on bg (Tmavý (výjimečný)) and surface-sunken (Tmavý (výjimečný)); 2 more grounds passhard to read onsurface

text-mutedrb-spanish-grey2.8:1Poor contrast, 2.8 to 1 on bg (Světlý (standard)), below 4.5 to 1; also below 4.5 to 1 on surface-page (Světlý (standard)) and surface-sunken (Světlý (standard)) and surface-card (Světlý (standard)) and surface (Světlý (standard))hard to read onbgrb-spanish-grey2.8:1Poor contrast, 2.8 to 1 on surface-page (Tmavý (výjimečný)), below 4.5 to 1; also below 4.5 to 1 on surface-card (Tmavý (výjimečný)) and surface (Tmavý (výjimečný)); 2 more grounds passhard to read onsurface-page

text-on-darkrb-whiterb-white

text-accentrb-wine7.4:1Good contrast, 7.4 to 1 on bg (Světlý (standard)); 4 more grounds passrb-wine1.2:1Poor contrast, 1.2 to 1 on surface (Tmavý (výjimečný)), below 4.5 to 1; also below 4.5 to 1 on bg (Tmavý (výjimečný)) and surface-sunken (Tmavý (výjimečný)); 2 more grounds passhard to read onsurface

textrb-anthracite9.3:1Good contrast, 9.3 to 1 on bg (Světlý (standard)); 4 more grounds passrb-white1.0:1Poor contrast, 1.0 to 1 on surface-card (Tmavý (výjimečný)), below 4.5 to 1; also below 4.5 to 1 on surface-page (Tmavý (výjimečný)); 3 more grounds passhard to read onsurface-card

text-caption-colorrb-spanish-grey2.8:1Poor contrast, 2.8 to 1 on bg (Světlý (standard)), below 4.5 to 1; also below 4.5 to 1 on surface-page (Světlý (standard)) and surface-sunken (Světlý (standard)) and surface-card (Světlý (standard)) and surface (Světlý (standard))hard to read onbgrb-grey2.0:1Poor contrast, 2.0 to 1 on surface-page (Tmavý (výjimečný)), below 4.5 to 1; also below 4.5 to 1 on surface-card (Tmavý (výjimečný)); 3 more grounds passhard to read onsurface-page

accent

NameSvětlý (standard)Tmavý (výjimečný)

accentrb-red-buttonrb-red-button

accent-darkmoderb-apple-redrb-apple-red

accent-textrb-winerb-grey

accent-displayrb-winerb-apple-red

button

NameSvětlý (standard)Tmavý (výjimečný)

button-primaryrb-red-buttonrb-red-button

border

NameSvětlý (standard)Tmavý (výjimečný)

border-subtle#e2e2e2#e2e2e2

border-brandrb-winerb-wine

borderlogo-gray-lightrb-red-black

border-controlrb-spanish-greyrb-grey

action

NameSvětlý (standard)Tmavý (výjimečný)

actionrb-red-buttonrb-apple-red

action-hoverrb-winerb-red-button

on

NameSvětlý (standard)Tmavý (výjimečný)

on-action#ffffff4.8:1Good contrast, 4.8 to 1 on action (Světlý (standard))#ffffff3.8:1Poor contrast, 3.8 to 1 on action (Tmavý (výjimečný)), below 4.5 to 1hard to read onaction

on-inverse#ffffff#ffffff

fill

NameSvětlý (standard)Tmavý (výjimečný)

fill-hoverlogo-gray-lightrb-red-black

inverse

NameSvětlý (standard)Tmavý (výjimečný)

inverse-bgrb-winerb-wine

success

NameSvětlý (standard)Tmavý (výjimečný)

success-bg#f0fdf4rgba(13,84,43,0.25)

success-text#008236#05df72

warning

NameSvětlý (standard)Tmavý (výjimečný)

warning-bg#fffbebrgba(123,51,6,0.25)

warning-text#bb4d00#ffb900

error

NameSvětlý (standard)Tmavý (výjimečný)

error-bg#fef2f2rgba(254,26,63,0.12)

error-textrb-red-buttonrb-apple-red

# Typography

Nadpisy (Rubik)

NamePreview

h1-heroThe quick brown fox jumps over the lazy dogRubik · 128/1 · 900 · -0.01em

h1The quick brown fox jumps over the lazy dogRubik · 64/1.05 · 900

h2The quick brown fox jumps over the lazy dogRubik · 42/1.15 · Heavy

h3The quick brown fox jumps over the lazy dogRubik · 24/1.3 · Bold

Akcent (Permanent Marker, web a tisk)

NamePreview

h2-markerThe quick brown fox jumps over the lazy dogPermanent Marker · 42/1.2 · Regular

h4-markerThe quick brown fox jumps over the lazy dogPermanent Marker · 24/1.3 · Regular

marker-tagThe quick brown fox jumps over the lazy dogPermanent Marker · 18/1.2 · Regular

Text (Rubik)

NamePreview

leadThe quick brown fox jumps over the lazy dogRubik · 21/1.45 · Medium

bodyThe quick brown fox jumps over the lazy dogRubik · 18/1.55 · Regular

buttonThe quick brown fox jumps over the lazy dogRubik · 16/1.25 · Heavy

eyebrowThe quick brown fox jumps over the lazy dogRubik · 16/1.3 · Bold · 0.1em

captionThe quick brown fox jumps over the lazy dogRubik · 16/1.45 · Regular

uiThe quick brown fox jumps over the lazy dogRubik · 14/1.43 · Medium

ui-smallThe quick brown fox jumps over the lazy dogRubik · 12/1.33 · Regular

Prezentace – Rubik (plátno 1920×1080)

NamePreview

slide-cover-titleThe quick brown fox jumps over the lazy dogRubik · 107/0.95 · 900

slide-titleThe quick brown fox jumps over the lazy dogRubik · 56/1.15 · 900

slide-step-numberThe quick brown fox jumps over the lazy dogRubik · 47/1 · 900

slide-page-numberThe quick brown fox jumps over the lazy dogRubik · 27/1 · 900

slide-bodyThe quick brown fox jumps over the lazy dogRubik · 28/1.45 · Regular

slide-body-strongThe quick brown fox jumps over the lazy dogRubik · 28/1.45 · Bold

slide-leadThe quick brown fox jumps over the lazy dogRubik · 24/1.4 · Regular

slide-dateThe quick brown fox jumps over the lazy dogRubik · 28/1.3 · Medium

slide-card-textThe quick brown fox jumps over the lazy dogRubik · 20/1.4 · Regular

slide-captionThe quick brown fox jumps over the lazy dogRubik · 24/1.35 · Regular

Prezentace – ruční písmo (Permanent Marker)

NamePreview

slide-taglineThe quick brown fox jumps over the lazy dogPermanent Marker · 48/1.2 · Regular

slide-big-figureThe quick brown fox jumps over the lazy dogPermanent Marker · 48/1.1 · Regular

slide-accentThe quick brown fox jumps over the lazy dogPermanent Marker · 32/1.25 · Regular

slide-section-tagThe quick brown fox jumps over the lazy dogPermanent Marker · 28/1 · Regular

Prezentace – ruční písmo s češtinou (Kalam)

NamePreview

slide-accent-czThe quick brown fox jumps over the lazy dogKalam · 32/1.25 · Bold

Font files

permanentmarker-regular-czech-fix.otfPermanent Marker 400

# Spacing

NameValue

space-14px

space-28px

space-312px

space-416px

space-524px

space-632px

space-748px

space-864px

space-996px

slide-width1920px

slide-height1080px

slide-margin-x106px

slide-title-top112px

slide-content-top210px

slide-header-line-top38px

slide-card-width315px

slide-page-number-offset64px

# Corner radius

NameValue

radius-none0px

radius-card6px

radius-button6px

radius-pill999px

# Shadows

NameSvětlý (standard)Tmavý (výjimečný)

shadow-cardNoneNone

shadow-float0, 8 · 32px0, 8 · 32px

# Font weight

NameValue

weight-regular400

weight-medium500

weight-bold700

weight-extrabold800

weight-black900

# Font size

NameValue

text-h1-hero128px

text-h164px

text-h242px

text-h324px

text-sub24px

text-lead21px

text-p18px

text-button16px

text-caption14px

# Line height

NameValue

leading-tight1.05

leading-heading1.15

leading-body1.6

# Letter spacing

NameValue

tracking-heading0em

tracking-caps0.08em

# Breakpoint

NameValue

bp-sm640px

bp-md768px

bp-lg1024px

bp-xl1280px

# Layout

NameValue

container-max1200px

header-height72px

logo-min-height20px

logo-clearspace50%

# Z index

NameValue

z-header30

z-overlay50

# Components

Světlý (standard)

NamePreview

ICON\_NAMES
No preview yet — ask Claude for components/ICON\_NAMES/preview.html.

Icon
No preview yet — ask Claude for components/Icon/preview.html.


Logo
No preview yet — ask Claude for components/Logo/preview.html.


MarkerNote
No preview yet — ask Claude for components/MarkerNote/preview.html.


NetPattern
No preview yet — ask Claude for components/NetPattern/preview.html.


Badge
No preview yet — ask Claude for components/Badge/preview.html.


Card
No preview yet — ask Claude for components/Card/preview.html.


Tabs
No preview yet — ask Claude for components/Tabs/preview.html.


Tag
No preview yet — ask Claude for components/Tag/preview.html.


Dialog
No preview yet — ask Claude for components/Dialog/preview.html.


Toast
No preview yet — ask Claude for components/Toast/preview.html.


Tooltip
No preview yet — ask Claude for components/Tooltip/preview.html.


Button
No preview yet — ask Claude for components/Button/preview.html.


Checkbox
No preview yet — ask Claude for components/Checkbox/preview.html.


IconButton
No preview yet — ask Claude for components/IconButton/preview.html.


Input
No preview yet — ask Claude for components/Input/preview.html.


Radio
No preview yet — ask Claude for components/Radio/preview.html.


Select
No preview yet — ask Claude for components/Select/preview.html.


Switch
No preview yet — ask Claude for components/Switch/preview.html.


PhotoPost
No preview yet — ask Claude for components/PhotoPost/preview.html.


SocialPost
No preview yet — ask Claude for components/SocialPost/preview.html.


Brand



BrandRules



Display



Feedback

![check](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-18.svg)Přihláška odeslána!×

![cross](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-19.svg)Něco se pokazilo.

Manuál (hover)![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/components/Feedback/assets/frames/frame-short-wine.svg)Marker tooltip![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/frames/frame-short-red.svg)Otevřít dialog



Forms

![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/frames/frame-short-red.svg)Jdu do toho!![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/frames/frame-short-wine.svg)Více info![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/frames/frame-short-grey.svg)NeživéStáhnoutCelý program![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/frames/frame-short-red.svg)Odesláno![arrow-right](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-16.svg)![mail](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-15.svg)

![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/frames/frame-long-red-2.svg)Chci vědět více o programuFilled fallbackOutline fallback

E-mailJménoPovinné poleProgram
R(e)BeLeaderBrain&BreakCircles

Souhlasím s podmínkamiNewsletterMěsíčněRočněNotifikace



Index

Red Button — Social kit

![Red Button](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/logos/logo-light-logo.svg)Šablony příspěvků

SvětláVínováAntracit

![Red Button](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/logos/logo-light-logo.svg)

READY

TO LEAD

![idea-bulb](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-26.svg)

Rozvojový program pro Albert

![arrow-curve-left](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-10.svg)

Šitý na míru, aby měnil mindset, ne jen dovednosti.

![arrow-curve-left](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-10.svg)

Protože přechod z experta na lídra je cesta, ne okamžik.

![arrow-curve-left](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-10.svg)

![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/patterns/zakladni-sit.svg)

Foto příspěvek

#Leadership![Red Button](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/logos/logo-light-logo.svg)

![](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/photos/photo-filtered-bw.webp)

NEJSTE V TOM SAMI

„Máme skvělé odborníky. Ale nejsou připraveni vést lidi.“

Tuhle větu slyšíme ve firmách čím dál častěji — silní experti excelují ve své oblasti, ale v roli lídra tápou. Chybí jim nejen potřebné dovednosti, ale především mindset a sebevědomí.

![idea-bulb](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/project/assets/icons/icon-26.svg)

www.redbuttonedu.cz



Personas

Persony klient

# Komu píšeme

Kupují vizi

## Leaders

„Potřebuji parťáka pro byznys, ne školení pro zaměstnance.“

Co kupují

- Řešení na klíč („Mr. Wolf“) a klid
- Transformaci mindsetu, ne kurzy
- Benchmark a exkluzivní komunitu

Jazyk salesu

- Výsledky, ROI, efektivita, riziko
- Consultative sales, ne katalog

Gatekeeper & stratég

## L&D Owners

„Chci být architektem změny, ne objednávka školení.“

Co kupují

- Strategické partnerství, jistotu
- Munici pro board (RB Index, data)
- Capability building, ne jednorázovky

Jazyk salesu

- Co-creation, spolutvorba
- L&D terminologie + byznys dopad

Evaluator & influencer

## L&D Operations

„Potřebuji, aby to fungovalo, bavilo lidi a ušetřilo mi práci.“

Co kupují

- Úsporu času, bezstarostnost
- Hotové produkty (EDUtéka, katalog)
- Podklady pro interní prodej

Jazyk salesu

- Support & educate, demo ne vize
- Nasazení do 48 h, žádné IT projekty



# Assets

### Images

NamePreviewType

cutout-example.webp![cutout-example.webp](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/60cb48c6d96b3b88761edda7b6a682a4)WEBP · 357 KB

ilustrace-27.svg![ilustrace-27.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/fa804c3dbd3ee8f43a19493f6bbe1fc1)SVG · 39 KB

ilustrace-31.svg![ilustrace-31.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/c52aace33055fb2b0f349cd8ccbff709)SVG · 48 KB

ilustrace-46.svg![ilustrace-46.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/7ced070294abe9553d0c5e1bc3ee1fd9)SVG · 39 KB

ilustrace-47.svg![ilustrace-47.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/51c730b033eaa58b77b029489832a2f1)SVG · 31 KB

ilustrace-48.svg![ilustrace-48.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/2562e120ef86b41dff48d31c52d15b19)SVG · 57 KB

ilustrace-49.svg![ilustrace-49.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/054266067874ae330f716e2c0c416bd8)SVG · 69 KB

ilustrace-50.svg![ilustrace-50.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/a392e1e1decd8b1a577b2e8e8298cbba)SVG · 19 KB

photo-conversation-net.webp![photo-conversation-net.webp](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/c1ca2f897d33dfd42a87d043dd37fc99)WEBP · 485 KB

### Logos

NamePreviewType

logo-dark-alternativni.svg![logo-dark-alternativni.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/b656fe8de6030a73b88649b66ff68edc)SVG · 8 KB

logo-dark-logo.svg![logo-dark-logo.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/041da01038e564e4f18cc03794e49bc1)SVG · 8 KB

logo-light-logo.svg![logo-light-logo.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/99267bf181473e16d3ee847a1816ff03)SVG · 8 KB

logo-universal-symbol.svg![logo-universal-symbol.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/bc9abeed4618424758aa0d8c28573e29)SVG · 1 KB

### Reference

NamePreviewType

background-red.png![background-red.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/0bbdd57d09db1f4191d478b6b65f04d3)PNG · 42 KB

sit-1.svg![sit-1.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/406f7c6a5b3b31ad66b0bd05ba389bfd)SVG · 232 KB

zakladni-sit.svg![zakladni-sit.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/78d342273c74c896cd32cf56d1cfde36)SVG · 108 KB

### backgrounds

NamePreviewType

background.png![background.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/ffbe9e3cfa95b06a7c25842989268394)PNG · 38 KB

### frames

NamePreviewType

frame-long-grey.svg![frame-long-grey.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/78d16502dedefb8bbcdb33f64de04cc3)SVG · 109 KB

frame-long-red-2.svg![frame-long-red-2.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/32136d76d98b21aeb8a32b39c7852039)SVG · 111 KB

frame-long-red.svg![frame-long-red.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/1b94a2ce15ae0ad08b52e051fde3da92)SVG · 110 KB

frame-long-wine.svg![frame-long-wine.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/e516d0b150b45c6a139f1de3e862712f)SVG · 109 KB

frame-short-grey.svg![frame-short-grey.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/83e23e17a30eb3f01c1663eface584bc)SVG · 108 KB

frame-short-red-2.svg![frame-short-red-2.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/73965f2cdd2ac738ca6203bd0a80fdd6)SVG · 108 KB

frame-short-red.svg![frame-short-red.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/ab9931cc52293f68917fc12a8e272ce6)SVG · 108 KB

frame-short-wine.svg![frame-short-wine.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/833e641cd6d8a773833bb3b35aa0c4bf)SVG · 108 KB

### icons

NamePreviewType

icon-01.svg![icon-01.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/f2278a6ab41f3457e2a728e56a90917f)SVG · 5 KB

icon-02.svg![icon-02.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/e45ff67af96503f363cb5da4153af880)SVG · 3 KB

icon-03.svg![icon-03.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/50739b709a0360fe83e7dae444901057)SVG · 3 KB

icon-04.svg![icon-04.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/ffcf3d4e89388018f846341d80fd25e0)SVG · 5 KB

icon-05.svg![icon-05.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/5014fcb3f20bda0f840769c6895fd800)SVG · 3 KB

icon-06.svg![icon-06.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/b37ee1093ea708dff63093e2c941849a)SVG · 5 KB

icon-07.svg![icon-07.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/ffcef64aa1128cb7e12ce74d2218ee4d)SVG · 8 KB

icon-08.svg![icon-08.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/8d4a399baef18e270b7e1f17ce05ced7)SVG · 953 B

icon-09.svg![icon-09.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/97d9fe50a41c7c2de8e040c0d14b1775)SVG · 1 KB

icon-10.svg![icon-10.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/edda8752b543ad0b2dab779fee9a8af2)SVG · 3 KB

icon-11.svg![icon-11.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/b347b43d186e495d7129027c8b66f160)SVG · 6 KB

icon-12.svg![icon-12.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/ccb384e349d9f17fa060d8e952833c43)SVG · 6 KB

icon-13.svg![icon-13.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/a57f2452456c088c89df35eae1084c68)SVG · 8 KB

icon-14.svg![icon-14.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/80a5718928be0bc7af6f050001c33cc6)SVG · 9 KB

icon-15.svg![icon-15.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/c565e6d50132a5e0a7c5f5386fb19763)SVG · 9 KB

icon-16.svg![icon-16.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/2f2755868093e6d6fe4acaeae0831be1)SVG · 7 KB

icon-17.svg![icon-17.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/d039851367f7d5ab2218d1352655d3a8)SVG · 6 KB

icon-18.svg![icon-18.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/947085c770940fdfdd36b726deb39efb)SVG · 7 KB

icon-19.svg![icon-19.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/bdbc42b205df3445cbc1099902876e5d)SVG · 15 KB

icon-20.svg![icon-20.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/dd9242f11fb2ecda388a277b428954b7)SVG · 9 KB

icon-21.svg![icon-21.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/ec92f9ad54b62f6fa7d6439c3639246a)SVG · 14 KB

icon-22.svg![icon-22.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/105b9bb2fb3a9aeca2f9fea18c4560e9)SVG · 10 KB

icon-23.svg![icon-23.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/7b2f0b8baa135bd93415c7a5b2527401)SVG · 18 KB

icon-24.svg![icon-24.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/e0c5d108032259852831d27c514a0b56)SVG · 10 KB

icon-25.svg![icon-25.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/575bd2dd73f4a41ef564a429edc4966e)SVG · 17 KB

icon-26.svg![icon-26.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/250511e58360c631fbc2238f9aa2c238)SVG · 14 KB

icon-27.svg![icon-27.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/1043a90fe193ccc931b8dbeaba30d7b4)SVG · 6 KB

icon-28.svg![icon-28.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/2d82e022cb31730394d90aadcfe6c87a)SVG · 12 KB

icon-29.svg![icon-29.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/366f0f4bbb32b02f21f6b84cbc1d8129)SVG · 26 KB

icon-30.svg![icon-30.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/d753b2f9d87f88af1d6d8d40686544da)SVG · 7 KB

icon-31.svg![icon-31.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/be51f051fe57c19763fefaa3c494abf4)SVG · 11 KB

icon-32.svg![icon-32.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/6434444fa22b41e06a15d2304af93eb9)SVG · 8 KB

icon-33.svg![icon-33.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/4b2ef28b72cf40e2bcf60f405a325e9d)SVG · 7 KB

icon-34.svg![icon-34.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/216fcd301f5c372903e48473557658ad)SVG · 10 KB

icon-35.svg![icon-35.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/a8ea00c8bad60d0cd0529af931a9d0e9)SVG · 8 KB

icon-36.svg![icon-36.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/2fc1b11fdb322ee0b94279d972c3b76d)SVG · 6 KB

icon-37.svg![icon-37.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/5ef4db9aba7e0169ff760650b2241058)SVG · 7 KB

icon-38.svg![icon-38.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/db9be6c19983ebb95933e809f0f56983)SVG · 12 KB

icon-39.svg![icon-39.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/7611ba8575a904f0d1a569ad2ddf4788)SVG · 8 KB

icon-40.svg![icon-40.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/7b6c15a7ed1d0559600aa1be115e4a5e)SVG · 5 KB

icon-41.svg![icon-41.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/d510a9e6911671f487c65ef1d24cce4c)SVG · 8 KB

icon-42.svg![icon-42.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/0619d5c797be474d070dfcd23c201e05)SVG · 6 KB

### logos

NamePreviewType

logo-light-alternativni.svg![logo-light-alternativni.svg](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/dd2ce4ba066744ac98167438af39741f)SVG · 8 KB

rb\_horizontalni\_full\_color\_cmyk.pdfPDF · 24 KB

rb\_horizontalni\_negativ\_cmyk.pdfPDF · 20 KB

rb\_piktogram\_full\_color\_cmyk.pdfPDF · 23 KB

rb\_vertikalni\_full\_color\_cmyk.pdfPDF · 28 KB

rb\_vertikalni\_negativ\_cmyk.pdfPDF · 20 KB

### photos

NamePreviewType

photo-filtered-bw.webp![photo-filtered-bw.webp](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/5f055be3d1c8b1957215bc4d1f77ceae)WEBP · 478 KB

photo-net-corner-1.webp![photo-net-corner-1.webp](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/147213932e36529375f150771b67ecab)WEBP · 486 KB

photo-net-corner-2.webp![photo-net-corner-2.webp](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/d776bde3982486dd39f751f75679272f)WEBP · 480 KB

portrait-cutout.webp![portrait-cutout.webp](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/aa08a19a369ea009bcc5fe5e88fecff4)WEBP · 180 KB

### Slides

NamePreviewType

kruh-tmavy.png![kruh-tmavy.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/0834ecfbf775c5d139be86b605021289)PNG · 42 KB

linka-hlavicky.png![linka-hlavicky.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/6c32e9a541edd1d7a5a6d95d75093dc9)PNG · 908 B

linka-teckovana.png![linka-teckovana.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/80f1061d923be7e51c358e7a1df98d82)PNG · 4 KB

oblouk-roh.png![oblouk-roh.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/a8ab2f805530d5b5d83dd534dce30486)PNG · 32 KB

plocha-cervena.png![plocha-cervena.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/c573cd9faaa967f7a8ce56f873986100)PNG · 16 KB

pozadi-papir.png![pozadi-papir.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/91c3ef18490519484a3ac65134a04873)PNG · 1.9 MB

skvrna.png![skvrna.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/cb8bdc5db29f78c25987837c385bc835)PNG · 11 KB

tahy-zdurazneni.png![tahy-zdurazneni.png](https://82a5cdfd-4a71-494e-8ff5-18d4e18f4521.frame.claudeusercontent.com/_f/1791585516-d87a/_blob/923d69216a6604402ab7fb8e875b66c4)PNG · 2 KB

README.mdMarkdown · 994 B

Stored alongside the page: 85 files · 6.4 MB of 1024 MB used

Sign in to see this artifact’s data

Sign in to see this artifact’s data [Sign in](https://claude.ai/login?returnTo=%2Fartifact%2FH8iBbMwMhU7RQ8efaZVuDS)
