"""Ingest decisions: pair sent mail, draft only when a reply is expected, never add_task."""
from __future__ import annotations

import re
from dataclasses import dataclass

GMAIL_COMPOSE_FORBIDDEN = ("drafts.send", "messages.send")

SEND_POLICY_REL = "00-System/send-policy.yaml"
PLAYBOOK_REL = "00-System/reply-playbook.md"
PENDING_REL = "00-System/Triage-Pending/assistant-inbox.md"
INGEST_STATE_REL = "00-System/assistant-ingest-state.json"

SEND_POLICY_TEXT = """mode: draft_only
# Hub must not call Gmail drafts.send or messages.send.
# Internal meeting notes on a known Slack channel are a separate Mac-session path.
"""

PLAYBOOK_TEXT = """# Reply playbook

Krátké zvyklosti pro drafty (ne skill). Když draft upravíš a chceš, aby se to opakovalo, dopiš sem jeden řádek.

- Oslovení: Ahoj, / Hoj, — kolegové tykání, velké T.
- Konec mailu: Díky + L.
- Slack draft: bez L. na konci.
- Čísla a odkazy, žádná výplň.
- Externí účastník schůzky: jen Gmail draft, nikdy odeslat.
"""

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_REPLY_RE = re.compile(
    r"\?|prosím|prosim|můžeš|muzes|můžete|could you|can you|\bplease\b",
    re.IGNORECASE,
)
_LUKAS_SPEAKER_RE = re.compile(r"^\*\*Lukáš", re.MULTILINE)
_DROP_FROM_RE = re.compile(
    r"calendar-noreply|calendar-notification@google\.com|notify@google\.com",
    re.IGNORECASE,
)

INBOX_DIRS = (
    "01-INBOX/slack",
    "01-INBOX/email",
    "01-INBOX/email/sent",
    "01-INBOX/sembly",
)


@dataclass
class InboxItem:
    rel: str
    fm: dict[str, str]
    body: str


@dataclass
class Action:
    op: str  # handle | draft_email | draft_slack | deep | skip
    item: InboxItem
    reason: str = ""


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FM_RE.match(text)
    if not match:
        return {}, text
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, text[match.end() :]


def set_status(text: str, status: str) -> str:
    fm, body = parse_frontmatter(text)
    fm["status"] = status
    lines = ["---"]
    for key, value in fm.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append(body if body.startswith("\n") else "\n" + body)
    return "\n".join(lines).replace("---\n\n\n", "---\n\n")


def drop_email(item: InboxItem) -> bool:
    blob = " ".join(
        [
            item.fm.get("from", ""),
            item.fm.get("to", ""),
            item.fm.get("subject", ""),
            item.body[:500],
        ]
    )
    return bool(_DROP_FROM_RE.search(blob))


def last_speaker_is_lukas(body: str) -> bool:
    speakers = _LUKAS_SPEAKER_RE.findall(body)
    others = re.findall(r"^\*\*[^*]+\*\*\s+\d{1,2}:\d{2}", body, re.MULTILINE)
    if not others:
        return False
    return bool(re.match(r"^\*\*Lukáš", others[-1]))


def expects_reply(item: InboxItem) -> bool:
    kind = item.fm.get("kind") or item.fm.get("source") or ""
    if kind in {"sent", "sembly"} or item.rel.startswith("01-INBOX/sembly"):
        return False
    if item.rel.startswith("01-INBOX/email/sent") or item.fm.get("source") == "sent":
        return False
    sender = (item.fm.get("from") or "").lower()
    if "lukas@redbuttonedu.cz" in sender and not item.rel.startswith("01-INBOX/slack"):
        return False
    if last_speaker_is_lukas(item.body):
        return False
    if item.fm.get("status") in {"handled_by_user", "skipped"}:
        return False
    return bool(_REPLY_RE.search(item.body))


def thread_ids(item: InboxItem) -> set[str]:
    ids = set()
    for key in ("gmail_thread_id", "threadId"):
        value = (item.fm.get(key) or "").strip()
        if value:
            ids.add(value)
    return ids


def pair_sent(sent: InboxItem, inbound: list[InboxItem]) -> InboxItem | None:
    sent_threads = thread_ids(sent)
    reply_to = (sent.fm.get("in_reply_to") or "").strip().strip("<>")
    for item in inbound:
        if item.rel.startswith("01-INBOX/email/sent"):
            continue
        if sent_threads and sent_threads & thread_ids(item):
            return item
        msg = (item.fm.get("message_id") or "").strip().strip("<>")
        if reply_to and msg and reply_to == msg:
            return item
    return None


def plan_actions(items: list[InboxItem]) -> list[Action]:
    """No add_task. Sent mail closes the inbound; drafts only when a reply is expected."""
    sent = [i for i in items if i.fm.get("source") == "sent" or "/email/sent/" in i.rel]
    inbound = [i for i in items if i not in sent]
    handled_rels: set[str] = set()
    actions: list[Action] = []

    for item in sent:
        match = pair_sent(item, inbound)
        if match is not None:
            handled_rels.add(match.rel)
            actions.append(Action("handle", match, "sent_pair"))

    for item in inbound:
        if item.rel in handled_rels:
            continue
        if item.rel.startswith("01-INBOX/sembly") or item.fm.get("source") == "sembly":
            actions.append(Action("deep", item, "sembly"))
            continue
        if item.rel.startswith("01-INBOX/email") and drop_email(item):
            actions.append(Action("skip", item, "drop_list"))
            continue
        if not expects_reply(item):
            actions.append(Action("skip", item, "no_reply_expected"))
            continue
        if item.rel.startswith("01-INBOX/slack"):
            actions.append(Action("draft_slack", item, "slack_reply"))
        elif item.rel.startswith("01-INBOX/email"):
            actions.append(Action("draft_email", item, "email_reply"))
        else:
            actions.append(Action("deep", item, "unclassified"))
    return actions


def draft_text(item: InboxItem) -> str:
    """Placeholder Lukáš can edit. Rules, not a guessed answer."""
    return "Ahoj,\n\n\nDíky\nL.\n"


def slack_pointer(item: InboxItem, text: str) -> str:
    return (
        "---\n"
        "status: draft\n"
        f"source_rel: {item.rel}\n"
        f"kind: {item.fm.get('kind') or 'slack'}\n"
        "---\n\n"
        f"Zdroj: `{item.rel}`\n\n"
        "## Návrh\n\n"
        f"{text}\n"
    )


def email_pointer(item: InboxItem, text: str, draft_id: str = "") -> str:
    return (
        "---\n"
        "status: draft\n"
        f"source_rel: {item.rel}\n"
        f"gmail_thread_id: {item.fm.get('gmail_thread_id', '')}\n"
        f"gmail_draft_id: {draft_id}\n"
        "---\n\n"
        f"Zdroj: `{item.rel}`\n\n"
        "## Návrh\n\n"
        f"{text}\n"
    )
