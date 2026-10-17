"""Human-in-the-loop approval through external channels (TASK-0022, DEC-0019).

Flow: a run pauses at a Human node whose `data.approval` names a channel -> `on_waiting` posts a message with
Approve/Reject buttons (signed, single-use, expiring tokens) -> the platform calls back -> `handle_callback` verifies
the request, maps the channel user to a studio user, checks they are the run owner or a listed approver, records the
decision (compare-and-set, so a token works once), queues a `resume` job and edits the original message.
Every step lands in the audit log. Without a configured channel everything is a no-op.
"""
import base64, hashlib, hmac, json, secrets as pysecrets, threading, time, uuid
from typing import Callable, Optional
from ..core import config, crypto
from ..core.errors import CATALOG, AppError
from ..core.logging import get_logger
from ..models import ApprovalAudit, ApprovalRequest
from ..repositories import ApprovalRepository, IdentityTaken, RunRepository, UserRepository, WorkflowRepository
from .approval_channels import ADAPTERS, ApprovalChannel, ApprovalMessage

log = get_logger("approvals")
DECISIONS = {"a": "approved", "r": "rejected"}
BACKGROUND = True  # send/edit messages off the request thread; tests switch it off for determinism


def callback_path(kind: str, cid: str) -> str: return f"/api/approvals/callback/{kind}/{cid}"


