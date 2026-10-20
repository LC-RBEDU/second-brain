# Prezentace (slidy, Google Slides, tiskové jednostránky)

Vizuální jazyk prezentací Red Button EDU: světlé pozadí, antracitové verzálky Rubik Black, Wine jako hlavní barva značky, ručně kreslené prvky (rámečky, kruhy, šipky) a ruční písmo. Působí lidsky a „rukodělně“, ne korporátně. Zdroj: firemní šablona *Šablona RB prezentace* (41 slidů, 1920 × 1080 px) sladěná s brand manuálem (rozhodnutí Lukáše Cypry, 9. 10. 2026). Pravidla pro web: `web-ui.md`.

## Principy

1. **Papír, ne bílá.** Obsahové slidy mají papírovou texturu `assets/Slides/pozadi-papir.png` (náhrada, když textura nejde vložit: plná barva `rb-off-white` #fafafa). Plné červené pozadí jen titul a předěly ve Wine (`surface-brand`). Čistě bílé pozadí obsahového slidu nepoužívej.
2. **Wine je hlavní barva.** Akcent v nadpisu, štítek, linka hlavičky, karty, čísla. Ostatní je Anthracite a šedé.
3. **Red Button `#e4003a` je jen akcent, ~5 % plochy.** Nejvýš jedno zvýraznění na slide (klíčové číslo, CTA, zakroužkování). Ne v nadpisu, na štítku, na ploše karet ani v textu odstavců. Nikdy červený text na Wine ploše.
4. **Ruka + systém.** Strukturu nesou Rubik verzálky a mřížka, lidskost dodávají kreslené rámečky, kruhy, šipky a ruční písmo. Na jednom slidu nejvýš 2–3 kreslené prvky.
5. **Dvoubarevný nadpis.** Nadpis verzálkami v Anthracite, klíčová část (2–3 slova) ve Wine: „CÍLE PROGRAMU ANEB **KAM MÍŘÍME**“.
6. **Každý obsahový slide má stejnou hlavičku:** hashtag štítek vlevo, Wine linka, logo Red Button vpravo, číslo strany vpravo dole.
7. **Málo textu, velké písmo.** Text min. 24 px na plátně 1920; odstavce max. 4–5 řádků; detail patří do poznámek řečníka.

## Barvy (hodnoty z manuálu)

- **Wine** `rb-wine` #a11834 – hlavní akcent a plné plochy. Bílý text 7,79:1.
- **Anthracite** `rb-anthracite` #444444 – nadpisy, text, tmavé karty a kroužky.
- **Red Button** `rb-red-button` #e4003a – akcent ≤ 5 %.
- **Grey** `rb-grey` #b0b2b6 – oddělovače, šedé rámečky. **Spanish Grey** `rb-spanish-grey` #969696 – jen nedůležité doplňky (2,96:1, pod AA).
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
|---|---|---|
| štítek `#Téma` | vlevo nahoře, x 106, y 28 (řádek 34 px) – svisle na středu linky hlavičky; VŽDY na jednom řádku | `slide-section-tag`, Wine |
| linka hlavičky | y 38, výška 14 (střed y 45); začíná 24 px za koncem štítku (u „#Design“ ≈ x 236) a končí ~20 px před logem (x ≈ 1626) | `assets/Slides/linka-hlavicky.png` roztažená |
| logo | vpravo nahoře, ~210 × 58 | logo Red Button (skupina *Logos*) |
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
- **Lektor / průvodce, Reference, Cena a rozsah, O nás, Další krok / kontakt, Text + fotka** – layouty podle šablony *Šablona RB prezentace*.

## Obrázky a ilustrace

- **Fotky vždy černobílé** (nebo tónované do Wine), lidé často vystřižení z pozadí v cutoutu.
- **Ilustrace a ikony jsou ručně kreslené:** Wine na světlém, bílé na Wine nebo tmavé ploše (v kroužku `kruh-tmavy.png`). Neskládej je s plochými ikonami z knihoven. Ikony, ilustrace, rámečky a vzor sítě jsou ve skupinách *icons*, *Images* a *frames*.
- Skupina *Slides* obsahuje papírové pozadí `pozadi-papir` a kreslené prvky specifické pro slidy: `linka-hlavicky`, `linka-teckovana`, `oblouk-roh`, `tahy-zdurazneni`, `plocha-cervena`, `kruh-tmavy`, `skvrna`. Barvy přenesených kreslených prvků jsem změřil: Wine (`#a11834`), Anthracite, Grey a Spanish Grey. Red Button v nich není.
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
