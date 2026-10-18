"""Workflow CRUD with ownership, naming rules and validation."""
from __future__ import annotations
import json, time, uuid
from sqlalchemy.exc import IntegrityError
from ..core import config
from ..core import permissions as P
from ..core.errors import AppError
from ..engine import subgraphs
from ..engine.examples import EXAMPLE
from ..models import Workflow, WorkflowVersion
from ..repositories import RunRepository, WorkflowRepository, WorkflowVersionRepository
from .workflow_diff import diff_workflows
from .naming import clean_name, unique_name


VERSION_RETRIES = 3
PAGE_MAX = 200
READ_ONLY = ("id", "access", "mine", "owner_email")  # response-only fields, never stored


def _dumps(d) -> str: return json.dumps(d, ensure_ascii=False)
def new_id() -> str: return uuid.uuid4().hex[:8]


class WorkflowService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository, versions: WorkflowVersionRepository | None = None,
                 access=None, shares=None, users=None, teams=None, audit=None):
        self.repo, self.runs, self.versions = workflows, runs, versions
        self.access, self.shares, self.users = access, shares, users
        self.teams, self.audit = teams, audit  # TeamRepository, AuditService (TASK-0029)  # AccessService etc. (TASK-0014); None = owner-only

    # -- persistence: every write goes through here so versions stay in sync (TASK-0008) --
    def _write(self, wid: str, name: str, wf: dict, uid: str, *, new: bool = True, note: str | None = None) -> None:
        data, now = _dumps(wf), time.time()
        if new: self.repo.save(wid, name, data, now, uid)
        else: self.repo.update_name(wid, name, data, now)
        if self.versions is None: return
        last = self.versions.latest(wid)
        if last is not None and last.data == data: return  # nothing changed: no new version
        for attempt in range(VERSION_RETRIES):  # two concurrent saves can pick the same number: retry with the next one
            n = self.versions.next_number(wid)
            try:
                self.versions.add(WorkflowVersion(id=f"{wid}-v{n}", workflow_id=wid, version=n, name=name, data=data,
                                                  author=uid, created=now, note=note)); break
            except IntegrityError:
                if attempt + 1 == VERSION_RETRIES: raise
        if (keep := config.version_keep()): self.versions.prune(wid, keep)  # retention (runs keep their versions)

    def write_as(self, wid: str, name: str, wf: dict, uid: str, note: str | None = None) -> None:
        """A versioned in-place write by another service (ownership transfer); the owner column is untouched."""
        self._write(wid, name, wf, uid, new=False, note=note)

    def _versions(self) -> WorkflowVersionRepository:
        if self.versions is None: raise RuntimeError("versioning not configured")
        return self.versions

    def _version(self, wid: str, n: int) -> WorkflowVersion:
        v = self._versions().get(wid, n)
        if v is None: raise AppError("VERSION_NOT_FOUND")
        return v

    def list_versions(self, wid: str, uid: str, limit: int = 50, offset: int = 0) -> dict:
        """One page, newest first: {items, total, limit, offset}."""
        self.owned(wid, uid); repo = self._versions()
        limit, offset = max(1, min(PAGE_MAX, int(limit))), max(0, int(offset))
        latest = repo.latest(wid); rows = repo.list_with_authors(wid, limit, offset)
        latest = latest.version if latest else None
        items = [{"version": v.version, "name": v.name, "created": v.created, "author_email": e, "note": v.note,
                 "node_count": len(json.loads(v.data or "{}").get("nodes", [])), "current": v.version == latest} for v, e in rows]
        return {"items": items, "total": repo.count(wid), "limit": limit, "offset": offset, "children_changed": self.children_changed(wid, uid)}

    def children_changed(self, wid: str, uid: str) -> list[dict]:
        """Subgraph children saved after this workflow's latest version (their changes apply to its next runs)."""
        if self.versions is None: return []
        w = self.repo.get(wid); mine = self.versions.latest(wid)
        if w is None or mine is None: return []
        out = []
        for _, ref in subgraphs.refs(json.loads(w.data or "{}")):
            c = self.versions.latest(ref) if ref else None
            if c is not None and c.created > mine.created and (self.access is None or self.access.may(ref, uid)):
                out.append({"id": ref, "name": c.name, "version": c.version, "at": c.created})
        return out

    def get_version(self, wid: str, n: int, uid: str) -> dict:
        self.owned(wid, uid); v = self._version(wid, n)
        return {"version": v.version, "created": v.created, "note": v.note, "workflow": {"id": wid, **json.loads(v.data or "{}")}}

    def diff_versions(self, wid: str, a: int, b: int, uid: str) -> dict:
        self.owned(wid, uid)
        va, vb = self._version(wid, a), self._version(wid, b)
        return {"a": a, "b": b, **diff_workflows(json.loads(va.data or "{}"), json.loads(vb.data or "{}"))}

    def restore_version(self, wid: str, n: int, uid: str) -> dict:
        """Copy version n's graph into the workflow as a NEW latest version (history is never rewritten).
        The current name is kept so restoring can't collide with another workflow's name."""
        w = self.owned(wid, uid, P.EDIT); old = json.loads(self._version(wid, n).data or "{}")
        cur = json.loads(w.data or "{}")
        wf = {**old, "name": w.name}
        if cur.get("source"): wf["source"] = cur["source"]
        before = self._versions().latest(wid)
        self._write(wid, w.name, wf, uid, new=False, note=f"Restored from v{n}")
        after = self._versions().latest(wid)
        # restoring content identical to the current version is a no-op: no new version (the UI says so)
        return {"id": wid, "version": after.version, "unchanged": before is not None and after.id == before.id, "workflow": {"id": wid, **wf}}

    def current_version(self, wid: str) -> tuple[int, dict] | None:
        """(number, data) of the latest stored version, used to tag runs."""
        if self.versions is None: return None
        v = self.versions.latest(wid)
        return (v.version, json.loads(v.data or "{}")) if v else None

    def owned(self, wid: str, uid: str, action: str = P.VIEW) -> Workflow:
        """The workflow if `uid` may perform `action` on it (owner, share or admin, TASK-0014)."""
        if self.access is not None: return self.access.workflow(wid, uid, action)
        w = self.repo.get_owned(wid, uid)
        if w is None: raise AppError("WORKFLOW_NOT_FOUND")
        return w

    def _require(self, uid: str, permission: str) -> None:
        if self.access is not None: self.access.require(uid, permission)

    def _emails(self, ids) -> dict[str, str]:
        return {i: u.email for i, u in self.users.by_ids(list(set(ids))).items()} if self.users is not None else {}

    def list(self, uid: str, all_: bool = False) -> list[dict]:
        """Own and shared workflows with the caller's access; `all_` lists every workflow for admins."""
        rows = self.access.visible(uid, all_) if self.access is not None else [(w, "owner") for w in self.repo.list_for_owner(uid)]
        emails = self._emails(w.owner for w, _ in rows)
        out = []
        for w, acc in rows:
            last = self.runs.last_for_workflow(w.id); d = json.loads(w.data or "{}")
            out.append({"id": w.id, "name": w.name, "updated": w.updated, "node_count": len(d.get("nodes", [])),
                        "last_run_status": last.status if last else None, "last_run_at": last.started if last else None,
                        "access": acc, "mine": w.owner == uid, "owner_email": emails.get(w.owner)})
        return out

    def get(self, wid: str, uid: str) -> dict:
        w = self.owned(wid, uid)
        acc = self.access.access_of(w, uid) if self.access is not None else "owner"
        return {"id": w.id, **json.loads(w.data or "{}"), "access": acc, "mine": w.owner == uid,
                "owner_email": self._emails([w.owner]).get(w.owner)}

    def save(self, wf: dict, uid: str) -> dict:
        wid = wf.get("id") or new_id()
        wf = {k: v for k, v in wf.items() if k not in READ_ONLY}
        ex = self.repo.get(wid)
        if ex:
            if self.access is not None: self.owned(wid, uid, P.EDIT)  # editors of a shared workflow save it in place
            elif ex.owner != uid: raise AppError("WORKFLOW_FORBIDDEN")
        else: self._require(uid, P.WORKFLOWS_CREATE)
        old = json.loads(ex.data or "{}") if ex else {}
        wf["name"] = clean_name(wf.get("name", "Untitled workflow"))
        if not ex: wf["name"] = unique_name(self.repo.names_for_owner(uid), wf["name"])
        wf.pop("source", None)  # never trust client-provided source metadata
        if old.get("source"): wf["source"] = old["source"]
        self._write(wid, wf.get("name", "Untitled"), wf, uid, new=not ex)  # the owner never changes
        return {"id": wid, "errors": [] if wf.get("source") else self.validate(wf, uid, wid)}

    def validate(self, wf: dict, uid: str, wid=None):
        """Static checks, with subgraph references resolved against this user's workflows (TASK-0011)."""
        return subgraphs.validate_with(wf, self._loader(uid), wid or wf.get("id"))

    def _loader(self, uid: str):
        """Subgraph references resolve to workflows this user can open (own, shared, any for admins; TASK-0014)."""
        def load(ref: str):
            if self.access is not None: row = self.repo.get(ref) if self.access.may(ref, uid) else None
            else: row = self.repo.get_owned(ref, uid)
            return json.loads(row.data or "{}") if row else None
        return load

    def rename(self, wid: str, name: str, uid: str) -> dict:
        w = self.owned(wid, uid, P.EDIT); name = clean_name(name)
        if name in self.repo.names_for_owner(w.owner, exclude=wid): raise AppError("WORKFLOW_NAME_TAKEN")
        d = json.loads(w.data or "{}"); d["name"] = name
        self._write(wid, name, d, uid, new=False)
        return {"ok": True, "name": name}

    def duplicate(self, wid: str, uid: str) -> dict:
        w = self.owned(wid, uid); self._require(uid, P.WORKFLOWS_CREATE); d = json.loads(w.data or "{}")
        d["name"] = unique_name(self.repo.names_for_owner(uid), w.name or "")
        nid = new_id(); self._write(nid, d["name"], d, uid)
        return {"id": nid, "name": d["name"]}

    def dependents(self, wid: str, uid: str) -> list[dict]:
        """Workflows that embed `wid` as a subgraph. Names are shown only where the caller has access (TASK-0029)."""
        out = []
        for w in self.repo.referencing(wid):
            if any(ref == wid for _, ref in subgraphs.refs(json.loads(w.data or "{}"))):
                vis = self.access is None or self.access.may(w.id, uid)
                out.append({"id": w.id if vis else None, "name": w.name if vis else None})
        return out

    def delete(self, wid: str, uid: str, force: bool = False) -> dict:
        """Refuses (WORKFLOW_IN_USE with the dependents) while other workflows embed this one, unless `force`."""
        w = self.owned(wid, uid, P.DELETE)
        deps = self.dependents(wid, uid)
        if deps and not force: raise AppError("WORKFLOW_IN_USE", details={"count": len(deps), "dependents": deps}, count=len(deps))
        self.repo.delete(wid); self.runs.delete_for_workflow(wid)
        if self.teams is not None: self.teams.delete_shares_for_workflow(wid)
        if self.audit is not None and (deps or w.owner != uid): self.audit.record(uid, "workflow.delete", "workflow", wid, w.name, dependents=len(deps))
        if self.shares is not None: self.shares.delete_for_workflow(wid)
        if self.versions is not None: self.versions.delete_for_workflow(wid)
        return {"ok": True}

    def create(self, wf: dict, uid: str) -> str:
        """Insert a workflow as-is (used by repo import finalize)."""
        self._require(uid, P.WORKFLOWS_CREATE); wid = new_id(); self._write(wid, wf["name"], wf, uid); return wid

    def seed_example(self, uid: str, wid: str | None = None) -> str:
        wid = wid or new_id(); self._write(wid, EXAMPLE["name"], dict(EXAMPLE), uid); return wid
