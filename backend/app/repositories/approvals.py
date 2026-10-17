import json, time, uuid
from typing import Optional
from sqlalchemy import delete, or_, select, update
from ..models import ApprovalAudit, ApprovalChannel, ApprovalRequest, ChannelIdentity
from ..models.database import Database


class ApprovalRepository:
    """Channels, identities, approval requests and their audit log (TASK-0022)."""
    def __init__(self, db: Database): self.db = db

    # ---- channels ----
    def channels_visible(self, uid: str) -> list[ApprovalChannel]:
        """The user's own channels plus every org-wide channel."""
        with self.db.session() as s:
            q = select(ApprovalChannel).where(or_(ApprovalChannel.owner == uid, ApprovalChannel.scope == "org"))
            return list(s.scalars(q.order_by(ApprovalChannel.scope.desc(), ApprovalChannel.kind, ApprovalChannel.created)))

    def channel(self, cid: str) -> Optional[ApprovalChannel]:
        with self.db.session() as s: return s.get(ApprovalChannel, cid)

    def find_channel(self, owner: str, kind: str, scope: str) -> Optional[ApprovalChannel]:
        with self.db.session() as s:
            return s.scalars(select(ApprovalChannel).where(ApprovalChannel.owner == owner, ApprovalChannel.kind == kind, ApprovalChannel.scope == scope)
                             .order_by(ApprovalChannel.created)).first()

    def org_channel(self, kind: str) -> Optional[ApprovalChannel]:
        with self.db.session() as s:
            return s.scalars(select(ApprovalChannel).where(ApprovalChannel.kind == kind, ApprovalChannel.scope == "org").order_by(ApprovalChannel.created)).first()

    def save_channel(self, row: ApprovalChannel) -> ApprovalChannel:
        """Insert, or update the row with this id (the id, and so the callback URL, stays the same)."""
        with self.db.session() as s: row = s.merge(row); s.commit(); s.refresh(row); return row

    def delete_channel(self, cid: str) -> int:
        with self.db.session() as s:
            n = s.execute(delete(ApprovalChannel).where(ApprovalChannel.id == cid)).rowcount; s.commit(); return n or 0

    @staticmethod
    def new_id() -> str: return uuid.uuid4().hex[:12]

    # ---- identities ----
    def identities(self, uid: str) -> dict[str, ChannelIdentity]:
        with self.db.session() as s: return {i.kind: i for i in s.scalars(select(ChannelIdentity).where(ChannelIdentity.user_id == uid))}

    def identity(self, uid: str, kind: str) -> Optional[ChannelIdentity]:
        with self.db.session() as s: return s.get(ChannelIdentity, (uid, kind))

    def user_for(self, kind: str, external_id: str) -> Optional[str]:
        """The studio user with a *verified* link to this account (None when nobody proved it)."""
        with self.db.session() as s:
            return s.scalar(select(ChannelIdentity.user_id).where(ChannelIdentity.kind == kind, ChannelIdentity.external_id == external_id,
                                                                  ChannelIdentity.verified_at.is_not(None)))

    def put_identity(self, uid: str, kind: str, external_id: Optional[str]) -> None:
        """Link (unverified, no code yet) or unlink with None. Relinking the same account keeps its state."""
        with self.db.session() as s:
            row = s.get(ChannelIdentity, (uid, kind))
            if row is not None and row.external_id == external_id: return
            if row is not None: s.delete(row); s.flush()
            if external_id: s.add(ChannelIdentity(user_id=uid, kind=kind, external_id=external_id, created=time.time(), code_attempts=0))
            s.commit()

    def set_identity(self, uid: str, kind: str, **vals) -> None:
        with self.db.session() as s:
            s.execute(update(ChannelIdentity).where(ChannelIdentity.user_id == uid, ChannelIdentity.kind == kind).values(**vals)); s.commit()

    def count_attempt(self, uid: str, kind: str) -> int:
        """Atomically count a wrong code; returns the new count."""
        with self.db.session() as s:
            s.execute(update(ChannelIdentity).where(ChannelIdentity.user_id == uid, ChannelIdentity.kind == kind)
                      .values(code_attempts=ChannelIdentity.code_attempts + 1)); s.commit()
            return s.scalar(select(ChannelIdentity.code_attempts).where(ChannelIdentity.user_id == uid, ChannelIdentity.kind == kind)) or 0

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
