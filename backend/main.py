from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from .core.module_registry import ModuleRegistry
from .core.event_bus import EventBus
from .services.perimeter_scout.core import AegisCore
from .services.admiral.admiral_engine import AdmiralEngine
from .services.admirai.orchestrator import Admirai
from .routers import security_ops, modules_ops, admin_ops, inventory_ops
from .middleware.aegis_middleware import aegis_auth_middleware
from .security.ip_monitor import aegis_monitor

app = FastAPI(title="Pioneer Ecosystem")

# CORS: explicit allowlist for the Citadel Nexus Faceplate (Vercel HUD).
# This is the only authorized production browser origin permitted to call
# the Aegis API. Add additional origins here only with explicit approval.
ALLOWED_ORIGINS = [
    "https://citadel-nexus-private.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add Aegis middleware
app.middleware("http")(aegis_auth_middleware)


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
    
    # Start daily security digest task
    from tasks.security_digest import daily_security_digest
    app.state.security_digest_task = asyncio.create_task(daily_security_digest())
    print("✅ Aegis Security Digest Task Started")


app.include_router(security_ops.router, prefix="/api/v1")
app.include_router(modules_ops.router, prefix="/api/v1")
app.include_router(admin_ops.router, prefix="/api/v1")
app.include_router(inventory_ops.router, prefix="/api/v1")


@app.get("/health/security")
async def security_health():
    """
    Get current Aegis security status.
    Public endpoint - no authentication required.
    """
    summary = aegis_monitor.get_daily_summary()
    
    return {
        "status": "operational",
        "aegis_version": "3.1.0",
        "banned_ips_count": len(aegis_monitor.banned_ips),
        "today_events": summary['total_events'],
        "today_bans": summary['auto_bans']
    }


@app.get("/health/live")
async def health_live():
    """
    Liveness probe. Returns 200 as long as the process is running and the
    event loop can serve a request. Used by the Vercel HUD and container
    orchestrators to detect a hung process.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def health_ready():
    """
    Readiness probe. Returns 200 once core subsystems (module registry,
    event bus, Aegis core) have been initialized by the startup handler.
    Returns 503 while the app is still starting up.
    """
    registry = getattr(app.state, "registry", None)
    event_bus = getattr(app.state, "event_bus", None)
    aegis = getattr(app.state, "aegis", None)

    components = {
        "registry": registry is not None,
        "event_bus": event_bus is not None,
        "aegis": aegis is not None,
    }
    ready = all(components.values())

    if not ready:
        return JSONResponse(
            status_code=503,
            content={"status": "starting", "components": components},
        )

    return {"status": "ready", "components": components}

