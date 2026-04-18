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


def _post(path: str, payload: Dict[str, Any]) -> Any:
    url = PIONEER_TRADER_URL.rstrip("/") + path
    resp = requests.post(url, json=payload, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def ingest_document(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forward a RAG ingestion request to the mapping-and-inventory hub
    (`POST /v1/ingest`). The hub owns the global FAISS vector store; this
    client is a thin proxy so Perimeter Scout never holds index state
    locally.

    The expected payload shape is the hub's own ingest contract — typically
    ``{"documents": [{"id": ..., "text": ..., "metadata": {...}}, ...]}`` —
    but this function is intentionally schema-agnostic so it does not drift
    from the hub.
    """
    try:
        return _post("/v1/ingest", payload)
    except requests.exceptions.ConnectionError:
        logger.warning("Pioneer Trader (mapping-inventory hub) unreachable at %s", PIONEER_TRADER_URL)
        return {"status": "UNREACHABLE", "error": "Mapping-inventory hub not available"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "error": "Ingest request timed out"}
    except requests.exceptions.HTTPError as exc:
        logger.error("Hub rejected ingest: %s", exc)
        return {"status": "ERROR", "error": str(exc)}
    except Exception as exc:
        logger.error("Ingest failed: %s", exc)
        return {"status": "ERROR", "error": str(exc)}


def query_index(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forward a RAG query to the mapping-and-inventory hub
    (`POST /v1/query`). Same proxy pattern as :func:`ingest_document`.
    """
    try:
        return _post("/v1/query", payload)
    except requests.exceptions.ConnectionError:
        logger.warning("Pioneer Trader (mapping-inventory hub) unreachable at %s", PIONEER_TRADER_URL)
        return {"status": "UNREACHABLE", "error": "Mapping-inventory hub not available"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "error": "Query request timed out"}
    except requests.exceptions.HTTPError as exc:
        logger.error("Hub rejected query: %s", exc)
        return {"status": "ERROR", "error": str(exc)}
    except Exception as exc:
        logger.error("Query failed: %s", exc)
        return {"status": "ERROR", "error": str(exc)}
