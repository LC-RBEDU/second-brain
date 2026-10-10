"""B43 / T3 — shared builder has no session API; LESSON_TAKEAWAY_RE present."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import agent_context_build as mod  # noqa: E402


def test_lesson_takeaway_re_present():
    assert hasattr(mod, "LESSON_TAKEAWAY_RE")
    assert mod.LESSON_TAKEAWAY_RE.search("- Příště **udělej:** něco")


def test_builder_has_no_open_vault_or_session_api():
    src = Path(mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    banned = {"open_vault", "begin_session", "end_session"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in banned:
                raise AssertionError(f"banned call {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in banned:
                raise AssertionError(f"banned call .{node.func.attr}")
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in banned:
                    raise AssertionError(f"banned import {alias.name}")
    # Docstring may mention the ban; ban is AST import/call above.


def test_bundle_api_signature():
    assert callable(mod.build_and_write_context_bundle)
