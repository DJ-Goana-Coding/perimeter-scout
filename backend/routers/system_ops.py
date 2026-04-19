"""
System telemetry router.

Exposes the standardized ``GET /v1/system/status`` (and the same handler
under ``/api/v1/system/status``) endpoint that every node in the Pioneer /
Citadel ecosystem ships, per the Universal Alignment Protocol Phase 2.2.

Response shape::

    {
      "repo": "perimeter-scout",
      "version": "3.1.0",
      "commit": "abc1234" | null,
      "uptime_seconds": 12.34,
      "modules": {"admiral": {...}, "perimeter_scout": {...}, ...},
      "dependencies_ok": true,
      "time": "2026-04-19T00:00:00Z"
    }

The endpoint is unauthenticated and side-effect-free so the Vercel HUD and
the Librarian's mapping crawler can poll it cheaply.
"""

from __future__ import annotations

import datetime as _dt
import os
import time
from typing import Any, Dict

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])

# Module-level start time so uptime is process-lifetime, not per-request.
_PROCESS_START = time.monotonic()

# Best-effort commit discovery. Resolved at import time so we don't shell
# out on every request. Order: explicit env var (set by CI), then
# fallback to ``git rev-parse`` if a working tree is available.
_COMMIT: str | None = (
    os.getenv("GIT_COMMIT")
    or os.getenv("GITHUB_SHA")
    or os.getenv("HF_COMMIT_SHA")
)
if not _COMMIT:
    try:  # pragma: no cover - environment-dependent
        import subprocess
        _COMMIT = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode().strip() or None
    except Exception:
        _COMMIT = None


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_dependencies() -> bool:
    """Lightweight import-presence check for required runtime libs."""
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import requests  # noqa: F401
        return True
    except Exception:
        return False


async def _build_status(request: Request) -> Dict[str, Any]:
    registry = getattr(request.app.state, "registry", None)
    modules: Dict[str, Any] = {}
    if registry is not None:
        try:
            modules = registry.capabilities()
        except Exception as exc:  # pragma: no cover - defensive
            modules = {"_error": str(exc)}

    # Repo version sourced from the Aegis core when available, falling back
    # to a static label so the field is always populated.
    aegis = getattr(request.app.state, "aegis", None)
    version = getattr(aegis, "VERSION", None) or "unknown"

    return {
        "repo": "perimeter-scout",
        "version": version,
        "commit": _COMMIT,
        "uptime_seconds": round(time.monotonic() - _PROCESS_START, 3),
        "modules": modules,
        "dependencies_ok": _check_dependencies(),
        "time": _now_iso(),
    }


@router.get("/v1/system/status")
async def system_status_v1(request: Request) -> Dict[str, Any]:
    """Standardized cross-node telemetry endpoint."""
    return await _build_status(request)


@router.get("/api/v1/system/status")
async def system_status_apiv1(request: Request) -> Dict[str, Any]:
    """Same handler exposed under ``/api/v1/system/status`` for parity with
    the existing router-prefixed routes (`/api/v1/security`, etc.)."""
    return await _build_status(request)
