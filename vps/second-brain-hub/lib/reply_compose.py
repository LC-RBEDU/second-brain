"""Reply body for a draft. Cron only files what this returns.

The runner is injectable so tests never call cursor-agent.
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess

from assistant_ingest import InboxItem

AGENT_FLAGS = ["--trust", "--mode", "ask", "--model", "auto", "--print", "--output-format", "text"]

_PROMPT = """Napiš odpověď za Lukáše Cypru. Výstup je jen text zprávy, nic kolem.

Pravidla:
- Čeština. Ty/Tě/Ti s velkým T u kolegů. Mail končí „Díky“ a „L.“. Slack bez „L.“.
- Drž se playbooku níže. Když playbook mlčí, buď stručný a konkrétní.
- Neposílej. Nevymýšlej fakta, která ve zprávě nejsou.
- Žádný nadpis, žádné uvozovky kolem celého textu, žádný komentář.

PLAYBOOK:
{playbook}

ZPRÁVA ({kind}):
od: {sender}
předmět: {subject}
{body}
"""


def _strip_fences(text: str) -> str:
    lines = [line for line in text.strip().splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip()


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()
    proc.wait(timeout=5)


def _cursor_agent(prompt: str) -> str:
    api_key = (os.environ.get("CURSOR_API_KEY") or "").strip()
    agent = shutil.which("cursor-agent") or shutil.which("agent")
    if not api_key or not agent:
        print("reply_compose: CURSOR_API_KEY or cursor-agent missing")
        return ""
    proc = subprocess.Popen(
        [agent, *AGENT_FLAGS, prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env={**os.environ, "CURSOR_API_KEY": api_key},
    )
    try:
        out, err = proc.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        print("reply_compose: agent timed out")
        return ""
    except OSError as exc:
        print(f"reply_compose: agent failed: {exc}")
        return ""
    if proc.returncode != 0:
        print(f"reply_compose: agent exit {proc.returncode}: {(err or '')[:300]}")
        return ""
    return out or ""


def compose_reply(item: InboxItem, playbook: str, *, run=None) -> str:
    kind = "slack" if item.rel.startswith("01-INBOX/slack") else "email"
    prompt = _PROMPT.format(
        playbook=(playbook or "").strip()[:4000],
        kind=kind,
        sender=(item.fm.get("from") or item.fm.get("kind") or "").strip()[:200],
        subject=(item.fm.get("subject") or "").strip()[:200],
        body=(item.body or "").strip()[:2500],
    )
    text = _strip_fences((run or _cursor_agent)(prompt))
    if len(text) < 8:
        return ""
    return text
