"""get_triage_candidates — F4 default L1 = live Slack + Gmail + daily/sembly."""
from __future__ import annotations

import os
from typing import Any

from app.gmail_client import list_l1
from app.vault_deps import brain_vault

SLACK_DUMP = "01-INBOX/slack"
EMAIL_DUMP = "01-INBOX/email"
DAILY = "01-INBOX/daily"
SEMBLY = "01-INBOX/sembly"


def _list_md(vault: Any, folder: str) -> list[str]:
    if not vault.exists(folder):
        return []
    try:
        metas = vault.list_dir(folder, pattern="*.md", recursive=True)
    except Exception:
        return []
    return [getattr(m, "rel_path", "") for m in metas if getattr(m, "rel_path", "")]


def get_triage_candidates(
    *,
    include_live_slack: bool = True,
    include_gmail: bool = True,
    env: dict | None = None,
    gmail_fetcher=None,
) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    sources: dict[str, Any] = {
        "slack_dump": [],
        "email_dump": [],
        "daily": [],
        "sembly": [],
        "gmail": [],
        "live_slack": [],
    }
    error_reason: str | None = None
    fail_path_hint: str | None = None

    with brain_vault(mode="read", env=env) as vault:
        # Residual dump list only — not the operational L1 queue after F4.
        sources["slack_dump"] = _list_md(vault, SLACK_DUMP)
        sources["email_dump"] = _list_md(vault, EMAIL_DUMP)
        sources["daily"] = _list_md(vault, DAILY)
        sources["sembly"] = _list_md(vault, SEMBLY)

    if include_gmail:
        result = list_l1(fetcher=gmail_fetcher)
        if result.error_reason:
            error_reason = result.error_reason
            fail_path_hint = "client_connector_list"
        else:
            sources["gmail"] = [
                {
                    "id": m.id,
                    "thread_id": m.thread_id,
                    "mailbox": m.mailbox,
                    "label": m.label,
                    "date": m.date,
                    "subject": m.subject,
                    "l2_eligible": m.label == "INBOX",
                }
                for m in result.messages
            ]

    if include_live_slack:
        from app.tools.slack_live import slack_live_search

        live = slack_live_search(env=env)
        sources["live_slack"] = live.get("candidates") or []
        if live.get("error_reason") and not error_reason:
            error_reason = live["error_reason"]

    out: dict[str, Any] = {
        "sources": sources,
        "default_l1": "live",
        "include_live_slack": include_live_slack,
    }
    if error_reason:
        out["error_reason"] = error_reason
        out["fail_path_hint"] = fail_path_hint or "client_connector_list"
    return out
