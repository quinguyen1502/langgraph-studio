"""In-app notifications (TASK-0020): the header bell."""
from fastapi import APIRouter, Depends
from ..deps import current_user, notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(unread: bool = False, user=Depends(current_user), svc=Depends(notification_service)):
    return svc.list(user["id"], unread_only=unread)

@router.post("/read-all")
def read_all(user=Depends(current_user), svc=Depends(notification_service)): return svc.mark_all_read(user["id"])

@router.post("/{nid}/read")
def read_one(nid: str, user=Depends(current_user), svc=Depends(notification_service)): return svc.mark_read(user["id"], nid)
