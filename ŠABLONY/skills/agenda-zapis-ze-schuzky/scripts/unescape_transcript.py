#!/usr/bin/env python3
"""Rozbalí Sembly přepis z tool resultu Google Drive a nechá ho číst po blocích.

`read_file_content` u velkých přepisů (150–250 kB) vrátí JSON uložený na disk,
uvnitř kterého je obsah dvakrát escapovaný. Tenhle skript z něj udělá čistý text
a umí ho vypsat po částech, aby se nenačítal celý najednou.

Použití:
    # 1) rozbalit
    python3 scripts/unescape_transcript.py --in tool_result.json --out transcript.md

    # 2) číst po blocích (default 40 000 znaků)
    python3 scripts/unescape_transcript.py --file transcript.md --chunk 1
    python3 scripts/unescape_transcript.py --file transcript.md --chunk 2 --size 40000

    # 3) jen hlavička (účastníci, datum) a statistika
    python3 scripts/unescape_transcript.py --file transcript.md --head
"""
import argparse
import json
import pathlib
import re
import sys


def extract(raw: str) -> str:
    """Vytáhne fileContent z tool resultu, ať je zabalený jakkoli hluboko."""
    data = json.loads(raw)

    # tool result bývá list bloků {"text": "<json string>"}
    if isinstance(data, list) and data:
        first = data[0]
        inner = first.get("text") if isinstance(first, dict) else first
        if isinstance(inner, str):
            try:
                data = json.loads(inner)
            except json.JSONDecodeError:
                return inner

    if isinstance(data, dict) and "fileContent" in data:
        content = data["fileContent"]
    elif isinstance(data, str):
        content = data
    else:
        content = json.dumps(data, ensure_ascii=False)

    # Sembly escapuje markdown ("\\#", "\\*"). Zdvojené zpětné lomítko je skutečné.
    content = content.replace("\\\\", "\x00").replace("\\", "").replace("\x00", "\\")
    return content


def show_head(text: str) -> None:
    header = text[:1200]
    print(header)
    print("---")
    print(f"délka: {len(text):,} znaků".replace(",", " "))
    speakers = sorted(set(re.findall(r"^([A-ZŠČŘŽÝÁÍÉÚŮŤĎŇ][^\d\n]{2,40}?) \d\d:\d\d:\d\d", text, re.M)))
    print(f"mluvčí v přepisu ({len(speakers)}): {', '.join(speakers) if speakers else '—'}")
    last = re.findall(r"(\d\d:\d\d:\d\d)", text)
    if last:
        print(f"poslední timestamp: {last[-1]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="src", help="JSON tool result z read_file_content")
    parser.add_argument("--out", help="Kam zapsat čistý přepis")
    parser.add_argument("--file", help="Už rozbalený přepis (pro --chunk / --head)")
    parser.add_argument("--chunk", type=int, help="Číslo bloku k vypsání (od 1)")
    parser.add_argument("--size", type=int, default=40000, help="Velikost bloku ve znacích")
    parser.add_argument("--head", action="store_true", help="Vypsat hlavičku a statistiku")
    args = parser.parse_args()

    if args.src:
        text = extract(pathlib.Path(args.src).read_text(encoding="utf-8"))
        out = pathlib.Path(args.out or "transcript.md")
        out.write_text(text, encoding="utf-8")
        blocks = (len(text) + args.size - 1) // args.size
        print(f"OK: {out} ({len(text):,} znaků, {blocks} bloků po {args.size:,})".replace(",", " "))
        return 0

    if not args.file:
        parser.error("zadej --in (rozbalení) nebo --file (čtení)")

    text = pathlib.Path(args.file).read_text(encoding="utf-8")

    if args.head:
        show_head(text)
        return 0

    if args.chunk:
        start = (args.chunk - 1) * args.size
        if start >= len(text):
            print(f"Blok {args.chunk} neexistuje — přepis má {len(text)} znaků.", file=sys.stderr)
            return 1
        print(text[start:start + args.size])
        return 0

    show_head(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
