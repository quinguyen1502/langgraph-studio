from fastapi import APIRouter, Depends
from ...engine.validator import validate
from ...schemas.workflow import Rename, WorkflowIn
from ..deps import current_user, limit_body, run_service, workflow_service

router = APIRouter(prefix="/api", tags=["workflows"])

@router.get("/workflows")
def list_wf(user=Depends(current_user), svc=Depends(workflow_service)): return svc.list(user["id"])

@router.get("/workflows/{wid}")
def get_wf(wid: str, user=Depends(current_user), svc=Depends(workflow_service)): return svc.get(wid, user["id"])

@router.post("/workflows", dependencies=[Depends(limit_body)])
def save_wf(body: WorkflowIn, user=Depends(current_user), svc=Depends(workflow_service)): return svc.save(body.as_dict(), user["id"])

@router.patch("/workflows/{wid}")
def rename_wf(wid: str, body: Rename, user=Depends(current_user), svc=Depends(workflow_service)): return svc.rename(wid, body.name, user["id"])

@router.post("/workflows/{wid}/duplicate")
def dup_wf(wid: str, user=Depends(current_user), svc=Depends(workflow_service)): return svc.duplicate(wid, user["id"])

@router.delete("/workflows/{wid}")
def del_wf(wid: str, user=Depends(current_user), svc=Depends(workflow_service)): return svc.delete(wid, user["id"])

@router.get("/workflows/{wid}/runs")
def runs(wid: str, user=Depends(current_user), svc=Depends(run_service)): return svc.history(wid, user["id"])

@router.post("/validate", dependencies=[Depends(limit_body)])
def validate_wf(body: WorkflowIn, user=Depends(current_user)): return {"errors": validate(body.as_dict())}
