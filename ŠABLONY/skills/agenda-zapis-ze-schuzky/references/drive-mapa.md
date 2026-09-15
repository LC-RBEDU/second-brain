# Mapa Obsidian vaultu na Google Drive

Vault: `My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`
Kořen: `1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-`

| Složka | ID |
|---|---|
| `00-System` | `1WoFjIHe6N33WTxHOEsxAg8MWdRWNazol` |
| `01-INBOX` | `19RqMWHiOdTsiHwkyKylU4SVPOWTKLG9N` |
| `01-INBOX/sembly` | `1ZpH6GiQu5IdUefhck5kVAgoZgw3Xp1Tt` |
| `01-INBOX/daily` | `1moQEEiLVpoMSayZMKkAbLu8aDvfKprEG` |
| `01-INBOX/slack` | `1EppTJt45A8kOyQJoZ8BuneHtiU5nWlXN` |
| `01-INBOX/email` | `1P_vA0pfNSxfj6ykb-MEEreKspoUJkmYC` |
| `02-PROJEKTY` | `1V3Gd_sM7Fqds8WPj6EXDixsYVe5ZuG3o` |
| `03-AREAS` | `1A1Bub7CAZagNPslxsHtqajhbRHY22Oog` |
| `05-RESOURCES` | `1xxAOznczfQFNqUeG2iHPXjqP0LxiO01P` |
| `05-RESOURCES/lide` | `1Tn56S6Jl7Y2oT69cliPhYoLzjUMNiCjI` |
| `05-RESOURCES/vystupy` | `1k1sVAxx0eFLHEPogut-TF4n8aCicpb9m` |
| `05-RESOURCES/attachments` | `1pk3zsocXSE8BMzFYNwKMLTA-6K7PJtSE` |
| `06-CANVAS` | `10otXXkC1claq07PQ3LZbLJyHaoPrGN_C` |
| `07-ARCHIV` | `1wZrOAz1BTQw-Ti0dc8eWZ6gGfGO1Z1Vk` |
| `07-ARCHIV/inbox-processed` | `1F4NzjEopRpiOuZZ6irFZjJhViTVSTLij` |

`inbox-processed` je členěný `<rok>/<měsíc>/<zdroj>`, např. `2026/09/sembly`.
Starší přepisy hledej tam, ne v živém inboxu.

---

## Postup hledání přepisu

```
search_files: title contains '2026-09-14'
```

Názvy mají tvar `RRRR-MM-DD-HHMM-<slug>.md`. Když je výsledků víc, ukaž seznam
(čas + název) a nech vybrat.

**Známý problém:** ID vrácené z jednoho hledání se někdy nedá otevřít —
`read_file_content` vrátí „Requested entity was not found". Řešení: zopakovat
`search_files` se `snippetVerbosity: BRIEF` (bez `excludeContentSnippets`).
Druhý dotaz vrátí platné ID a rovnou i náhled hlavičky s účastníky.

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