class ApprovalService:
    def __init__(self, repo: ApprovalRepository, users: UserRepository, workflows: WorkflowRepository, runs: RunRepository,
                 enqueue: Optional[Callable[[dict], None]] = None, adapters: Optional[dict[str, ApprovalChannel]] = None, background: Optional[bool] = None):
        self.repo, self.users, self.workflows, self.runs, self.enqueue = repo, users, workflows, runs, enqueue
        self.adapters = adapters if adapters is not None else ADAPTERS
        self.background = BACKGROUND if background is None else background

    def adapter(self, kind: str) -> ApprovalChannel:
        if kind not in self.adapters: raise AppError("CHANNEL_KIND_UNSUPPORTED", kind=kind)
        return self.adapters[kind]

    # ---- tokens: "<a|r>.<request id>.<hmac>" (fits Telegram's 64-byte callback_data) ----
    @staticmethod
    def _sig(r: ApprovalRequest, d: str) -> str:
        msg = f"{r.id}:{d}:{r.nonce}:{int(r.expires)}".encode()
        return base64.urlsafe_b64encode(hmac.new(crypto.derive_key("approval-token"), msg, hashlib.sha256).digest()[:16]).decode().rstrip("=")

    def token(self, r: ApprovalRequest, d: str) -> str: return f"{d}.{r.id}.{self._sig(r, d)}"

    def _parse(self, token: str) -> tuple[Optional[ApprovalRequest], Optional[str]]:
        parts = (token or "").split(".")
        if len(parts) != 3 or parts[0] not in DECISIONS: return None, None
        r = self.repo.request(parts[1])
        if r is None or not hmac.compare_digest(self._sig(r, parts[0]), parts[2]): return None, None
        return r, DECISIONS[parts[0]]

    # ---- owner: channel connections ----
    def public_channel(self, c) -> dict:
        base = config.public_url()
        return {"id": c.id, "kind": c.kind, "hint": c.hint, "created": c.created,
                "callback_url": (base + callback_path(c.kind, c.id)) if base else None, "callback_path": callback_path(c.kind, c.id)}

    def list_channels(self, uid: str) -> dict:
        have = {c.kind: self.public_channel(c) for c in self.repo.channels(uid)}
        return {"kinds": [{"kind": k, "fields": list(a.fields), "optional": list(a.optional), "channel": have.get(k)} for k, a in self.adapters.items()],
                "public_url": config.public_url() or None}

    def save_channel(self, uid: str, kind: str, body) -> dict:
        a = self.adapter(kind); vals = a.prepare(body if isinstance(body, dict) else {})
        c = self.repo.save_channel(uid, kind, crypto.encrypt(json.dumps(vals)), crypto.mask(vals[a.hint_field]))
        return self.public_channel(c)

    def delete_channel(self, uid: str, kind: str) -> dict:
        self.adapter(kind)
        if not self.repo.delete_channel(uid, kind): raise AppError("CHANNEL_NOT_FOUND")
        return {"ok": True}

    def register_webhook(self, uid: str, kind: str) -> dict:
        a = self.adapter(kind); c = self.repo.channel_for(uid, kind)
        if c is None: raise AppError("CHANNEL_NOT_FOUND")
        base = config.public_url()
        if not base.startswith("https://"): raise AppError("CHANNEL_PUBLIC_URL_REQUIRED")
        url = base + callback_path(kind, c.id)
        return {"callback_url": url, **a.register(self._secrets(c), url)}

    @staticmethod
    def _secrets(c) -> dict: return json.loads(crypto.decrypt(c.secrets))

    # ---- user: channel identities ----
    def identities(self, uid: str) -> dict:
        mine = self.repo.identities(uid)
        return {k: mine.get(k) for k in self.adapters}

    def set_identities(self, uid: str, body) -> dict:
        if not isinstance(body, dict) or not body: raise AppError("IDENTITY_INVALID", kind="channel")
        for kind, v in body.items():
            a = self.adapter(kind); v = v.strip() if isinstance(v, str) else v
            if v and (not isinstance(v, str) or not a.valid_identity(v)): raise AppError("IDENTITY_INVALID", kind=a.label)
            try: self.repo.set_identity(uid, kind, v or None)
            except IdentityTaken: raise AppError("IDENTITY_TAKEN", kind=a.label)
        return self.identities(uid)

    # ---- audit ----
    def _audit(self, owner, kind, action, r: Optional[ApprovalRequest] = None, code=None, actor=None, external=None, run_id=None, wid=None):
        try: self.repo.audit(ApprovalAudit(id=uuid.uuid4().hex[:12], owner=owner, request_id=r.id if r else None, run_id=r.run_id if r else run_id,
                                           workflow_id=r.workflow_id if r else wid, kind=kind, action=action, code=code, actor_id=actor,
                                           external_id=external, created=time.time()))
        except Exception: log.exception("writing an approval audit entry failed")

    def audit_log(self, uid: str) -> list[dict]:
        names, emails = {}, {}
        def name(wid):
            if wid and wid not in names: w = self.workflows.get(wid); names[wid] = w.name if w else None
            return names.get(wid)
        def email(u):
            if u and u not in emails: x = self.users.get_by_id(u); emails[u] = x.email if x else None
            return emails.get(u)
        return [{"id": e.id, "at": e.created, "kind": e.kind, "action": e.action, "code": e.code, "run_id": e.run_id, "workflow_id": e.workflow_id,
                 "workflow_name": name(e.workflow_id), "actor": email(e.actor_id), "external_id": e.external_id} for e in self.repo.audit_for(uid)]

    # ---- producer: a run paused at a Human node ----
    def on_waiting(self, rid: str, owner: str, wid: Optional[str], workflow: dict, ev: dict) -> None:
        node = next((n for n in workflow.get("nodes") or [] if n.get("id") == ev.get("node")), None)
        cfg = ((node or {}).get("data") or {}).get("approval") or {}
        kind, target = cfg.get("channel"), str(cfg.get("target") or "").strip()
        if not kind or not target or kind not in self.adapters: return  # this node does not use an external channel
        job = lambda: self._request(rid, owner, wid, node, cfg, kind, target, ev)  # noqa: E731
        threading.Thread(target=job, daemon=True).start() if self.background else job()

    def _request(self, rid, owner, wid, node, cfg, kind, target, ev) -> Optional[ApprovalRequest]:
        c = self.repo.channel_for(owner, kind)
        if c is None:
            self._audit(owner, kind, "not_configured", code="CHANNEL_NOT_FOUND", run_id=rid, wid=wid); return None
        approvers = [u.id for e in cfg.get("approvers") or [] if isinstance(e, str) and (u := self.users.get_by_email(e.strip().lower()))]
        r = self.repo.add_request(ApprovalRequest(id=uuid.uuid4().hex[:12], run_id=rid, node_id=node["id"], owner=owner, workflow_id=wid, channel_id=c.id,
                                                  kind=kind, target=target, approvers=json.dumps(approvers), nonce=pysecrets.token_hex(8),
                                                  expires=time.time() + config.approval_ttl(), status="pending", created=time.time()))
        w = self.workflows.get(wid) if wid else None
        lines = [f"Workflow: {w.name}" if w else None, f"Step: {ev.get('label') or node['id']}", ev.get("prompt") and f"Question: {ev['prompt']}",
                 f"Run: {rid}", f"Expires: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(r.expires))}"]
        link = f"{config.public_url()}/workflows/{wid}?run={rid}" if config.public_url() and wid else None
        msg = ApprovalMessage("Approval needed", [x for x in lines if x], link, self.token(r, "a"), self.token(r, "r"))
        try:
            ref = self.adapter(kind).send_request(self._secrets(c), target, msg)
            self.repo.set_ref(r.id, ref); self._audit(owner, kind, "requested", r)
        except AppError as e:
            self.repo.set_ref(r.id, None, "failed"); self._audit(owner, kind, "send_failed", r, code=e.code)
            log.warning("approval request for run %s via %s failed: %s", rid, kind, e.message)
        return r

    # ---- platform callback ----
    def handle_callback(self, kind: str, cid: str, headers: dict, body: bytes) -> dict:
        a = self.adapter(kind); c = self.repo.channel(cid)
        if c is None or c.kind != kind: raise AppError("CHANNEL_NOT_FOUND")
        sec = self._secrets(c)
        a.verify(sec, {k.lower(): v for k, v in headers.items()}, body)  # 401 CHANNEL_SIGNATURE_INVALID
        cb = a.handle_callback(body)
        if cb is None: return {"outcome": "ignored"}
        code, r, decision = self.decide(kind, cid, cb.token, cb.external_user)
        if code:
            a.acknowledge(sec, cb, CATALOG[code][1].format(kind=a.label), accepted=False)
            return {"outcome": "refused", "code": code}
        who = self.users.get_by_id(r.decided_by); text = f"{'✅ Approved' if decision == 'approved' else '❌ Rejected'} by {who.email if who else cb.external_user}"
        a.acknowledge(sec, cb, text, accepted=True)
        self._update(a, sec, r, f"{text} at {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
        return {"outcome": decision}

    def decide(self, kind, cid, token, external) -> tuple[Optional[str], Optional[ApprovalRequest], Optional[str]]:
        """Returns (refusal code, request, decision). Audits every attempt."""
        r, decision = self._parse(token)
        if r is None or r.channel_id != cid:
            log.warning("approval callback with an invalid token on channel %s", cid)
            return "APPROVAL_TOKEN_INVALID", None, None
        uid = self.repo.user_for(kind, external) if external else None
        def refuse(code):
            self._audit(r.owner, kind, "denied", r, code=code, actor=uid, external=external); return code, r, None
        if r.status != "pending": return refuse("APPROVAL_ALREADY_DECIDED")
        if time.time() > r.expires:
            if self.repo.decide(r.id, "expired"): self._audit(r.owner, kind, "expired", r)
            return refuse("APPROVAL_TOKEN_EXPIRED")
        if uid is None: return refuse("APPROVAL_IDENTITY_UNKNOWN")
        if uid != r.owner and uid not in json.loads(r.approvers or "[]"): return refuse("APPROVAL_FORBIDDEN")
        run = self.runs.get(r.run_id)
        if run is None or run.status != "waiting":
            self.repo.decide(r.id, "superseded"); return refuse("APPROVAL_ALREADY_DECIDED")
        if not self.repo.decide(r.id, decision, uid, external): return refuse("APPROVAL_ALREADY_DECIDED")  # lost the race: single use
        self._audit(r.owner, kind, decision, r, actor=uid, external=external)
        if self.enqueue: self.enqueue({"kind": "resume", "run_id": r.run_id, "owner": r.owner, "response": decision,
                                       "workflow_id": r.workflow_id, "approval_id": r.id, "by": {"channel": kind, "user_id": uid}})
        return None, self.repo.request(r.id), decision

    def _update(self, a: ApprovalChannel, sec: dict, r: ApprovalRequest, text: str) -> None:
        if not r.message_ref: return
        try: a.update(sec, json.loads(r.message_ref), text)
        except AppError as e: log.warning("updating the approval message of run %s failed: %s", r.run_id, e.message)

    # ---- the run went on without the channel (answered in the studio, cancelled, expired) ----
    def decided_elsewhere(self, rid: str) -> bool:
        """True when a channel decision for this run is already queued (the studio must not resume it a second time)."""
        return any(r.status in DECISIONS.values() for r in self.repo.requests_for_run(rid)) and \
            (run := self.runs.get(rid)) is not None and run.status == "waiting"

    def close_run(self, rid: str, reason: str) -> int:
        """Mark open requests of the run superseded/expired now (compare-and-set, so a late button press is refused) and
        edit their messages in the background. reason: answered | cancelled | expired | finished."""
        closed = []
        for r in self.repo.requests_for_run(rid, "pending"):
            action = "expired" if reason == "expired" else "superseded"
            if self.repo.decide(r.id, action): closed.append(r); self._audit(r.owner, r.kind, action, r)
        if closed:
            text = {"answered": "Answered in LangGraph Studio", "cancelled": "The run was cancelled", "expired": "The request expired"}.get(reason, "The run went on without this request")
            def edit():
                for r in closed:
                    c = self.repo.channel(r.channel_id)
                    if c is not None and r.kind in self.adapters: self._update(self.adapters[r.kind], self._secrets(c), r, text)
            threading.Thread(target=edit, daemon=True).start() if self.background else edit()
        return len(closed)
