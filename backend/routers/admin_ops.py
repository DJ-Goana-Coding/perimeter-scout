from fastapi import APIRouter, Request

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reload")
async def admin_reload(request: Request = None):
    app = request.app
    admirai = getattr(app.state, "admirai", None)
    if admirai and hasattr(admirai, "policy"):
        admirai.policy.load()
    return {"status": "reloaded", "components": ["policy_engine"]}
