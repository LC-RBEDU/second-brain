# Mapa cest vaultu a sdílených Drive složek zápisů

Vault SSOT: git `~/GitHub/second-brain-vault`. Přepis čti z klonu, zápis přes Brain.

| Co | Cesta v klonu |
|---|---|
| `00-System` | `~/GitHub/second-brain-vault/00-System/` |
| `01-INBOX` | `~/GitHub/second-brain-vault/01-INBOX/` |
| `01-INBOX/sembly` | `~/GitHub/second-brain-vault/01-INBOX/sembly/` |
| `01-INBOX/daily` | `~/GitHub/second-brain-vault/01-INBOX/daily/` |
| `02-PROJEKTY` | `~/GitHub/second-brain-vault/02-PROJEKTY/` |
| `05-RESOURCES` | `~/GitHub/second-brain-vault/05-RESOURCES/` |
| `05-RESOURCES/lide` | `~/GitHub/second-brain-vault/05-RESOURCES/lide/` |
| `05-RESOURCES/vystupy` | `~/GitHub/second-brain-vault/05-RESOURCES/vystupy/` |
| `07-ARCHIV/inbox-processed` | `~/GitHub/second-brain-vault/07-ARCHIV/inbox-processed/` |

`inbox-processed` je členěný `<rok>/<měsíc>/<zdroj>`, např. `2026/09/sembly`.
Starší přepisy hledej tam, ne v živém inboxu.

---

## Postup hledání přepisu

V klonu `~/GitHub/second-brain-vault` hledej soubor `RRRR-MM-DD-HHMM-<slug>.md` v `01-INBOX/sembly/` a v `07-ARCHIV/inbox-processed/`. Když je výsledků víc, ukaž seznam (čas + název) a nech vybrat.

## Párování s kalendářem

Z názvu přepisu vezmi datum a čas (`2026-09-14`, `1214`) a najdi událost,
která tomu času odpovídá:

```
list_events / search_events: timeMin = 2026-09-14T00:00:00+02:00
                             timeMax = 2026-09-15T00:00:00+02:00
```

Sembly zakládá soubor v čase zahájení, takže událost obvykle začíná ve stejnou
nebo velmi blízkou minutu. Z události ber:
- oficiální název schůzky (do titulku zápisu),
- **přílohy** — soubory připnuté k události; to jsou podklady,
- seznam pozvaných (doplněk k účastníkům z přepisu — nemusí se krýt).

## Práce s tabulkami jako podkladem

`read_file_content` na Google Sheet vrací **všechny listy zřetězené za sebou**,
bez názvů listů a bez `gid`. Nedá se z toho spolehlivě určit, který list uživatel
myslel. Proto: popiš, co v jednotlivých blocích vidíš (podle hlaviček sloupců),
a nech si potvrdit list i sloupce, které mají tvořit osnovu.

## Ukládání výstupu (Cursor / Second Brain)

| Výstup | Kam |
|---|---|
| HTML (sdílení) | `~/Downloads/YYYY-MM-DD_<slug>_zapis.html` |
| MD (kanón) | `05-RESOURCES/vystupy/zapisy/YYYY-MM/` |
| Odkaz v projektu | stub v `02-PROJEKTY/<slug>/materials/` → wikilink na MD |

Ukládej **MD** do vaultu. HTML do Downloads (Obsidian ho nerenderuje).
Detail workflow: `../SKILL.md`.
