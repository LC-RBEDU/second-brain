# Plán: Second Brain dashboard — save / refresh performance (2026-10-21) — **k=3 r=3**

*(Hlavní agent: přepiš [`docs/plans/2026-10-21-sb-dashboard-save-perf.md`](file:///Users/lukascypra/My%20Drive%20(lukas@redbuttonedu.cz)/SECOND_BRAIN/docs/plans/2026-10-21-sb-dashboard-save-perf.md). Stabilize DONE `a13cd696` neměnit; busy UI beze změny → B18 skip probe OK; žádné B-V* wireframy.)*

**Generace:** k=3. **r=3** (strop; grill g=2 + g=3 Q1=**1** editorial).  
**Přístup:** tip-safe `git_io` + durable registry; worker = `push_tip_ff_only` + poll ≤ 5 s; **Coolify = hub first + Brain auto-deploy off + `BRAIN_DEFER_PUSH` default-off do T32**. **Ostrý wall DoD = T20-live / F6 po F5b ∧ F5c.** Lokální T20 = preflight F0–F4 (fixture defer + A61), mimo Coolify bránu.

---

## Zadání a požadavky

| R# | Požadavek | Zdroj |
|---|---|---|
| R1 | Zrychlení save/refresh: lehčí post-save **a** zrychlení Brain PATCH. | Uživatel + CLARIFY Q1=**2** |
| R2 | Wall **&lt; 3 s** warm (**single-mutation only**), **až po F5b∧F5c** (defer=1 **a** F2 reconcile live). Cleanup **mimo** wall SLO. **Do F5b** = sync (B32). **F5b∧¬F5c** = defer live, FE export ještě možný — **ne** B32, **ne** R2 PASS. | CLARIFY Q2 + g=2 Q1=2 + 207e357c + **349040b7 NEW-1** |
| R3 | Všechny mutace s dnešním `onRefresh` po ok (cleanup = reconcile ano, wall ne). | CLARIFY Q2=**2a** |
| R4 | Root cause PATCH vs export (BFF, Brain, vault CAS/git). | Brief |
| R5 | Local reconcile first; Boot = full export; F3d jen fallback. | Brief + grill g1 Q2 |
| R6 | B20' reconcile (ne povinný full export); B11 mutex; busy smí zkrátit, ne flikat. | Brief |
| R7 | P: wall &lt;3 s + PATCH p50 do 200 (**post F5b∧F5c**); export jen Boot (+ B13). | Brief + **g=2 Q1** |
| R8 | B# / T# / Fáze; RBAC N/A; migrace N/A. | Brief |
| R9 | Rizika vč. async push fail (**Keep tip**, bez UI retry). | Brief + grill g2 (Keep tip) |
| R10 | Vizuál busy beze změny; layout probe jen při UI změně. | Brief |
| R11 | `testerGate=ano`; npm test + BFF pytest; push main → Coolify. | Profil |
| R12 | Baseline wall ~9–10 s; export ~1 s; PATCH ~8 s; image `a13cd696`. | Brief |
| R13 | F3c: 200 po local commit+oid; async push; tip-gate — **aktivní až defer=1**. | Grill g1 Q1 |
| R14 | parent/deadline = local merge + normalizace, 0× export. | Grill g1 Q2 |
| R15 | Cleanup **vždy** bez `_open_ids` (0× export) — success i failure. | Grill g1 Q4 + k=3 grill Q3=**2** |
| R16 | F3b po F1. | Grill g1 Q5 |
| R17 | **Keep tip:** push fail **NESMÍ** `reset --hard`. | Grill g2 Q1=**1** |
| R18 | **Allow chain:** healthy pending OK; tip-gate jen fail/orphan. | Grill g2 Q2=**2** |
| R19 | Push fail: N=3, pak hard gate + SSH; **žádný** UI retry. | Grill g2 Q3 + g3 A23 |
| **R20** | Hub Keep tip; tip-aware begin. | Critic Q1=**1** |
| **R21** | F3c = mutate **i** rebuild; 200 = local commit (+oid) při defer=1. | Critic k=1 |
| **R22** | Cleanup `saved` z request patchů (ne export open_ids). | 065f + b1ab NEW-1 |
| **R23** | Worker = `push_tip_ff_only`. | 065f NEW-2 |
| **R24** | Worker poll ≤ 5 s; HTTP wake bonus. | 065f NEW-3 |
| **R25** | Coolify: Brain auto-deploy off → F5a hub + T32 → F5b; defer default-off do T32, pak `1`. | NEW-6 + g5 Q1=**3** |
| **R26** | Enqueue fail → `GitEnqueueError` → 503 + tip Keep. | 4aeede NEW-7 |
| **R27** | T32: A57 reject remote + grep + **A55″** SSH tip clear; abort A56. | b1ab NEW-3 + grill |
| **R28** | Ostrý DoD = **T20-live** po **F5b ∧ F5c**. T20-live ⊆ B2–B6. Fáze: **do F5b** = B32; **F5b∧¬F5c** = interim (defer=1, export možný) — **ne** B32, **ne** R2; **F5b∧F5c** = T20-live. Lokální T20 ≠ Coolify brána (R29). | 207e357c + g=2/g=3 + **349040b7 NEW-1** |
| **R29** | Lokální T20 (F0–F4): fixture defer; **A60ᵀ** hard-skip bez defer; **A61** stub jen remote push. Formální R2 PASS = T20-live. | g=2 Q2/Q3 + g=3 Q1=1 |

**Mimo rozsah:** redesign shellu; vault schema při exportu; lehčí Boot; wall SLO cleanup; UI retry; redesign hub cronů (jen tip-safe); stabilize `a13cd696`; povinný HTTP wake.

**R3 call-sites:** `saveDetail`, `move`, `confirmDoing`, `confirmWaiting`, `patchDate`, `submitCleanup`, `applyFocus`, `createTask`, Q9. **Ne:** `proposeFocus`, `openDetail`, Boot.

### Grill / critic rozhodnutí (zavřené)

| Zdroj | Volba | Dopad |
|---|---|---|
| g1–g3 + Critic Q1 | F3c; Keep tip; Allow chain; hub; N=3 | R13–R21 |
| 065f / 4aeede / b1ab / 207e357c | A11‴; push_tip; poll; enqueue 503; F5 hub-first; A52″; A59 fáze; A55″ | R22–R28 |
| Grill k=3 g=1 | A57; A55″; A11‴; A58 | R15, R27 |
| **Grill k=3 g=2** (doporučené) | Q1=**2** F5b∧F5c; Q2=**1** A60ᵀ; Q3=**1** A61 | **R28, R29, A59′, A60ᵀ, A61** |
| **Grill k=3 g=3** (doporučené) | Q1=**1** oddělit lokální T20 vs T20-live | R28/R29/B16; A60ᵀ hard-skip |
| **Critic 349040b7** | B33 interim; A60ᵀ rename | R2, R28, P11, A59′ |

---

## Předpoklady

| A# | Předpoklad |
|---|---|
| A1 | Baseline: PATCH ≫ export; BFF timeout ≥ vault CAS. |
| A2 | Dnes: push fail → vždy `reset --hard` (`git_io.py:727–754`). |
| A3 | Export ~1 s. |
| A4 | PATCH `{path, oid, patched}`; SPA reconcile + norm. |
| A5–A6 | create / applyFocus (+ optional `push`). |
| A7 | R2 = F2 + F3c **po F5b ∧ F5c**. |
| A8 | Busy vizuál stabilize; visual gate neopakovat. |
| A9 | ~500 open tasks; QA count+bytes. |
| A10 | F3c kód povinný; live defer až F5b. |
| **A11‴** | Cleanup **vždy 0×** `_open_ids`. `saved` = written minus request `patch.status ∈ {Done,Cancelled}`; keep bez status ∈ saved. Fail path bez exportu. FE `hiddenWrittenIds` (`App.jsx:120–124,186,625–627`). |
| A12 | F3b po F1. |
| A13–A19 | siblings; wall≠cleanup; no UI retry; keep_tip prod; healthy/orphan; N=3. |
| **A20′** | `push_on_end=False` jen při defer (A52″); jinak sync (B32). |
| A21–A48 | tip-gate Allow jen defer=1; push≠push_on_end; enqueue před unlock; registry; replica=1; hub A29″; GitEnqueueError; push_tip; poll≤5s; A46′ keep bez status; ERROR_TEXT; A45. |
| **A49** | Coolify oddělené app; Brain `COPY …/lib/` (`Dockerfile:14`). |
| **A50′–A51** | F5 hub→Brain; A51 503 okno. |
| **A52″** | Brain: **`vault_deps._env_flag(env, key)`** 2-arg (`:32–34`); unset/`""`→False = sync. Ne `git_io._env_flag` 3-arg. Flip `1` až po T32+F5b. |
| **A53–A58** | T32 PASS / **A55″** SSH tip clear / A56 abort / A57 reject remote / A58 residual Brain reset = baseline. |
| **A59′** | **Tři fáze:** (1) **Do F5b:** defer=0 → **B32**. (2) **F5b ∧ ¬F5c (interim):** `BRAIN_DEFER_PUSH=1` → async push; FE ještě může exportovat — **B33**; **ne** B32, **ne** R2/B16 PASS. (3) **F5b ∧ F5c:** formální R2 = **T20-live ⊆ B2–B6**. F6 = F5b∧F5c. Lokální T20 = F0–F4. B20–B29 tip smí po F5b; F6 čeká F5c kvůli 0× export. |
| **A60ᵀ** | **T20 test skip** (≠ runtime A60–A64 tip/PUSH gate v `vault_deps.py`). Happy-path fixture = truthy defer. Bez → **hard-skip**. Defer=0 = T29/B2′/B32. |
| **A61** | **T20 stub:** jen remote / `git push`. Local commit + oid + enqueue běží. |

---

## Současný stav (ověřeno v kódu)

| Soubor:řádky | Fakt |
|---|---|
| `dashboard/web/src/writes.js:118–125` | keep → `{review_deadline}` bez status |
| `dashboard/web/src/ui/App.jsx:120–124,186,625–627` | `hiddenWrittenIds` = written\saved |
| `dashboard/web/src/main.jsx:78–95,114` | `onRefresh` = full export |
| `dashboard/bff/.../app.py:293–372` | cleanup vždy `_open_ids`; saved ∩ open_ids |
| `brain/.../vault_deps.py:32–34` | `_env_flag(env, key)` 2-arg; empty→False |
| `brain/.../vault_deps.py:62–81,161–175` | tip-ahead→503; jen `GitPushError` |
| `hub/lib/git_io.py:61–65` | `_env_flag` 3-arg — **jiná** fn |
| `hub/lib/git_io.py:229–237,727–754` | commit-gated push; reset `@{upstream}` |
| `brain/Dockerfile:14` | `COPY second-brain-hub/lib/` |

---

## Root cause (R4)

```text
Dnes: Wall ≈ T(sync push) + T(export)
Po F2 only: Wall ≈ T(sync push) + reconcile (defer=0)
Po F5b∧F5c: Wall ≈ T(write+commit+oid) + reconcile → <3s
```

**Deploy:** defer-on před hub keep_tip = data loss → A52″ default-off. Ostrý wall bez F5c = měří defer bez reconcile → falešný / neúplný DoD → A59′.

---

## Návrh

### F2 — SPA/BFF

reconcile + R3; cleanup vždy 0× `_open_ids` (A11‴); A46′ saved; ERROR_TEXT. **F5c musí být live před T20-live.**

```python
by_id = {str(i["id"]): i for i in items}
TERMINAL = {"Done", "Cancelled"}
saved = [
    tid for tid in written
    if str((by_id.get(tid) or {}).get("patch") or {}).get("status") or "")
    not in TERMINAL
]
```

### F3-core / F3c / Hub tip-safe

keep_tip; `push_tip_ff_only`; registry; `GitEnqueueError`; Brain defer přes **A52″** 2-arg; worker/Allow jen defer=1.

### F5 — Coolify

```text
F5-prep Brain auto-deploy off; BRAIN_DEFER_PUSH unset/0   → B32
F5a      hub keep_tip → T32 → A55″ tip clear
F5b      Brain deploy; BRAIN_DEFER_PUSH=1                 → B33 interim (ne R2)
F5c      dashboard F2 reconcile live
         → F5b ∧ F5c odemyká T20-live / F6 / R2 (A59′)
```

### Docs

Keep tip; hub→Brain; enqueue 503; defer default-off; T32+A55″; wall DoD = F5b∧F5c; T20 A60ᵀ/A61; B33 interim.

### RBAC / migrace / Alembic / subnav

**Netýká se.**

---

## Kontrakt chování (B#)

| B# | Vstup / stav | Očekávaný výsledek | R# | T# |
|---|---|---|---|---|
| B1 | Boot cold | 1× full export | R5 | T1, T30 |
| **B2–B6** | R3 mutace **∧ defer=1** (lokál: F2 v tree; live: F5b∧F5c) | 200 pre-push; **0× export** post-save; wall &lt;3 s | R1–3, R28 | T2–T6, **T20** (lokál), **T20-live** (Coolify) |
| **B2′–B6′** | R3 **∧ defer=0** (do F5b) | = **B32**; ne FAIL R2 | R25, A59′ | T29 |
| **B33** | R3 **∧ F5b ∧ ¬F5c** (interim) | defer=1 async; FE export možný; wall nesmí se brát jako R2/B16 PASS; **ne** B32 | R28, A59′ | smoke poznámka / ne T20-live |
| **B7** | cleanup keep+Done | 0× `_open_ids`; keep∈saved; Done∉saved | R15,R22 | T16, T16b |
| B8–B15 | Done/child/CAS/B11/… | stávající | R3–R9 | T8–T15 |
| **B16** | wall **∧ defer=1** (formální live PASS = T20-live po F5b∧F5c) | &lt;3 s | R2,R28 | T20 (preflight), T20-live, T31 |
| **B17** | p50 do 200 **∧ defer=1** (live po F5b∧F5c) | &lt;2.5 s pre-push | R7 | T21 |
| B18–B19 | busy | skip / regress | R6,R10 | T17, T9 |
| B20–B29 | tip/push/enqueue (defer=1) | Keep tip; N=3; 503 enqueue | R17–R26 | T22–T28c |
| **B30–B31** | F5a / F5b | 0× reset @{upstream}; defer 0→1 po T32+A55″ | R25,R27 | T32 |
| **B32** | defer off (**do F5b**) | sync; žádný defer Allow | A52″,A59′ | T29 |

### Checklist A

| # | Stav |
|---|---|
| 1–2 | B1 / B2 (post F5b∧F5c) |
| 3–5 | **netýká se** |
| 6 | B20–B32 + **A59′ live DoD** |
| 7–11 | B7; B11; errors; hub↔Brain F5 |

---

## Výkonový rozpočet (P)

| # | Bod | Plán |
|---|---|---|
| 1 | Objem | ~500 open; QA bytes |
| 2 | SQL | **N/A** |
| 3 | Python | 1 write+commit; cleanup 0× export |
| 4 | Externí | do F5b sync; po F5b async+worker; F5c bez sync push na FE cestě |
| 5–7 | Payload / cache | optional `push`; FE reconcile |
| 8–10 | Násobení / FE / worker | 1 HTTP; B11; poll≤5 s (defer=1) |
| 11 | Cíl | **B16/B17 = T20-live po F5b∧F5c**; do F5b = B32; F5b∧¬F5c = B33 (ne wall SLO); B25 ≤5 s **po F5b** (worker, ne B32) |

---

## Testy (T#)

| T# | Typ | Owner | Poznámka | B# |
|---|---|---|---|---|
| T1–T15 | vitest/pytest | gate | + reconcile unit | B1, B8–B15 |
| **T16** / T16b | pytest / vitest | gate | keep+Done; 0× `_open_ids` | B7 |
| T17–T19 | vitest | gate | busy | B18–B19 |
| **T20** | PW-smoke / pytest | gate | F0–F4 preflight: fixture defer=1; wall+pre-push+0×export; **A60ᵀ** hard-skip bez defer; **A61** stub jen `git push` — **mimo** Coolify F5c bránu | B2–B6, B16, R29 |
| **T20-live** | smoke/QA | QA | Formální R2/B16 DoD: **⊆ B2–B6** na Coolify **až po F5b ∧ F5c** (1 warm R3) | B2–B6, B16, R28 |
| **T21** | pytest + QA | gate+QA | p50: lokál defer=1 (A60ᵀ/A61); live po F5b∧F5c | B17 |
| T22–T28c | pytest | gate | tip/push/enqueue | B20–B29 |
| **T29** | pytest | gate | defer unset→sync = B32 / B2′ | B32 |
| **T32** | smoke/QA | gate+QA | F5a + A55″ + A56 | B30–B31 |
| T30–T31 | PW-T6-full | Tester | po F5b∧F5c | B1–B32 |

### T20 kontrakt (A60ᵀ / A61) — lokální preflight

1. Happy-path fixture nastaví truthy `BRAIN_DEFER_PUSH`. Bez → **hard-skip** (A60ᵀ); defer=0 = T29.
2. Stub **pouze** remote push; assert: local commit, oid, enqueue (A61).
3. Assert B2–B6 subset lokálně (ne nahrazuje T20-live).
4. **T20-live** (po F5b∧F5c): stejný triple na Coolify = formální R2 PASS.

### T32 recept

1. A57 reject remote → hub write.
2. PASS: 0× `resetting hard to @{upstream}`; tip ahead ≥1.
3. **A55″** SSH `git -C /data/vault push`; `HEAD == @{upstream}`.
4. A56 abort → ne F5b.

**Gate lokálně:** npm test · bff/hub/brain pytest (T20 respektuje A60ᵀ).  
**Gate deploy:** T32+A55″ → F5b; **T20-live / F6 až po F5b ∧ F5c**.

---

## Pořadí implementace

| F | Obsah | Závisí |
|---|---|---|
| F0–F4 | keep_tip / push_tip / enqueue; F2 A11‴; F3c default-off; T20(A60ᵀ/A61)+T29 | — |
| F5-prep | Brain auto-deploy off; defer=0 | F4 |
| F5a | hub → T32 → **A55″** | F5-prep |
| F5b | Brain + defer=1 | F5a PASS |
| F5c | dashboard F2 live | F4; **povinně před F6** (∥ F5b OK, ale F6 čeká obojí) |
| **F6** | QA T20-live ⊆ B2–B6 + B20–B32 | **F5b ∧ F5c** |
| F7 | Tester T6 | F6 |
| F8 | DONE | F7 |

---

## Rizika a zpětná kompatibilita

1. F5b před F5a → data loss.
2. A51 503 — A55″ hned.
3. Enqueue bez typed map → 500.
4. Špatný `saved` → hide keep.
5. Defer default-on → data loss.
6. T32 bez abort → chaos.
7. **T20-live po F5b bez F5c** → wall OK, ale 0× export / reconcile neověřeno — porušení A59′ / R28.
8. T20 bez A60ᵀ hard-skip na defer=0 → falešný B16 FAIL.
8b. Brát F5b∧¬F5c wall jako B32 nebo R2 → porušení A59′ / B33.
9. T20 stub celého end_session → slepý enqueue (porušení A61).
9b. Zaměnit T20 (lokál) s T20-live (Coolify) v R28 → falešný / předčasný R2 PASS.
10. Záměna vault_deps vs git_io `_env_flag`.
11. Žádný UI retry; A58 residual baseline.

---

## Otevřené otázky pro uživatele

*Žádné.*

---

## C# / rozhodnutí → jak vyřešeno (k=3 r=3)

| ID | Typ | Verdikt | Jak |
|---|---|---|---|
| **g=2 Q1** | grill (BLOKUJÍCÍ) | **zapsáno** | **A59′ / R28:** F6 + T20-live = **F5b ∧ F5c**; T20-live ⊆ B2–B6. |
| **g=2 Q2** | grill | **zapsáno** | **A60ᵀ / R29:** T20 hard-skip bez truthy defer; defer=0 → T29/B2′/B32. |
| **g=2 Q3** | grill | **zapsáno** | **A61 / R29:** T20 stubuje jen remote/`git push`; commit+oid+enqueue běží. |
| **g=3 Q1** | grill (BLOKUJÍCÍ) | **zapsáno** | Coolify = T20-live; T20 = F0–F4 (A60ᵀ). |
| **NEW-1** (349040b7) | critic MAJOR | **vyřešeno** (editorial) | R2/R28/P11/A59′: do F5b=B32; F5b∧¬F5c=**B33**; F5b∧F5c=T20-live. |
| **NEW-2** (349040b7) | critic MINOR | **vyřešeno** (editorial) | A60 → **A60ᵀ** (≠ vault_deps A60 gate). |
| NEW-1…3 (207e357c) | critic | **vyřešeno** | A59′; A52″; A55″. |
| NEW-1…3 (b1ab1542) | critic | **vyřešeno** | A11‴; defer off; T32 recept. |
| 065f / 4aeede | critic | **ověřeno** | beze změny intentu. |

### Delta k=3 r=2 → k=3 r=3 (pro IMPL)

1. **F6 / T20-live** až po **F5b ∧ F5c**; formální R2 = T20-live ⊆ B2–B6.
2. **T20** lokál = F0–F4 preflight (A60ᵀ; A61) — **ne** Coolify brána.
3. A59′ tři fáze + **B33** interim; R28/R29.
