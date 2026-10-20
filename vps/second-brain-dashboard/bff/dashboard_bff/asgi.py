"""Production app. Env is set by Coolify; tests build the app through create_app."""

from __future__ import annotations

import os

from dashboard_bff.app import HttpxBrain, create_app


def create_production_app():
    base = (os.environ.get("BRAIN_BASE_URL") or "").strip()
    token = (os.environ.get("BRAIN_SERVICE_TOKEN") or "").strip()
    secret = (os.environ.get("DASHBOARD_SESSION_SECRET") or "").strip()
    if not base or not token or not secret:
        raise RuntimeError("BRAIN_BASE_URL, BRAIN_SERVICE_TOKEN and DASHBOARD_SESSION_SECRET are required")
    return create_app(HttpxBrain(base, token), secret=secret)


app = create_production_app()
