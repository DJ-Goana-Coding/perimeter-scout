from fastapi import APIRouter

from ..services.mapping_inventory.client import (
    get_fleet_inventory,
    get_cockpit_health,
    get_tia_summary,
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
