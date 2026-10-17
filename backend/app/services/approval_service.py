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
from ..core.errors import AppError
from ..core.logging import get_logger
from ..models import ApprovalAudit, ApprovalRequest
from ..repositories import ApprovalRepository, RunRepository, UserRepository, WorkflowRepository
from .approval_channels import ApprovalChannel, ApprovalMessage
from .approval_channels.messages import lang_of, text
from .channel_service import ChannelService

log = get_logger("approvals")
DECISIONS = {"a": "approved", "r": "rejected"}
BACKGROUND = True  # send/edit messages off the request thread; tests switch it off for determinism


class ApprovalService:
    def __init__(self, repo: ApprovalRepository, users: UserRepository, workflows: WorkflowRepository, runs: RunRepository, channels: ChannelService,
                 enqueue: Optional[Callable[[dict], None]] = None, background: Optional[bool] = None):
        self.repo, self.users, self.workflows, self.runs, self.channels, self.enqueue = repo, users, workflows, runs, channels, enqueue
        self.adapters = channels.adapters
        self.background = BACKGROUND if background is None else background

    def adapter(self, kind: str) -> ApprovalChannel: return self.channels.adapter(kind)
    def _lang(self, uid: Optional[str]) -> str: return lang_of(self.users.get_by_id(uid)) if uid else "en"
    def _secrets(self, c) -> dict: return self.channels.secrets(c)

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
        target = str(cfg.get("target") or "").strip()
        if not (cfg.get("channel_id") or cfg.get("channel")) or not target: return  # this node does not use an external channel
        job = lambda: self._request(rid, owner, wid, node, cfg, target, ev)  # noqa: E731
        threading.Thread(target=job, daemon=True).start() if self.background else job()

    def _request(self, rid, owner, wid, node, cfg, target, ev) -> Optional[ApprovalRequest]:
        c = self.channels.for_node(owner, cfg)
        if c is None:
            kind = cfg.get("channel") or (ch.kind if (ch := self.repo.channel(str(cfg.get("channel_id")))) else "channel")
            self._audit(owner, kind, "not_configured", code="CHANNEL_NOT_FOUND", run_id=rid, wid=wid); return None
        kind = c.kind
        approvers = [u.id for e in cfg.get("approvers") or [] if isinstance(e, str) and (u := self.users.get_by_email(e.strip().lower()))]
        r = self.repo.add_request(ApprovalRequest(id=uuid.uuid4().hex[:12], run_id=rid, node_id=node["id"], owner=owner, workflow_id=wid, channel_id=c.id,
                                                  kind=kind, target=target, approvers=json.dumps(approvers), nonce=pysecrets.token_hex(8),
                                                  expires=time.time() + config.approval_ttl(), status="pending", created=time.time()))
        w = self.workflows.get(wid) if wid else None; lang = self._lang(owner)
        lines = [w and text(lang, "workflow", v=w.name), text(lang, "step", v=ev.get("label") or node["id"]), ev.get("prompt") and text(lang, "question", v=ev["prompt"]),
                 text(lang, "run", v=rid), text(lang, "expires", v=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(r.expires)))]
        link = f"{config.public_url()}/workflows/{wid}?run={rid}" if config.public_url() and wid else None
        msg = ApprovalMessage(text(lang, "title"), [x for x in lines if x], link, self.token(r, "a"), self.token(r, "r"),
                              text(lang, "approve"), text(lang, "reject"), text(lang, "open"))
        try:
            ref = self.adapter(kind).send_request(self._secrets(c), target, msg)
            self.repo.set_ref(r.id, ref); self._audit(owner, kind, "requested", r)
        except AppError as e:
            self.repo.set_ref(r.id, None, "failed"); self._audit(owner, kind, "send_failed", r, code=e.code)
            log.warning("approval request for run %s via %s failed: %s", rid, kind, e.message)
        return r

    # ---- platform callback ----
    def _connection(self, a: ApprovalChannel, cid: Optional[str], headers: dict, body: bytes, cb) -> tuple:
        """The connection a callback authenticates against -> (row, secrets). Per-connection URL: that row. Shared URL
        (cid None): the rows of the claimed account (Slack team_id) whose secret verifies the signature; when several
        do (the same app connected twice), the one the button's request was sent through."""
        if cid is not None:
            c = self.repo.channel(cid)
            if c is None or c.kind != a.kind: raise AppError("CHANNEL_NOT_FOUND")
            sec = self._secrets(c); a.verify(sec, headers, body); return c, sec  # 401 CHANNEL_SIGNATURE_INVALID
        team = a.route_key(body) if a.shared_callback else None
        rows = self.repo.channels_by_team(a.kind, team) if team else []  # unknown team: same 401 as a bad signature
        ok = []
        for c in rows:
            sec = self._secrets(c)
            try: a.verify(sec, headers, body); ok.append((c, sec))
            except AppError: continue
        if not ok: raise AppError("CHANNEL_SIGNATURE_INVALID")
        want = (cb.token.split(".") + ["", ""])[1] if cb else ""
        req = self.repo.request(want) if want else None
        return next(((c, sec) for c, sec in ok if req is not None and c.id == req.channel_id), ok[0])

    def handle_callback(self, kind: str, cid: Optional[str], headers: dict, body: bytes) -> dict:
        """cid None = the shared callback URL of the kind (Slack: routed by team_id)."""
        a = self.adapter(kind); headers = {k.lower(): v for k, v in headers.items()}
        cb = a.handle_callback(body)  # parsing only; nothing is trusted before the signature check below
        c, sec = self._connection(a, cid, headers, body, cb)
        if cb is None: return {"outcome": "ignored"}
        code, r, decision = self.decide(kind, c.id, cb.token, cb.external_user)
        presser = self.repo.user_for(kind, cb.external_user) if cb.external_user else None
        mine = self._lang(presser or (r.owner if r else None))  # private answers: the presser's language, else the owner's
        if code:
            a.acknowledge(sec, cb, text(mine, code, kind=a.label), accepted=False)
            return {"outcome": "refused", "code": code}
        who = self.users.get_by_id(r.decided_by); name = who.email if who else cb.external_user
        key = "approved_by" if decision == "approved" else "rejected_by"
        a.acknowledge(sec, cb, text(mine, key, who=name), accepted=True)
        lang = self._lang(r.owner)  # the shared message: the owner's language, like the request
        self._update(a, sec, r, text(lang, "at", text=text(lang, key, who=name), when=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())))
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
            key = reason if reason in ("answered", "cancelled", "expired") else "finished"
            def edit():
                for r in closed:
                    c = self.repo.channel(r.channel_id)
                    if c is not None and r.kind in self.adapters: self._update(self.adapters[r.kind], self._secrets(c), r, text(self._lang(r.owner), key))
            threading.Thread(target=edit, daemon=True).start() if self.background else edit()
        return len(closed)
