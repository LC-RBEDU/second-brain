"""Evening L1 digest — match, caps, deliver helpers, dry-run paths."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

HUB = Path(__file__).resolve().parents[1]
LIB = HUB / "lib"


import sys

sys.path.insert(0, str(LIB))
import evening_l1_digest as evening  # noqa: E402


def test_id_word_boundary_s12_vs_s120():
    pool = [
        evening.MatchTask("S12", "Short", "", "p1"),
        evening.MatchTask("S120", "Longer", "", "p2"),
    ]
    cands = [
        evening.Candidate("live_slack", "1", "see S120 please", "see S120 please", ""),
    ]
    r = evening.match_candidates(pool, cands)
    assert "S120" in r.matched
    assert "S12" not in r.matched


def test_title_and_body_match():
    pool = [
        evening.MatchTask(
            "RBU-S70",
            "Cashflow planned náklady",
            "znulování planned expenses v Allfredu",
            "p",
        ),
    ]
    title_hit = evening.Candidate(
        "live_slack", "a", "cashflow planned náklady fix", "…", ""
    )
    body_hit = evening.Candidate(
        "gmail", "b", "Subject: znulování planned expenses", "…", ""
    )
    miss = evening.Candidate("live_slack", "c", "random lunch plans", "…", "")
    r = evening.match_candidates(pool, [title_hit, body_hit, miss])
    assert "RBU-S70" in r.matched
    assert len(r.matched["RBU-S70"]) >= 2
    assert any(c.ref == "c" for c in r.unmatched)


def test_display_caps_truncated_in_render():
    pool = [
        evening.MatchTask(f"T{i}", f"Title token{i}xxxx", "", f"p{i}")
        for i in range(45)
    ]
    cands = [
        evening.Candidate(
            "live_slack",
            str(i),
            f"mention Title token{i}xxxx here",
            f"preview {i}",
            "",
        )
        for i in range(45)
    ]
    # also many unmatched
    cands += [
        evening.Candidate("live_slack", f"u{i}", f"zzz unique{i}qqq", f"u{i}", "")
        for i in range(45)
    ]
    match = evening.match_candidates(pool, cands)
    md = evening.render_digest_md(
        day="2026-10-12", match=match, generated_at="2026-10-12T18:00:00+02:00"
    )
    assert "truncated_tasks" in md
    assert "truncated_unmatched" in md
    assert "Evening L1 — 2026-10-12" in md
    assert "Snapshot ~18:00" in md


def test_parse_deliver_and_saturnin_soft_truncate():
    md = "---\ntype: evening-l1-digest\ndeliver: FAIL\n---\nbody\n"
    assert evening.parse_deliver(md) == "FAIL"
    assert evening.parse_deliver("# no fm\n") is None
    big = "x" * 30000
    out = evening.saturnin_payload(big, soft_chars=100)
    assert len(out) < 30000
    assert "truncated" in out


def test_writers_paused():
    assert evening.writers_paused({"VAULT_WRITERS_PAUSED": "1"}) is True
    assert evening.writers_paused({"VAULT_WRITERS_PAUSED": "0"}) is False


def test_gmail_flatten_uses_subject():
    sources = {
        "gmail": [{"id": "m1", "subject": "Invoice Allfred"}],
        "live_slack": [],
    }
    cands = evening.flatten_candidates(sources)
    assert len(cands) == 1
    assert cands[0].haystack == "Invoice Allfred"


def test_proactivity_evening_dry_run_force_no_write(tmp_path, monkeypatch):
    """B4: --force --dry-run does not write digest."""
    cron = HUB / "cron" / "proactivity_dispatch.py"
    # Ensure import path
    monkeypatch.setenv("TZ", "Europe/Prague")
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    monkeypatch.delenv("BRAIN_PUBLIC_URL", raising=False)
    monkeypatch.delenv("BRAIN_SERVICE_TOKEN", raising=False)

    # Mock open_vault to in-memory-ish stub
    class FakeVault:
        skipped = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def exists(self, rel):
            return False

        def mkdir_p(self, *a, **k):
            raise AssertionError("mkdir should not run in dry-run rebuild")

        def write_text(self, *a, **k):
            raise AssertionError("write should not run in dry-run")

        def list_dir(self, *a, **k):
            return []

        def read_text(self, *a, **k):
            raise AssertionError("unexpected read")

    import vault_factory

    monkeypatch.setattr(vault_factory, "open_vault", lambda: FakeVault())

    # Also patch evening helpers used after import inside cron
    import evening_l1_digest as eld

    monkeypatch.setattr(
        eld,
        "fetch_l1_brain",
        lambda **k: (None, "brain_env_missing"),
    )

    def boom_pool(vault):
        return []

    monkeypatch.setattr(eld, "load_match_pool", boom_pool)

    # Load cron module fresh
    sys.path.insert(0, str(HUB / "cron"))
    sys.path.insert(0, str(LIB))
    spec = importlib.util.spec_from_file_location("proactivity_dispatch", cron)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Inject mocked evening into module namespace before exec — re-exec after patch
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "fetch_l1_brain", lambda **k: (None, "brain_env_missing"))
    monkeypatch.setattr(mod, "open_vault", lambda: FakeVault())
    monkeypatch.setattr(
        mod,
        "build_match_from_brain",
        lambda vault, payload, total_error=None: evening.MatchResult(
            total_degrade=True, degrade_reason=total_error or "x"
        ),
    )
    monkeypatch.setattr(
        mod,
        "render_digest_md",
        lambda **k: "# dry\n",
    )

    mod._run_evening(dry_run=True, force=True, brain_url="")


def test_crontab_still_has_evening_line():
    text = (HUB / "deploy" / "crontab").read_text(encoding="utf-8")
    assert "proactivity_dispatch.py --trigger evening" in text
    assert "0 18 * * 1-5" in text
