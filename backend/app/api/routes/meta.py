from fastapi import APIRouter, Depends
from ...core import config
from ...engine.tools import TOOLS
from ..deps import current_user, get_db, get_run_bus

router = APIRouter(prefix="/api", tags=["meta"])

@router.get("/health")
def health():
    bus = get_run_bus()
    return {"ok": True, "llm_mode": config.llm_mode(), "database": get_db().engine.dialect.name,
            "run_bus": bus.kind, "run_bus_ok": bus.ping()}

@router.get("/tools")
def tools(user=Depends(current_user)): return [{"name": k, "doc": (v.__doc__ or "").strip()} for k, v in TOOLS.items()]
