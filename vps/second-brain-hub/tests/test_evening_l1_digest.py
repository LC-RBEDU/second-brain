"""Evening L1 digest — match, caps, deliver helpers, dry-run paths."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HUB = Path(__file__).resolve().parents[1]
LIB = HUB / "lib"

sys.path.insert(0, str(LIB))
import evening_l1_digest as evening  # noqa: E402
from drive_io import DriveConflictError, FileMeta  # noqa: E402


def _load_cron(monkeypatch):
    cron = HUB / "cron" / "proactivity_dispatch.py"
    sys.path.insert(0, str(HUB / "cron"))
    sys.path.insert(0, str(LIB))
    spec = importlib.util.spec_from_file_location("proactivity_dispatch", cron)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MemVault:
    """Minimal vault stub: exists/read/write + optional CAS conflict."""

    def __init__(self, files: dict[str, str] | None = None, *, conflict_on_write: bool = False):
        self.files = dict(files or {})
        self.conflict_on_write = conflict_on_write
        self.writes: list[str] = []
        self.skipped = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def exists(self, rel):
        return rel in self.files

    def mkdir_p(self, *a, **k):
        return None

    def list_dir(self, *a, **k):
        return []

    def read_text(self, rel):
        from datetime import datetime, timezone

        text = self.files[rel]
        return text, FileMeta(
            id="id1",
            name=rel.rsplit("/", 1)[-1],
            mime_type="text/markdown",
            modified_time=datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc),
            size=len(text.encode("utf-8")),
            parent_id=None,
            rel_path=rel,
            oid="abc123",
        )

    def write_text(self, rel, text, **kwargs):
        if self.conflict_on_write:
            raise DriveConflictError("cas conflict test")
        if kwargs.get("expect_mtime") or kwargs.get("expect_md5"):
            # CAS path — still write unless conflict flag
            pass
        self.files[rel] = text
        self.writes.append(rel)


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


def test_body_cap_3072_no_hit_beyond():
    """B8: token only after 3072 B must not match."""
    prefix = "x" * 3072
    body = prefix + " unikátníznulováníabcdef "
    pool = [evening.MatchTask("T1", "Other", body, "p")]
    # haystack has the token that sits past the cap in task body
    cand = evening.Candidate(
        "live_slack", "1", "unikátníznulováníabcdef mentioned", "…", ""
    )
    # body_cap truncates — token not in first 3072 unicode-decoded bytes
    capped = body.encode("utf-8")[:3072].decode("utf-8", errors="ignore")
    pool[0] = evening.MatchTask("T1", "Other", capped, "p")
    r = evening.match_candidates(pool, [cand])
    assert "T1" not in r.matched
    assert r.unmatched


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
    # >8 hits for one task
    mega = evening.MatchTask("MEGA", "Megatokenzzzz", "", "pm")
    pool.append(mega)
    for j in range(10):
        cands.append(
            evening.Candidate(
                "live_slack",
                f"m{j}",
                f"Megatokenzzzz hit{j}",
                f"hit{j}",
                "",
            )
        )
    match = evening.match_candidates(pool, cands)
    md = evening.render_digest_md(
        day="2026-10-12", match=match, generated_at="2026-10-12T18:00:00+02:00"
    )
    assert "truncated_tasks" in md
    assert "truncated_unmatched" in md
    assert "truncated_hits" in md
    assert "Evening L1 — 2026-10-12" in md
    assert "Snapshot ~18:00" in md
    assert "CTA:" in md


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


def test_enrich_path_uses_vault_head_not_path_only():
    """B24: dump haystack includes file body head."""
    vault = MemVault(
        {
            "01-INBOX/sembly/foo.md": "---\ntitle: x\n---\nuniquebodytokenzzzz content\n",
        }
    )
    cands = [
        evening.Candidate(
            "sembly",
            "01-INBOX/sembly/foo.md",
            "",
            "foo.md",
            "01-INBOX/sembly/foo.md",
        )
    ]
    out = evening.enrich_path_sources(vault, cands)
    assert "uniquebodytokenzzzz" in out[0].haystack


def test_load_match_pool_excludes_epic(monkeypatch):
    """B14: epics excluded from pool."""

    class T:
        def __init__(self, tid, typ, terminal=False):
            self._tid = tid
            self.frontmatter = {"title": tid, "type": typ}
            self.body = "body"
            self.rel_path = f"p/{tid}.md"
            self.is_terminal = terminal

        @property
        def task_id(self):
            return self._tid

    monkeypatch.setattr(
        evening,
        "iter_active_tasks",
        lambda vault: [
            T("RBU-E1", "epic"),
            T("RBU-S2", "story"),
            T("RBU-S3", "story", terminal=True),
        ],
    )
    pool = evening.load_match_pool(MemVault())
    ids = {t.task_id for t in pool}
    assert ids == {"RBU-S2"}


def test_patch_deliver_quotes_detail_and_cas_conflict():
    vault = MemVault(
        {"00-System/digests/2026-10-12-evening-l1.md": "---\ntype: evening-l1-digest\n---\nbody\n"}
    )
    meta = vault.read_text("00-System/digests/2026-10-12-evening-l1.md")[1]
    ok = evening.patch_deliver_frontmatter(
        vault,
        "00-System/digests/2026-10-12-evening-l1.md",
        status="OK",
        detail="error: timeout: boom",
        meta=meta,
    )
    assert ok is True
    text = vault.files["00-System/digests/2026-10-12-evening-l1.md"]
    assert 'deliver_detail: "error: timeout: boom"' in text or "deliver_detail: \"error: timeout: boom\"" in text
    assert evening.parse_deliver(text) == "OK"

    vault.conflict_on_write = True
    meta2 = vault.read_text("00-System/digests/2026-10-12-evening-l1.md")[1]
    ok2 = evening.patch_deliver_frontmatter(
        vault,
        "00-System/digests/2026-10-12-evening-l1.md",
        status="FAIL",
        detail="x",
        meta=meta2,
    )
    assert ok2 is False
    assert evening.parse_deliver(vault.files["00-System/digests/2026-10-12-evening-l1.md"]) == "OK"


def test_proactivity_evening_dry_run_force_no_write(tmp_path, monkeypatch):
    """B4: --force --dry-run does not write digest; Brain may be called (R9)."""
    monkeypatch.setenv("TZ", "Europe/Prague")
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")

    vault = MemVault()
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)
    called = {"brain": 0}

    def brain(**k):
        called["brain"] += 1
        return None, "brain_env_missing"

    monkeypatch.setattr(mod, "fetch_l1_brain", brain)
    monkeypatch.setattr(
        mod,
        "build_match_from_brain",
        lambda vault, payload, total_error=None: evening.MatchResult(
            total_degrade=True, degrade_reason=total_error or "x"
        ),
    )
    monkeypatch.setattr(mod, "render_digest_md", lambda **k: "# dry\n")
    mod._run_evening(dry_run=True, force=True, brain_url="")
    assert vault.writes == []
    assert called["brain"] == 1


def test_evening_force_rebuild_despite_deliver_ok(monkeypatch):
    """B3/T4: exists deliver OK + --force → Brain + rebuild path (not skip)."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    from datetime import datetime
    from zoneinfo import ZoneInfo

    rel = evening.digest_rel_path("2026-10-12")
    vault = MemVault(
        {rel: "---\ntype: evening-l1-digest\ndeliver: OK\n---\nold\n"}
    )
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 10, 12, 18, 0, tzinfo=ZoneInfo("Europe/Prague"))

    monkeypatch.setattr(mod, "datetime", FakeDT)
    called = {"brain": 0, "grok": 0}

    def brain(**k):
        called["brain"] += 1
        return {"sources": {"live_slack": [], "gmail": []}}, None

    monkeypatch.setattr(mod, "fetch_l1_brain", brain)
    monkeypatch.setattr(
        mod,
        "build_match_from_brain",
        lambda vault, payload, total_error=None: evening.MatchResult(candidate_count=0),
    )
    monkeypatch.setattr(
        mod,
        "render_digest_md",
        lambda **k: "---\ntype: evening-l1-digest\n---\n# rebuilt\n",
    )
    monkeypatch.setattr(
        mod, "deliver_to_saturnin", lambda *a, **k: (called.__setitem__("grok", 1) or True, "ok")
    )
    mod._run_evening(dry_run=False, force=True, brain_url="")
    assert called["brain"] == 1
    assert called["grok"] == 1
    assert rel in vault.writes
    assert "# rebuilt" in vault.files[rel]


