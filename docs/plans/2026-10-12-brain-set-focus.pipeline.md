# Pipeline: Brain set_focus (OAuth human)

**Projekt:** SECOND_BRAIN  
**Base:** `origin/main` @ `046bed8`  
**Stav:** DONE  
**Tip:** `63902a2`  
**REVIEW:** SCHVÁLENO  
**QA:** PASS (2026-10-12)  
**TESTER:** přeskočeno (profil SECOND_BRAIN)

## Zamčené

Q1a · Q2a · Q3a · A1 oauth+Bearer · ghost overflow neřešit

## Ledger

| Stav | Detail |
|------|--------|
| PLAN | k=1 r=2 |
| GRILL | HOTOVÝ |
| CRITIC | SCHVÁLENO |
| IMPLEMENT | `1b9b806` + `d9e4631` |
| REVIEW | SCHVÁLENO |
| QA | PASS — Brain+hub image `63902a2`; import `set_focus`+`count_focus_slots`; `POST /v1/set_focus` bez auth → **401** |
| DONE | 2026-10-12 |

## QA důkazy

- Brain: `23c9620d…:63902a2` healthy  
- Hub: `140b40c7…:63902a2` Up  
- `PYTHONPATH=/app:/app/lib` → `count_focus_slots` + `app.tools.set_focus` OK  
- `curl POST https://brain.cyprovi.cz/v1/set_focus` → `401 authentication required`
