"""Tests for build_sources_routing.py"""
from __future__ import annotations

import os

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CATALOG = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault")) / "00-System" / "Zdroje-katalog.md"
ROUTING = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault")) / "00-System" / "sources-routing.json"
BUILD = REPO / "scripts" / "build_sources_routing.py"


def test_catalog_has_yaml_blocks():
    text = CATALOG.read_text(encoding="utf-8")
    assert "```yaml" in text
    assert "tag: rb-mcp" in text


def test_routing_json_in_sync():
    r = subprocess.run(
        [sys.executable, str(BUILD), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def test_routing_has_expected_tags():
    data = json.loads(ROUTING.read_text(encoding="utf-8"))
    assert "google-workspace" in data["tags"]
    assert "rb-mcp" in data["routes"]
    catalog_sha = hashlib.sha256(CATALOG.read_text(encoding="utf-8").encode()).hexdigest()
    assert data["catalog_sha256"] == catalog_sha
