---
name: agenda-capture
description: "Use this skill when the user pastes content into chat, drops a file/screenshot/audio into Cowork, or refers to 'INBOX', 'capture', 'zapiš si', 'hoď to k tématu', 'rozhoď to'. Also trigger automatically when new files appear in CLAUDE COWORK/INBOX/* subfolders during a session. Captures fragments from any source, extracts content (vision for images, text for docs, transcript reading for Sembly/Slack), proposes the right AGENDA topic, drafts metadata (Eisenhower quadrant, ICE score, return date, blocker), and saves to AGENDA/<topic>.md after user confirmation. Originals are moved to HOTOVO/processed/ as audit trail. NEVER triage silently — always show the user what you propose and wait for OK."
---

# agenda-capture

> Bere libovolný "střípek" a integruje ho do živého systému AGENDA.

## Kdy spouštět

- Uživatel paste-ne text do chatu (zpráva, e-mail, poznámka, transkript)
- V Cowork chatu se objeví soubor (PDF, .docx, .xlsx, .png, .jpg, audio)
- V `CLAUDE COWORK/INBOX/<podsložka>/` se objevily nové soubory (zkontroluj `mtime`)
- Uživatel řekne "zapiš si to", "hoď to k tématu X", "rozhoď to", "máš tam něco v inboxu?"

## Workflow

### 1. Načti kontext

Vždycky před tím, než cokoli uděláš:

1. Přečti `CLAUDE COWORK/O MNĚ/about-me.md` (pokud ještě v session ne)
2. Přečti `MrLUC/02-PROJEKTY/_index.md` (znát existující témata)
3. Pokud capture skill spouští čtení z INBOXu, projdi všechny `CLAUDE COWORK/INBOX/*/` podsložky a najdi soubory novější než cokoli, co už je v `HOTOVO/processed/`

### 2. Vytěž obsah podle zdroje

- **Text v chatu** → ber jak je
- **PDF / .docx / .xlsx** → použij `pdf` / `docx` / `xlsx` skill k extrakci textu
- **Obrázek / screenshot** → vision: popiš co vidíš + extrahuj veškerý čitelný text (OCR ekvivalent)
- **Audio** → pokud bash/whisper k dispozici, transkribuj; jinak řekni uživateli, že potřebuje text variantu
- **Sembly soubor v INBOX/sembly/** → už je v markdownu, ber jak je
- **Slack soubor v INBOX/slack/** → už je v markdownu (z n8n workflow), ber jak je
- **E-mail v INBOX/email/** → už je v markdownu z n8n Gmail trigger (přeposlané na `lukas.cypra+cowork@gmail.com`); pozornost na přílohy (uložené vedle .md souboru) — případně je samostatně otevři a vytěž

### 3. Rozsekej na položky

Z jednoho streamu může vzniknout víc položek. Pravidla:
- Každý **akční bod** = jedna položka
- **Nápad bez akce** = položka do Backlogu daného tématu
- **Otázka / čeká na odpověď** = položka do Otevřených otázek
- **Pouhý kontext** (např. citace, screenshot bez akce) = Materiály a poznámky daného tématu

### 4. Navrhni téma pro každou položku

- Projdi soubory v `AGENDA/*.md` (slugy a Kontext sekce)
- Pro každou položku navrhni **existující téma** nebo **vytvoř nové**
- Pokud Sembly soubor má v hlavičce `Suggested topic: X`, použij to jako default návrh, ale můžeš překlopit

### 5. Navrhni metadata

Pro každý **akční** úkol:
- **Eisenhower kvadrant** (Q1–Q4): odhad podle deadlinů, blokátorů a dopadu
- **ICE skóre** (Impact / Confidence / Effort, každé 1–10): odhad
- **Score** = (I × C) / E
- **Vrátit se** (datum nebo slovo): kdy znova kouknout
- **Blokováno**: nic / čím

### 6. Ukaž uživateli návrh PŘED ukládáním

Format:

```
## Návrh capture (X položek z [zdroj])

### → AGENDA/rb-universe.md
- [Aktivní] [Q2, ICE 8/7/4, S=14] Přidat retry do FIO syncu
  Vrátit se: 2026-05-05 | Blokováno: nic

- [Backlog] Nápad: ReBeL by mohl umět odpovídat přes Slack (zatím bez akce)

### → AGENDA/ceo-reporting.md (NOVÉ TÉMA — vytvořit?)
- [Otevřená otázka] CEO chce report konverzního trychtýře EDUtéky → chybí napojení na Mixpanel
  Čeká na: vyjasnění, jestli můžeme přes API

### → Drop (nepoužitelné)
- Pozdrav z Sembly úvodu — žádný akční obsah

OK přesunout? (ano / uprav / vyhoď [čísla])
```

Uživatel potvrdí, opraví, nebo škrtne. Pokud uživatel řekne jen "ano", proveď.

### 7. Zapiš a archivuj

- Pro každé téma: otevři `AGENDA/<slug>.md`, vlož položky do správných sekcí
- Pokud téma nezná, vytvoř nový soubor podle `AGENDA/_ŠABLONA.md`
- Update `00-System/Index.md` (počet aktivních úkolů, top priorita podle S, datum)
- **Originál capture** přesuň z INBOXu do `HOTOVO/processed/<rok>/<měsíc>/<den>-<filename>`
- V `AGENDA/<slug>.md` v sekci "Materiály a poznámky" přidej odkaz na archiv: `viz HOTOVO/processed/2026/04/28-…`

### 8. Hláška uživateli

Krátká, akční, bez patosu. Příklad:

```
Hotovo. 4 položky → 2 témata. Nové téma: ceo-reporting.
Top z dnešního capture: [Q1, S=18] Předělat dashboardu pro CEO sales review.
Vrátit se: zítra (CEO 1:1).
```

## Speciální případy

- **Nejasný obsah** → polož 1 cílenou otázku, neházej hloupé defaulty
- **Položka, co je jasně Q1** → zmiň to v hlášce explicitně, ať to nezapadne
- **Capture bez tématu (chat smalltalk)** → říct uživateli, že to není capture-worthy, a nezapisovat
- **Obsahuje osobní/citlivá data** (mzdy, hesla) → upozorni uživatele, ať potvrdí, že se to má uložit do Drive
