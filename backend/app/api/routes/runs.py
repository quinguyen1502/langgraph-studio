"""REST run controls (TASK-0009). Execution itself streams over /ws/run."""
from fastapi import APIRouter, Depends
from ..deps import current_user, run_service

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("/{run_id}/cancel")
def cancel_run(run_id: str, user=Depends(current_user)):
    """Ask a running run (on any API worker when Redis is configured) to stop at its next step."""
    run_service().cancel(run_id, user["id"])
    return {"run_id": run_id, "cancel_requested": True}
