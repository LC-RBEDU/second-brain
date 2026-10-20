# Red Button Design System

**Red Button** is a Czech ecosystem/network of business professionals — leaders, lecturers, entrepreneurs, experts and change guides — connecting people for 10+ years. Motto: *"Nejsme vzdělávací agentura. Jsme síť."* (We are not a training agency. We are a network.) Sub-brand **Red Button EDU** partners with companies on people development ("zlepšujeme společnost skrze rozvoj firem" — we improve society through developing companies). Network of 90+ experts. Sub-brands include Exponential Summit, Network, Shortcut, Kniha měsíce, L&D, Eduteka, Circles, B&B, EDU.

**Primary language of all copy: Czech.** Web: www.redbuttonedu.cz · IG: @red_button_edu

## Sources
- **Authoritative:** `guidelines/brand-manual.cs.md` — the **complete** Visualbook export (2026-07-22), including the previously-protected sections (client personas, brand rules, tone of voice). English condensation in `guidelines/brand-manual.en.md`.
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
- **Type (UI kit 19. 10. 2026):** H1 Rubik Black 64px (hero 128px), ALL-CAPS for display headlines (`h1`, `h1-hero`); **H2 Permanent Marker 42px** (`h2`); H3 Rubik Bold 24px (`h3`); **H4 Permanent Marker 24px** (`h4-marker`, box and card titles); **paragraphs Gotham Medium** – large 18px (`lead`), regular 16px (`body`), family `body` (Gotham is not bundled yet: until its licensed font file is added to `fonts/`, text falls back to Rubik Medium); buttons and captions Rubik Extrabold 16px (`button`, `caption`). Section labels ALL-CAPS with tracking in `label-section` (Wine on light, Red Button on dark). A headline mixing Rubik and Marker keeps equal line spacing above and below the marker line. Accent font **Permanent Marker** (Czech-fixed OTF in `assets/fonts/`) for subheadings (24/42px), hashtags, quotes, annotations — always Wine or white, never long text. Fallbacks (open decks only): Arial Black/Arial/Kalam. **Slides exception (decision 2026-10-09):** on slides and in Google Slides, including internal decks such as Town hall, hand-written text containing Czech diacritics (ě š č ř ž ů ť ď ň) is set in Kalam Bold, ALL-CAPS, because Permanent Marker does not render them well; see `guidelines/slides.md`. Web, print, branding and merch always use the Czech-fix Permanent Marker.
- **Backgrounds:** off-white `#fafafa` with a subtle paper grain is the primary background (`backgrounds/pozadi-papir-bile.png`; red variant `pozadi-papir-cervene.png` in #e4003a), never pure white; Wine or Anthracite full-bleed panels for contrast slides/posts. Photography full-bleed with white or wine overlay panels. No gradients.
- **Buttons (UI kit 19. 10. 2026):** primary = solid Red Button with a hand-drawn outline offset outside the shape (`Button`, frame `frames/frame-short-red.svg`); secondary = outline with a hand-drawn double line, Anthracite on light, white on dark (`Button variant="secondary"`, `onDark`); reversed = button on an Anthracite surface. Radius 4px (`radius-button`). Inputs: grey fill `field-bg` (#b0b2b6) with a hand-drawn red outline (`field-line`), Wine on focus, radius 4px (`radius-input`).
- **Motifs:** the hand-drawn **network pattern** (`NetPattern`, files in group *Síť*) decorates dead space: light variant grey `#b1b3b6`, Anthracite or light grey `#d0d0d0`; dark variant white or Red Button. Large, may bleed off the edge (never cut at the top), lightly rotated down towards the footer, dense at the edge and thinning towards the centre, always clearly visible, never over text or faces, always whole inside a photo. **Cards and boxes are never straight rectangles:** use the thin hand-drawn box (`Card`, `DrawnBox`, files `Komponenty/box-tenky-*`), sized to the content; boxes in one row of the same type. Wine footers and number bands have a **torn edge** (`TornBand`, `TornEdge`). Hand-drawn lines, double underline (`DrawnUnderline`, small, never touching the letters), circles (`DrawnCircle`, page numbers) and carousel arrows (`CarouselArrow`, red drawn circle with a white arrow). Vary the elements within one output. Hand-drawn **brush frames** around buttons/panels, **torn-edge banners** (program tags), hand-drawn arrows/underlines/circles from the icon set, and the scribble **bulb** symbol.
- **Photography:** always B&W (or red/wine-toned duotone), real people in context — conversation, collaboration, reflection; smart casual; never stock-feel. Portraits become **cutouts**: irregular hand-painted silhouette frame — wine frame on light bg, white frame on dark bg.
- **Corners & borders:** radius 4px on buttons, inputs and flat UI (UI kit 19. 10. 2026); card and box edges are hand-drawn (thin line is always better), not CSS borders.
- **Shadows:** essentially flat; soft shadow only for floating UI. Buttons/cards sit flat on the page.
- **Hover/press:** manual defines none; convention here — hover darkens red (`#e4003a` → `#a11834`) or lifts opacity, press scales 0.98. Keep subtle.
- **Animation:** manual defines none; keep to quick fades/slides (150–250ms ease-out) if needed.
- **Layout:** generous whitespace, strong left-aligned typographic hierarchy: red kicker caps → ALL-CAPS black headline → marker subheading → body. Logo top-left or top-right, page number bottom-right, net pattern bottom corner.

## ICONOGRAPHY
- **One system only:** 42 hand-drawn marker-stroke SVGs in Wine (`assets/icons/icon-01.svg` … `icon-42.svg`), 500×500. No icon font, no CDN set, no emoji. Recolor via CSS filter or by editing fill. Icons 01–12 are annotation scribbles (ovals, underlines, arrows) used to mark up text like a whiteboard. Keep annotation scribbles small — never scale the underline (03) to full main-headline width; underlines belong under short marker subtitles only.
- Legend: 01 oval-scribble · 02 arrow-up-left · 03 underline · 04 oval-highlight · 05 arrow-bent-down · 06 arrow-squiggle · 07 arrow-s-curve · 08 double-underline · 09 arrow-down-right · 10 arrow-curve-left · 11 circle-scribble · 12 asterisk · 13 map-pin · 14 phone · 15 mail · 16 arrow-right · 17 arrow-down · 18 check · 19 cross · 20 shield · 21 crown · 22 search · 23 compass · 24 presentation · 25 people-group · 26 idea-bulb (brand bulb) · 27 growth-chart · 28 puzzle · 29 gear · 30 arrows-scatter · 31 instagram · 32 facebook · 33 youtube · 34 linkedin · 35 code · 36 road · 37 arrow-up-right · 38 people-pair · 39 checklist · 40 pen · 41 shapes-transform · 42 ellipse
- **Illustrations:** 7 outline program illustrations in Wine (`assets/illustrations/`): target, Charles-bridge, cloud-gears, grad-cap, puzzle, AI badge, tech-book.
- **Logos** (`assets/logos/`): horizontal logo light/dark bg, vertical (alternativní) light/dark, universal symbol (red dot button). Min height 20px screen. Protection zone 50% of logo height. Never rotate/recolor/shadow/deform. Forbidden on Apple Red.

## Web style (UI kit) — 2026-10-19
Source: brand manual §4 „Webový styl (UI kit)“ and references `Reference/web-styleguide-svetly.png`, `Reference/web-styleguide-tmavy-summit.png`. Where earlier values in this README or `guidelines/web-ui.md` differ, this section wins.
- **Light is the default for every product.** The near-black dark variant (`surface-darkmode`, Apple Red accent) is primarily for Exponential Summit; for dark visuals of other products (and Summit too) use Anthracite `#444444`, where a Wine torn footer may stay and a white net on Wine is fine.
- **Colour ratio:** off-white 60 %, Wine 20 %, Anthracite 10 %, Red Button 5 %, `#b0b2b6` 3 %, `#969696` 2 %. The red paper texture is always Red Button `#e4003a`.
- **Torn lines:** light variant Wine or Red Button, dark variant white or Red Button. **Net:** light grey / Anthracite / light grey, dark white or Red Button.
- **Text in boxes** never overflows: equal inner padding top and bottom, content vertically centred; rather a smaller size. Words that belong together never break across lines. Text aligns to the left edge of the text above it.
- **Icons and illustrations** may use every brand colour, but few at once: Wine or Anthracite on light, Red Button or white mainly on dark or standing alone. Icons lean slightly towards the larger part of the composition; icons with people stand straight.
- **Photos** black-and-white (filter Noir); graphics never cover a face.

## Review rules — 2026-10-19 (Lucie Přibylová)
Rules from the review of the first web artifact built on this system. They apply to every output (web, posts, decks) and win over any older value in this README.
- **Only approved components.** Build from this system's components and assets; never invent a visual element (a button, tag, underline, divider, shape). If something is missing here, say so and ask instead of improvising.
- **Buttons side by side share the same artwork** and differ only in colour: primary = filled frame, secondary = the same frame as an outline (`Button`). Text never overflows a button. On a Wine or Anthracite surface the button is white (`Button onDark`: white fill with Wine label, or white outline).
- **Accent word in a headline:** a Permanent Marker word next to Rubik is the same size and set in capitals, so the letter heights match (`TŘI CESTY, JAK RŮST`).
- **Wine label / #hashtag on a photo:** the torn-edge `Badge` (Rubik Bold on Wine), not a rounded or rotated marker tag.
- **Underline:** only the approved double underline (`DrawnUnderline`, icon 08); never compose your own from lines.
- **Not too many boxes in one visual.** Keep drawn boxes for cards; show KPIs and charts without boxes, e.g. a figure with an approved icon above it. Vary the elements.
- **Net:** only one net in adjacent sections, never two stacked above each other. A net coming from the right is mirrored (dense and largest at the right edge, thinning to the left). The net keeps a clear gap from buttons and text and never overlaps them.
- **Statistics band:** each number and its label are centred in their column.
- **Colour ratio on a page:** when the page already has Wine bands, boxes or cards, the footer is Anthracite with a torn edge, so Wine stays near 20 %.

## Web × slides — one system (2026-10-09)
This system now covers digital outputs and presentations; it replaces the separate systems *RB EDU – Web UI* and *RB EDU – prezentace*. Decisions: values follow the brand manual (Wine ~20 % surface, Red Button `#e4003a` ~5 % accent, one button red); old slide token names live on as aliases (`rb-crimson` → `rb-wine`, `rb-ink` → `rb-anthracite`, `rb-paper` → `rb-off-white` …); token names stay as in this system and the semantic web tokens (`bg`, `surface`, `text`, `action`, `focus`, … with a dark theme) were added.
- Slides: `guidelines/slides.md`, tokens prefixed `slide-*`, assets in group *Slides*.
- Web and UI: `guidelines/web-ui.md`; contrast and known weaknesses: `guidelines/accessibility.md`.

## Index
- `styles.css` → `tokens/` (fonts, colors, typography, spacing)
- `assets/` — logos, fonts, icons (42), illustrations (7), patterns (net ×2), backgrounds, photos
- `guidelines/` — brand manual (cs authoritative / en), specimen cards incl. colors (core, support, semantic, ratio, dark-mode), type, logos, icons, photography, and **voice cards** (tone-of-voice, brand-rules, personas)
- `components/forms/` — Button, IconButton, Input, Select, Checkbox, Radio, Switch
- `components/display/` — Card (hand-drawn box), Badge, Tag, Tabs
- `components/feedback/` — Dialog, Toast, Tooltip
- `components/brand/` — Logo, Icon, NetPattern, MarkerNote, Drawn (DrawnBox, TornBand, TornEdge, DrawnLine, DrawnUnderline, DrawnCircle, CarouselArrow)
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


---

## Consuming this system (generated — do not edit)

Every path named below is under `project/` in this design system: read `project/api/tokens.md`, not `api/tokens.md`.

`components/bundle.js` defines `window.RedButtonDesignSystem_3b681f` (21 components); `components/bundle.css` is its stylesheet; `tokens.css` is every token as a CSS variable plus `@font-face` for the fonts. The bundle needs `components/lib/react.production.min.js` (`window.React`), `components/lib/react-dom.production.min.js` (`window.ReactDOM`), loaded before it. Build any UI by mounting these components; never hand-build a control or draw an icon the system provides.

- **Standalone page:** inline `tokens.css` and `components/bundle.css` in a `<style>`, then the library files and `components/bundle.js` as classic scripts (a file containing `</style`, `</script` or `<!--` breaks an inline element: write the sequence `<\/style`, `<\/script` or `\x3C!--` in your copy, or load that file by URL).
- **Design canvas:** bring `components/bundle.css` and `components/bundle.js` onto the canvas in full, as the canvas type’s design-system components reference says (a server-side copy first where it offers one); load the stylesheet before the script; skip the library files (the artboard supplies React); mount with `<x-import component-from-global-scope="RedButtonDesignSystem_3b681f.<Comp>" …>`.
- **Slides deck, or any surface that cannot run the bundle:** tokens and fonts — the values are on `api/tokens.md`; the deck takes `tokens.json` by file path for its colour pickers, and fonts as “Fonts” below says.

Fonts: `tokens.css` loads each font from its file, by path.

- **Design canvas:** copy `tokens.css` and `fonts/permanentmarker-regular-czech-fix.otf` to the same paths under the canvas’s `project/ds/<folder>/` (`<folder>` is the folder you install this system under; `fonts/permanentmarker-regular-czech-fix.otf` lands on `project/ds/<folder>/fonts/permanentmarker-regular-czech-fix.otf`), in the same call that installs this system. Link that copy of `tokens.css` in the artboard’s `<head>` as `ds/<folder>/tokens.css`, or as Design’s instructions say for an artboard in a folder. If the install’s reply leaves a font out, bring that font in as for any other page.
- **Slides deck:** for each family you use in the deck (`faces` holds at most the number of typefaces Slides’ `deck-files.md` gives), install its file with the system and name the path it lands on as that family’s `src` in `project/deck.json` `faces`, under the key in the Slides column. A deck takes a font as a file only under the rule in Slides’ `fonts.md` (no space or leading underscore in its path, for two): any other font, or one kept by id, is uploaded as `fonts.md` says.
- **Any other page:** one file per family is enough (below: the upright face nearest regular weight; bold and italic synthesize). Fetch it as the fetch column says (Artifact tool `read`, that id or path as `path`), upload it as an asset (`publish`, `file_path`, `asset:true`) and declare it with an `@font-face { font-family: "<family>"; src: url(<uploaded>) }` rule.

| family | file | fetch | CSS | Slides `faces` key |
| --- | --- | --- | --- | --- |
| Permanent Marker | `fonts/permanentmarker-regular-czech-fix.otf` (weight 400) | `read` the file with `project/` in front | `var(--font-accent)` | `permanent-marker` |

**Read, per thing:** a component’s props, parts and examples: `api/components/<Comp>.md`; token values: `api/tokens.md`; stored assets and their paths: `api/assets/<Group>.md`. After this README, fetch the cards and fonts you need in ONE message as parallel calls — none depends on another.

**Two rules.** Before you use a thing — a component, a token group, an icon, an asset — read its card from the index below; a value you did not read from a card is a guess. `tokens.json`, `manifest.json` and `design-system.json` are sources for tools: hand them over. `components/<Comp>/README.md` and `assets/<Group>/README.md` are the long-form second read a card links to; `SKILL.md` and `artifact-type/` beside them are authoring guidance, not needed to consume the system.

## Index (generated — do not edit)

**Tokens**

- `api/tokens.md` — Every token: surface, text, fill, border, palette, type, spacing, radius, shadow, font-weight, font-size, line-height, letter-spacing, breakpoint, layout, z-index. (20.7k)

**Icons and assets**

- `api/assets/Images.md` — 9 files, by asset id. (1.4k)
- `api/assets/Logos.md` — 4 files, by asset id. (1.0k)
- `api/assets/Reference.md` — 8 files, by asset id. (1.3k)
- `api/assets/backgrounds.md` — 1 file, by asset id. (0.7k)
- `api/assets/frames.md` — 8 files, by asset id. (1.3k)
- `api/assets/icons.md` — 42 files, by asset id. (3.9k)
- `api/assets/photos.md` — 4 files, by asset id. (1.0k)
- `api/assets/Slides.md` — 8 files, by asset id. (2.3k)
- `api/assets/Komponenty.md` — 19 files, by asset id. (4.0k)

**Components** (`api/components/<Comp>.md`, 28; 7 of them showcase pages)

- `ICON_NAMES` — ICON_NAMES · `Icon` — Hand-drawn brand icon; the only icon system allowed · `Logo` — Official logo lockups · `MarkerNote` — Handwritten accent text in Permanent Marker · `NetPattern` — Brand network pattern anchored to a container corner · `Badge` — Torn-edge banner badge for program names and labels.\n\njsx\n Program #Rebeleader \n Novinka \n · `Card` — Flat content card, 6px radius, no shadow · `Tabs` — Underline tab bar.\n\njsx\n \n · `Tag` — Topic tag · `Dialog` — Modal dialog with uppercase Rubik Black title and primary/secondary actions.\n\njsx\n setOpen(false)}>Přihláška do programu R(e)BeLeader. \n · `Toast` — Toast notification, wine (success) or anthracite, with a hand-drawn icon.\n\njsx\n \n · `Tooltip` — Anthracite hover tooltip.\n\njsx\n Manuál \n · `Button` — Brand CTA button; the default is the brand's hand-drawn brush frame (real SVG artwork from the manual) around a transparent button · `Checkbox` — Checkbox; wine square with white check · `IconButton` — Icon-only square button (44px min hit target) with a hand-drawn brand icon · `Input` — Labeled text input · `Radio` — Radio; wine dot when selected · `Select` — Branded native select · `Switch` — Toggle switch, wine track when on · `PhotoPost` — IG photo post: hashtag header with wine rule + logo, B&W photo, torn wine banner headline overlapping the photo, marker quote, body, wine URL footer.\n\njsx\n… · `SocialPost` — IG post template (4:5) recreating the brand social layout: logo top-right, two-line caps headline + bulb icon, hand underline, marker subtitle, arrow bullets,…
- **Components**: `Brand` (showcase page) — Logo, Icon, NetPattern, MarkerNote · `Display` (showcase page) — Card, Badge, Tag, Tabs · `Feedback` (showcase page) — Dialog, Toast, Tooltip · `Forms` (showcase page) — Button, IconButton, Input, Select, Checkbox, Radio, Switch
- **Voice & Content**: `BrandRules` (showcase page) — 7 pravidel práce se značkou + jak chceme a nechceme působit · `Personas` (showcase page) — Leaders · L&D Owners · L&D Operations — komu píšeme a co reálně kupují
- **Social**: `Index` (showcase page) — Interactive recreation of the brand's IG post templates
