"""
Mapping & Inventory Client
Connects Perimeter Scout to the Pioneer Trader mapping-and-inventory service.
"""
import os
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

PIONEER_TRADER_URL = os.getenv(
    "PIONEER_TRADER_URL", "http://localhost:8001"
)
_REQUEST_TIMEOUT = 10  # seconds


def _get(path: str) -> Any:
    url = PIONEER_TRADER_URL.rstrip("/") + path
    resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_fleet_inventory() -> Dict[str, Any]:
    """Fetch T.I.A. fleet inventory from Pioneer Trader."""
    try:
        return _get("/cockpit/status")
    except requests.exceptions.ConnectionError:
        logger.warning("Pioneer Trader service unreachable at %s", PIONEER_TRADER_URL)
        return {"status": "UNREACHABLE", "error": "Pioneer Trader service not available"}
    except requests.exceptions.Timeout:
        logger.warning("Pioneer Trader request timed out")
        return {"status": "TIMEOUT", "error": "Request to Pioneer Trader timed out"}
    except Exception as exc:
        logger.error("Mapping-inventory fetch failed: %s", exc)
        return {"status": "ERROR", "error": str(exc)}


def get_cockpit_health() -> Dict[str, Any]:
    """Fetch cockpit health from Pioneer Trader."""
    try:
        return _get("/cockpit/health")
    except requests.exceptions.ConnectionError:
        return {"status": "UNREACHABLE", "error": "Pioneer Trader service not available"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "error": "Request timed out"}
    except Exception as exc:
        logger.error("Cockpit health fetch failed: %s", exc)
        return {"status": "ERROR", "error": str(exc)}


def get_tia_summary() -> Dict[str, Any]:
    """Fetch T.I.A. risk summary from Pioneer Trader."""
    try:
        return _get("/cockpit/tia/summary")
    except requests.exceptions.ConnectionError:
        return {"status": "UNREACHABLE", "error": "Pioneer Trader service not available"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "error": "Request timed out"}
    except Exception as exc:
        logger.error("T.I.A. summary fetch failed: %s", exc)
        return {"status": "ERROR", "error": str(exc)}
