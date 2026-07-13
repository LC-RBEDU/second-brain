---
name: agenda-retro
description: "Use for retrospektiva spolupráce, retro MrLUC, vylepšení systému/vault/dashboard/skills. Weekly (Sunday evening) after weekly draft. Reads retro-YYYY-Www-draft.md, writes retro-YYYY-Www.md with Keep/Problem/Try. Meta-level — not project tasks. ALWAYS preview before write."
---

# agenda-retro

> Týdenní meta-reflexe: jak funguje MrLUC jako systém práce (ne obsah projektů).

## Kdy spouštět

- "Retro" / "retrospektiva" / "jak zlepšit MrLUC"
- Neděle večer — typicky po `agenda-weekly-review`
- Draft: `00-System/Memory/retro-YYYY-Www-draft.md`

## Vstupy

1. Retro draft (cron skeleton)
2. Weekly draft nebo finální `00-System/weekly/YYYY-Www.md` ze stejného týdne
3. `00-System/Triage-Applied/` — co se aplikovalo tento týden (soubory podle data)
4. `00-System/agent-context.json` — system snapshot
5. Volné poznámky uživatele v chatu

**Vault (v2):** `/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN`

## Výstupní struktura (`retro-YYYY-Www.md`)

```markdown
# Retro — týden YYYY-Www

## Keep (co nechat)
- ...

## Problem (co bolí)
- ...

## Try next week (1 experiment)
- Jedna konkrétní změna procesu/nástroje, měřitelná příští týden
```

## Workflow

1. Načti draft + weekly
2. Doplň Keep/Problem/Try — buď konkrétní (ne „lépe komunikovat“)
3. Preview celého souboru
4. Po „schval“ zapiš finální `retro-YYYY-Www.md`

## Pravidla

- **1 experiment** max na týden — jinak se nic nezmění
- Neřeš obsah obchodních projektů — k tomu weekly review
- Návrhy na kód/cron/skills jsou vítané; implementace až v další session
