"""Workflow CRUD with ownership, naming rules and validation."""
import json, time, uuid
from ..core.errors import AppError
from ..engine.examples import EXAMPLE
from ..engine.validator import validate
from ..models import Workflow
from ..repositories import RunRepository, WorkflowRepository
from .naming import clean_name, unique_name


def _dumps(d) -> str: return json.dumps(d, ensure_ascii=False)
def new_id() -> str: return uuid.uuid4().hex[:8]


class WorkflowService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository):
        self.repo, self.runs = workflows, runs

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
        self.repo.save(wid, wf.get("name", "Untitled"), _dumps(wf), time.time(), uid)
        return {"id": wid, "errors": [] if wf.get("source") else validate(wf)}

    def rename(self, wid: str, name: str, uid: str) -> dict:
        w = self.owned(wid, uid); name = clean_name(name)
        if name in self.repo.names_for_owner(uid, exclude=wid): raise AppError("WORKFLOW_NAME_TAKEN")
        d = json.loads(w.data or "{}"); d["name"] = name
        self.repo.update_name(wid, name, _dumps(d), time.time())
        return {"ok": True, "name": name}

    def duplicate(self, wid: str, uid: str) -> dict:
        w = self.owned(wid, uid); d = json.loads(w.data or "{}")
        d["name"] = unique_name(self.repo.names_for_owner(uid), w.name or "")
        nid = new_id(); self.repo.save(nid, d["name"], _dumps(d), time.time(), uid)
        return {"id": nid, "name": d["name"]}

    def delete(self, wid: str, uid: str) -> dict:
        self.owned(wid, uid); self.repo.delete(wid); self.runs.delete_for_workflow(wid)
        return {"ok": True}

    def create(self, wf: dict, uid: str) -> str:
        """Insert a workflow as-is (used by repo import finalize)."""
        wid = new_id(); self.repo.save(wid, wf["name"], _dumps(wf), time.time(), uid); return wid

    def seed_example(self, uid: str, wid: str | None = None) -> str:
        wid = wid or new_id(); self.repo.save(wid, EXAMPLE["name"], _dumps(EXAMPLE), time.time(), uid); return wid
