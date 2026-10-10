"""T3 / B9: vault_import_inventory classification."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "vault_import_inventory.py"


def test_classify_md_blob_and_large_drive_only(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    (root / "a.md").write_text("x" * 100, encoding="utf-8")
    big = root / "big.bin"
    big.write_bytes(b"0" * (41 * 1024 * 1024))
    mid = root / "mid.bin"
    mid.write_bytes(b"1" * (2 * 1024 * 1024))
    tsv = tmp_path / "out.tsv"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(root), "--tsv", str(tsv)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    text = tsv.read_text(encoding="utf-8")
    assert "a.md\t" in text and "\tblob" in text
    assert "mid.bin" in text and "lfs" in text
    assert "big.bin" in text and "drive-only" in text
