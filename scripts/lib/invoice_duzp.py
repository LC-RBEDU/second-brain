"""Parse DUZP / VS / issuer from Czech invoice PDF text."""
from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Prague")

_DATE_CAP = r"(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](\d{2,4})"

_DUZP_PATTERNS = [
    re.compile(rf"(?i)DUZP\s*[:\-]?\s*{_DATE_CAP}"),
    re.compile(rf"(?i)Datum\s+zdaniteln[ée]ho\s+pln[eě]n[ií]\s*[:\-]?\s*{_DATE_CAP}"),
    re.compile(rf"(?i)Datum\s+zdan\.?\s*pln\.?\s*[:\-]?\s*{_DATE_CAP}"),
    # Alza: "Datum uskut. zdaň. plnění:"
    re.compile(
        rf"(?i)Datum\s+uskut\.?\s*zda[nň]\.?\s*pln[eě]n[ií]\.?\s*[:\-]?\s*{_DATE_CAP}"
    ),
    re.compile(rf"(?i)Date\s+of\s+taxable\s+supply\s*[:\-]?\s*{_DATE_CAP}"),
]
_DUZP_LABEL = re.compile(
    r"(?i)(?:DUZP|Datum\s+zdaniteln[ée]ho\s+pln[eě]n[ií]|Datum\s+zdan\.?\s*pln\.?|"
    r"Datum\s+uskut\.?\s*zda[nň]\.?\s*pln[eě]n[ií]\.?|"
    r"Date\s+of\s+taxable\s+supply)"
)
# AlzaNEO period line when column extract puts dates away from DUZP label
_OBDOBI_START = re.compile(
    r"(?i)Obdob[ií]\s*:\s*(\d{4})-(\d{2})-(\d{2})"
)
_ISSUED_PATTERNS = [
    re.compile(rf"(?i)Datum\s+vystaven[ií]\s*[:\-]?\s*{_DATE_CAP}"),
]
_VS_LABEL = re.compile(
    r"(?i)(?:variabiln[ií]\s+symbol|VS)\s*[:\-]?\s*(\d{6,10})",
    re.MULTILINE,
)
# Allow label and number on adjacent lines (PDF column extract)
_VS_LABEL_NL = re.compile(
    r"(?i)(?:variabiln[ií]\s+symbol|VS)\s*[:\-]?\s*\n\s*(\d{6,10})"
)
_VS_LOOSE = re.compile(r"\b(\d{8,10})\b")

_ALLOWLIST_MAP = {
    "alza": "alza-neo",
    "neo": "alza-neo",
    "alzaneo": "alza-neo",
    "vodafone": "vodafone",
    "o2": "o2",
    "tmobile": "tmobile",
    "t-mobile": "tmobile",
    "innogy": "innogy",
    "cez": "cez",
    "pre": "pre",
    "eon": "eon",
    "fakturoid": "fakturoid",
}


def _parse_date_groups(d: str, m: str, y: str) -> date | None:
    try:
        yi = int(y)
        if yi < 100:
            yi += 2000
        return date(yi, int(m), int(d))
    except ValueError:
        return None


def _first_date(patterns: list[re.Pattern[str]], text: str) -> date | None:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return _parse_date_groups(m.group(1), m.group(2), m.group(3))
    return None


