from fastapi import APIRouter, Depends, Request
from ..services.perimeter_scout.core import AegisCore

router = APIRouter(prefix="/security", tags=["security"])


def get_aegis(request: Request) -> AegisCore:
    return request.app.state.aegis


@router.get("/intel")
async def aegis_intel(mode: str = "deep", aegis: AegisCore = Depends(get_aegis)):
    if mode == "sample":
        return await aegis.sample_intel()
    return await aegis.deep_intel()


@router.get("/timeline/minimal")
async def aegis_timeline_minimal(limit: int = 200):
    from ..services.perimeter_scout.minilog import LOG_PATH
    import os, json

    if not os.path.exists(LOG_PATH):
        return []
    events = []
    with open(LOG_PATH, "r") as f:
        for line in f.readlines()[-limit:]:
            try:
                events.append(json.loads(line))
            except:
                continue
    return events
