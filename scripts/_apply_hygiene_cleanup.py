#!/usr/bin/env python3
"""Hygiene cleanup applier — idempotent.

Implements the manual decisions tied to `_audit_task_hygiene.py` 2026-05-26:
  Action 1 — K3 cross-project duplicity (4 deletes; firemni-procesy/P* → archive log into allfred/AF*).
  Action 2 — K2 2A: 3 MOVE+RE-ID firemni-procesy/F* → finance/F<new>.
  Action 3 — K2 2B: 8 RE-ID firemni-procesy/P* → firemni-procesy/FP<new>.
  Action 4 — DELETE empty orphan folder `02-PROJEKTY/obchodni-podminky-rb-edu/`.
  Wikilink rewrite across whole OBSIDIAN/ vault (idempotent — old stem/IDs replaced
  with new targets).

Dry-run by default. Pass `--write` to mutate the vault.

The script is intentionally ad-hoc (underscore prefix), kept untracked.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "ERROR: pyyaml not installed. Run: "
        "pip3 install --user --break-system-packages pyyaml\n"
    )
    sys.exit(1)

VAULT_ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN_ROOT = VAULT_ROOT / "OBSIDIAN"
PROJEKTY_DIR = OBSIDIAN_ROOT / "02-PROJEKTY"
ARCHIV_DIR = OBSIDIAN_ROOT / "07-ARCHIV" / "tasks-done"

EM_DASH = "\u2014"
SEPARATOR = f" {EM_DASH} "

LOG_DATE = "2026-05-26"

WIKILINK_SCAN_DIRS = (
    "00-System",
    "01-INBOX",
    "02-PROJEKTY",
    "03-AREAS",
    "05-RESOURCES",
    "06-CANVAS",
    "07-ARCHIV",
)

OPERATIONAL_HEADERS = {
    "## Operativní kroky",
    "## Akční kroky",
    "## Subtasky",
    "## Steps",
    "## Akční položky",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)

PREFERRED_FM_ORDER = [
    "id", "type", "title", "project", "slug", "aliases",
    "status", "ice_i", "ice_c", "ice_e",
    "deadline", "waitUntil", "created", "updated", "done_at",
    "materials", "source", "blocked_by",
    "recurring", "extra_module", "extra_state_file",
]


# ---------------------------------------------------------------------------
# sanitize_title: replicate rename_tasks_to_human_filenames.py
# ---------------------------------------------------------------------------

def sanitize_title(title: str) -> str:
    if not title:
        return ""
    s = title
    s = s.replace("\n", " ").replace("\t", " ").replace("\r", " ")
    s = s.replace(":", " ")
    s = s.replace("/", " -")
    s = s.replace("\\", " -")
    s = s.replace("?", "")
    s = s.replace("*", "")
    s = s.replace("<", "\u2039")
    s = s.replace(">", "\u203a")
    s = s.replace("|", "-")
    s = s.replace('"', "'")
    s = "".join(ch for ch in s if ord(ch) >= 0x20)
    s = re.sub(r" +", " ", s).strip()
    return s


def task_filename(task_id: str, title: str) -> str:
    sanitized = sanitize_title(title or "")
    if sanitized:
        return f"{task_id}{SEPARATOR}{sanitized}.md"
    return f"{task_id}.md"


# ---------------------------------------------------------------------------
# Action specs
# ---------------------------------------------------------------------------

@dataclass
class K3Delete:
    """Delete a firemni-procesy/P* duplicate, log into corresponding allfred/AF*."""
    old_id: str
    af_id: str
    src_relpath: str  # relative to OBSIDIAN/
    af_relpath: str   # relative to OBSIDIAN/


@dataclass
class K2Move:
    """Move firemni-procesy/F* (or archive F1) → finance/F<new>, with RE-ID."""
    old_id: str
    new_id: str
    src_relpath: str
    archive: bool


@dataclass
class K2Reid:
    """Renumber firemni-procesy/P* → FP<new>, no folder change."""
    old_id: str
    new_id: str
    src_relpath: str
    archive: bool


# Hard-coded plan from user instructions, with collision-safe IDs.
K3_DELETES = [
    K3Delete(
        old_id="P9", af_id="AF1",
        src_relpath="02-PROJEKTY/firemni-procesy/tasks/P9 — Otestovat Request for Invoicing proces v Alfrédu (PM vs. finance práva).md",
        af_relpath="02-PROJEKTY/allfred/tasks/AF1 — Otestovat Request for Invoicing proces v Alfrédu (PM vs. finance práva).md",
    ),
    K3Delete(
        old_id="P20", af_id="AF7",
        src_relpath="02-PROJEKTY/firemni-procesy/tasks/P20 — Platby vs. expenses v Alfredovi sjednotit postup.md",
        af_relpath="02-PROJEKTY/allfred/tasks/AF7 — Platby vs. expenses v Alfredovi sjednotit postup.md",
    ),
    K3Delete(
        old_id="P21", af_id="AF8",
        src_relpath="02-PROJEKTY/firemni-procesy/tasks/P21 — Příprava faktur v Alfredovi doplnit kroky s Dominikem.md",
        af_relpath="02-PROJEKTY/allfred/tasks/AF8 — Příprava faktur v Alfredovi doplnit kroky s Dominikem.md",
    ),
    K3Delete(
        old_id="P1", af_id="AF9",
        src_relpath="02-PROJEKTY/firemni-procesy/tasks/P1 — Project closing process v Alfrédu.md",
        af_relpath="02-PROJEKTY/allfred/tasks/AF9 — Project closing process v Alfrédu.md",
    ),
]

K2_MOVES = [
    K2Move(old_id="F6", new_id="F26",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/F6 — Firemní karty pravidla co proplácet přes firmu.md",
           archive=False),
    K2Move(old_id="F8", new_id="F27",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/F8 — Pravidla pro náhrady za cestovné (use-case list).md",
           archive=False),
    K2Move(old_id="F1", new_id="F28",
           src_relpath="07-ARCHIV/tasks-done/firemni-procesy/F1 — Alokace nákladů na projekty (utilizace).md",
           archive=True),
]

# Existing FP IDs in firemni-procesy: FP1, FP14, FP15. Next free starts at FP16.
# Allocate FP16..FP23 to the 8 remaining P* tasks deterministically by P number ascending.
K2_REIDS = [
    K2Reid(old_id="P3", new_id="FP16",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/P3 — Smlouvy s kontraktory - švárc.md",
           archive=False),
    K2Reid(old_id="P5", new_id="FP17",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/P5 — Pravidla evidence dovolené a volna.md",
           archive=False),
    K2Reid(old_id="P6", new_id="FP18",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/P6 — AI-based procesní řízení inspirace a směr.md",
           archive=False),
    K2Reid(old_id="P15", new_id="FP19",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/P15 — PM progress milníky vs. finance tracking (4 pohledy).md",
           archive=False),
    K2Reid(old_id="P22", new_id="FP20",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/P22 — Kurzová politika faktur ECB vs. ČNB (interní směrnice).md",
           archive=False),
    K2Reid(old_id="P23", new_id="FP21",
           src_relpath="02-PROJEKTY/firemni-procesy/tasks/P23 — Komentáře Jardy Fulneka k procesnímu dokumentu.md",
           archive=False),
    K2Reid(old_id="P7", new_id="FP22",
           src_relpath="07-ARCHIV/tasks-done/firemni-procesy/P7 — Napsat aktualizovaný medailonek pro web.md",
           archive=True),
    K2Reid(old_id="P8", new_id="FP23",
           src_relpath="07-ARCHIV/tasks-done/firemni-procesy/P8 — Neurazitelný stav podpisu smlouvy + náklady Káťa Gaillard.md",
           archive=True),
]

ORPHAN_FOLDER = OBSIDIAN_ROOT / "02-PROJEKTY/obchodni-podminky-rb-edu"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    k3_deletes_done: int = 0
    k3_deletes_skipped_idempotent: int = 0
    k2_moves_done: int = 0
    k2_moves_skipped_idempotent: int = 0
    k2_reids_done: int = 0
    k2_reids_skipped_idempotent: int = 0
    af_logs_appended: int = 0
    orphan_deleted: bool = False
    orphan_skipped_idempotent: bool = False
    wikilink_files_changed: int = 0
    wikilink_replacements: int = 0
    edge_cases: list[str] = field(default_factory=list)
    fail_reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------

ALL_TASK_GLOBS = (
    PROJEKTY_DIR / "*" / "tasks",
    ARCHIV_DIR,
)


def _all_task_md_paths() -> Iterable[Path]:
    for tasks_dir in sorted(PROJEKTY_DIR.glob("*/tasks")):
        if tasks_dir.is_dir():
            yield from sorted(tasks_dir.glob("*.md"))
    if ARCHIV_DIR.exists():
        for slug_dir in sorted(ARCHIV_DIR.iterdir()):
            if slug_dir.is_dir():
                yield from sorted(slug_dir.glob("*.md"))


def collect_existing_ids() -> set[str]:
    out: set[str] = set()
    for md in _all_task_md_paths():
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict):
            continue
        tid = fm.get("id")
        if tid:
            out.add(str(tid))
    return out


def preflight_id_collisions(stats: Stats) -> bool:
    existing = collect_existing_ids()
    new_ids: list[tuple[str, str]] = []
    for m in K2_MOVES:
        new_ids.append((m.new_id, m.old_id))
    for r in K2_REIDS:
        new_ids.append((r.new_id, r.old_id))

    bad = []
    for new_id, old_id in new_ids:
        if new_id == old_id:
            continue
        if new_id in existing and old_id != new_id:
            # collision unless this slot is already occupied by the corresponding
            # successfully-renamed task (idempotent re-run case)
            bad.append(f"new_id {new_id} already in use (would collide with re-id of {old_id})")

    if bad:
        # Distinguish idempotent re-runs (where new_id IS the file being renamed)
        # from real collisions. We check that the target file exists and the
        # source file does NOT — that's an idempotent state.
        real_bad = []
        for new_id, old_id in new_ids:
            if new_id == old_id:
                continue
            if new_id in existing:
                # Find source — does it still exist?
                src_relpaths = [
                    m.src_relpath for m in K2_MOVES if m.old_id == old_id and m.new_id == new_id
                ] + [
                    r.src_relpath for r in K2_REIDS if r.old_id == old_id and r.new_id == new_id
                ]
                src_exists = any((OBSIDIAN_ROOT / p).exists() for p in src_relpaths)
                if src_exists:
                    real_bad.append(f"FAIL: target ID {new_id} already in use AND source {old_id} still exists")
        if real_bad:
            stats.fail_reasons.extend(real_bad)
            return False
    return True


# ---------------------------------------------------------------------------
# YAML helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def serialize_frontmatter(fm: dict) -> str:
    ordered: dict = {}
    for key in PREFERRED_FM_ORDER:
        if key in fm:
            ordered[key] = fm[key]
    for key, value in fm.items():
        if key not in ordered:
            ordered[key] = value
    return yaml.safe_dump(
        ordered,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=1000,
    )


def render_task_text(fm: dict, body: str) -> str:
    fm_text = serialize_frontmatter(fm)
    if not body.endswith("\n"):
        body = body + "\n"
    return f"---\n{fm_text}---\n{body}"


# ---------------------------------------------------------------------------
# Body transforms
# ---------------------------------------------------------------------------

H1_RE = re.compile(r"^# +([A-Z]+\d+[a-z]?)( +" + re.escape(EM_DASH) + r" +)(.+)$", re.MULTILINE)


def update_h1(body: str, old_id: str, new_id: str) -> str:
    """Replace `# OLD — Title` with `# NEW — Title`. Idempotent."""
    def _sub(m: re.Match[str]) -> str:
        cur_id = m.group(1)
        if cur_id == new_id:
            return m.group(0)
        if cur_id == old_id:
            return f"# {new_id}{m.group(2)}{m.group(3)}"
        return m.group(0)
    return H1_RE.sub(_sub, body, count=1)


CHECKBOX_PREFIX_RE = re.compile(r"^(\s*-\s+\[[ xX]\]\s+)\*\*([A-Z]+\d+[a-z]?)-(\d+)\*\*(\s+)(.*)$")


def renumber_subtasks(body: str, old_id: str, new_id: str) -> str:
    """Rewrite **OLD-N** prefixes to **NEW-N** within OPERATIONAL_HEADERS sections.
    Idempotent — running with same NEW is a no-op.
    """
    lines = body.splitlines(keepends=False)
    out: list[str] = []
    in_op_section = False
    for line in lines:
        if line.startswith("## "):
            in_op_section = line.strip() in OPERATIONAL_HEADERS
            out.append(line)
            continue
        if in_op_section:
            m = CHECKBOX_PREFIX_RE.match(line)
            if m:
                cur_id = m.group(2)
                if cur_id == old_id:
                    new_line = f"{m.group(1)}**{new_id}-{m.group(3)}**{m.group(4)}{m.group(5)}"
                    out.append(new_line)
                    continue
        out.append(line)
    new_body = "\n".join(out)
    if body.endswith("\n") and not new_body.endswith("\n"):
        new_body += "\n"
    return new_body


def append_log_line(body: str, log_line: str) -> tuple[str, bool]:
    """Append a `- <log_line>` line to `## Poznámky / log` section. Idempotent.
    Returns (new_body, changed).
    """
    target_line = f"- {log_line}"
    if target_line in body:
        return body, False

    lines = body.splitlines(keepends=False)
    out: list[str] = []
    appended = False
    found = False
    in_section = False

    for i, line in enumerate(lines):
        out.append(line)
        if line.startswith("## "):
            if in_section and not appended:
                # Insert before the new section header
                out.insert(-1, target_line)
                appended = True
                in_section = False
            in_section = (line.strip() == "## Poznámky / log")
            found = found or in_section
            continue

    if in_section and not appended:
        # Section is the last one — append at end
        # Remove trailing empties before appending
        while out and out[-1].strip() == "":
            out.pop()
        out.append(target_line)
        appended = True

    if not found:
        # Section missing — create at end
        while out and out[-1].strip() == "":
            out.pop()
        out.append("")
        out.append("## Poznámky / log")
        out.append(target_line)
        appended = True

    new_body = "\n".join(out)
    if body.endswith("\n") and not new_body.endswith("\n"):
        new_body += "\n"
    return new_body, appended


def ensure_aliases(fm: dict, new_id: str) -> dict:
    new_fm = dict(fm)
    existing = new_fm.get("aliases")
    if existing is None:
        new_fm["aliases"] = [new_id]
        return new_fm
    if isinstance(existing, str):
        existing_list = [existing]
    elif isinstance(existing, list):
        existing_list = [str(x) for x in existing if x]
    else:
        existing_list = [str(existing)]
    if new_id not in existing_list:
        existing_list.append(new_id)
    new_fm["aliases"] = existing_list
    return new_fm


# ---------------------------------------------------------------------------
# Wikilink rewrite
# ---------------------------------------------------------------------------

def _build_wikilink_pattern(stems: Iterable[str]) -> re.Pattern[str]:
    alts = sorted(set(stems), key=len, reverse=True)
    if not alts:
        return re.compile(r"(?!x)x")
    escaped = "|".join(re.escape(s) for s in alts)
    # match `[[(prefix?)(stem)` followed by `]`, `|`, or `#`
    return re.compile(
        r"\[\["
        r"((?:[^\[\]#|]*?/)?"
        r"(?:" + escaped + r"))"
        r"(?=[\]|#])"
    )


def rewrite_wikilinks_in_text(text: str, table: dict[str, str], pattern: re.Pattern[str]) -> tuple[str, int]:
    if not table:
        return text, 0

    def _sub(m: re.Match[str]) -> str:
        full = m.group(1)
        if "/" in full:
            prefix, stem = full.rsplit("/", 1)
            prefix = prefix + "/"
        else:
            prefix, stem = "", full
        if stem not in table:
            return m.group(0)
        return f"[[{prefix}{table[stem]}"

    return pattern.subn(_sub, text)


def iter_vault_md_files() -> Iterable[Path]:
    for sub in WIKILINK_SCAN_DIRS:
        base = OBSIDIAN_ROOT / sub
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            yield path


def build_wikilink_table(planned_renames_old_new: list[tuple[str, str]]) -> dict[str, str]:
    """planned_renames_old_new is list of (old_stem_or_id, new_stem_or_id).

    Returns a dict mapping every variant we want rewritten:
      - bare ID (`P9` → `AF1`)
      - full old stem → new stem
    """
    table: dict[str, str] = {}
    for old, new in planned_renames_old_new:
        if old != new:
            table[old] = new
    return table


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def apply_k3_deletes(stats: Stats, dry_run: bool, write_log: list[str]) -> dict[str, str]:
    """Returns mapping {old_stem→AF_stem, old_id→AF_id} for wikilink rewrite."""
    rewrite_map: dict[str, str] = {}
    for spec in K3_DELETES:
        src = OBSIDIAN_ROOT / spec.src_relpath
        af = OBSIDIAN_ROOT / spec.af_relpath
        if not af.exists():
            stats.fail_reasons.append(f"FAIL: AF counterpart not found: {spec.af_relpath}")
            continue

        # Always plan wikilink rewrite (idempotent — even if file already gone)
        old_stem = src.stem
        af_stem = af.stem
        rewrite_map[old_stem] = af_stem
        rewrite_map[spec.old_id] = spec.af_id

        # Append log to AF — idempotent
        af_text = _read(af) or ""
        af_fm, af_body = parse_frontmatter(af_text)
        log_line = f"{LOG_DATE}: Sloučen duplicit z firemni-procesy/{spec.old_id}"
        new_body, changed = append_log_line(af_body, log_line)
        if changed:
            new_af_text = render_task_text(af_fm, new_body) if af_fm else f"---\n---\n{new_body}"
            if not dry_run:
                af.write_text(new_af_text, encoding="utf-8")
            stats.af_logs_appended += 1
            write_log.append(f"  AF log appended → {spec.af_relpath}")
        else:
            write_log.append(f"  AF log already present → {spec.af_relpath} (idempotent)")

        # Edge case: P9 has many more subtasks than AF1 — flag it
        src_text = _read(src)
        if src_text is not None:
            src_fm, src_body = parse_frontmatter(src_text)
            src_subs = len([1 for line in src_body.splitlines() if CHECKBOX_PREFIX_RE.match(line)])
            af_subs = len([1 for line in af_body.splitlines() if CHECKBOX_PREFIX_RE.match(line)])
            if src_subs > af_subs:
                stats.edge_cases.append(
                    f"K3 delete {spec.old_id}→{spec.af_id}: source has {src_subs} subtasks, target has {af_subs}. "
                    f"Extra subtasks in {spec.old_id} will be lost (per user instruction). Source preserved in Google Drive history."
                )

        # Delete source — idempotent
        if src.exists():
            if not dry_run:
                src.unlink()
            stats.k3_deletes_done += 1
            write_log.append(f"  DELETED → {spec.src_relpath}")
        else:
            stats.k3_deletes_skipped_idempotent += 1
            write_log.append(f"  already deleted → {spec.src_relpath} (idempotent)")

    return rewrite_map


def _apply_re_id_or_move(
    spec: K2Move | K2Reid,
    new_slug: str,
    new_project: str,
    archive_target_dir: Path,
    live_target_dir: Path,
    log_line_template: str,
    is_move: bool,
    stats: Stats,
    dry_run: bool,
    write_log: list[str],
) -> tuple[str, str] | None:
    """Generic apply for both MOVE+RE-ID and RE-ID-only.
    Returns (old_stem, new_stem) for wikilink table, or None if skipped/failed.
    """
    src = OBSIDIAN_ROOT / spec.src_relpath
    target_dir = archive_target_dir if spec.archive else live_target_dir

    if not src.exists():
        # Idempotent — already moved? Look for a file in target with new ID
        candidates = list(target_dir.glob(f"{spec.new_id} *.md")) + list(target_dir.glob(f"{spec.new_id}.md"))
        if candidates:
            new_stem = candidates[0].stem
            old_stem = Path(spec.src_relpath).stem
            write_log.append(f"  already done → {spec.old_id}→{spec.new_id} (idempotent, target {candidates[0].name})")
            if is_move:
                stats.k2_moves_skipped_idempotent += 1
            else:
                stats.k2_reids_skipped_idempotent += 1
            return old_stem, new_stem
        else:
            stats.fail_reasons.append(
                f"FAIL: source missing AND no target found for {spec.old_id}→{spec.new_id} (path={spec.src_relpath})"
            )
            return None

    text = _read(src)
    if text is None:
        stats.fail_reasons.append(f"FAIL: cannot read {spec.src_relpath}")
        return None

    fm, body = parse_frontmatter(text)
    if not fm:
        stats.fail_reasons.append(f"FAIL: no frontmatter in {spec.src_relpath}")
        return None

    # Update frontmatter
    new_fm = dict(fm)
    new_fm["id"] = spec.new_id
    if is_move:
        new_fm["slug"] = new_slug
        new_fm["project"] = new_project
    new_fm = ensure_aliases(new_fm, spec.new_id)
    # Drop old ID alias (avoid stale references)
    if isinstance(new_fm.get("aliases"), list):
        new_fm["aliases"] = [a for a in new_fm["aliases"] if a != spec.old_id]
        if spec.new_id not in new_fm["aliases"]:
            new_fm["aliases"].append(spec.new_id)

    # Update H1, subtasks
    new_body = update_h1(body, spec.old_id, spec.new_id)
    new_body = renumber_subtasks(new_body, spec.old_id, spec.new_id)

    # Append log
    log_line = log_line_template.format(old=spec.old_id, new=spec.new_id)
    new_body, _ = append_log_line(new_body, log_line)

    title = str(new_fm.get("title") or "")
    new_filename = task_filename(spec.new_id, title)
    new_path = target_dir / new_filename

    new_text = render_task_text(new_fm, new_body)

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        new_path.write_text(new_text, encoding="utf-8")
        if new_path.resolve() != src.resolve():
            src.unlink()

    write_log.append(f"  {'MOVE+RE-ID' if is_move else 'RE-ID'} {spec.old_id} → {spec.new_id}: "
                     f"{spec.src_relpath} → {new_path.relative_to(OBSIDIAN_ROOT)}")

    if is_move:
        stats.k2_moves_done += 1
    else:
        stats.k2_reids_done += 1

    old_stem = Path(spec.src_relpath).stem
    new_stem = new_path.stem
    return old_stem, new_stem


def apply_k2_moves(stats: Stats, dry_run: bool, write_log: list[str]) -> dict[str, str]:
    rewrite_map: dict[str, str] = {}
    finance_live = PROJEKTY_DIR / "finance" / "tasks"
    finance_archive = ARCHIV_DIR / "finance"
    log_template = (
        f"{LOG_DATE}: Přesunuto z firemni-procesy do finance, "
        "RE-ID {old} → {new} (hygiene cleanup)."
    )
    for spec in K2_MOVES:
        result = _apply_re_id_or_move(
            spec=spec,
            new_slug="finance",
            new_project="[[Finance]]",
            archive_target_dir=finance_archive,
            live_target_dir=finance_live,
            log_line_template=log_template,
            is_move=True,
            stats=stats,
            dry_run=dry_run,
            write_log=write_log,
        )
        if result:
            old_stem, new_stem = result
            rewrite_map[old_stem] = new_stem
            rewrite_map[spec.old_id] = spec.new_id
    return rewrite_map


def apply_k2_reids(stats: Stats, dry_run: bool, write_log: list[str]) -> dict[str, str]:
    rewrite_map: dict[str, str] = {}
    fp_live = PROJEKTY_DIR / "firemni-procesy" / "tasks"
    fp_archive = ARCHIV_DIR / "firemni-procesy"
    log_template = f"{LOG_DATE}: RE-ID P{{old}} → {{new}} (prefix unify, hygiene cleanup).".replace(
        "P{old}", "{old}"  # keep template literal; we pass full old_id so just `{old}`
    )
    log_template = f"{LOG_DATE}: RE-ID {{old}} → {{new}} (prefix unify, hygiene cleanup)."
    for spec in K2_REIDS:
        result = _apply_re_id_or_move(
            spec=spec,
            new_slug="firemni-procesy",
            new_project="[[Firemní procesy]]",
            archive_target_dir=fp_archive,
            live_target_dir=fp_live,
            log_line_template=log_template,
            is_move=False,
            stats=stats,
            dry_run=dry_run,
            write_log=write_log,
        )
        if result:
            old_stem, new_stem = result
            rewrite_map[old_stem] = new_stem
            rewrite_map[spec.old_id] = spec.new_id
    return rewrite_map


def apply_orphan_delete(stats: Stats, dry_run: bool, write_log: list[str]) -> None:
    if not ORPHAN_FOLDER.exists():
        stats.orphan_skipped_idempotent = True
        write_log.append(f"  orphan already gone → {ORPHAN_FOLDER.relative_to(OBSIDIAN_ROOT)} (idempotent)")
        return
    children = list(ORPHAN_FOLDER.iterdir())
    if children:
        names = ", ".join(c.name for c in children)
        stats.fail_reasons.append(
            f"FAIL: orphan folder not empty: {ORPHAN_FOLDER.relative_to(OBSIDIAN_ROOT)} contains: {names}"
        )
        return
    if not dry_run:
        ORPHAN_FOLDER.rmdir()
    stats.orphan_deleted = True
    write_log.append(f"  ORPHAN DELETED → {ORPHAN_FOLDER.relative_to(OBSIDIAN_ROOT)}")


def apply_wikilink_rewrite(table: dict[str, str], stats: Stats, dry_run: bool, write_log: list[str]) -> None:
    if not table:
        return
    pattern = _build_wikilink_pattern(table.keys())
    for path in iter_vault_md_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new_text, n = rewrite_wikilinks_in_text(text, table, pattern)
        if n:
            stats.wikilink_files_changed += 1
            stats.wikilink_replacements += n
            rel = path.relative_to(OBSIDIAN_ROOT)
            write_log.append(f"  WIKILINK {'WOULD UPDATE' if dry_run else 'UPDATED'} {rel} ({n} link(s))")
            if not dry_run:
                path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()
    dry_run = not args.write

    print("=" * 70)
    print(f"_apply_hygiene_cleanup — {'DRY-RUN' if dry_run else 'WRITE'}")
    print(f"vault root: {OBSIDIAN_ROOT}")
    print("=" * 70)

    stats = Stats()
    write_log: list[str] = []

    # Pre-flight
    if not preflight_id_collisions(stats):
        print("Pre-flight ID collision check FAILED:")
        for r in stats.fail_reasons:
            print(f"  - {r}")
        return 2

    # 1. K3 deletes
    print("\n[Action 1] K3 cross-project duplicity (DELETE firemni-procesy/P*, log into allfred/AF*)")
    rw_k3 = apply_k3_deletes(stats, dry_run, write_log)

    # 2. K2 MOVE+RE-ID (firemni-procesy → finance)
    print("\n[Action 2] K2 2A: MOVE+RE-ID (firemni-procesy/F* → finance/F<new>)")
    rw_k2m = apply_k2_moves(stats, dry_run, write_log)

    # 3. K2 RE-ID (P → FP)
    print("\n[Action 3] K2 2B: RE-ID (firemni-procesy/P* → firemni-procesy/FP<new>)")
    rw_k2r = apply_k2_reids(stats, dry_run, write_log)

    # Wikilink rewrite (combined)
    print("\n[Wikilink rewrite] across whole OBSIDIAN/ vault")
    rewrite_table = {**rw_k3, **rw_k2m, **rw_k2r}
    apply_wikilink_rewrite(rewrite_table, stats, dry_run, write_log)

    # 4. Orphan delete
    print("\n[Action 4] DELETE orphan folder")
    apply_orphan_delete(stats, dry_run, write_log)

    print("\n" + "-" * 70)
    print("WRITE LOG:")
    for line in write_log:
        print(line)

    if stats.fail_reasons:
        print("\n" + "!" * 70)
        print("FAIL — stop. Reasons:")
        for r in stats.fail_reasons:
            print(f"  - {r}")
        return 3

    print("\n" + "=" * 70)
    print(
        f"SUMMARY (mode={'DRY-RUN' if dry_run else 'WRITE'}):\n"
        f"  K3 deletes done            = {stats.k3_deletes_done}\n"
        f"  K3 deletes skipped (no-op) = {stats.k3_deletes_skipped_idempotent}\n"
        f"  AF logs appended           = {stats.af_logs_appended}\n"
        f"  K2 moves done              = {stats.k2_moves_done}\n"
        f"  K2 moves skipped (no-op)   = {stats.k2_moves_skipped_idempotent}\n"
        f"  K2 re-ids done             = {stats.k2_reids_done}\n"
        f"  K2 re-ids skipped (no-op)  = {stats.k2_reids_skipped_idempotent}\n"
        f"  orphan deleted             = {stats.orphan_deleted}\n"
        f"  orphan skipped (no-op)     = {stats.orphan_skipped_idempotent}\n"
        f"  wikilink files changed     = {stats.wikilink_files_changed}\n"
        f"  wikilink replacements      = {stats.wikilink_replacements}\n"
    )
    if stats.edge_cases:
        print("EDGE CASES (manual review recommended):")
        for ec in stats.edge_cases:
            print(f"  - {ec}")
    if dry_run:
        print("Dry-run only — pass --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
