# Implementační plán — migrace na Drive API

> **Status (2026-05-23):** Phase **0–3** hotové. **Coolify Redeploy hotov** — běží image **`881b458`** (`140b40c7afe90d0827d8489a-012514625772`, supercronic OK). Phase **4.1 částečně** — triage + build + hourly cron ověřeno; **`edu_news_refresh --dry-run` padá** (`NameError: key` v `collect_hotovo_candidates`, ř. 203 — chybí `f"{slug}:{tid}"`). Phase **4.2–4.3** čekají na čas / E2E.
>
> **Phase 4.1 smoke (2026-05-23, image `881b458`, po redeploy):**
> - `triage_run` OK (`no inbox files to triage`)
> - `build_dashboard` OK (`inbox=0 pending=0 waiting=8`, bez tracebacku)
> - `/app/crontab` — hourly `build_dashboard` **8–21, :35** ✓; sent fallback v `triage_run.py` (`proposalType`, `archive_only`) ✓
> - `edu_news_refresh --dry-run` **FAIL** — `NameError: name 'key' is not defined` (`collect_hotovo_candidates`); `progressBaseline` / `cycleStartedAt` nelze ověřit dokud není fix
>
> **Předchozí smoke (image `29df869`, před redeploy):** `triage_run` OK (`proposals=1`); `build_dashboard` OK (`inbox=1 pending=3`); `edu_news_refresh` běžel, ale bez `progressBaseline` logiky z novějších commitů.

**Aktuální vault root:** `1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-` (`SECOND_BRAIN/OBSIDIAN/` na lukas@redbuttonedu.cz).

## Phase 0 — Prerequisites

- [x] **0.1** GCP project + Desktop App OAuth client (project ID `154572355439`). Drive API enabled. OAuth consent screen v Workspace org `redbuttonedu.cz` → refresh token nevyprší.
- [x] **0.2** Mac path `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN/` je verifikován jako Google Drive Desktop mirror folderu `1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-`. Smoke vidí všechny existující foldery (`01-INBOX`, `02-PROJEKTY`, `00-System`, `07-ARCHIV`, …) i 16 hub `.md` souborů.
- [x] **0.3** Architektura zdokumentována v `docs/sync-architecture.md`.
- [x] **0.4** Implementační plán zdokumentován v `docs/sync-implementation-plan.md` (tento soubor).
- [x] **0.5** OAuth refresh token získán: `~/.config/mrluc/oauth_creds.json` (mode 0600). Hodnota toho JSONu = `GOOGLE_DRIVE_OAUTH_JSON` env pro Coolify.

## Phase 1 — DriveVault library ✅ HOTOVO

**Cíl:** `lib/drive_io.py` s API, které se použije ve všech cron skriptech. Žádný cron skript se ještě nemění.

**Výsledek smoke testu (2026-05-21 15:55, lokálně proti reálnému Drive):**

```
== auth mode: oauth ==
== root meta: id=1YTTs... name=OBSIDIAN ==
== 01-INBOX children: daily, email, sembly, slack ==
== 02-PROJEKTY/*.md count: 16 hubs ==
== write + read + CAS rewrite + trash delete: ALL OK ==
```

### 1.1 `lib/drive_io.py`

API:

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class FileMeta:
    id: str
    name: str
    mime_type: str
    modified_time: datetime  # UTC, sec precision
    size: int | None  # None pro Google-native (folder)

class DriveVaultError(Exception): ...
class DriveConflictError(DriveVaultError): ...  # CAS mismatch
class DriveNotFoundError(DriveVaultError): ...