def test_evening_brain_fail_writes_degrade_md(monkeypatch):
    """B20/T11: Brain env missing + non-dry → write total-degrade MD (not silent skip)."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    from datetime import datetime
    from zoneinfo import ZoneInfo

    rel = evening.digest_rel_path("2026-10-12")
    vault = MemVault()
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 10, 12, 18, 0, tzinfo=ZoneInfo("Europe/Prague"))

    monkeypatch.setattr(mod, "datetime", FakeDT)
    monkeypatch.setattr(mod, "fetch_l1_brain", lambda **k: (None, "brain_env_missing"))
    monkeypatch.setattr(evening, "load_match_pool", lambda vault: [])
    monkeypatch.setattr(
        mod,
        "build_match_from_brain",
        lambda vault, payload, total_error=None: evening.build_match_from_brain(
            vault, payload, total_error=total_error
        ),
    )
    monkeypatch.setattr(mod, "deliver_to_saturnin", lambda *a, **k: (True, "ok"))
    mod._run_evening(dry_run=False, force=False, brain_url="")
    assert rel in vault.writes
    md = vault.files[rel]
    assert "Total degrade" in md or "total_degrade" in md
    assert "brain_env_missing" in md


def test_evening_skip_when_deliver_ok(monkeypatch):
    """B2: exists + deliver OK + !force → 0 write, 0 Grok."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    rel = evening.digest_rel_path("2026-10-12")
    # freeze day
    from datetime import datetime
    from zoneinfo import ZoneInfo

    vault = MemVault(
        {rel: "---\ntype: evening-l1-digest\ndeliver: OK\n---\nbody\n"}
    )
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)
    monkeypatch.setattr(mod, "TZ", ZoneInfo("Europe/Prague"))

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 10, 12, 18, 0, tzinfo=ZoneInfo("Europe/Prague"))

    monkeypatch.setattr(mod, "datetime", FakeDT)

    called = {"brain": 0, "grok": 0}

    def boom_brain(**k):
        called["brain"] += 1
        return None, "no"

    def boom_grok(*a, **k):
        called["grok"] += 1
        return True, "ok"

    monkeypatch.setattr(mod, "fetch_l1_brain", boom_brain)
    monkeypatch.setattr(mod, "deliver_to_saturnin", boom_grok)
    mod._run_evening(dry_run=False, force=False, brain_url="")
    assert called["brain"] == 0
    assert called["grok"] == 0
    assert vault.writes == []


