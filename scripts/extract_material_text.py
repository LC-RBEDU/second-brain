#!/usr/bin/env python3
"""Generate/update attachment sidecar .md with ## Extrahovaný text.

Convention: co-located binary + sidecar `<basename>.md` in materials/.
Sidecar frontmatter: type: attachment, project, source, captured, file.

Usage:
  python3 scripts/extract_material_text.py path/to/file.pdf
  python3 scripts/extract_material_text.py --dir OBSIDIAN/02-PROJEKTY/finance/materials/
  python3 scripts/extract_material_text.py --dry-run file.pdf
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pip3 install pyyaml\n")
    sys.exit(1)

DEFAULT_VAULT = Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
BINARY_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".pptx"} | IMAGE_EXTENSIONS


def _extract_pdf(path: Path) -> str:
    try:
        import fitz  # pymupdf

        doc = fitz.open(path)
        parts = [page.get_text() for page in doc]
        doc.close()
        text = "\n\n".join(p.strip() for p in parts if p.strip())
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception as exc:
        return f"_(PDF extrakce selhala: {exc})_"

    try:
        r = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except FileNotFoundError:
        return "_(pdftotext/pymupdf nedostupné — nainstaluj pymupdf nebo poppler)_"
    except Exception as exc:
        return f"_(pdftotext selhal: {exc})_"
    return "_(PDF bez extrahovatelného textu)_"


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document

        doc = Document(str(path))
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(parts) if parts else "_(prázdný docx)_"
    except ImportError:
        return "_(python-docx nedostupné — pip install python-docx)_"
    except Exception as exc:
        return f"_(docx extrakce selhala: {exc})_"


def _extract_plain(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        return f"_(čtení selhalo: {exc})_"


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in (".docx", ".doc"):
        return _extract_docx(path)
    if ext in TEXT_EXTENSIONS:
        return _extract_plain(path)
    if ext in IMAGE_EXTENSIONS:
        return (
            "_(obrázek — vision caption doplní agent při triáži/analyze; "
            f"embed: ![[{path.name}]])_"
        )
    return f"_(extrakce pro {ext} zatím neimplementována)_"


def _infer_project(path: Path, vault: Path) -> str:
    parts = path.parts
    if "02-PROJEKTY" in parts:
        idx = parts.index("02-PROJEKTY")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return ""


def sidecar_path(binary: Path) -> Path:
    return binary.with_suffix(binary.suffix + ".md")


def build_sidecar(
    binary: Path,
    *,
    vault: Path,
    project: str = "",
    source: str = "manual",
    extracted: str = "",
) -> str:
    project = project or _infer_project(binary, vault)
    fm = {
        "type": "attachment",
        "project": project,
        "source": source,
        "captured": date.today().isoformat(),
        "file": binary.name,
    }
    body = [
        "---",
        yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        f"![[{binary.name}]]",
        "",
        "## Extrahovaný text",
        "",
        extracted or "_(prázdné)_",
        "",
    ]
    return "\n".join(body)


def update_sidecar_extracted(content: str, extracted: str) -> str:
    if "## Extrahovaný text" in content:
        return re.sub(
            r"(## Extrahovaný text\s*\n)([\s\S]*?)(\n## |\Z)",
            lambda m: m.group(1) + extracted + "\n\n" + (m.group(3) if m.group(3).startswith("## ") else ""),
            content,
            count=1,
        )
    return content.rstrip() + f"\n\n## Extrahovaný text\n\n{extracted}\n"


def process_file(path: Path, *, vault: Path, dry_run: bool = False) -> bool:
    if path.suffix.lower() not in BINARY_EXTENSIONS and path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    if path.name.endswith(".md"):
        return False

    sc = sidecar_path(path) if path.suffix.lower() in BINARY_EXTENSIONS else path
    extracted = extract_text(path)

    if sc.exists() and sc != path:
        existing = sc.read_text(encoding="utf-8")
        new_content = update_sidecar_extracted(existing, extracted)
    else:
        new_content = build_sidecar(path, vault=vault, extracted=extracted)

    if dry_run:
        print(f"DRY {sc.relative_to(vault) if sc.is_relative_to(vault) else sc}: {len(extracted)} chars")
        return True

    sc.write_text(new_content, encoding="utf-8")
    print(f"OK {sc.relative_to(vault) if sc.is_relative_to(vault) else sc}")
    return True


def iter_binaries(directory: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(directory.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in BINARY_EXTENSIONS and not p.name.endswith(".md"):
            out.append(p)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--dir", type=Path, action="append", default=[])
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets: list[Path] = list(args.paths)
    for d in args.dir:
        if d.exists():
            targets.extend(iter_binaries(d))

    if not targets:
        parser.print_help()
        return 1

    n = 0
    for p in targets:
        if not p.exists():
            sys.stderr.write(f"SKIP missing: {p}\n")
            continue
        if process_file(p.resolve(), vault=args.vault, dry_run=args.dry_run):
            n += 1
    print(f"extract_material_text: {n} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
