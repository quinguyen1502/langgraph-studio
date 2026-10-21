"""Workflow tests (TASK-0067, REQ-0042, DEC-0044): saved test cases and the suite runs that check them.

A test case is an input, the answers to give at Human nodes (in order, per node) and checks (engine.checks). A suite
runs some or all cases against the workflow's saved version. Each case is an ordinary queued run with
`source="test"` and the job flag `test`, so the run sends no e-mail, channel message, notification or callback, and with
the suite's `mock` option every LLM node uses the offline mock. At most STUDIO_TEST_PARALLEL cases of a suite run at
once; when a test run settles (RunService.settled -> `on_settled`) the suite records it, or answers its Human node with
the next scripted answer, and starts the next case. One suite runs per workflow at a time.

Permissions: users who can view the workflow see its cases and results; users who can edit it change and run them.
"""
import json, time, uuid
from typing import Callable, Optional
from ..core import config, permissions as P
from ..core.errors import AppError
from ..core.logging import get_logger
from ..engine import checks as C
from ..engine.limits import size
from ..models import Run, WorkflowTest, WorkflowTestResult, WorkflowTestSuite
from ..repositories import RunRepository, WorkflowRepository, WorkflowTestRepository, WorkflowVersionRepository
from .job_queue import JobQueue
from .run_service import RESPONSE_MAX

log = get_logger("tests")
NAME_MAX = 120
ANSWERS_MAX = 20  # scripted answers per Human node
FINAL = ("passed", "failed", "cancelled")
RESUME_DELAY = 1.0  # seconds before a scripted Human answer resumes a test run


def _id() -> str: return uuid.uuid4().hex[:12]