def test_evening_saturnin_only_dry_run_no_brain(monkeypatch):
    """B4b: exists FAIL + dry-run → 0 Brain, 0 Grok, 0 write."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    from datetime import datetime
    from zoneinfo import ZoneInfo

    rel = evening.digest_rel_path("2026-10-12")
    vault = MemVault(
        {rel: "---\ntype: evening-l1-digest\ndeliver: FAIL\n---\nold\n"}
    )
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 10, 12, 18, 0, tzinfo=ZoneInfo("Europe/Prague"))

    monkeypatch.setattr(mod, "datetime", FakeDT)
    called = {"brain": 0, "grok": 0}
    monkeypatch.setattr(
        mod, "fetch_l1_brain", lambda **k: (called.__setitem__("brain", 1), None)[1]
    )
    monkeypatch.setattr(
        mod, "deliver_to_saturnin", lambda *a, **k: (called.__setitem__("grok", 1), (True, "x"))[1]
    )
    mod._run_evening(dry_run=True, force=False, brain_url="")
    assert called["brain"] == 0
    assert called["grok"] == 0
    assert vault.writes == []


def test_evening_saturnin_only_retry_patches_fail(monkeypatch):
    """B2b/B10: Saturnin-only on FAIL; Grok fail → deliver FAIL, exit 0."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    from datetime import datetime
    from zoneinfo import ZoneInfo

    rel = evening.digest_rel_path("2026-10-12")
    vault = MemVault(
        {rel: "---\ntype: evening-l1-digest\ndeliver: FAIL\n---\nold body\n"}
    )
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 10, 12, 18, 0, tzinfo=ZoneInfo("Europe/Prague"))

    monkeypatch.setattr(mod, "datetime", FakeDT)
    monkeypatch.setattr(mod, "fetch_l1_brain", lambda **k: (_ for _ in ()).throw(AssertionError("no brain")))
    monkeypatch.setattr(mod, "deliver_to_saturnin", lambda *a, **k: (False, "grok_down"))
    mod._run_evening(dry_run=False, force=False, brain_url="")
    assert evening.parse_deliver(vault.files[rel]) == "FAIL"
    assert rel in vault.writes


