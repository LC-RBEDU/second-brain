# Pipeline: Rozhraní nástrojů Wiki / Drive / Architekt / Claude / Universe

Stav: AWAITING_USER (z: schválení plánu)
Plán: docs/plans/2026-10-06-rozhrani-nastroju.md
Schvalování plánu uživatelem: ano
Architekt: nová generace k=2/3, kolo r=1/3 (předchozí 60489607 po 3. kole, kritik K PŘEPRACOVÁNÍ)
Šťoural: agent ID a2d86e5d-a13a-4312-8917-7b7f47d579cd · kolo grill g=2 · POTŘEBUJE ODPOVĚDI · Q2 a Q3 BLOKUJÍCÍ
Počítadla: návraty do PLAN z REVIEW/QA/TESTER 0/3 · kola REVIEW 0/5 · kola QA 0/5 · kola TESTER 0/5 · ENV opravy 0/2
Base: neaplikuje se (žádný kód) · Kódový SHA: — · Review SCHVÁLENO na: — · QA PASS na: — · TESTER PASS na: přeskočeno (profil SECOND_BRAIN; výstup je text stránky, ne kód)
Plán schválen uživatelem: nevyžadováno do čtvrtka; zápis na Wiki až po schválení
Goal: bez goalu (uživatel nespustil /goal)

## Rozhodnutí z grillu

Q1, 2026-10-06, Lukáš (mimo karty A/B/C): Rozhodnutí, které má dopad na celou firmu a zároveň je veřejné, patří na Wiki. Rozhodnutí, které veřejné není, patří na Drive. Až se stane veřejným, umístí se na Wiki.

Grill kolo 2, 2026-10-06:
- Přechod bez celofiremního dopadu: varianta C. Po zveřejnění bez dopadu na celou firmu zůstane na Drive týmu. Na Wiki nejde.
- Zápis: mimo karty. „Zápis ze schůzky včetně rozhodnutí jde po schůzce na Drive - automaticky. Rozhodnutí samotné pak owner schůzky či tématu zveřejní na wiki, aby bylo dohledatelné kýmkoliv ve firmě. Duplicita v tomto případě nevadí.“

## Zadání (doslovně) a rozhodnutí

Uživatel chce smyčku nad stránkou https://wiki.redbuttonedu.cz/tymove-sekce/technari/rozhrani-nastroju-wiki-drive-architekt-claude

Dohodnutý průběh (2026-10-06):

1. Architekt navrhne úpravu stránky. Rozpor, který plyne z textu, srovná. Rozhodnutí, které z textu neplyne, nechá jako explicitní otevřenou volbu a nevybere ji.
2. Šťoural návrh projde. Verdikt HOTOVÝ GRILL, nebo blokující otázky.
3. Blokující otázky pokládá hlavní agent uživateli kartou (AskQuestion), ne subagent v chatu.
4. Kritik až po grillu bez blokujících otázek, jen na strukturu textu (jestli se podle něj dají napsat global instructions a skill). Kritik neověřuje kód RB Universe.
5. Na Wiki se do čtvrtka nezapisuje. Úkol IAD-S27 je Waiting, review_deadline 2026-10-08.

## Průběh

| # | Čas | Stav | Agent (ID) | Verdikt | BLOCKER/MAJOR/MINOR | Poznámka / přechod |
|---|-----|------|------------|---------|---------------------|--------------------|
| 1 | 2026-10-06 | PLAN | 60489607-21eb-4272-8a94-323f5d2f8965 | návrh textu | — | otevřené varianty, kolize 5 srovnaná z textu |
| 2 | 2026-10-06 | GRILL | 5b25039b-b625-4cf7-adb4-295dbcd18e40 | POTŘEBUJE ODPOVĚDI | Q1 BLOKUJÍCÍ | Patří pořád ukládá rozhodnutí na Wiki vedle otevřeného bodu |
| 3 | 2026-10-06 | AWAITING_USER (z: grill) | — | — | Q1 | karta |

## Otevřené nálezy

| ID | Závažnost | Typ IMPL/PLAN/ENV | Stav | Kolikrát vznesen |
|----|-----------|-------------------|------|------------------|