class WorkflowTestService:
    def __init__(self, repo: WorkflowTestRepository, workflows: WorkflowRepository, runs: RunRepository, versions: WorkflowVersionRepository,
                 jobs: JobQueue, run_service: Callable[[], object], access=None):
        self.repo, self.workflows, self.runs, self.versions, self.jobs, self.access = repo, workflows, runs, versions, jobs, access
        self.run_service = run_service  # -> RunService: closes a test run that waits with no answer left, cancels running cases

    def _workflow(self, wid: str, uid: str, action: str = P.VIEW):
        if self.access is not None: return self.access.workflow(wid, uid, action)
        w = self.workflows.get_owned(wid, uid)
        if w is None: raise AppError("WORKFLOW_NOT_FOUND")
        return w

    def _editable(self, wid: str, uid: str):
        w = self._workflow(wid, uid, P.EDIT)
        if json.loads(w.data or "{}").get("source"): raise AppError("TEST_NOT_SUPPORTED")  # imported LangGraph repositories
        return w

    def _case(self, wid: str, tid: str) -> WorkflowTest:
        t = self.repo.get(tid)
        if t is None or t.workflow_id != wid: raise AppError("TEST_NOT_FOUND")
        return t

    # ---- views ----
    @staticmethod
    def public(t: WorkflowTest, last: Optional[WorkflowTestResult] = None) -> dict:
        return {"id": t.id, "name": t.name, "input": json.loads(t.input), "answers": json.loads(t.answers), "checks": json.loads(t.checks),
                "created": t.created, "updated": t.updated,
                "last": {"status": last.status, "suite_id": last.suite_id, "version": last.version, "ended": last.ended} if last else None}

    @staticmethod
    def public_suite(s: WorkflowTestSuite, results: Optional[list[WorkflowTestResult]] = None) -> dict:
        out = {"id": s.id, "workflow_id": s.workflow_id, "version": s.version, "status": s.status, "mock": s.mock, "total": s.total,
               "passed": s.passed, "failed": s.failed, "started": s.started, "ended": s.ended}
        if results is not None:
            out["results"] = []
            for r in results:
                case = json.loads(r.case); got = json.loads(r.checks) if r.checks else None
                out["results"].append({"id": r.id, "test_id": r.test_id, "name": r.name, "status": r.status, "run_id": r.run_id, "version": r.version,
                                       "reason": r.reason, "detail": r.detail, "ended": r.ended,
                                       "checks": [{**c, **(got[i] if got else {})} for i, c in enumerate(case["checks"])]})
        return out

    def list(self, wid: str, uid: str) -> dict:
        w = self._workflow(wid, uid)
        cases = self.repo.list_for_workflow(wid); last = self.repo.latest_results([t.id for t in cases])
        suites = self.repo.suites(wid)
        return {"items": [self.public(t, last.get(t.id)) for t in cases], "suites": [self.public_suite(s) for s in suites],
                "can_edit": (self.access is None or self.access.may(wid, uid, P.EDIT)) and not json.loads(w.data or "{}").get("source"),
                "limit": config.test_cases_max()}

    def suite(self, wid: str, sid: str, uid: str) -> dict:
        self._workflow(wid, uid); s = self.repo.suite(sid)
        if s is None or s.workflow_id != wid: raise AppError("TEST_SUITE_NOT_FOUND")
        return self.public_suite(s, self.repo.results(sid))

    # ---- test cases ----
    @staticmethod
    def _clean(body) -> dict:
        if not isinstance(body, dict): raise AppError("TEST_CASE_INVALID", reason="the body must be an object")
        name = body.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > NAME_MAX:
            raise AppError("TEST_CASE_INVALID", reason=f"the name must be 1-{NAME_MAX} characters")
        inp = body.get("input") if body.get("input") is not None else {}
        if not isinstance(inp, dict): raise AppError("RUN_INPUT_INVALID")
        if size(inp) > config.input_max(): raise AppError("RUN_INPUT_TOO_LARGE", max_kb=config.input_max() // 1024)
        answers = body.get("answers") if body.get("answers") is not None else {}
        if not isinstance(answers, dict) or any(not isinstance(k, str) or not isinstance(v, list) or len(v) > ANSWERS_MAX
                                                or any(not isinstance(a, str) or len(a) > RESPONSE_MAX for a in v) for k, v in answers.items()):
            raise AppError("TEST_CASE_INVALID", reason=f"answers must be text, at most {ANSWERS_MAX} per Human node")
        if (errs := C.errors(body.get("checks"))): raise AppError("TEST_CASE_INVALID", reason="; ".join(errs))
        return {"name": name.strip(), "input": json.dumps(inp, ensure_ascii=False), "answers": json.dumps({k: v for k, v in answers.items() if v}, ensure_ascii=False),
                "checks": json.dumps(body["checks"], ensure_ascii=False)}

    def create(self, wid: str, uid: str, body) -> dict:
        self._editable(wid, uid); v = self._clean(body)
        n = self.repo.count_for_workflow(wid)
        if n >= config.test_cases_max(): raise AppError("TEST_CASES_LIMIT", max=config.test_cases_max())
        now = time.time()
        return self.public(self.repo.add(WorkflowTest(id=_id(), workflow_id=wid, position=n, author=uid, created=now, updated=now, **v)))

    def update(self, wid: str, tid: str, uid: str, body) -> dict:
        self._editable(wid, uid); self._case(wid, tid)
        self.repo.set_fields(tid, updated=time.time(), **self._clean(body))
        return self.public(self.repo.get(tid))

    def delete(self, wid: str, tid: str, uid: str) -> dict:
        self._editable(wid, uid); self._case(wid, tid); self.repo.delete(tid)
        return {"ok": True}

    # ---- suite runs ----
    def run(self, wid: str, uid: str, body) -> dict:
        """Run the cases `test_ids` (all when omitted) on the saved version. TEST_SUITE_RUNNING while one runs."""
        self._editable(wid, uid); body = body if isinstance(body, dict) else {}
        cases = self.repo.list_for_workflow(wid); ids = body.get("test_ids")
        if ids is not None:
            if not isinstance(ids, list) or not ids or any(i not in {t.id for t in cases} for i in ids): raise AppError("TEST_NOT_FOUND")
            cases = [t for t in cases if t.id in ids]
        if not cases: raise AppError("TEST_NOT_FOUND")
        latest = self.versions.latest(wid); now = time.time()
        suite = WorkflowTestSuite(id=_id(), workflow_id=wid, version=latest.version if latest else None, owner=uid, status="running",
                                  mock=bool(body.get("mock")), total=len(cases), passed=0, failed=0, started=now)
        results = [WorkflowTestResult(id=_id(), suite_id=suite.id, test_id=t.id, name=t.name, position=i, status="queued",
                                      case=json.dumps({"input": json.loads(t.input), "answers": json.loads(t.answers), "checks": json.loads(t.checks)},
                                                      ensure_ascii=False)) for i, t in enumerate(cases)]
        if not self.repo.start_suite(suite, results): raise AppError("TEST_SUITE_RUNNING")
        self._advance(suite.id)
        return self.suite(wid, suite.id, uid)

    def cancel(self, wid: str, sid: str, uid: str) -> dict:
        self._editable(wid, uid); s = self.repo.suite(sid)
        if s is None or s.workflow_id != wid: raise AppError("TEST_SUITE_NOT_FOUND")
        rs = self.repo.results(sid); now = time.time()
        if self.repo.end_suite(sid, "cancelled", sum(r.status == "passed" for r in rs), sum(r.status == "failed" for r in rs), now):
            for r in rs:
                if r.status in FINAL or not self.repo.finish_result(r.id, "cancelled", now): continue
                if r.run_id:
                    try: self.run_service().cancel(r.run_id, s.owner)  # queued, running or waiting for its next answer
                    except AppError: pass  # already finished
        return self.suite(wid, sid, uid)

    def _advance(self, sid: str) -> None:
        """Start queued cases up to the parallel limit; end the suite once every case has a result."""
        s = self.repo.suite(sid)
        if s is None or s.status != "running": return
        rs = self.repo.results(sid); running = sum(r.status == "running" for r in rs)
        for r in rs:
            if r.status != "queued": continue
            if running >= config.test_parallel(): return
            if self._start(s, r): running += 1
        if running == 0 and all(r.status in FINAL for r in self.repo.results(sid)):
            rs = self.repo.results(sid)
            self.repo.end_suite(sid, "done", sum(r.status == "passed" for r in rs), sum(r.status == "failed" for r in rs), time.time())

    def _start(self, s: WorkflowTestSuite, r: WorkflowTestResult) -> bool:
        rid = uuid.uuid4().hex[:10]
        if not self.repo.claim_result(r.id, rid): return False
        inp = json.loads(r.case)["input"]
        self.runs.add(Run(id=rid, workflow_id=s.workflow_id, input=json.dumps(inp, ensure_ascii=False), events="[]", status="queued",
                          started=time.time(), owner=s.owner, source="test"))
        self.jobs.enqueue({"run_id": rid, "workflow_id": s.workflow_id, "owner": s.owner, "input": inp, "callback_url": None, "token_id": None,
                           "source": "test", "test": {"mock": bool(s.mock)}})
        return True

    # ---- a test run settled (RunService.settled) ----
    def on_settled(self, rid: str) -> None:
        res = self.repo.result_for_run(rid)
        if res is None or res.status != "running": return
        run = self.runs.get(rid); s = self.repo.suite(res.suite_id)
        if run is None or s is None or run.status in ("queued", "running"): return
        case = json.loads(res.case); now = time.time()
        if s.status != "running": self.repo.finish_result(res.id, "cancelled", now); return
        if run.status == "waiting":
            events = json.loads(run.events or "[]")
            node = next((e.get("node") for e in reversed(events) if e.get("type") == "run_waiting"), None)
            used = sum(1 for e in events if e.get("type") == "run_resumed" and e.get("node") == node)
            answers = case["answers"].get(node) or []
            if used < len(answers):  # answer like a channel decision would; the worker's claim makes it happen once
                # a second later: this segment is still settling, and must leave the run bus before the next one joins it
                self.jobs.enqueue_at({"kind": "resume", "run_id": rid, "owner": run.owner, "response": answers[used], "workflow_id": run.workflow_id,
                                      "by": {"channel": "test"}, "test": {"mock": bool(s.mock)}}, now + RESUME_DELAY)
                return
            try: self.run_service().cancel_waiting(rid, run.owner)
            except AppError: pass
            self.repo.finish_result(res.id, "failed", now, version=run.workflow_version, reason="no_answer", detail=node)
        else:
            got = C.evaluate(case["checks"], {"status": run.status, "final_state": json.loads(run.final_state or "null"),
                                              "events": json.loads(run.events or "[]"), "duration_ms": run.duration_ms, "cost_usd": run.cost_usd},
                             self._graph(run))
            ok = C.passed(case["checks"], got, run.status or "error")
            self.repo.finish_result(res.id, "passed" if ok else "failed", now, version=run.workflow_version, checks=json.dumps(got, ensure_ascii=False),
                                    reason=None if ok or run.status == "ok" else "run_status", detail=None if run.status == "ok" else run.status)
        self._advance(s.id)

    def _graph(self, run: Run) -> dict:
        """The graph the test run ran: its stored version, else the workflow as it is now."""
        v = self.versions.get(run.workflow_id, run.workflow_version) if run.workflow_version else None
        if v is not None: return json.loads(v.data or "{}")
        w = self.workflows.get(run.workflow_id)
        return json.loads(w.data or "{}") if w else {}
