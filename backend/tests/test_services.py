"""Service unit tests with in-memory fake repositories (no DB, no HTTP)."""
import asyncio, json
from types import SimpleNamespace as NS
import pytest
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound, Unauthorized
from app.services.auth_service import AuthService
from app.services.run_service import RunService
from app.services.workflow_service import WorkflowService


class FakeWorkflows:
    def __init__(self): self.rows = {}
    def list_for_owner(self, o): return sorted([r for r in self.rows.values() if r.owner == o], key=lambda r: -r.updated)
    def get(self, wid): return self.rows.get(wid)
    def get_owned(self, wid, o): r = self.rows.get(wid); return r if r and r.owner == o else None
    def names_for_owner(self, o, exclude=None): return {r.name for r in self.rows.values() if r.owner == o and r.id != exclude}
    def save(self, wid, name, data, updated, owner): self.rows[wid] = NS(id=wid, name=name, data=data, updated=updated, owner=owner)
    def update_name(self, wid, name, data, updated): self.rows[wid].__dict__.update(name=name, data=data, updated=updated)
    def delete(self, wid): self.rows.pop(wid, None)
    def exists(self, wid): return wid in self.rows
    def adopt_unowned(self, o): pass

class FakeRuns:
    def __init__(self): self.rows = []
    def add(self, r): self.rows.append(r)
    def last_for_workflow(self, wid): rs = [r for r in self.rows if r.workflow_id == wid]; return max(rs, key=lambda r: r.started) if rs else None
    def list_for_workflow(self, wid, limit=50): return [r for r in self.rows if r.workflow_id == wid][:limit]
    def delete_for_workflow(self, wid): self.rows = [r for r in self.rows if r.workflow_id != wid]

class FakeUsers:
    def __init__(self): self.rows = {}
    def get_by_email(self, e): return self.rows.get(e)
    def add(self, uid, email, pw, created): self.rows[email] = NS(id=uid, email=email, password=pw, created=created)


@pytest.fixture
def svc():
    wf, runs = FakeWorkflows(), FakeRuns()
    return NS(wf=wf, runs=runs, workflows=WorkflowService(wf, runs), runner=RunService(wf, runs))


def test_workflow_crud_naming_and_ownership(svc):
    s = svc.workflows
    a = s.save({"name": "  Flow   A ", "nodes": [], "edges": []}, "u1")
    b = s.save({"name": "Flow A"}, "u1")
    assert s.get(a["id"], "u1")["name"] == "Flow A" and s.get(b["id"], "u1")["name"] == "Flow A (copy)"
    with pytest.raises(NotFound): s.get(a["id"], "u2")
    with pytest.raises(Forbidden): s.save({"id": a["id"], "name": "x"}, "u2")
    with pytest.raises(Conflict): s.rename(b["id"], "Flow A", "u1")
    with pytest.raises(BadRequest): s.rename(b["id"], "   ", "u1")
    assert s.duplicate(a["id"], "u1")["name"] == "Flow A (copy 2)"
    s.delete(a["id"], "u1"); assert len(s.list("u1")) == 2


def test_save_keeps_server_source_and_ignores_client_source(svc):
    svc.wf.save("imp", "Imp", json.dumps({"name": "Imp", "source": {"kind": "langgraph_import"}}), 1, "u1")
    out = svc.workflows.save({"id": "imp", "name": "Imp", "source": {"kind": "evil"}}, "u1")
    assert out["errors"] == [] and json.loads(svc.wf.rows["imp"].data)["source"]["kind"] == "langgraph_import"
    fresh = svc.workflows.save({"name": "N", "source": {"kind": "langgraph_import"}}, "u1")
    assert "source" not in json.loads(svc.wf.rows[fresh["id"]].data)


def test_list_includes_last_run(svc):
    wid = svc.workflows.seed_example("u1")
    svc.runner.record("r1", wid, {}, [{"type": "run_started"}], {"x": 1}, "ok", 5.0)
    [row] = svc.workflows.list("u1")
    assert row["last_run_status"] == "ok" and row["last_run_at"] == 5.0 and row["node_count"] > 0
    assert svc.runner.history(wid, "u1")[0]["final_state"] == {"x": 1}
    with pytest.raises(NotFound): svc.runner.history(wid, "u2")


def test_auth_register_login(svc):
    users = FakeUsers(); a = AuthService(users, svc.workflows)
    out = a.register(" Bob@Example.com ", "abc12345")
    assert out["user"]["email"] == "bob@example.com" and svc.workflows.list(out["user"]["id"])  # example seeded
    with pytest.raises(Conflict): a.register("bob@example.com", "abc12345")
    with pytest.raises(BadRequest): a.register("nope", "abc12345")
    with pytest.raises(BadRequest): a.register("c@d.ef", "short")
    assert AuthService.user_from_token(a.login("BOB@example.com", "abc12345")["token"])["email"] == "bob@example.com"
    with pytest.raises(Unauthorized): a.login("bob@example.com", "wrong999")
    with pytest.raises(Unauthorized): AuthService.user_from_token(None)


def test_run_plan_rejections(svc):
    p = svc.runner.plan
    with pytest.raises(BadRequest): p("u1", [1])
    with pytest.raises(NotFound): p("u1", {"workflow_id": "missing"})
    with pytest.raises(BadRequest): p("u1", {"input": "x"})
    with pytest.raises(BadRequest): p("u1", {"workflow": "x"})


def test_run_execute_records_history(svc):
    wid = svc.workflows.seed_example("u1")
    plan = svc.runner.plan("u1", {"workflow_id": wid, "input": {"message": "where is my order 123"}})
    sent = []
    async def send(ev): sent.append(ev); return True
    async def listen(): await asyncio.sleep(3600)
    assert asyncio.run(svc.runner.execute(plan, send, listen)) == "ok"
    assert sent[0]["type"] == "run_started" and sent[-1]["type"] == "run_finished"
    [r] = svc.runs.rows; assert r.status == "ok" and r.workflow_id == wid


def test_run_execute_cancel(svc):
    plan = svc.runner.plan("u1", {"workflow": {"name": "x"}, "input": {}})
    async def send(ev): return True
    async def listen(): return "cancelled"
    status = asyncio.run(svc.runner.execute(plan, send, listen))
    assert status in ("cancelled", "error") and svc.runs.rows[0].workflow_id == "adhoc"
