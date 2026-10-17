"""Workflow CRUD with ownership, naming rules and validation."""
import json, time, uuid
from sqlalchemy.exc import IntegrityError
from ..core import config
from ..core.errors import AppError
from ..engine.examples import EXAMPLE
from ..engine.validator import validate
from ..models import Workflow, WorkflowVersion
from ..repositories import RunRepository, WorkflowRepository, WorkflowVersionRepository
from .workflow_diff import diff_workflows
from .naming import clean_name, unique_name


VERSION_RETRIES = 3
PAGE_MAX = 200


def _dumps(d) -> str: return json.dumps(d, ensure_ascii=False)
def new_id() -> str: return uuid.uuid4().hex[:8]


class WorkflowService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository, versions: WorkflowVersionRepository | None = None):
        self.repo, self.runs, self.versions = workflows, runs, versions

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
        return {"items": items, "total": repo.count(wid), "limit": limit, "offset": offset}

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
        w = self.owned(wid, uid); old = json.loads(self._version(wid, n).data or "{}")
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

    def owned(self, wid: str, uid: str) -> Workflow:
        w = self.repo.get_owned(wid, uid)
        if w is None: raise AppError("WORKFLOW_NOT_FOUND")
        return w

    def list(self, uid: str) -> list[dict]:
        out = []
        for w in self.repo.list_for_owner(uid):
            last = self.runs.last_for_workflow(w.id); d = json.loads(w.data or "{}")
            out.append({"id": w.id, "name": w.name, "updated": w.updated, "node_count": len(d.get("nodes", [])),
                        "last_run_status": last.status if last else None, "last_run_at": last.started if last else None})
        return out

    def get(self, wid: str, uid: str) -> dict:
        w = self.owned(wid, uid)
        return {"id": w.id, **json.loads(w.data or "{}")}

    def save(self, wf: dict, uid: str) -> dict:
        wid = wf.get("id") or new_id()
        wf = {k: v for k, v in wf.items() if k != "id"}
        ex = self.repo.get(wid)
        if ex and ex.owner != uid: raise AppError("WORKFLOW_FORBIDDEN")
        old = json.loads(ex.data or "{}") if ex else {}
        wf["name"] = clean_name(wf.get("name", "Untitled workflow"))
        if not ex: wf["name"] = unique_name(self.repo.names_for_owner(uid), wf["name"])
        wf.pop("source", None)  # never trust client-provided source metadata
        if old.get("source"): wf["source"] = old["source"]
        self._write(wid, wf.get("name", "Untitled"), wf, uid)
        return {"id": wid, "errors": [] if wf.get("source") else validate(wf)}

    def rename(self, wid: str, name: str, uid: str) -> dict:
        w = self.owned(wid, uid); name = clean_name(name)
        if name in self.repo.names_for_owner(uid, exclude=wid): raise AppError("WORKFLOW_NAME_TAKEN")
        d = json.loads(w.data or "{}"); d["name"] = name
        self._write(wid, name, d, uid, new=False)
        return {"ok": True, "name": name}

    def duplicate(self, wid: str, uid: str) -> dict:
        w = self.owned(wid, uid); d = json.loads(w.data or "{}")
        d["name"] = unique_name(self.repo.names_for_owner(uid), w.name or "")
        nid = new_id(); self._write(nid, d["name"], d, uid)
        return {"id": nid, "name": d["name"]}

    def delete(self, wid: str, uid: str) -> dict:
        self.owned(wid, uid); self.repo.delete(wid); self.runs.delete_for_workflow(wid)
        if self.versions is not None: self.versions.delete_for_workflow(wid)
        return {"ok": True}

    def create(self, wf: dict, uid: str) -> str:
        """Insert a workflow as-is (used by repo import finalize)."""
        wid = new_id(); self._write(wid, wf["name"], wf, uid); return wid

    def seed_example(self, uid: str, wid: str | None = None) -> str:
        wid = wid or new_id(); self._write(wid, EXAMPLE["name"], dict(EXAMPLE), uid); return wid
