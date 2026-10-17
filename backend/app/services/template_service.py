"""Template library (TASK-0025, DEC-0028): list built-in + personal + org templates, save a workflow as a template,
import/export the portable file, start a workflow from a template, delete. Persistence via TemplateRepository; graph
sanitising and the file format live in engine.templates; new workflows go through WorkflowService.save (unique name)."""
from __future__ import annotations
import json, time, uuid
from ..core import permissions as P
from ..core.errors import AppError
from ..engine import templates as T
from ..models import WorkflowTemplate
from ..repositories import TemplateRepository
from .access import AccessService
from .workflow_service import WorkflowService

NAME_MAX, DESC_MAX = 120, 500


def _name(v) -> str:
    n = " ".join(str(v or "").split())
    if not n: raise AppError("TEMPLATE_NAME_REQUIRED")
    return n[:NAME_MAX]


class TemplateService:
    def __init__(self, repo: TemplateRepository, workflows: WorkflowService, access: AccessService):
        self.repo, self.workflows, self.access = repo, workflows, access

    # ---- views ----
    @staticmethod
    def _summary(tid, name, desc, scope, graph, *, mine=False, owner=None) -> dict:
        return {"id": tid, "name": name, "description": desc or "", "scope": scope, "mine": mine, "owner": owner,
                "nodes": [{"id": n["id"], "type": n["type"], "position": n.get("position") or {"x": 0, "y": 0}} for n in graph.get("nodes", [])],
                "edges": [{"source": e["source"], "target": e["target"]} for e in graph.get("edges", [])]}

    def _can_delete(self, t: WorkflowTemplate, uid: str) -> bool:
        return t.owner == uid if t.scope == "user" else self.access.can(uid, P.ORG_MANAGE)

    def list(self, uid: str) -> list[dict]:
        out = [self._summary(b["id"], b["name"], b["description"], "builtin", b["workflow"]) for b in T.BUILTINS]
        for t in self.repo.visible(uid):
            s = self._summary(t.id, t.name, t.description, t.scope, json.loads(t.data), mine=t.owner == uid, owner=t.owner)
            s["deletable"] = self._can_delete(t, uid); out.append(s)
        return out

    def _load(self, tid: str, uid: str) -> tuple[str, str, dict]:
        """(name, description, graph) of a template this user can see."""
        for b in T.BUILTINS:
            if b["id"] == tid: return b["name"], b["description"], b["workflow"]
        t = self.repo.get(tid)
        if t is None or (t.scope == "user" and t.owner != uid): raise AppError("TEMPLATE_NOT_FOUND")
        return t.name, t.description or "", json.loads(t.data)

    # ---- writes ----
    def _add(self, uid: str, name, description, scope: str, graph: dict) -> dict:
        if scope not in ("user", "org"): raise AppError("BAD_REQUEST")
        if scope == "org" and not self.access.can(uid, P.ORG_MANAGE): raise AppError("TEMPLATE_SCOPE_FORBIDDEN")
        now = time.time()
        t = WorkflowTemplate(id="tpl-" + uuid.uuid4().hex[:12], name=_name(name), description=(description or "").strip()[:DESC_MAX] or None,
                             scope=scope, owner=uid, data=json.dumps(T.sanitize(graph)), created=now, updated=now)
        self.repo.add(t)
        return {**self._summary(t.id, t.name, t.description, t.scope, json.loads(t.data), mine=True, owner=uid), "deletable": True}

    def save_from_workflow(self, uid: str, wid: str, name, description, scope: str = "user") -> dict:
        self.access.require(uid, P.WORKFLOWS_CREATE)
        return self._add(uid, name, description, scope, self.workflows.get(wid, uid))  # get() enforces view access

    def import_file(self, uid: str, payload, scope: str = "user") -> dict:
        self.access.require(uid, P.WORKFLOWS_CREATE)
        errs = T.problems(payload)
        if errs: raise AppError("TEMPLATE_INVALID", details=errs)
        return self._add(uid, payload.get("name"), payload.get("description"), scope, payload["workflow"])

    def export(self, tid: str, uid: str) -> dict:
        name, desc, graph = self._load(tid, uid); return T.export_payload(name, desc, graph)

    def use(self, tid: str, uid: str, name: str | None = None) -> dict:
        tname, _, graph = self._load(tid, uid)
        return self.workflows.save({**T.sanitize(graph), "name": name or tname}, uid)  # new id, unique name, WORKFLOWS_CREATE check

    def delete(self, tid: str, uid: str) -> dict:
        if tid in T.BUILTIN_IDS: raise AppError("TEMPLATE_READ_ONLY")
        t = self.repo.get(tid)
        if t is None or (t.scope == "user" and t.owner != uid): raise AppError("TEMPLATE_NOT_FOUND")
        if not self._can_delete(t, uid): raise AppError("TEMPLATE_READ_ONLY")
        self.repo.delete(tid); return {"ok": True}
