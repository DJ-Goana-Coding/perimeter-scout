from typing import Any, Dict

from fastapi import APIRouter, Body

from ..services.mapping_inventory.client import (
    get_fleet_inventory,
    get_cockpit_health,
    get_tia_summary,
    ingest_document,
    query_index,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/fleet")
async def fleet_inventory():
    """Fetch T.I.A. fleet inventory from Pioneer Trader mapping-and-inventory."""
    return get_fleet_inventory()


@router.get("/health")
async def inventory_health():
    """Fetch Pioneer Trader cockpit health."""
    return get_cockpit_health()


@router.get("/tia/summary")
async def tia_summary():
    """Fetch T.I.A. risk summary from Pioneer Trader."""
    return get_tia_summary()


# ---------------------------------------------------------------------------
# RAG hub-and-spoke proxy
#
# These endpoints are thin proxies onto the mapping-and-inventory hub's
# `/v1/ingest` and `/v1/query` routes. The hub owns the global FAISS vector
# store; Perimeter Scout never holds index state locally. Final mounted
# paths (after `app.include_router(..., prefix="/api/v1")` in backend/main.py)
# are:
#     POST /api/v1/inventory/ingest
#     POST /api/v1/inventory/query
# ---------------------------------------------------------------------------


@router.post("/ingest")
async def rag_ingest(payload: Dict[str, Any] = Body(default_factory=dict)):
    """Forward a RAG ingestion request to the mapping-and-inventory hub."""
    return ingest_document(payload)


@router.post("/query")
async def rag_query(payload: Dict[str, Any] = Body(default_factory=dict)):
    """Forward a RAG query to the mapping-and-inventory hub."""
    return query_index(payload)