def test_evening_paused_no_work(monkeypatch):
    """B21: PAUSED → 0 write, 0 Grok."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "1")
    mod = _load_cron(monkeypatch)
    called = {"vault": 0}

    def boom_vault():
        called["vault"] += 1
        return MemVault()

    monkeypatch.setattr(mod, "open_vault", boom_vault)
    mod._run_evening(dry_run=False, force=True, brain_url="")
    assert called["vault"] == 0


def test_evening_cas_conflict_on_deliver_patch_exit_0(monkeypatch):
    """B22: CAS on deliver patch → no false OK flip if conflict mid-patch."""
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "0")
    from datetime import datetime
    from zoneinfo import ZoneInfo

    rel = evening.digest_rel_path("2026-10-12")
    vault = MemVault(
        {rel: "---\ntype: evening-l1-digest\ndeliver: FAIL\n---\nold\n"},
        conflict_on_write=True,
    )
    mod = _load_cron(monkeypatch)
    monkeypatch.setattr(mod, "open_vault", lambda: vault)

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return datetime(2026, 10, 12, 18, 0, tzinfo=ZoneInfo("Europe/Prague"))

    monkeypatch.setattr(mod, "datetime", FakeDT)
    monkeypatch.setattr(mod, "deliver_to_saturnin", lambda *a, **k: (True, "ok"))
    # Should not raise
    mod._run_evening(dry_run=False, force=False, brain_url="")
    assert evening.parse_deliver(vault.files[rel]) == "FAIL"


def test_crontab_still_has_evening_line():
    text = (HUB / "deploy" / "crontab").read_text(encoding="utf-8")
    assert "proactivity_dispatch.py --trigger evening" in text
    assert "0 18 * * 1-5" in text


def test_sembly_cut_drops_transcript_token():
    """B1: token only in ## Plný transkript → outside haystack."""
    text = (
        "## Shrnutí\nsummary only\n\n"
        "## Akční body\naction only\n\n"
        "## Plný transkript\n"
        "unikátnítranskripttokenzzzz only here\n"
    )
    body = evening.sembly_match_body(text)
    assert "unikátnítranskripttokenzzzz" not in body
    assert "summary only" in body
    assert "action only" in body


def test_sembly_keeps_summary_action_tokens():
    """B2: tokens in Shrnutí/Akční body stay in haystack."""
    text = (
        "## Shrnutí\nshrnutitokenzzzz here\n\n"
        "## Akční body\nakcitokenzzzz here\n\n"
        "## Plný transkript\nnoise\n"
    )
    body = evening.sembly_match_body(text)
    assert "shrnutitokenzzzz" in body
    assert "akcitokenzzzz" in body


def test_sembly_cut_aliases_and_non_exact():
    """B3 / B3n: Plný přepis / Full transcript cut; ### / # / substring do not primary-cut."""
    assert "secretzzz" not in evening.sembly_match_body(
        "## Shrnutí\nok\n## Plný přepis\nsecretzzz\n"
    )
    assert "secretzzz" not in evening.sembly_match_body(
        "## Summary\nok\n## Full transcript\nsecretzzz\n"
    )
    # ### is not ## → stays in body until keep-cut before ## Other
    body_h3 = evening.sembly_match_body(
        "## Shrnutí\nok\n### Plný transkript\nsecretzzz\n## Other\n"
    )
    assert "secretzzz" in body_h3
    # single # is not ##
    body_h1 = evening.sembly_match_body(
        "## Shrnutí\nok\n# Plný transkript\nsecretzzz\n## Other\n"
    )
    assert "secretzzz" in body_h1
    # substring heading → keep-cut before it
    body_sub = evening.sembly_match_body(
        "## Shrnutí\nok\n## Foo Plný transkript\nsecretzzz\n"
    )
    assert "secretzzz" not in body_sub


def test_sembly_keep_cut_cap_8192():
    """B4: after keep, cut before non-keep ##; cap 8192."""
    pad = "y" * 100
    text = f"## Shrnutí\n{pad}\n## Other section\naftercutzzzz\n"
    body = evening.sembly_match_body(text)
    assert "aftercutzzzz" not in body
    assert pad in body
    assert len(body.encode("utf-8")) <= 8192


def test_sembly_keep_only_uses_8192_not_4096():
    """A10.2: keep sections, no further ## → cap 8192 not 4096."""
    pad = "k" * 5000
    text = f"## Shrnutí\n{pad}\nkeeponlytokenzzzz\n"
    body = evening.sembly_match_body(text)
    assert "keeponlytokenzzzz" in body
    assert len(body.encode("utf-8")) <= 8192
    assert len(body.encode("utf-8")) > 4096


def test_sembly_fallback_4kib_without_markers():
    """B5: no markers → 4096 B cap."""
    prefix = "a" * 4096
    text = prefix + "unikátníza4096zzzz"
    body = evening.sembly_match_body(text)
    assert "unikátníza4096zzzz" not in body
    assert len(body.encode("utf-8")) <= 4096


