# Plán: Evening L1 harden — Sembly haystack A + Brain 503 retry (k=1 r=3)

## Zadání a požadavky

| R# | Požadavek |
|---|---|
| R1 | Max. kvalita match Sembly ↔ open tasky/stories bez bourání Brain/workflow |
| R2 | Haystack **A**: stem + FM + Shrnutí/Akční body (EN ekv.); **bez** full transcript |
| R3 | Pool = open tasky/stories bez epic; ne `03-AREAS` |
| R4 | Retry 1–2× při HTTP 503 na Brain GET triage/candidates → pak `brain_http_503`; krátký backoff |
| R5 | Brain API / Sembly webhook / vault layout / Brain app **neměnit** |
| R6 | SSOT: `evening_l1_digest.py` + `proactivity_dispatch.py` |
| R7 | ID/title/body match rules beze změny; mění se jen haystack u `sembly` |
| R8 | Haystack A **jen** `source_key == "sembly"` (ne daily/dumps) |
| R9 | `slack_token_missing` — ENV hotovo; mimo PR |

**Mimo rozsah:** areas, Brain app, scorované C / vypnutí body B, Slack token, crontab.

## Předpoklady

- **A1** — ~158 matched při 8 cand = body tokeny z transcriptu v prvních 8 KiB.
- **A2** — Alias cut: `plný přepis` \| `plný transkript` \| `full transcript` (casefold).
- **A3** — Až **2 retry** = max **3** HTTP pokusy; jen kód **503**.
- **A4** — Backoff `1.0s` pak `2.0s`; `sleep=` inject pro pytest.
- **A5** — daily/dumps beze změny; deliver/dry-run/CAS beze změny.
- **A6** — Preview ze ořezaného body; Tester skip.
- **A7** — Timeout 120 s i na retry; log na **stdout** `evening_l1_digest: brain retry 503 attempt N`; žádné další aliasy.
- **A8** — Heading cut: exact casefold+trim, jen řádky `## …` (ne `###`, ne substring).
- **A9** — `total_error` = výsledek **posledního** pokusu; sleep jen mezi pokusy.
- **A10** — Byte capy haystack body (UTF-8): (1) po transcript cut → **8192**; (2) po keep-cut → **8192**; (3) žádný marker ani keep → **4096**.
- **A11** — Grill Q1=**b** / Q2=**a** (T15 smoke).
- **A12** — P: happy path (0×503) tick **&lt;180 s**; 503-retry path až ~3×120 s + 3 s sleep = **přijatý overrun** (ne happy-path budget).

## Současný stav

- `HEAD_CAP_BYTES = 8192`; `enrich_path_sources` = `stem + text[:8KiB]` pro všechny PATH_SOURCES.
- `fetch_l1_brain` — jeden `urlopen`, `HTTPError` → hned `brain_http_{code}`.
- Match rules word-boundary / title≥3 / body≥4; pool bez epic.
- Šablona Sembly: `## Shrnutí` / `## Akční body` / `## Plný transkript`.

## Návrh

### F1 — `_sembly_match_body(text) -> str` + sembly větev v `enrich_path_sources`

**Primární cut:** první řádek přesně `## …` (ne `###`) jehož casefold heading (trim) ∈ `{plný přepis, plný transkript, full transcript}` → body = vše **před** tím řádkem, pak UTF-8 cap **8192** (A10.1). Cut **před** capem (ne cap souboru a pak cut).

**Fallback keep-cut:** po `seen_keep` (heading ∈ `{shrnutí, summary, akční body, action items, action points, actions}`) cut před dalším `## ` ∉ keep; pak cap **8192** (A10.2).

**Fallback none:** žádný transcript ani keep → max **4096 B** (A10.3).

**Enrich (jen sembly):** `hay = stem + "\n" + body`; preview z ořezaného body (strip FM, ≤280). Ostatní PATH_SOURCES = stem+8KiB beze změny.

### F2 — `fetch_l1_brain` 503 retry

`max_503_retries=2`, injectable `sleep=time.sleep`; 502/500/… bez retry; finální chyba = mapování **posledního** pokusu. Log retry na **stdout**.

### F3–F5 — pytest → gate → push → Coolify dry-run smoke → TESTER skip.

## B#

| B# | Vstup | Výsledek | T# |
|---|---|---|---|
| B1 | Token jen v `## Plný transkript` | mimo haystack → žádný body-match | T1 |
| B2 | Token ve Shrnutí/Akčních bodech | v haystack → match OK | T2 |
| B3 | `## Plný přepis` / `## Full transcript` | cut | T3 |
| B3n | `### Plný transkript` / `## Foo Plný transkript` / `# Plný transkript` | **necut** → fallback A10 | T3n |
| B4 | Keep-cut pak non-keep `##` | cut před non-keep + cap 8192 | T4 |
| B5 | Bez markerů/keep, token za 4 KiB | mimo haystack | T5 |
| B5b | Transcript cut, pre-transcript &gt;8192, token Akční body za 8192 | mimo haystack; token před capem → match; cut před capem | T5b |
| B6 | `daily` s transcript heading v 8 KiB | stále včetně (ne A) | T6 |
| B7 | ID / title / body rules | beze změny | T7 |
| B8 | epic | excluded | T8 |
| B9 | 503→200 | success + 1 sleep(1.0) | T9 |
| B10 | 503×2→200 | success + sleep 1.0 pak 2.0 | T9b |
| B11 | 503×3 | `brain_http_503`; sleep 2× | T10 |
| B12 | 502 | hned bez retry | T11 |
| B13 | 503→URLError | `brain_error:…` (poslední pokus) | T10b |

## P

- Happy path (Brain 200 napoprvé): tick **&lt;180 s**.
- 503-retry path: až ~3×`BRAIN_TIMEOUT`(120) + 3 s = **přijatý overrun** (A12); cron nemá hard kill.

## T#

T1–T6 / T3n / T5b haystack · T7–T8 match/epic · T9–T11 / T10b retry · T14 gate · T15 Coolify `--force --dry-run` smoke · T16 TESTER skip.

## Pořadí

F1 → F2 → gate → push → QA smoke → Tester skip.

## Rizika

1. Neznámý heading transcriptu → fallback 4 KiB může šumět.
2. 503×hang 120 s → tick overrun (A12 přijato).
3. True-positive jen v transcriptu ztracen (záměr A).
4. Daily beze změny (R8).

## C# uzavřeno v r=3

NEW-1 P vs 3×120 → A12 · NEW-2 fallback capy → A10 · NEW-3 A8 negativní → B3n · NEW-4 post-cut 8192 → B5b · NEW-5/6 sleep+stdout.
