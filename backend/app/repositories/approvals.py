import json, time, uuid
from typing import Optional
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from ..models import ApprovalAudit, ApprovalChannel, ApprovalRequest, ChannelIdentity
from ..models.database import Database


class IdentityTaken(Exception):
    """The channel account is already linked to another studio user."""


class ApprovalRepository:
    """Channels, identities, approval requests and their audit log (TASK-0022)."""
    def __init__(self, db: Database): self.db = db

    # ---- channels ----
    def channels(self, owner: str) -> list[ApprovalChannel]:
        with self.db.session() as s: return list(s.scalars(select(ApprovalChannel).where(ApprovalChannel.owner == owner).order_by(ApprovalChannel.kind)))

    def channel(self, cid: str) -> Optional[ApprovalChannel]:
        with self.db.session() as s: return s.get(ApprovalChannel, cid)

    def channel_for(self, owner: str, kind: str) -> Optional[ApprovalChannel]:
        with self.db.session() as s:
            return s.scalars(select(ApprovalChannel).where(ApprovalChannel.owner == owner, ApprovalChannel.kind == kind)).first()

    def save_channel(self, owner: str, kind: str, secrets: str, hint: str) -> ApprovalChannel:
        """Insert or replace the owner's channel of this kind (the id, and so the callback URL, stays the same)."""
        with self.db.session() as s:
            row = s.scalars(select(ApprovalChannel).where(ApprovalChannel.owner == owner, ApprovalChannel.kind == kind)).first()
            if row is None: row = ApprovalChannel(id=uuid.uuid4().hex[:12], owner=owner, kind=kind, created=time.time()); s.add(row)
            row.secrets, row.hint = secrets, hint
            s.commit(); s.refresh(row); return row

    def delete_channel(self, owner: str, kind: str) -> int:
        with self.db.session() as s:
            n = s.execute(delete(ApprovalChannel).where(ApprovalChannel.owner == owner, ApprovalChannel.kind == kind)).rowcount; s.commit(); return n or 0

    # ---- identities ----
    def identities(self, uid: str) -> dict[str, str]:
        with self.db.session() as s: return {i.kind: i.external_id for i in s.scalars(select(ChannelIdentity).where(ChannelIdentity.user_id == uid))}

    def user_for(self, kind: str, external_id: str) -> Optional[str]:
        with self.db.session() as s:
            return s.scalar(select(ChannelIdentity.user_id).where(ChannelIdentity.kind == kind, ChannelIdentity.external_id == external_id))

    def set_identity(self, uid: str, kind: str, external_id: Optional[str]) -> None:
        """Link (or unlink with None). Raises IdentityTaken when another user already linked that account."""
        with self.db.session() as s:
            s.execute(delete(ChannelIdentity).where(ChannelIdentity.user_id == uid, ChannelIdentity.kind == kind))
            if external_id: s.add(ChannelIdentity(user_id=uid, kind=kind, external_id=external_id, created=time.time()))
            try: s.commit()
            except IntegrityError: s.rollback(); raise IdentityTaken(kind)

    # ---- requests ----
    def add_request(self, r: ApprovalRequest) -> ApprovalRequest:
        with self.db.session() as s: s.add(r); s.commit(); return r

    def request(self, aid: str) -> Optional[ApprovalRequest]:
        with self.db.session() as s: return s.get(ApprovalRequest, aid)

    def requests_for_run(self, rid: str, status: Optional[str] = None) -> list[ApprovalRequest]:
        with self.db.session() as s:
            q = select(ApprovalRequest).where(ApprovalRequest.run_id == rid)
            if status: q = q.where(ApprovalRequest.status == status)
            return list(s.scalars(q))

    def set_ref(self, aid: str, ref: Optional[dict], status: Optional[str] = None) -> None:
        with self.db.session() as s:
            vals = {"message_ref": json.dumps(ref) if ref is not None else None, **({"status": status} if status else {})}
            s.execute(update(ApprovalRequest).where(ApprovalRequest.id == aid).values(**vals)); s.commit()

    def decide(self, aid: str, status: str, by: Optional[str] = None, external: Optional[str] = None) -> bool:
        """Compare-and-set pending -> status. Exactly one caller wins (single-use tokens)."""
        with self.db.session() as s:
            n = s.execute(update(ApprovalRequest).where(ApprovalRequest.id == aid, ApprovalRequest.status == "pending")
                          .values(status=status, decided_by=by, decided_external=external, decided_at=time.time())).rowcount
            s.commit(); return n == 1

    # ---- audit ----
    def audit(self, e: ApprovalAudit) -> None:
        with self.db.session() as s: s.add(e); s.commit()

    def audit_for(self, owner: str, limit: int = 100) -> list[ApprovalAudit]:
        with self.db.session() as s:
            return list(s.scalars(select(ApprovalAudit).where(ApprovalAudit.owner == owner).order_by(ApprovalAudit.created.desc()).limit(limit)))
