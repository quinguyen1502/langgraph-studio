from fastapi import APIRouter, Depends
from ...core import config
from ...engine.tools import TOOLS
from ..deps import current_user

router = APIRouter(prefix="/api", tags=["meta"])

@router.get("/health")
def health(): return {"ok": True, "llm_mode": config.llm_mode()}

@router.get("/tools")
def tools(user=Depends(current_user)): return [{"name": k, "doc": (v.__doc__ or "").strip()} for k, v in TOOLS.items()]
