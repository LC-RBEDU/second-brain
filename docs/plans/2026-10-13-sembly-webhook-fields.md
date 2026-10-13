# Plán: Sembly webhook field mapping + dedupe (Brain ingest)

Generace architekta k=2. Schvalování člověkem: ne → po SCHVÁLENO kritika → IMPLEMENT.

## Zadání a požadavky

| R# | Požadavek |
|---|---|
| R1 | Mapovat `meeting_title` / `meeting_started_at` / `meeting_transcription`. |
| R2 | Duration může být v sekundách; koerce + práh ≥1000 → minuty. |
| R3 | Stop false `deduped` přes `unknown-time-meeting.md`. |
| R4 | Dedupe SSOT = `.keys/<meeting_id>`. |
| R5 | Unit testy webhook + ingest. |
| R6 | Backward compat: legacy + `started_at`, `full_transcript`, `auto_summary`, `url`/`permalink`. |
| R7 | `python3 -m pytest vps/second-brain-brain/tests -q`. |
| R8 | Commit + push `main` (jen app+testy). |
| R9 | Coolify + smoke fake id. |
| R10 | Recovery / n8n / hub mimo scope. |
| R11 | Cleanup `unknown-time-meeting.md` + otrávené keys (hard gate F6; exact path). |
| R12 | TESTER přeskočeno. |
| R13 | attendees = participants alias; empty/whitespace skip. |
| R14 | Docs skip (A10). |
| R15 | Top-level `meeting_*` > nested legacy. |

## Předpoklady A1–A16

| A# | Text |
|---|---|
| A1 | Primární pole top-level `meeting_title` / `meeting_started_at` / `meeting_transcription`. Nested blob = legacy. Top-level `meeting_*` vždy vyhraje. |
| A2 | `duration_minutes` first. Else `duration`/`meeting_duration`: coerce number; ≥1000 → `round(n/60)` min; else minutes. Edge: real seconds &lt;1000 = known limit. |
| A3 | Collision: `cand=filename_for`; if exists → `{stem}-{key12}.md`; n=2; while exists → `{stem}-{key12}-{n}.md`. |
| A4 | Dedupe = `.keys/{safe}.path` only; **delete** `exists(rel)→deduped`. |
| A5 | Smoke `meeting_id=brain-smoke-<unix_ts>` + cleanup. |
| A6 | `attendees` alias `participants`. |
| A7 | Po T7 vždy R11 (i když smoke nevytvořil unknown-time). |
| A8 | R11 = MD **i** keys; bez obou → F6 FAIL. |
| A9 | Recovery mimo scope. |
| A10 | Docs skip. |
| A11 | Key: `id` → `meeting_id` → `meeting.id` → `meeting.meeting_id` → sha256[:16]. `_fs_safe`: non `[A-Za-z0-9._-]` → `_`. Path `.keys/{safe}.path`. |
| A12 | `_duration_minutes_value` → int \| `"—"`. Render: int → `**Trvání**: {n} min`; `"—"` → `**Trvání**: —`. |
| A13 | `_pick`: skip None / `""` / whitespace-only; `0` OK; strip strings. |
| A14 | Poison key: `.path` content `strip() == "01-INBOX/sembly/unknown-time-meeting.md"` (exact). |
| A15 | Tester skip. |
| A16 | `_meeting_blob` = first dict from `meeting` \| `meeting_data` \| `data` \| `{}`. |

## Současný stav

- `sembly_template.py`: chybí `meeting_*`; duration raw; participants bez attendees.
- `ingest_sembly.py`: `exists(rel)→deduped` (R3); key jen top-level id/meeting_id.
- `git_io.delete` raise if missing → exists guard; `list_dir` raise if dir missing.

## Návrh

### 1) `sembly_template.py`

Helpers `_meeting_blob`, `_pick` (A13), `_duration_minutes_value` (A2/A12).

| Pole | Klíče (payload pak blob) |
|---|---|
| Title | meeting_title → title → name → subject → meetingName |
| Start | meeting_started_at → start_time → started_at → meeting_start |
| Transcript | meeting_transcription → transcript → transcription → full_transcript → content |
| Summary | summary → auto_summary |
| Permalink | permalink → url → meeting_url |
| Participants | participants → attendees |
| Duration | duration_minutes → duration / meeting_duration (A2) |

### 2) `ingest_sembly.py`

