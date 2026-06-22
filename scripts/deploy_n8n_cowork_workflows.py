#!/usr/bin/env python3
"""Deploy ŠABLONY/n8n cowork workflows to n8n.redbuttonedu.cz via REST API.

Preserves live credentials, trigger filters, and Drive folder IDs.
Usage:
  python3 scripts/deploy_n8n_cowork_workflows.py
  python3 scripts/deploy_n8n_cowork_workflows.py --dry-run
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "ŠABLONY" / "n8n"
ENV_FILE = Path.home() / "GitHub/Allfred invoices - Equilibrium/.env"

DEPLOYS = [
    {
        "template": "email-to-cowork.json",
        "workflow_id": "omQRpDBa48ePiKnT",
        "action": "put",
    },
    {
        "template": "workspace-sent-to-inbox.json",
        "workflow_id": "7fhDXThOaxl1yNtE",
        "action": "put",
        "gmail_options": {"downloadAttachments": True},
    },
    {
        "template": "mobile-capture-to-cowork.json",
        "workflow_id": None,
        "action": "post",
        "name": "SECOND BRAIN: Mobile → INBOX/daily",
        "daily_folder_id": "1hJWgIxgq5lJpMmjV7OILpRpmUu7zpA2K",
    },
]

TRIGGER_PREFIXES = ("Gmail:", "Slack:", "Webhook:")


def load_env() -> tuple[str, str]:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    host = os.environ.get("N8N_HOST", "https://n8n.redbuttonedu.cz").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not key:
        raise RuntimeError("N8N_API_KEY not found (expected in Allfred .env)")
    return host, key


def api_request(host: str, key: str, method: str, path: str, payload: dict | None = None) -> dict:
    url = f"{host}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "X-N8N-API-KEY": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed {e.code}: {body[:500]}") from e


def fetch_workflow(host: str, key: str, wf_id: str) -> dict:
    return api_request(host, key, "GET", f"/api/v1/workflows/{wf_id}")


def build_cred_pool(live: dict) -> dict[str, dict]:
    pool: dict[str, dict] = {}
    for node in live.get("nodes", []):
        creds = node.get("credentials") or {}
        for ctype, cval in creds.items():
            pool[ctype] = copy.deepcopy(cval)
        if "Drive" in node.get("name", ""):
            fid = node.get("parameters", {}).get("folderId")
            if fid:
                pool.setdefault("_folderId", copy.deepcopy(fid))
    return pool


def merge_nodes(template_nodes: list, live: dict, *, gmail_options: dict | None = None) -> list:
    live_by_name = {n["name"]: n for n in live.get("nodes", [])}
    pool = build_cred_pool(live)
    merged = []
    for tn in template_nodes:
        node = copy.deepcopy(tn)
        ln = live_by_name.get(node["name"])
        if ln:
            if ln.get("id"):
                node["id"] = ln["id"]
            if ln.get("credentials"):
                node["credentials"] = copy.deepcopy(ln["credentials"])
            if ln.get("webhookId"):
                node["webhookId"] = ln["webhookId"]
            name = node.get("name", "")
            if any(name.startswith(p) for p in TRIGGER_PREFIXES):
                node["parameters"] = copy.deepcopy(ln.get("parameters", {}))
                if gmail_options and "Gmail" in name:
                    opts = node["parameters"].setdefault("options", {})
                    opts.update(gmail_options)
            else:
                for key in ("folderId", "driveId"):
                    lv = (ln.get("parameters") or {}).get(key)
                    if lv:
                        node.setdefault("parameters", {})[key] = copy.deepcopy(lv)
        else:
            # New node — inherit credentials by node type
            ntype = node.get("type", "")
            if "googleDrive" in ntype and pool.get("_folderId"):
                node.setdefault("parameters", {})["folderId"] = copy.deepcopy(pool["_folderId"])
            if "googleDrive" in ntype and "googleDriveOAuth2Api" in pool:
                node["credentials"] = {"googleDriveOAuth2Api": copy.deepcopy(pool["googleDriveOAuth2Api"])}
            if "gmailTrigger" in ntype and "gmailOAuth2" in pool:
                node["credentials"] = {"gmailOAuth2": copy.deepcopy(pool["gmailOAuth2"])}
        merged.append(node)
    return merged


def apply_folder_override(nodes: list, folder_id: str) -> None:
    folder_ref = {
        "__rl": True,
        "mode": "id",
        "value": folder_id,
    }
    url_ref = {
        "__rl": True,
        "mode": "url",
        "value": f"https://drive.google.com/drive/u/0/folders/{folder_id}",
    }
    for node in nodes:
        if "Drive" in node.get("name", ""):
            node.setdefault("parameters", {})["folderId"] = copy.deepcopy(url_ref)
            if "driveId" in node.get("parameters", {}):
                node["parameters"]["driveId"] = {
                    "__rl": True,
                    "mode": "list",
                    "value": "My Drive",
                }


def put_payload(name: str, nodes: list, connections: dict) -> dict:
    return {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
    }


def deploy_one(host: str, key: str, spec: dict, dry_run: bool) -> dict:
    tpl_path = TEMPLATES / spec["template"]
    template = json.loads(tpl_path.read_text(encoding="utf-8"))
    live = fetch_workflow(host, key, spec["workflow_id"]) if spec.get("workflow_id") else {"nodes": []}

    if spec["action"] == "put":
        name = live.get("name") or template.get("name")
        nodes = merge_nodes(
            template["nodes"],
            live,
            gmail_options=spec.get("gmail_options"),
        )
        payload = put_payload(name, nodes, template["connections"])
        if dry_run:
            print(f"DRY PUT {spec['workflow_id']} {name} nodes={len(nodes)}")
            return {"dry_run": True, "id": spec["workflow_id"]}
        result = api_request(host, key, "PUT", f"/api/v1/workflows/{spec['workflow_id']}", payload)
        print(f"PUT OK {result.get('id')} {result.get('name')} updatedAt={result.get('updatedAt')}")
        return result

    # POST mobile
    name = spec.get("name") or template.get("name")
    # seed credentials from email workflow
    seed = fetch_workflow(host, key, "omQRpDBa48ePiKnT")
    nodes = merge_nodes(template["nodes"], seed)
    apply_folder_override(nodes, spec["daily_folder_id"])
    payload = put_payload(name, nodes, template["connections"])
    if dry_run:
        print(f"DRY POST {name} nodes={len(nodes)}")
        return {"dry_run": True}
    result = api_request(host, key, "POST", "/api/v1/workflows", payload)
    wf_id = result.get("id")
    print(f"POST OK {wf_id} {result.get('name')}")
    # activate
    api_request(host, key, "POST", f"/api/v1/workflows/{wf_id}/activate", {})
    print(f"ACTIVATED {wf_id}")
    return result


def sync_export(workflow_id: str, out_path: Path, host: str, key: str) -> None:
    wf = fetch_workflow(host, key, workflow_id)
    out_path.write_text(json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"synced export → {out_path.relative_to(REPO)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    host, key = load_env()

    results = []
    for spec in DEPLOYS:
        print(f"\n--- {spec['template']} ({spec['action']}) ---")
        results.append(deploy_one(host, key, spec, args.dry_run))

    if args.dry_run:
        return 0

    # Re-fetch and sync exports
    sync_export("omQRpDBa48ePiKnT", TEMPLATES / "email-to-cowork.json", host, key)
    sync_export("7fhDXThOaxl1yNtE", TEMPLATES / "workspace-sent-to-inbox.json", host, key)
    mobile = results[-1]
    if mobile.get("id"):
        sync_export(mobile["id"], TEMPLATES / "mobile-capture-to-cowork.json", host, key)

    return 0


if __name__ == "__main__":
    sys.exit(main())