def test_sembly_post_cut_cap_8192():
    """B5b: cut before transcript, then 8192; token before cap matches, after does not."""
    early = "earlytokenzzzz "
    pad = "x" * (8200 - len(early))
    text = (
        f"## Shrnutí\n{early}{pad}\n"
        "## Akční body\nakcizatokenzzzz\n"
        "## Plný transkript\nignored\n"
    )
    body = evening.sembly_match_body(text)
    assert "ignored" not in body
    assert "earlytokenzzzz" in body
    assert "akcizatokenzzzz" not in body
    assert len(body.encode("utf-8")) <= 8192


def test_daily_still_includes_transcript_heading_bytes():
    """B6 / R8: daily keeps stem+8KiB including transcript-like heading."""
    vault = MemVault(
        {
            "01-INBOX/daily/x.md": (
                "## Shrnutí\nok\n## Plný transkript\ndailytranskripttokenzzzz\n"
            ),
        }
    )
    cands = [
        evening.Candidate(
            "daily", "01-INBOX/daily/x.md", "", "x.md", "01-INBOX/daily/x.md"
        )
    ]
    out = evening.enrich_path_sources(vault, cands)
    assert "dailytranskripttokenzzzz" in out[0].haystack


def test_sembly_enrich_excludes_transcript_from_match():
    """Integration: body match does not hit transcript-only token."""
    vault = MemVault(
        {
            "01-INBOX/sembly/m.md": (
                "## Shrnutí\nnothing special\n"
                "## Plný transkript\n"
                "cashflow planned náklady znulování\n"
            ),
        }
    )
    cands = evening.flatten_candidates(
        {"sembly": ["01-INBOX/sembly/m.md"], "live_slack": [], "gmail": []}
    )
    cands = evening.enrich_path_sources(vault, cands)
    pool = [
        evening.MatchTask(
            "RBU-S70",
            "Cashflow planned náklady",
            "znulování planned expenses",
            "p",
        )
    ]
    r = evening.match_candidates(pool, cands)
    assert "RBU-S70" not in r.matched


def test_fetch_l1_brain_retries_503_then_ok(monkeypatch):
    """B9: 503 → 200 with one sleep(1.0)."""
    sleeps: list[float] = []
    calls = {"n": 0}

    class Resp:
        def read(self):
            return b'{"sources": {}}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", hdrs=None, fp=None)
        return Resp()

    import urllib.error
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    data, err = evening.fetch_l1_brain(
        brain_url="https://brain.example",
        token="t",
        sleep=lambda s: sleeps.append(s),
    )
    assert err is None
    assert data == {"sources": {}}
    assert sleeps == [1.0]
    assert calls["n"] == 2


def test_fetch_l1_brain_two_503_then_ok(monkeypatch):
    """B10 / T9b: 503→503→200; sleeps 1.0 then 2.0."""
    import urllib.error
    import urllib.request

    sleeps: list[float] = []
    calls = {"n": 0}

    class Resp:
        def read(self):
            return b'{"sources": {}}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", hdrs=None, fp=None)
        return Resp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    data, err = evening.fetch_l1_brain(
        brain_url="https://brain.example",
        token="t",
        sleep=lambda s: sleeps.append(s),
    )
    assert err is None
    assert data == {"sources": {}}
    assert sleeps == [1.0, 2.0]
    assert calls["n"] == 3


def test_fetch_l1_brain_503_exhausted(monkeypatch):
    """B11: 503×3 → brain_http_503; two sleeps."""
    import urllib.error
    import urllib.request

    sleeps: list[float] = []

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", hdrs=None, fp=None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    data, err = evening.fetch_l1_brain(
        brain_url="https://brain.example",
        token="t",
        sleep=lambda s: sleeps.append(s),
    )
    assert data is None
    assert err == "brain_http_503"
    assert sleeps == [1.0, 2.0]


def test_fetch_l1_brain_503_then_urlerror(monkeypatch):
    """B13 / T10b: last attempt maps URLError → brain_error:…"""
    import urllib.error
    import urllib.request

    sleeps: list[float] = []
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", hdrs=None, fp=None)
        raise urllib.error.URLError("down")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    data, err = evening.fetch_l1_brain(
        brain_url="https://brain.example",
        token="t",
        sleep=lambda s: sleeps.append(s),
    )
    assert data is None
    assert err == "brain_error:URLError"
    assert sleeps == [1.0]


def test_fetch_l1_brain_502_no_retry(monkeypatch):
    """B12: 502 → immediate fail, no sleep."""
    import urllib.error
    import urllib.request

    sleeps: list[float] = []

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 502, "Bad Gateway", hdrs=None, fp=None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    data, err = evening.fetch_l1_brain(
        brain_url="https://brain.example",
        token="t",
        sleep=lambda s: sleeps.append(s),
    )
    assert data is None
    assert err == "brain_http_502"
    assert sleeps == []
