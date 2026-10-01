#!/usr/bin/env python3
"""Import Fio XML payment order for Lukáš's personal account (příkazy k podpisu).

Token from $FIO_PERSONAL_TOKEN or ~/.config/second-brain/fio-personal.env.
Never prints the token. Upload lands in IB as unsigned payment orders.
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import urllib.error
import urllib.parse
import urllib.request

ENV_FILE = Path.home() / ".config" / "second-brain" / "fio-personal.env"
DEFAULT_BASE = "https://fioapi.fio.cz/v1/rest"


def _die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    if not ENV_FILE.exists():
        return out
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip("'\"")
    return out


def load_token() -> str:
    token = (os.environ.get("FIO_PERSONAL_TOKEN") or "").strip()
    if not token:
        token = (_load_env().get("FIO_PERSONAL_TOKEN") or "").strip()
    if not token:
        _die(
            "Chybí FIO_PERSONAL_TOKEN. Token patří do "
            f"{ENV_FILE} (nebo env). Nikdy ho nedávej do chatu."
        )
    return token


def parse_import_response(xml_text: str) -> dict[str, str | bool | None]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {
            "ok": False,
            "error_code": None,
            "status": None,
            "id_instruction": None,
            "message": f"XML parse error: {e}",
        }
    error_code = None
    status = None
    id_instruction = None
    for el in root.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        low = tag.lower()
        if low in ("errorcode", "error_code") and el.text:
            error_code = el.text.strip()
        if low == "status" and el.text and status is None:
            status = el.text.strip()
        if low in ("idinstruction", "id_instruction") and el.text:
            id_instruction = el.text.strip()
    ok = error_code in ("0", "00") or (status or "").lower() == "ok"
    if error_code and error_code not in ("0", "00") and (status or "").lower() == "error":
        ok = False
    msg = f"errorCode={error_code} status={status}"
    if id_instruction:
        msg += f" idInstruction={id_instruction}"
    return {
        "ok": ok,
        "error_code": error_code,
        "status": status,
        "id_instruction": id_instruction,
        "message": msg,
    }


def import_xml(path: Path, *, token: str, base_url: str) -> tuple[int, str]:
    xml_bytes = path.read_bytes()
    if b"<Import>" not in xml_bytes and b"<import>" not in xml_bytes.lower():
        _die(f"Soubor nevypadá jako Fio Import XML: {path}")

    url = f"{base_url.rstrip('/')}/import/?{urllib.parse.urlencode({'token': token, 'type': 'xml'})}"
    boundary = "----FioPersonalImportBoundary7MA4YWxk"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: application/xml\r\n\r\n"
    ).encode("utf-8") + xml_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, raw or str(e)


def main() -> None:
    p = argparse.ArgumentParser(description="Import personal Fio XML → příkazy k podpisu")
    p.add_argument("xml", type=Path, help="Cesta k Fio Import XML")
    p.add_argument(
        "--base-url",
        default=os.environ.get("FIO_BASE_URL") or DEFAULT_BASE,
        help="Fio REST base (default fioapi.fio.cz/v1/rest)",
    )
    args = p.parse_args()
    path = args.xml.expanduser().resolve()
    if not path.is_file():
        _die(f"XML neexistuje: {path}")

    token = load_token()
    http_status, raw = import_xml(path, token=token, base_url=args.base_url)
    print(f"http_status={http_status}")
    print(f"file={path.name}")

    if http_status >= 400:
        # Do not dump full body if it might echo token in query — keep short.
        snippet = (raw or "").replace(token, "***")[:500]
        print(f"ok=false")
        print(f"message=HTTP {http_status}")
        if snippet:
            print(f"body_snippet={snippet}")
        raise SystemExit(2)

    parsed = parse_import_response(raw)
    print(f"ok={str(parsed['ok']).lower()}")
    print(f"message={parsed['message']}")
    if parsed.get("id_instruction"):
        print(f"id_instruction={parsed['id_instruction']}")
    # Safe echo of response tags only (no token)
    safe = (raw or "").replace(token, "***")
    print(f"response={safe.strip()}")
    if not parsed["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