class DriveVault:
    def __init__(self, root_folder_id: str, sa_info: dict): ...

    # Read
    def exists(self, rel_path: str) -> bool: ...
    def stat(self, rel_path: str) -> FileMeta: ...
    def read_text(self, rel_path: str) -> tuple[str, FileMeta]: ...
    def read_json(self, rel_path: str) -> tuple[object, FileMeta]: ...
    def list_dir(
        self, rel_path: str, *,
        pattern: str | None = None,  # glob-like; backed by name contains
        recursive: bool = False,
        include_folders: bool = False,
    ) -> list[FileMeta]: ...

    # Write
    def write_text(
        self, rel_path: str, text: str, *,
        expect_mtime: datetime | None = None,  # CAS; None = blind write
    ) -> FileMeta: ...
    def write_json(
        self, rel_path: str, obj: object, *,
        expect_mtime: datetime | None = None,
    ) -> FileMeta: ...
    def mkdir_p(self, rel_path: str) -> str: ...  # vrací folder ID

    # Move / delete
    def move(self, src_rel: str, dst_rel: str) -> FileMeta: ...
    def delete(self, rel_path: str, *, permanent: bool = False) -> None: ...
```

Vnitřně:

- `_resolve(rel_path) -> FileMeta` — postupný `files.list(name=..., parents=...)`, per-instance LRU cache `path → FileMeta`
- `_retry(fn, *, max_attempts=5)` — decorator s exponential backoff (1s, 2s, 4s, 8s, 16s + jitter) na `googleapiclient.errors.HttpError` se status_code in {429, 500, 502, 503, 504}, `socket.timeout`, `ssl.SSLError`
- `_drive` — instance `googleapiclient.discovery.build("drive", "v3", credentials=..., cache_discovery=False)`
- pagination: vlastní helper `_list_all(query, fields)` co loopuje přes `nextPageToken`

### 1.2 `tests/test_drive_io.py`

Pokrýt (mock `googleapiclient.discovery.build`):

- path resolution: nested path, root, neexistující → `DriveNotFoundError`
- `list_dir` s pagination (2 stránky)
- `list_dir` s pattern filterem (case-insensitive substring)
- `read_text` + UTF-8 dekódování
- `write_text` nový soubor → `files.create`
- `write_text` existující bez CAS → `files.update`
- `write_text` s CAS, server mtime > expect → `DriveConflictError`
- `mkdir_p` idempotentní (existing folder)
- `move` přes `addParents/removeParents`
- retry na HttpError 429 → 503 → success
- retry exhausted → raise

### 1.3 Lokální smoke test

Skript `scripts/smoke_drive_io.py` (kompletní):

```bash
# Z Macu (preferred):
GOOGLE_DRIVE_OAUTH_JSON="$(cat ~/.config/mrluc/oauth_creds.json)" \
VAULT_DRIVE_ID=1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz- \
.venv/bin/python scripts/smoke_drive_io.py
```

Skript: `auto-detect creds (oauth/sa)` → root stat → list `01-INBOX` → count `02-PROJEKTY/*.md` → write+read+CAS+trash dummy file v `00-System/Triage-Pending/`.

**Checkpoint:** ✅ unit testy zelené, smoke test prošel z Macu (15:55). Smoke z kontejneru — provedeme až po Phase 3 deploy.

## Phase 2 — Migrace cron skriptů ✅ HOTOVO

- [x] **2a** `cron/fetch_calendar.py` — `vault.write_json("00-System/calendar-events.json", …)`
- [x] **2b** `cron/triage_run.py` — INBOX scan, Triage-Pending batch + summary (Drive API); sent fallback + `proposalType` (2026-05-23)
- [x] **2c** `cron/sync_tasks_from_projekty.py` — `02-PROJEKTY/*.md` → `dashboard-tasks-source.json`; orphan prune
- [x] **2d** `cron/build_dashboard.py` — full migrace vč. CAS reactivate Waiting→ASAP, calendar modul, Triage-Applied archive
- [x] **2e** `cron/edu_news_refresh.py` — OPS2, CAS na `operations.md`, `cycleStartedAt` + `progressBaseline`
- [x] **2f** `cron/weekly_summary_draft.py`, `cron/retro_draft.py` — drafty do `00-System/weekly/` a `Memory/`

Vždy stejný pattern:

1. nahradit `VAULT = Path(os.environ.get("VAULT_PATH", ...))` → `vault = DriveVault(root_id, sa_info)`
2. `Path("rel/path").exists()` → `vault.exists("rel/path")`
3. `path.read_text(...)` → `text, meta = vault.read_text("rel/path")`
4. `path.write_text(...)` → `vault.write_text("rel/path", text, expect_mtime=meta.modified_time)` kde to dává smysl, jinak bez CAS
5. `path.glob(...)` → `vault.list_dir(..., pattern=...)`
6. `path.stat().st_mtime` → `meta.modified_time`

### 2a — `cron/fetch_calendar.py`

Nejjednodušší — žádný read z vaultu, jen output `00-System/calendar-events.json`. `OUT.write_text(...)` → `vault.write_json("00-System/calendar-events.json", payload)`.

### 2b — `cron/triage_run.py`

- read: `vault.list_dir("01-INBOX/<sub>", pattern="*.md")` pro `sub in ("slack","sembly","email","daily")`
- read: `vault.read_text(item.rel_path)` pro každý soubor (skip pokud header obsahuje `ZPRACOVÁNO`)
- write: `vault.write_json("00-System/Triage-Pending/<batch_id>-batch.json", batch)`
- write: `vault.write_text("00-System/Triage-Pending/<batch_id>-summary.md", summary)`
- `mkdir_p("00-System/Triage-Pending")` před prvním zápisem

### 2c — `cron/sync_tasks_from_projekty.py`

- `needs_sync()` → porovnat `modifiedTime` u nejnovějšího `02-PROJEKTY/*.md` vs. `00-System/dashboard-tasks-source.json`
- read: `vault.list_dir("02-PROJEKTY", pattern="*.md")` + `vault.read_text(...)` per soubor
- write: `vault.write_json("00-System/dashboard-tasks-source.json", data)` (bez CAS — jediný writer)

### 2d — `cron/build_dashboard.py`

Největší migrace.

- `refresh_sources()` → spustí migrovaný `sync_tasks_from_projekty.py` jako modul, ne `subprocess`
- `load_tasks()` → `vault.read_json("00-System/dashboard-tasks-source.json")`
- `count_inbox()`, `list_inbox_items()` → přes `vault.list_dir("01-INBOX/<sub>")`
- `list_pending_items()` → `vault.list_dir("00-System/Triage-Pending")` + `read_json`
- `reactivate_expired_waiting_in_vault()`:
  - per task: `text, meta = vault.read_text("02-PROJEKTY/<file>.md")`
  - modify text
  - `vault.write_text("02-PROJEKTY/<file>.md", new_text, expect_mtime=meta.modified_time)`
  - on `DriveConflictError`: log warn, skip — další cron iterace zkusí znovu
- `load_calendar()` → spustí migrovaný `fetch_calendar.py` jako modul; výsledek = `vault.read_json("00-System/calendar-events.json")`
- write payload: `vault.write_json("00-System/dashboard-data.json", payload)`, `vault.write_json("00-System/dashboard-build-stamp.json", stamp)`, `vault.write_text("00-System/Dashboard.html", html)`
- `weekly_review_meta()` → `vault.exists("00-System/weekly/...")`, atd.
- `archive_auto_reactivated_waiting_pending()` → `vault.list_dir("00-System/Triage-Pending", pattern="waiting-...")` + `vault.write_json` do Triage-Applied + `vault.delete` (trash)

**Pozor:** `OUT_JSON` (default `web/dashboard-data.json` lokální v repo) — toto bylo dvojí psaní (lokální i vault). V containeru web/ neexistuje, takže `OUT_JSON` je jen vault path. Po migraci necháme jen vault write.

### 2e — `cron/edu_news_refresh.py`

- read: `vault.list_dir("02-PROJEKTY", pattern="*.md")`, `vault.read_text(...)`
- read: `vault.read_json("00-System/edu-news-topics.json")` (pokud exists)
- read: `vault.read_text("02-PROJEKTY/operations.md")` s mtime
- modify (OPS2 marker block)
- `vault.write_text("02-PROJEKTY/operations.md", new_text, expect_mtime=meta.modified_time)` — CAS
- write: `vault.write_json("00-System/edu-news-topics.json", topics)`
- write: `vault.write_json("00-System/dashboard-tasks-source.json", data)` (eduNews merge)
- pak volá `build_dashboard.main()` (přímo jako modul)

### 2f — `cron/weekly_summary_draft.py`, `cron/retro_draft.py`

- read: `vault.read_json("00-System/dashboard-tasks-source.json")`
- read: `vault.list_dir("01-INBOX/<sub>", pattern="*.md")` (počítání)
- read: `vault.list_dir("00-System/Triage-Pending")`, `Triage-Applied`
- write: `vault.write_text("00-System/weekly/<week>-draft.md", text)` — bez CAS (draft přepíše vše)
- write: `vault.write_text("00-System/Memory/retro-<week>-draft.md", text)` — bez CAS

**Checkpoint po každém 2x:** lokální smoke z Macu (`GOOGLE_DRIVE_SA_JSON=... VAULT_DRIVE_ID=... python3 cron/<skript>.py`), výstup vidíme přes Drive UI nebo Drive Desktop mirror.

## Phase 3 — Docker, Coolify, deployment ✅ HOTOVO

- [x] **3.1** `Dockerfile` — stateless, bez `VAULT_PATH` / `/data/mrluc`
- [x] **3.2** `deploy/crontab` — `VAULT_DRIVE_ID`, hourly `build_dashboard` **8–21** (`:35`, log `build-hourly.log`)
- [x] **3.3** `config.example.env` — `VAULT_DRIVE_ID`, `GOOGLE_DRIVE_OAUTH_JSON`, calendar env
- [x] **3.4** Coolify env — `VAULT_DRIVE_ID` + `GOOGLE_DRIVE_OAUTH_JSON` nastaveno (volume mount zatím kvůli Phase 5 safety net)

### 3.1 `Dockerfile`

```diff
- ENV VAULT_PATH=/data/mrluc \
+ # Stateless — Drive API only; logy do /var/log/second-brain
+ ENV \
     TZ=Europe/Prague \
-    DASHBOARD_JSON=/data/mrluc/00-System/dashboard-data.json \
-    LEGACY_TASKS=/data/mrluc/00-System/dashboard-tasks-source.json \
     PYTHONUNBUFFERED=1
```

`RUN mkdir -p /data/mrluc /var/log/second-brain` → `RUN mkdir -p /var/log/second-brain`.

### 3.2 `deploy/crontab`

```diff
- VAULT_PATH=/data/mrluc
- DASHBOARD_JSON=/data/mrluc/00-System/dashboard-data.json
- LEGACY_TASKS=/data/mrluc/00-System/dashboard-tasks-source.json
+ VAULT_DRIVE_ID=1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-
```

Ostatní jobs beze změny.

### 3.3 `config.example.env`

Přepis na nové env (`VAULT_DRIVE_ID`, `GOOGLE_DRIVE_OAUTH_JSON`, `CALENDAR_USER_EMAIL`).

### 3.4 Coolify

**Nové env (Available at Runtime):**

- `VAULT_DRIVE_ID=1YTTsTWFzrH6cNcZfvO_R-rhmSyFvlfz-`
- `GOOGLE_DRIVE_OAUTH_JSON=` ← obsah `~/.config/mrluc/oauth_creds.json` jako single-line JSON

**Smazat:** `VAULT_PATH`, `DASHBOARD_JSON`, `LEGACY_TASKS`, `GOOGLE_DRIVE_SA_JSON` (pokud byl nastavený), `GOOGLE_DRIVE_IMPERSONATE`.

**Nechat:** `CALENDAR_USER_EMAIL`, `CALENDAR_DAYS_AHEAD`, `GOOGLE_SERVICE_ACCOUNT_JSON` (calendar fetch má jiný flow), `TZ`.

**Volume mount** `/data/mrluc-second-brain → /data/mrluc` zůstává pro Phase 4 (safety net), v Phase 5 odebrat.

Git push `main` → Auto Deploy stáhne nový image.

## Phase 4 — Smoke a 24h cyklus

- [~] **4.1** Manuální smoke v kontejneru — **částečně hotovo** na image **`881b458`** (2026-05-23 redeploy): `triage_run` ✓, `build_dashboard` ✓, hourly cron 8–21 ✓, sent fallback v kódu ✓; **`edu_news_refresh --dry-run` ✗** (`NameError: key` — fix v `collect_hotovo_candidates` před uzavřením 4.1)
- [ ] **4.2** Sledování cron logů 24–48 h (Po–Pá triage 7/14/20, build +5 min, hourly build 8–21)
- [ ] **4.3** End-to-end: drop INBOX → batch → `agenda-triage` → hub + archiv → dashboard

### 4.1 Manuální spuštění v kontejneru

```bash
ssh coolify-dev "docker exec <container> python3 /app/cron/triage_run.py"
ssh coolify-dev "docker exec <container> python3 /app/cron/build_dashboard.py"
```

Kontrola:

- nový `Triage-Pending/<batch>-batch.json` v Drive UI (přímo)
- Drive Desktop sync na Mac (~1-60s) → vidíme batch v `OBSIDIAN/00-System/Triage-Pending/`
- Dashboard.html v Drive aktualizovaný (otevřít v Mac mirror, ověřit timestamp v hlavičce)

### 4.2 Sledování cron logů

```bash
ssh coolify-dev "docker exec <container> tail -f /var/log/second-brain/triage.log"
```

Sledovat 24-48h. Kontrola:

- `triage_run.py` 7:00, 14:00, 20:00 (Po-Pa) — `wrote ... proposals=N` nebo `no inbox files to triage`
- `build_dashboard.py` 7:05, 14:05, 20:05 — bez stack tracu
- žádný `DriveConflictError` na hub `.md` (kromě situace, kdy ses zrovna v Obsidianu editoval)

### 4.3 End-to-end test

1. Drop `.md` do Drive `01-INBOX/slack/` (přes Drive UI nebo n8n test)
2. Čekat na další cron iteraci (max 6h v pracovní dny)
3. Ověřit batch v `Triage-Pending/`
4. `agenda-triage` v Cursoru → schválit batch → změny v `02-PROJEKTY/...md`
5. Další cron build → dashboard aktualizovaný, archivovaný soubor v `07-ARCHIV/inbox-processed/...`

## Phase 5 — Cleanup (odloženo do stabilního týdne)

- [ ] **5.1** smazat `vps/second-brain-hub/scripts/sync_vault_to_vps.sh` — *deferred until 2026-05-30*
- [ ] **5.2** odstranit volume mount `/data/mrluc-second-brain → /data/mrluc` v Coolify — *deferred until 2026-05-30*
- [ ] **5.3** smazat data `/data/mrluc-second-brain` na coolify-dev (`sudo rm -rf`) — *deferred until 2026-05-30*
- [x] **5.4** README — přepsáno na Drive API architekturu (2026-05-23)
- [ ] **5.5** zkontrolovat `ŠABLONY/n8n/*.json` — INBOX root ID může být outdated — *deferred until 2026-05-30*

## Rollback

Každá fáze je samostatný commit. Coolify drží předchozí docker image v registry.

- **Phase 1 selhání:** nic se nezměnilo (jen nová knihovna, žádný kód ji nepoužívá)
- **Phase 2x selhání:** revert konkrétního commitu, push, Coolify Auto Deploy starší verzi
- **Phase 3-4 selhání:** revert Dockerfile commit, Coolify deploy předchozí tag; volume `/data/mrluc-second-brain` je stále tam (Phase 5 ještě neproběhla) → starý kód funguje
- **Phase 5 destruktivní operace** dělají se až po **>1 týdnu** stabilního běhu

## Validační kontrolní body

| Bod | Co měříme | Pass kritérium |
|---|---|---|
| Phase 1 | unit testy + smoke | `pytest` zelený, smoke skript print "OK" |
| Phase 2x | per-skript smoke z Macu | výstupní soubor v Drive odpovídá referenci (před migrací) |
| Phase 3 | Coolify Redeploy | `docker logs` ukazuje `supercronic ... level=info`, žádné Python ImportError |
| Phase 4 | cron 7:00 příštího dne | `triage.log` má `wrote ... batch ...` nebo `no inbox`, žádný traceback |
| Phase 5 | nic se nerozbije | po smazání volume další cron iterace stále funguje |
