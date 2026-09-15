#!/usr/bin/env python3
"""Složí hotovou HTML stránku zápisu v brand stylu Red Button EDU.

Vezme brand shell (assets/style.css), vloží logo jako base64 data URI
(assets/logo-rb-edu.txt), doplní hlavičku z meta.json a tělo z body.html.

Použití:
    python3 scripts/build_html.py --meta meta.json --body body.html --out zapis.html

meta.json (všechna pole kromě title/h1 jsou volitelná):
{
  "title":   "Priority na 2HY 2026 | Strategická schůzka 14. 9. 2026",
  "eyebrow": "#PRIORITY 2HY 2026",
  "h1":      "Priority na druhé pololetí",
  "kicker":  "Nedáváme nové věci. Dotahujeme to, co běží.",
  "stamp":   "Strategická schůzka · 14. 9. 2026",
  "meta_lines": [
    ["Účastníci", "Luboš Malý, Jan Mašek, ..."],
    ["Zdroj", "přepis schůzky (Sembly, 14. 9. 2026)"]
  ],
  "intro":   "Volitelný odstavec pod meta řádky v pravém sloupci hero.",
  "footer":  ["Odstavec 1 patičky.", "Odstavec 2 patičky."]
}
"""
import argparse
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"


def esc(value: str) -> str:
    return html.escape(str(value), quote=False)


def build_hero(meta: dict) -> str:
    left = [f'      <h1>{esc(meta["h1"])}</h1>']
    if meta.get("kicker"):
        left.append(f'      <div class="kicker">{esc(meta["kicker"])}</div>')
    if meta.get("stamp"):
        left.append(f'      <div class="stamp">{esc(meta["stamp"])}</div>')

    right = []
    for item in meta.get("meta_lines", []):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            label, value = item
            right.append(f'      <p class="meta"><b>{esc(label)}:</b> {esc(value)}</p>')
        else:
            right.append(f'      <p class="meta">{esc(item)}</p>')
    if meta.get("intro"):
        right.append(f'      <p style="margin-top:14px">{esc(meta["intro"])}</p>')

    if not right:
        return '  <section class="hero">\n    <div>\n' + "\n".join(left) + "\n    </div>\n  </section>"

    return (
        '  <section class="hero">\n    <div>\n'
        + "\n".join(left)
        + '\n    </div>\n    <div class="hero-right">\n'
        + "\n".join(right)
        + "\n    </div>\n  </section>"
    )


def build_footer(meta: dict) -> str:
    paragraphs = meta.get("footer") or []
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    if not paragraphs:
        return ""
    body = "\n".join(f"    <p>{p}</p>" for p in paragraphs)
    return f"  <footer>\n{body}\n  </footer>\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--meta", required=True, help="JSON s hlavičkou stránky")
    parser.add_argument("--body", required=True, help="HTML fragment s obsahem (bez <style>)")
    parser.add_argument("--out", required=True, help="Kam zapsat hotovou stránku")
    parser.add_argument("--assets", default=str(ASSETS), help="Složka s style.css a logo-rb-edu.txt")
    args = parser.parse_args()

    assets = pathlib.Path(args.assets)
    css_path = assets / "style.css"
    logo_path = assets / "logo-rb-edu.txt"
    for path in (css_path, logo_path):
        if not path.exists():
            print(f"CHYBA: chybí asset {path}", file=sys.stderr)
            return 1

    meta = json.loads(pathlib.Path(args.meta).read_text(encoding="utf-8"))
    if not meta.get("h1"):
        print("CHYBA: meta.json musí obsahovat 'h1'", file=sys.stderr)
        return 1

    body = pathlib.Path(args.body).read_text(encoding="utf-8")
    if "<style" in body.lower():
        print("CHYBA: body.html obsahuje <style>. Styl patří do assets/style.css.", file=sys.stderr)
        return 1

    css = css_path.read_text(encoding="utf-8")
    logo = logo_path.read_text(encoding="utf-8").strip()
    title = meta.get("title") or meta["h1"]
    eyebrow = meta.get("eyebrow", "#ZÁPIS")

    page = f"""<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
{css}</style>
</head>
<body>
<div class="grain" aria-hidden="true"></div>
<main class="page">

  <header class="topline">
    <div class="eyebrow">{esc(eyebrow)}</div><div class="line"></div>
    <img class="logo" alt="Red Button EDU" src="{logo}">
  </header>

{build_hero(meta)}

{body}
{build_footer(meta)}
</main>
</body>
</html>
"""

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"OK: {out} ({len(page):,} znaků)".replace(",", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
