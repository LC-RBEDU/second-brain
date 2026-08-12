"""Sort checkboxes in the `## Operativní kroky` section of task files.

Ordering rule (vault convention):

1. open steps first (`- [ ]`), then completed ones (`- [x]`),
2. within each group ascending by subtask number (`**S12-4**` before `**S12-14**`),
3. letter suffixes stay next to their base number (`F41-3` then `F41-3b`).

`### ` subheadings inside the section act as boundaries — items are sorted
within each block, never moved across a subheading, because the grouping
carries meaning (e.g. "Import expense forecastu (z AF19)").

Continuation lines (indented bullets, wrapped text) travel with the checkbox
they belong to. Blank lines between items are normalised away.
"""
from __future__ import annotations

import re
import unicodedata

__all__ = [
    "sort_operational_steps",
    "is_operational_header",
    "subtask_sort_key",
]

_CHECKBOX_RE = re.compile(r"^-\s+\[([ xX])\]\s?(.*)$")
_SUBTASK_ID_RE = re.compile(r"^\*\*(?P<base>[A-Za-z]+\d+)-(?P<num>\d+)(?P<suffix>[A-Za-z]*)\*\*")

# Items we cannot parse keep their relative order but sink below numbered ones.
_UNPARSED_NUM = 10**6


def _fold(text: str) -> str:
    """Lowercase + strip diacritics, so 'Operativní' == 'operativni'."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def is_operational_header(line: str) -> bool:
    """True for the `## Operativní kroky` heading (diacritics-insensitive)."""
    if not line.startswith("## "):
        return False
    return _fold(line[3:].strip()).startswith("operativni kroky")


def subtask_sort_key(checked: bool, text: str, fallback: int) -> tuple:
    """Sort key for a single step. `fallback` keeps unparsed items stable."""
    m = _SUBTASK_ID_RE.match(text.strip())
    if not m:
        return (1 if checked else 0, _UNPARSED_NUM, "", fallback)
    return (
        1 if checked else 0,
        int(m.group("num")),
        m.group("suffix").lower(),
        fallback,
    )


class _Item:
    __slots__ = ("checked", "text", "lines", "index")

    def __init__(self, checked: bool, text: str, first_line: str, index: int):
        self.checked = checked
        self.text = text
        self.lines = [first_line]
        self.index = index

    @property
    def key(self) -> tuple:
        return subtask_sort_key(self.checked, self.text, self.index)


def _sort_block(lines: list[str]) -> tuple[list[str], bool]:
    """Sort one contiguous block of steps (no `### ` headings inside).

    Returns (lines, reordered). `reordered` is False when the steps were
    already in the right order, so the caller can leave the block byte-for-byte
    alone instead of churning blank lines.
    """
    items: list[_Item] = []
    preamble: list[str] = []
    for raw in lines:
        m = _CHECKBOX_RE.match(raw)
        if m:
            items.append(_Item(m.group(1) in "xX", m.group(2), raw, len(items)))
        elif items:
            if raw.strip():
                items[-1].lines.append(raw)
            # blank lines between items are dropped once we reorder
        elif raw.strip():
            preamble.append(raw)

    if not items:
        return lines, False

    order_before = [it.index for it in items]
    items.sort(key=lambda it: it.key)
    if [it.index for it in items] == order_before:
        return lines, False

    out: list[str] = list(preamble)
    if preamble:
        out.append("")
    for it in items:
        out.extend(it.lines)
    return out, True


def sort_operational_steps(body: str) -> tuple[str, bool]:
    """Return (new_body, changed)."""
    lines = body.split("\n")
    out: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        if not is_operational_header(line):
            out.append(line)
            i += 1
            continue

        out.append(line)
        i += 1

        # Collect the whole section up to the next H2 (or EOF).
        section: list[str] = []
        while i < len(lines):
            nxt = lines[i]
            if nxt.startswith("## ") or (nxt.startswith("#") and not nxt.startswith("###")):
                break
            section.append(nxt)
            i += 1

        # Trailing blank lines belong to the document, not the section.
        trailing = 0
        while section and not section[-1].strip():
            section.pop()
            trailing += 1

        rebuilt: list[str] = []
        block: list[str] = []
        reordered = False

        def flush(blk: list[str]) -> None:
            nonlocal reordered
            sorted_blk, did = _sort_block(blk)
            reordered = reordered or did
            rebuilt.extend(sorted_blk)

        for ln in section:
            if ln.startswith("### "):
                if block:
                    flush(block)
                    block = []
                if rebuilt and rebuilt[-1].strip():
                    rebuilt.append("")
                rebuilt.append(ln)
            else:
                block.append(ln)
        if block:
            flush(block)

        if not reordered:
            # Nothing to fix — keep the section exactly as the user wrote it.
            out.extend(section)
            out.extend([""] * trailing)
            continue

        while rebuilt and not rebuilt[0].strip():
            rebuilt.pop(0)

        changed = True
        out.extend(rebuilt)
        out.extend([""] * max(trailing, 1))

    return "\n".join(out), changed
