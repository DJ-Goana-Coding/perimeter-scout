from fastapi import APIRouter, Depends, Request
from ..core.module_registry import ModuleRegistry
from ..core.event_bus import EventBus

router = APIRouter(prefix="/modules", tags=["modules"])


def get_registry(request: Request) -> ModuleRegistry:
    return request.app.state.registry


@router.get("/health")
async def modules_health(registry: ModuleRegistry = Depends(get_registry)):
    return {
        "modules": registry.list(),
        "capabilities": registry.capabilities(),
    }


@router.get("/events")
async def module_events(limit: int = 200, request: Request = None):
    bus: EventBus = request.app.state.event_bus
    return bus.read(limit)
