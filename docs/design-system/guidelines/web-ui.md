# Web a UI

Pravidla pro digitální výstupy Red Button EDU (web, aplikace, dashboardy). Vychází z brand manuálu; co manuál neurčuje, je v tokenech označené jako „odvozeno“ nebo „MIMO manuál“.

## Barvy a témata
- Světlý režim je standard: `bg` (#fafafa), `surface` (bílá), `text` (Anthracite), `accent-text` a `accent-display` (Wine), `action` (Red Button) pro primární CTA.
- Tmavý režim (téměř černé pozadí) jen pro Exponential Summit; tmavé plochy ostatních produktů jsou antracitové #444444: `data-theme="dark"` na `<html>`; akcent Apple Red, plochy Red Black. Nikdy v tisku a oficiálních materiálech.
- Odkazy `link` (#fe1a3f) jsou vždy podtržené.
- Stavové barvy `success-*` a `warning-*` manuál nemá, jsou doplněné pro UI. Chyby jsou v barvě značky (`error-text`).

## Typografie
- Podle UI kitu (19. 10. 2026): H1 Rubik Black 64/128 px, H2 Permanent Marker 42 px, H3 Rubik Bold 24 px, H4 Permanent Marker 24 px, odstavce Gotham Medium 18/16 px (`lead`, `body`; dokud není soubor Gotham ve `fonts/`, vykreslí se Rubik Medium), tlačítko a popisek Rubik Extrabold 16 px. Permanent Marker jen pro podnadpisy, nadpisy boxů, přímou řeč a citace, vždy v `accent-display`. Vždy CZ-fix verze `fonts/permanentmarker-regular-czech-fix.otf`; Kalam se na webu nepoužívá.
- Styly: `h1-hero`, `h1`, `h2`, `h3`, `lead`, `body`, `button`, `eyebrow`, `caption`; `ui` a `ui-small` jsou doplněk pro rozhraní.

## Rozvržení a tvary
- Zaoblení 4 px (`radius-button`, `radius-input`, `radius-card`) podle UI kitu 19. 10. 2026; tabulky a plné pásy bez zaoblení (`radius-none`). Karty a boxy jsou z tenkého kresleného boxu (`Card`, `DrawnBox`), ne rovné obdélníky. Vínové patičky a pásy mají natržený okraj (`TornBand`). Stíny jen u překryvných prvků.
- Tlačítka: primární plné Red Button s kreslenou obrysovou linkou; sekundární je stejná kresba rámečku jen jako obrysová linka (antracit na světlém). Dvě tlačítka vedle sebe mají vždy stejnou grafiku a liší se jen barvou. Na vínové nebo antracitové ploše je tlačítko bílé (`onDark`). Text nikdy nevystupuje z tlačítka. Vstupní pole: šedá výplň `field-bg` s kreslenou červenou linkou, při focusu vínová.
- Pozadí stránky: off-white s texturou papíru (`backgrounds/pozadi-papir-bile.png`), ne čistě bílá.
- Mezery ve škále `space-*`, max. šířka obsahu `container-max` (1200 px), hlavička `header-height` (72 px) – odvozené hodnoty, manuál je neurčuje.
- Focus: 2px plná linka v barvě `focus`, odsazení 2 px.

## Pravidla z revize 19. 10. 2026
- Používej jen schválené komponenty a assety tohoto systému; chybějící prvek nevymýšlej, řekni to.
- Markerové akcentové slovo v nadpisu vedle Rubiku: stejná velikost a verzálky.
- Vínový štítek nebo #hashtag na fotce: `Badge` s natrženým okrajem (Rubik Bold), ne zaoblený štítek v markeru.
- Podtržení jen schválená kresba `DrawnUnderline`.
- Na jednom vizuálu ne moc stejných boxů: boxy pro karty, KPI a grafy bez boxů (číslo se schválenou ikonou).
- Síť: v navazujících sekcích jen jedna, nikdy dvě nad sebou; zprava zrcadlená; s odstupem od tlačítek a textu.
- Pás se statistikami: číslo i popisek na střed sloupce.
- Poměr barev: když stránka má vínové pásy a karty, patička je antracitová s natrženým okrajem.

## Logo
- Na světlé pozadí `logo-light-logo.svg`, na tmavé a Wine pozadí `logo-dark-logo.svg`. Min. výška na obrazovce 20 px (alternativní 24 px), ochranná zóna 50 % výšky loga.
- Logo na barevném pozadí jen na #fafafa, #a11834 nebo #444444. Nikdy na Apple Red. Neotáčet, bez stínů, nepřebarvovat, nedeformovat.

## Implementace
- Načti `tokens.css`, Rubik z Google Fonts, `@font-face` pro Permanent Marker CZ (z `fonts/`) a `components/bundle.css`. Pak používej komponenty a třídy z návodů komponent.
