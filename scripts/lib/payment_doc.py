"""B1 payment-doc detection + B0/B4 helpers for personal Gmail receipts."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_ALLOWLIST = [
    "alza",
    "neo",
    "alzaneo",
    "vodafone",
    "o2",
    "tmobile",
    "t-mobile",
    "innogy",
    "cez",
    "pre",
    "eon",
    "fakturoid",
]
DEFAULT_SUBJECT_RE = re.compile(
    r"(?i)(faktur|vyúčtov|invoice|doklad|receipt|účtenk|platb|neo)"
)
DEFAULT_VS_RE = re.compile(r"\b(\d{6,10})\b")
DEFAULT_BODY_MONEY_RE = re.compile(
    r"(?i)(\d[\d\s]*\s*(Kč|CZK|EUR|USD)|faktura|invoice|vyúčtov)"
)
B4_PHRASE_RE = re.compile(
    r"(?i)(stáhnout\s+fakturu|stáhnout\s+doklad|stáhnout\s+pdf|"
    r"download\s+invoice|download\s+pdf|daňový\s+doklad)"
)
HREF_RE = re.compile(
    r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
)

INCLUDE_EXTS = {
    ".pdf",
    ".png",
    ".jpeg",
    ".jpg",
    ".gif",
    ".webp",
    ".heic",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".txt",
    ".csv",
}
SKIP_EXTS = {".ics", ".smime", ".p7s", ".p7m"}
SKIP_NAMES = {"winmail.dat", "smime.p7s", "smime.p7m"}
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_FILES = 20
INLINE_IMAGE_SKIP_BYTES = 8 * 1024


def load_payment_config(vault: Path | None = None) -> dict[str, Any]:
    if vault is None:
        vault = (
            Path.home()
            / "My Drive (lukas@redbuttonedu.cz)"
            / "SECOND_BRAIN"
            / "OBSIDIAN"
        )
    path = vault / "00-System" / "personal-payment-docs.json"
    if not path.is_file():
        return {
            "drive_root_folder_id": "1CpvJdkIgtzNqz33Bf61tseyyWXWySqDK",
            "subfolder_format": "MM-YYYY",
            "timezone": "Europe/Prague",
            "downloads_max_age_days": 14,
            "issuer_allowlist": DEFAULT_ALLOWLIST,
            "subject_regex": DEFAULT_SUBJECT_RE.pattern,
            "vs_regex": DEFAULT_VS_RE.pattern,
            "body_money_regex": DEFAULT_BODY_MONEY_RE.pattern,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def is_payment_doc(
    *,
    from_header: str = "",
    subject: str = "",
    body: str = "",
    stem_attachments: list[str] | None = None,
    config: dict[str, Any] | None = None,
) -> bool:
    cfg = config or {}
    allow = [a.lower() for a in (cfg.get("issuer_allowlist") or DEFAULT_ALLOWLIST)]
    subj_re = re.compile(cfg.get("subject_regex") or DEFAULT_SUBJECT_RE.pattern)
    vs_re = re.compile(cfg.get("vs_regex") or DEFAULT_VS_RE.pattern)
    money_re = re.compile(cfg.get("body_money_regex") or DEFAULT_BODY_MONEY_RE.pattern)

    from_l = (from_header or "").lower()
    signal = False
    if any(tok in from_l for tok in allow):
        signal = True
    elif subj_re.search(subject or ""):
        signal = True
    elif vs_re.search(body or "") and money_re.search(body or ""):
        signal = True

    if not signal:
        return False

    # Rule 4: if attachments exist, still require 1∨2∨3 (already true here)
    # When no signal, attachment alone is NOT enough (plan: stem AND (1∨2∨3))
    _ = stem_attachments
    return True


def should_download_pdf_href(
    *,
    href: str,
    anchor_text: str = "",
    is_payment: bool,
) -> bool:
    href_l = (href or "").lower()
    if B4_PHRASE_RE.search(anchor_text or ""):
        return True
    if ".pdf" in href_l and is_payment:
        return True
    return False


def extract_b4_pdf_urls(html: str, *, is_payment: bool) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for m in HREF_RE.finditer(html or ""):
        href, anchor = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        if should_download_pdf_href(href=href, anchor_text=anchor, is_payment=is_payment):
            if href not in seen:
                seen.add(href)
                urls.append(href)
    return urls


def b0_should_keep(
    *,
    filename: str = "",
    mime: str = "",
    size: int = 0,
    disposition: str = "",
) -> bool:
    name = (filename or "").strip()
    mime_l = (mime or "").lower()
    disp = (disposition or "").lower()
    if size <= 0 and not name:
        return False
    if size > MAX_FILE_BYTES:
        return False
    base = name.lower().rsplit("/", 1)[-1]
    if base in SKIP_NAMES:
        return False
    ext = ""
    if "." in base:
        ext = "." + base.rsplit(".", 1)[-1]
    if ext in SKIP_EXTS or "calendar" in mime_l or mime_l in {
        "text/calendar",
        "message/rfc822",
        "application/pkcs7-mime",
        "application/pkcs7-signature",
        "application/x-pkcs7-mime",
    }:
        return False
    if mime_l == "application/octet-stream" and not name:
        return False
    is_image = mime_l.startswith("image/") or ext in {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".heic",
    }
    if is_image and "inline" in disp and size < INLINE_IMAGE_SKIP_BYTES:
        return False
    if "attachment" in disp or name:
        if ext in INCLUDE_EXTS or mime_l in {
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
            "text/plain",
            "text/csv",
            "application/zip",
        }:
            return True
        # named attachment with known-ish mime
        if name and ("pdf" in mime_l or "image/" in mime_l or "officedocument" in mime_l):
            return True
    return False


def b0_select_largest(files: list[dict[str, Any]], limit: int = MAX_FILES) -> list[dict[str, Any]]:
    ranked = sorted(files, key=lambda f: int(f.get("size") or 0), reverse=True)
    return ranked[:limit]


def find_receipt_attachment(stem_dir: Path, stem: str) -> Path | None:
    """First pdf else first image matching `{stem}__*.{pdf,jpg,jpeg,png}` (case-insensitive ext)."""
    pdfs = sorted(
        p
        for p in stem_dir.glob(f"{stem}__*")
        if p.is_file() and p.suffix.lower() == ".pdf"
    )
    if pdfs:
        return pdfs[0]
    for ext in (".jpg", ".jpeg", ".png"):
        imgs = sorted(
            p
            for p in stem_dir.glob(f"{stem}__*")
            if p.is_file() and p.suffix.lower() == ext
        )
        if imgs:
            return imgs[0]
    return None