```
key = _idempotency_key(payload)  # A11 + _fs_safe
key_path = f"{SEMBLY_DIR}/.keys/{key}.path"
key12 = key[:12]
with brain_vault(...) as vault:
  if vault.exists(key_path): return deduped True
  cand = filename_for(payload)
  stem = cand[:-3] if cand.endswith(".md") else cand
  rel = f"{SEMBLY_DIR}/{cand}"
  if vault.exists(rel):
    cand = f"{stem}-{key12}.md"; rel = f"{SEMBLY_DIR}/{cand}"; n = 2
    while vault.exists(rel):
      cand = f"{stem}-{key12}-{n}.md"; rel = f"{SEMBLY_DIR}/{cand}"; n += 1
  # NO exists(rel)→deduped
  mkdir; write MD; write key_path
```

### 3) Testy

- Nový `test_sembly_webhook_fields.py` (T1)
- Nový `test_ingest_sembly_collision.py` (T5/T6)
- Extend capture + no_llm (T2–T4); B9: `assert "llm" not in md.casefold()`

### 4) Docs skip.

### 5) F6 ops

```
until curl -fsS https://brain.cyprovi.cz/healthz | grep -q '"status":"ok"'; do sleep 5; done
# Bearer from Coolify env — never to chat
TS=$(date +%s)
curl -fsS -X POST https://brain.cyprovi.cz/v1/ingest_sembly \
  -H "Authorization: Bearer ${BRAIN_SERVICE_TOKEN}" -H "Content-Type: application/json" \
  -d "{\"payload\":{\"meeting_id\":\"brain-smoke-${TS}\",\"meeting_title\":\"Brain Smoke\",\"meeting_started_at\":\"2026-10-13T12:00:00+02:00\",\"meeting_transcription\":\"smoke\",\"duration_minutes\":15}}"
# expect deduped=false, stamp in path
# R11 via brain_vault mutate:
#   exists-guard before every delete (smoke MD/key, TARGET, poisoned keys)
#   if vault.exists("01-INBOX/sembly/.keys"): list_dir; delete if strip()==TARGET
#   if vault.exists(TARGET): delete(TARGET)
# B12 assert; without B12 → not DONE
```

TARGET = `01-INBOX/sembly/unknown-time-meeting.md`

C19 (MINOR z kritiky k=2): F6 `exists` před `list_dir(.keys)` i před každým `delete` — zapracováno.

## B#

| B# | Očekávání | T# |
|---|---|---|
| B1 | Webhook fields → stamp + MD | T1,T2 |
| B2 | Legacy nested OK | T3,T4 |
| B3 | Missing start + 2 ids → 2 files | T5 |
| B4 | Same id 2× → deduped | T4,T6 |
| B5 | Collision → stem-key12[-n] | T5 |
| B6 | duration 2700 → `**Trvání**: 45 min` | T1 |
| B7 | duration_minutes 30 → `**Trvání**: 30 min` | T3 |
| B8 | Prod smoke | T7 |
| B9 | `"llm" not in md.casefold()` | T3 |
| B10 | tip/PAUSED 503 unchanged | — |
| B11 | attendees → jména | T1 |
| B12 | R11 MD+keys pryč | T7 |
| B13 | jen started_at → stamp | T1,T3 |
| B14 | jen full_transcript → MD | T1,T3 |
| B15 | meeting_title vs nested title → top wins | T1 |
| B16 | whitespace title → next/default | T1 |
| B17 | duration_minutes wins over duration | T1 |
| B18 | unsafe key chars sanitized | T2 |

## P

0 SQL; pick &lt;5 ms; vault push dominates; collision O(n) exists.

## T#

| T# | Soubor | B# |
|---|---|---|
| T1 | test_sembly_webhook_fields.py | B1,B6,B11,B13–B17 |
| T2 | capture / FakeVault | B1,B18 |
| T3 | test_ingest_no_llm_idempotent.py | B2,B7,B9,B13,B14 |
| T4 | test_ingest_capture.py | B2,B4 |
| T5 | test_ingest_sembly_collision.py | B3,B5 |
| T6 | same | B4 |
| T7 | Coolify ops | B8,B12 |
| T8 | skip | — |

## Pořadí

F1 template+T1 → F2 ingest+T2–T6 → F3 skip → F4 pytest → F5 push → F6 Coolify+T7+R11 → F7 TESTER skip.

## Rizika

A2 leak &lt;1000s; orphan keys (R11); hash fallback; Coolify race; delete/list_dir exists-guards; A14 exact match.

## C1–C18 → vyřešeno

C1 R11+B12; C2 B11; C3 B7 T3; C4 exists before delete; C5 A12; C6 A10; C7 A13; C8 field table+B13/14; C9 F6 runbook; C10 A13; C11 collision; C12 A11 embed; C13 A2 coerce+limit; C14 F6 exact; C15 collision pseudocode; C16 A/C tables; C17 B9 strict; C18 A1/R15/B15.
