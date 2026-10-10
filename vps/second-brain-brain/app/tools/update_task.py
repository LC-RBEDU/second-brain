"""update_task — CAS patch of frontmatter fields (B5); refuses focus / Stav auto."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from drive_io import DriveConflictError  # noqa: E402

from app.errors import BrainClientError
from app.policy import deny_focus_write, deny_stav_auto_write
from app.vault_deps import brain_vault

_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
_FORBIDDEN = frozenset({"focus"})


def update_task(
    *,
    path: str,
    patch: dict[str, Any],
    expect_oid: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not patch:
        raise BrainClientError(message="empty patch", status_code=400)
    if "focus" in patch:
        d = deny_focus_write()
        raise BrainClientError(message=d.reason, status_code=403, error_reason="policy_denied")
    for key in patch:
        if str(key).startswith("stav") or key == "stav_auto":
            d = deny_stav_auto_write()
            raise BrainClientError(
                message=d.reason, status_code=403, error_reason="policy_denied"
            )

    with brain_vault(mode="mutate", env=env) as vault:
        try:
            text, meta = vault.read_text(path)
            oid = getattr(meta, "oid", None)
            if expect_oid is not None and oid is not None and str(oid) != str(expect_oid):
                raise BrainClientError(
                    message=f"CAS conflict expect_oid={expect_oid!r} got={oid!r}",
                    status_code=409,
                    error_reason="cas_conflict",
                )
            m = _FM_RE.match(text)
            if not m:
                raise BrainClientError(message="no frontmatter", status_code=400)
            fm_raw, body = m.group(1), m.group(2)
            lines = fm_raw.splitlines(keepends=True)
            keys_done: set[str] = set()
            new_lines: list[str] = []
            for line in lines:
                if ":" in line and not line.strip().startswith("#"):
                    key = line.split(":", 1)[0].strip()
                    if key in patch:
                        val = patch[key]
                        new_lines.append(
                            f"{key}: {val}\n"
                            if not isinstance(val, str) or ":" not in val
                            else f'{key}: "{val}"\n'
                        )
                        keys_done.add(key)
                        continue
                new_lines.append(line if line.endswith("\n") else line + "\n")
            for key, val in patch.items():
                if key in keys_done:
                    continue
                new_lines.append(
                    f'{key}: "{val}"\n'
                    if isinstance(val, str) and (":" in val or val.startswith("[["))
                    else f"{key}: {val}\n"
                )
            new_text = "---\n" + "".join(new_lines) + "---\n" + body
            kwargs: dict[str, Any] = {}
            if expect_oid is not None:
                kwargs["expect_oid"] = expect_oid
            meta2 = vault.write_text(path, new_text, **kwargs)
        except DriveConflictError as exc:
            raise BrainClientError(
                message=str(exc),
                status_code=409,
                error_reason="cas_conflict",
            ) from exc
        return {
            "path": path,
            "oid": getattr(meta2, "oid", None),
            "patched": sorted(patch.keys()),
        }
