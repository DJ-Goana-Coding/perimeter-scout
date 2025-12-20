from fastapi import FastAPI
from .core.module_registry import ModuleRegistry
from .core.event_bus import EventBus
from .services.perimeter_scout.core import AegisCore
from .services.admiral.admiral_engine import AdmiralEngine
from .services.admirai.orchestrator import Admirai
from .routers import security_ops, modules_ops, admin_ops

app = FastAPI(title="Pioneer Ecosystem")


@app.on_event("startup")
async def startup():
    registry = ModuleRegistry()
    event_bus = EventBus()

    app.state.registry = registry
    app.state.event_bus = event_bus

    # Admiral (trading)
    admiral = AdmiralEngine()
    registry.register("admiral", admiral)

    # Perimeter Scout / Aegis
    aegis = AegisCore(event_bus=event_bus)
    app.state.aegis = aegis
    registry.register("perimeter_scout", aegis)

    # Admirai
    admirai = Admirai(registry=registry)
    app.state.admirai = admirai
    registry.register("admirai", admirai)

    print("✅ Module Registry Online")
    print("✅ Admiral Registered")
    print("✅ Perimeter Scout Registered")
    print("✅ Admirai Registered")


app.include_router(security_ops.router, prefix="/api/v1")
app.include_router(modules_ops.router, prefix="/api/v1")
app.include_router(admin_ops.router, prefix="/api/v1")