def _fold(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _slugify(s: str, max_len: int = 24) -> str:
    folded = _fold(s)
    out = re.sub(r"[^a-z0-9]+", "-", folded).strip("-")
    return (out[:max_len] or "unknown").rstrip("-")


def issuer_slug_from_text(
    text: str,
    *,
    from_header: str = "",
    subject: str = "",
    allowlist: list[str] | None = None,
) -> str:
    blob = _fold(f"{from_header} {subject} {text[:500]}")
    aliases = allowlist or list(_ALLOWLIST_MAP.keys())
    for token in aliases:
        t = _fold(token)
        if t and t in blob:
            return _ALLOWLIST_MAP.get(t, _slugify(t))
    # First word of From display name
    disp = re.sub(r"<[^>]+>", "", from_header).strip()
    if disp:
        return _slugify(disp.split()[0])
    return "unknown"


def _normalize_invoice_text(text: str) -> str:
    """Collapse NBSP / odd spaces so Czech invoice labels match."""
    t = (text or "").replace("\xa0", " ").replace("\u00a0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    return t


def parse_invoice_text(
    text: str,
    *,
    from_header: str = "",
    subject: str = "",
    email_date: date | None = None,
    allowlist: list[str] | None = None,
) -> dict[str, Any]:
    """Return duzp, issued, vs, issuer_raw, issuer_slug, confidence, subfolder."""
    text = _normalize_invoice_text(text)
    duzp = _first_date(_DUZP_PATTERNS, text)
    issued = _first_date(_ISSUED_PATTERNS, text)
    vs = None
    m = _VS_LABEL.search(text) or _VS_LABEL_NL.search(text)
    if m:
        vs = m.group(1)
    else:
        mlab = re.search(r"(?i)(?:variabiln[ií]\s+symbol|\bVS\b)\s*[:\-]?", text)
        if mlab:
            window = text[mlab.end() : mlab.end() + 200]
            # Prefer standalone VS; skip bank account fragments like 284636165/0300
            for dm in re.finditer(r"\b(\d{6,10})\b", window):
                end = dm.end()
                if end < len(window) and window[end] == "/":
                    continue
                vs = dm.group(1)
                break
        if not vs:
            m2 = _VS_LOOSE.search(text)
            if m2:
                vs = m2.group(1)

    # DUZP label then date: short window first; Alza often has no adjacent date
    if not duzp:
        mlab = _DUZP_LABEL.search(text)
        if mlab:
            short = text[mlab.end() : mlab.end() + 48]
            dm = re.search(_DATE_CAP, short)
            if dm:
                duzp = _parse_date_groups(dm.group(1), dm.group(2), dm.group(3))
            else:
                mob = _OBDOBI_START.search(text)
                if mob:
                    try:
                        duzp = date(int(mob.group(1)), int(mob.group(2)), int(mob.group(3)))
                    except ValueError:
                        duzp = None
            if not duzp:
                window = text[mlab.end() : mlab.end() + 280]
                dm = re.search(_DATE_CAP, window)
                if dm:
                    duzp = _parse_date_groups(dm.group(1), dm.group(2), dm.group(3))
                if not duzp:
                    # ISO yyyy-mm-dd in window (Období / EN invoices)
                    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", window)
                    if iso:
                        try:
                            duzp = date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
                        except ValueError:
                            duzp = None
    if not issued:
        mlab = re.search(r"(?i)Datum\s+vystaven[ií]", text)
        if mlab:
            window = text[mlab.end() : mlab.end() + 280]
            dm = re.search(_DATE_CAP, window)
            if dm:
                issued = _parse_date_groups(dm.group(1), dm.group(2), dm.group(3))

    slug = issuer_slug_from_text(
        text, from_header=from_header, subject=subject, allowlist=allowlist
    )

    if duzp:
        confidence = "duzp"
        use = duzp
    elif issued:
        confidence = "issued"
        use = issued
    elif email_date:
        confidence = "none"
        use = email_date
    else:
        confidence = "none"
        use = None

    subfolder = f"{use.month:02d}-{use.year}" if use else None
    return {
        "duzp": duzp.isoformat() if duzp else None,
        "issued": issued.isoformat() if issued else None,
        "vs": vs,
        "issuer_raw": from_header or None,
        "issuer_slug": slug,
        "confidence": confidence,
        "subfolder": subfolder,
        "effective_date": use.isoformat() if use else None,
    }


def parse_email_date(raw: str) -> date | None:
    """Parse common Gmail date header strings to a date (Prague calendar day)."""
    s = (raw or "").strip().strip('"').strip("'")
    if not s:
        return None
    # ISO
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    # Strip weekday
    s2 = re.sub(r"^[A-Za-z]{3},\s*", "", s)
    for fmt in (
        "%d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S",
        "%d %b %Y",
        "%d.%m.%Y",
    ):
        try:
            dt = datetime.strptime(s2[:26].strip(), fmt)
            if dt.tzinfo:
                dt = dt.astimezone(TZ)
            return dt.date()
        except ValueError:
            continue
    return None
