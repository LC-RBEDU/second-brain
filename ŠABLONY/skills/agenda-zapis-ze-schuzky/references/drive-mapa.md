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
| HTML (Slack příloha) | `~/Downloads/YYYY-MM-DD_<slug>_zapis.html` |
| MD (pracovní kopie agenta) | `05-RESOURCES/vystupy/zapisy/YYYY-MM/` |
| MD (kanonické sdílení s týmem) | sdílený **Drive folder** schůzky (`drive_folder:` v zápisu) → Slack jen **odkaz** |
| Odkaz v projektu | stub v `02-PROJEKTY/<slug>/materials/` → wikilink na vault MD |

### Drive foldery pro týmové MD zápisy

Lookup primárně: `.cursor/rules/internal-meeting-slack.mdc`. Není v tabulce → zeptej se.

| Schůzka | Folder ID | URL |
|---|---|---|
| Strategická schůzka / Strategy sync | `16AhvQQ9l1Ad76_N9AVh72WH9GCw1qc49` | https://drive.google.com/drive/folders/16AhvQQ9l1Ad76_N9AVh72WH9GCw1qc49?usp=drive_link |

Vault MD = agentí pracovní kopie. HTML do Downloads (Obsidian ho nerenderuje) → Slack attach.
Detail workflow: `../SKILL.md` → Krok 9.
