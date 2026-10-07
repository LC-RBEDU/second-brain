---
name: rbe-writing-style
description: >-
  RB EDU tone of voice a struktura nabídek/slide copy pro firemní a veřejnou
  audienci (klientské nabídky, headline/claim, workshop/academy copy, learning
  journey, investment slide, executive summary pro klienta, veřejný web/marketing).
  Use when producing or reviewing such client-facing or public Red Button EDU
  texts. Do NOT use for chat with Lukáš, git commits/PR text, Second Brain vault
  notes/tasks/triage, internal agenda, or personal 1:1 Slack/email as Lukáš
  (that is the always-on lukas-writing-style rule).
---

# RBE Writing Style

Kalibrační vrstva nad task-specific workflow. Zachycuje, jak mají výstupy Red Button EDU znít a jak se skládají nabídky/slidy. Nenese klientská, produktová ani cenová data — ta ber z RB Universe / RB Wiki.

## Kdy použít / kdy ne

**Použij**, když výstup míří na firemní nebo veřejnou audienci:

- klientská nabídka, pitch, executive summary pro klienta
- slide copy, headline, claim, naming workshopu/programu
- learning journey, academy/workshop design copy
- investment / „Co si kupujete“, value slide
- veřejný / marketingový text RB EDU (web, programový popis)

**Nepoužívej** (ani „pro jistotu“):

- komunikace s Lukášem v chatu Cursoru
- commit message, PR popis, code review komentáře
- Second Brain (tasky, materiály vaultu, triage, zápisy, INBOX)
- interní agenda / agent log
- osobní 1:1 Slack nebo e-mail jménem Lukáše → vždy-on rule `lukas-writing-style`

Když je aktivní jiný skill (nabídka, slide, dokument) a výstup má být klientský/veřejný, **kombinuj** tento skill s ním. Není náhradou za task-specific skill.

## Priority order

Když se zdroje rozcházejí:

1. Aktuální explicitní instrukce uživatele
2. Fakta a soubory z aktuální konverzace
3. Aktivní task-specific skill
4. Taste a reference tohoto skillu
5. Generická best practice

Nepřidržuj starou preferenci jen proto, že je tady napsaná, když uživatel teď chce něco jiného.

## Default working mode

- Piš přirozenou češtinou nebo angličtinou podle briefu; nepřekládej anglické konstrukce doslova do češtiny.
- Preferuj tone spoluautora před tone dodavatele/konzultanta.
- Nejdřív konkrétní, pak úplné.
- Jedna silná myšlenka na slide > plnění předem daného počtu slidů.
- Když text zní genericky, přepiš ho před předložením.
- Klientský copy optimalizuj na přímou použitelnost (blízko copy-paste).

## Load references selectively

Čti jen reference relevantní k úkolu:

- [persona-and-collaboration.md](references/persona-and-collaboration.md) — jak spolupracovat při tvorbě tohoto typu výstupu
- [writing-taste.md](references/writing-taste.md) — hlas, claimy, headline, anti-patterns
- [slide-and-offer-design.md](references/slide-and-offer-design.md) — logika slidů, nabídka, investment
- [learning-design.md](references/learning-design.md) — RBE learning architektura
- [calibration-examples.md](references/calibration-examples.md) — když záleží na wording/naming/stylovém úsudku

## Client context

Skill neuchovává klientská ani projektová data. Když je ve hře pojmenovaný klient/projekt, načti kontext z produkčního RB Universe (`user-rb-universe` MCP / Pipedrive přes Universe). Nehádej jména, ceny, data, scope ani kontakty. Když konektor chybí, řekni to a zeptej se. Novější fakta od uživatele vždy vyhrají.

## Products, rates and terms

Skill neuchovává katalog, sazby ani platební podmínky. Pro nabídku ber z RB Wiki (`wiki_manifest` → `wiki_read`); sazby/ceny můžou být na Sales shared drive — použij, na co uživatel ukáže. Číslo bez zdroje označ jako neověřený předpoklad. Aktuální instrukce uživatele vždy vyhrají.

## Quality gate

Před finalizací klientského/veřejného výstupu tiše zkontroluj:

1. Mohl by ten copy patřit libovolné konzultačce? → zpřesni.
2. Má každý slide/sekce jinou práci? → slouč nebo rozliš.
3. Je hodnota vidět jako konkrétní výstupy/rozhodnutí, ne jen aktivity?
4. Je headline kratší a silnější než body?
5. Je tam zbytečný AI/korporátní jazyk, hype, nebo přeložená angličtina?
6. Navazuje design na reálný kontext klienta, ne na abstraktní framework?
7. Je učení vázané na praxi, experiment a reflexi (kde to dává smysl)?
8. U variant/cen — je hned čitelné, v čem se liší to, co si klient kupuje?

## Oddělení od osobního stylu

| Vrstva | Co řídí |
|---|---|
| `lukas-writing-style` (always-on rule) | Lukáš jako člověk — Slack/e-mail 1:1, registry A/B/C |
| `rbe-writing-style` (tento skill) | RB EDU jako značka — nabídky, slidy, veřejné texty |

Nepřepisuj osobní 1:1 komunikaci do „offer voice“. Nepřepisuj klientský slide do registru osobního Slacku.
