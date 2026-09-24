"""Inbound e-mail: actionable ask for Lukáš → must propose ``add_task``.

Incident: Jana Kočová / DPH 8/2026 — triáž archivovala e-mail jako „Done“ bez tasku.

Použití:
- ``agenda-triage`` / manuální BATCH: **před** ``is_complex_source`` zavolej
  ``email_must_propose_task`` — True → vždy ``add_task`` ``agent: solo`` (ne DEEP).
- ``agenda-triage`` (chat BATCH/DEEP): totéž + ICE/deadline + platební kroky.
- Heuristika je SSOT v tomto modulu; inventory jen loguje.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# Inbound only — sent/ má vlastní commitment path.
_SENT_SUBDIR = "01-INBOX/email/sent/"

_FROM_FM_RE = re.compile(
    r"^from:\s*[\"']?(?P<name>[^\"'<\n]+)?[\"']?\s*<?(?P<email>[^>\s]+@[^>\s]+)>?",
    re.IGNORECASE | re.MULTILINE,
)
_MAILBOX_PERSONAL_RE = re.compile(
    r"^mailbox:\s*personal\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SB_PERSONAL_NAME_RE = re.compile(r"(?:^|/)sb-personal-", re.IGNORECASE)

# Bulk / no-reply — smí zůstat archive_only i při slabých signálech.
_BULK_FROM_RE = re.compile(
    r"(?:noreply|no-reply|donotreply|do-not-reply|newsletter|newsletter@|"
    r"notifications?@|mailer-daemon|bounce@|updates@)",
    re.IGNORECASE,
)

# Silné: platba / daň / splatnost — task i bez karty v lide/ (incident DPH 8/2026).
_STRONG_ACTION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"da[ňn]ov[áa]\s+povinnost", re.IGNORECASE),
    re.compile(r"\bDPH\b.{0,120}(?:splat|povinnost|K[čc]|úhrad)", re.IGNORECASE | re.DOTALL),
    re.compile(r"datum\s+splatnosti\s*:", re.IGNORECASE),
    re.compile(r"splatnost\s*:\s*\d", re.IGNORECASE),
    re.compile(
        r"variabiln[ií]\s+symbol.{0,80}(?:splat|K[čc]|\d{4,})",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"údaje\s+k\s+platb|platebn[ií]\s+údaj",
        re.IGNORECASE,
    ),
    re.compile(
        r"\d[\d\s]{2,}\s*(?:K[čc]|CZK|EUR|€).{0,120}(?:splat|úhrad|platb|povinnost)",
        re.IGNORECASE | re.DOTALL,
    ),
)

# Slabší: žádost o akci — task když známý kontakt NEBO personal mailbox.
_SOFT_ACTION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bDPH\b"),
    re.compile(r"variabiln[ií]\s+symbol", re.IGNORECASE),
    re.compile(r"\bVS\s*[:：]\s*\d+", re.IGNORECASE),
    re.compile(r"zapla[ťt]|uhradit|uhrad[ií]", re.IGNORECASE),
    re.compile(
        r"pros[ií]m(?:\s+T[eě]|\s+Vás)?\s+(?:o\s+)?(?:zaplacen|úhrad|potvrzen|podpis|odesl)",
        re.IGNORECASE,
    ),
    re.compile(
        r"potřebuj[ui]\s+(?:od\s+Tebe|po\s+Tob[eě]|od\s+Vás|a[ťt]\s+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:mus[ií][šs]|m[eě]l\s+bys|m[eě]li\s+byste)\s+\w+",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:do\s+kdy|term[ií]n|deadline).{0,40}(?:\d{1,2}\.\s*\d{1,2}|zítra|dnes)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:podepi[šs]|schval|po[šs]li|vra[ťt]|dopl[ňn]|objednej)\s",
        re.IGNORECASE,
    ),
)

_DEADLINE_RE = re.compile(
    r"(?:datum\s+splatnosti|splatnost)\s*:\s*"
    r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.?\s*(\d{2,4})?",
    re.IGNORECASE,
)

_AMOUNT_RE = re.compile(
    r"(\d[\d\s]{1,})\s*(?:K[čc]|CZK)\b",
    re.IGNORECASE,
)
_ACCOUNT_RE = re.compile(
    r"(?:[Čč]íslo\s+ú[čc]tu|ú[čc]et)\s*:\s*([0-9\-]+/[0-9]+)",
    re.IGNORECASE,
)
_VS_RE = re.compile(
    r"(?:[Vv]ariabiln[ií]\s+symbol|VS)\s*[:：]?\s*(\d{4,})",
    re.IGNORECASE,
)


@dataclass
class EmailActionableResult:
    must_propose_task: bool
    reasons: list[str] = field(default_factory=list)
    from_email: str = ""
    from_name: str = ""
    deadline_hint: str | None = None  # YYYY-MM-DD if parsed
    is_personal_mailbox: bool = False
    is_bulk: bool = False
    # Platební údaje (pokud v těle) — pro solo krok „připravit příkaz“.
    amount_czk: str | None = None
    account: str | None = None
    vs: str | None = None
    is_payment_obligation: bool = False


def _strip_frontmatter(body: str) -> tuple[str, str]:
    if not body.startswith("---"):
        return "", body
    end = body.find("\n---", 3)
    if end < 0:
        return "", body
    return body[3:end], body[end + 4 :]


def _parse_from(fm: str, body: str) -> tuple[str, str]:
    for blob in (fm, body[:2000]):
        m = _FROM_FM_RE.search(blob)
        if m:
            return (m.group("name") or "").strip(), (m.group("email") or "").strip().lower()
    return "", ""


def _parse_deadline_hint(text: str) -> str | None:
    m = _DEADLINE_RE.search(text)
    if not m:
        return None
    d, mo, y = m.group(1), m.group(2), m.group(3)
    if y:
        year = int(y)
        if year < 100:
            year += 2000
    else:
        from datetime import date

        year = date.today().year
    return f"{year:04d}-{int(mo):02d}-{int(d):02d}"


def _parse_payment_fields(text: str) -> tuple[str | None, str | None, str | None]:
    amt = _AMOUNT_RE.search(text)
    acc = _ACCOUNT_RE.search(text)
    vs = _VS_RE.search(text)
    amount = None
    if amt:
        amount = re.sub(r"\s+", "", amt.group(1))
    return (
        amount,
        acc.group(1) if acc else None,
        vs.group(1) if vs else None,
    )


def _is_inbound_email(rel: str) -> bool:
    norm = rel.replace("\\", "/")
    if _SENT_SUBDIR in norm or norm.startswith("email/sent/"):
        return False
    return (
        "/email/" in f"/{norm}"
        or norm.startswith("01-INBOX/email/")
        or norm.startswith("email/")
    )


def _known_sender_emails(lide_dir: Path | None) -> set[str]:
    """E-maily z ``05-RESOURCES/lide/*.md`` frontmatter ``email:``."""
    if lide_dir is None or not lide_dir.is_dir():
        return set()
    out: set[str] = set()
    email_re = re.compile(r"^email:\s*[\"']?([^\"'\s]+)[\"']?\s*$", re.I | re.M)
    for path in lide_dir.glob("*.md"):
        if path.name.startswith("_"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:4000]
        except OSError:
            continue
        m = email_re.search(text)
        if m:
            addr = m.group(1).strip().lower()
            if "@" in addr and addr not in ("", '""', "—", "-"):
                out.add(addr)
    return out


def evaluate_email_actionable(
    rel: str,
    body: str,
    *,
    lide_dir: Path | None = None,
    known_emails: set[str] | None = None,
) -> EmailActionableResult:
    """Vrátí, zda inbound e-mail musí jít do návrhu tasku (ne jen archiv)."""
    result = EmailActionableResult(must_propose_task=False)
    if not _is_inbound_email(rel):
        return result

    fm, rest = _strip_frontmatter(body)
    name, email = _parse_from(fm, body)
    result.from_name = name
    result.from_email = email
    result.is_personal_mailbox = bool(
        _MAILBOX_PERSONAL_RE.search(fm) or _SB_PERSONAL_NAME_RE.search(rel)
    )
    result.is_bulk = bool(email and _BULK_FROM_RE.search(email))

    if result.is_bulk:
        result.reasons.append("bulk/noreply From — archive_only přípustný")
        return result

    known = known_emails if known_emails is not None else _known_sender_emails(lide_dir)
    known_hit = bool(email and email in known)
    if known_hit:
        result.reasons.append(f"známý kontakt v lide/ ({email})")

    text = f"{fm}\n{rest}"
    strong = sum(1 for rx in _STRONG_ACTION_RES if rx.search(text))
    soft = sum(1 for rx in _SOFT_ACTION_RES if rx.search(text))
    if strong:
        result.reasons.append(f"silný akční signál ({strong}×)")
    if soft:
        result.reasons.append(f"měkký akční signál ({soft}×)")

    result.deadline_hint = _parse_deadline_hint(text)
    if result.deadline_hint:
        result.reasons.append(f"deadline_hint={result.deadline_hint}")
    if result.is_personal_mailbox:
        result.reasons.append("mailbox: personal")

    amount, account, vs = _parse_payment_fields(text)
    result.amount_czk = amount
    result.account = account
    result.vs = vs
    result.is_payment_obligation = bool(
        strong
        or (
            amount
            and (result.deadline_hint or account or vs)
            and re.search(r"povinnost|úhrad|splat|platb|DPH|da[ňn]", text, re.I)
        )
    )

    # Gate (ne-bulk inbound):
    # - silný signál (daň/splatnost/VS+platba) → vždy add_task
    # - měkký signál + (známý kontakt | personal mailbox) → add_task
    if strong or (soft and (known_hit or result.is_personal_mailbox)):
        result.must_propose_task = True
    elif soft and not known:
        # lide/ nedostupné — raději task než ztráta splatnosti
        result.must_propose_task = True
        result.reasons.append("lide/ nedostupné — fallback task")

    return result


def email_must_propose_task(
    rel: str,
    body: str,
    *,
    lide_dir: Path | None = None,
) -> bool:
    return evaluate_email_actionable(rel, body, lide_dir=lide_dir).must_propose_task


def payment_solo_steps(task_id: str, act: EmailActionableResult) -> list[str]:
    """Operativní kroky pro ``agent: solo`` platební povinnost."""
    parts: list[str] = []
    if act.amount_czk:
        parts.append(f"{act.amount_czk} Kč")
    if act.account:
        parts.append(f"účet {act.account}")
    if act.vs:
        parts.append(f"VS {act.vs}")
    if act.deadline_hint:
        parts.append(f"splatnost {act.deadline_hint}")
    detail = ", ".join(parts) if parts else "údaje z e-mailu"
    return [
        f"**{task_id}-1** Připravit platební příkaz ({detail}) a dát Lukášovi ke schválení",
        f"**{task_id}-2** Po schválení potvrdit úhradu / založit do logu",
    ]


def enforce_actionable_on_proposal(
    pr: dict,
    rel: str,
    body: str,
    *,
    build_add_task: Callable[..., dict] | None = None,
) -> dict:
    """Hard gate: archive/deep → add_task když heuristika říká True.

    ``build_add_task`` volitelný callback ``(rel, body, act) -> dict`` pro plný
    v2 proposal; jinak jen přepíše proposalType / agent / deadline / notes.
    """
    act = evaluate_email_actionable(rel, body)
    if not act.must_propose_task:
        return pr
    out = dict(pr)
    ptype = str(out.get("proposalType") or out.get("action") or "")
    needs_full_build = ptype in ("archive_only", "deep_analysis", "") or (
        ptype == "add_task"
        and act.is_payment_obligation
        and "Připravit platební příkaz" not in str(out.get("body") or "")
    )
    if needs_full_build and build_add_task is not None:
        built = build_add_task(rel, body, act)
        built["id"] = out.get("id") or built.get("id")
        return built
    if ptype in ("archive_only", "deep_analysis", ""):
        out["proposalType"] = "add_task"
        out["action"] = "add_task"
        out.pop("requires_deep_analysis", None)
        out.pop("deep_reasons", None)
    out["email_must_propose_task"] = True
    out["email_actionable_reasons"] = act.reasons
    if act.deadline_hint:
        out["deadline"] = act.deadline_hint
        fm = out.get("frontmatter")
        if isinstance(fm, dict):
            fm = dict(fm)
            fm["deadline"] = act.deadline_hint
            fm["agent"] = "solo"
            out["frontmatter"] = fm
    out.setdefault("ice", [9, 9, 2])
    out["agent"] = "solo"
    notes = str(out.get("notes") or "")
    tag = "inbound actionable — " + "; ".join(act.reasons)
    if tag not in notes:
        out["notes"] = f"{notes}; {tag}".strip("; ")
    return out