# Task

## Metadata

- Project: superstep
- Task ID: TASK-0067
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Requirement IDs: REQ-0042
- Design IDs: none (UX direction set in REQ-0042)
- Architecture IDs: DEC-0009, DEC-0013, DEC-0023, DEC-0036, DEC-0044 (new, this task)

## Objective

Let a workflow keep test cases (input, Human answers, checks) and run them, one or all, against the current version,
with pass / fail per check, and with no e-mail, channel message, notification or callback sent by a test run.

## Scope

### In Scope

- **Data** (models + Alembic migration):
  - `workflow_tests`: id, workflow id, name, input (JSON), human answers (JSON: node id -> list of answers), checks
    (JSON), position, created / updated, author;
  - `test_suite_runs`: id, workflow id, workflow version, who, started / ended, status (`running` | `done` |
    `cancelled`), mock model flag, passed / failed counts;
  - `test_case_results`: suite run id, test id, run id, status (`queued` | `running` | `passed` | `failed` | `error`),
    per-check results (JSON: check, expected, actual, passed, reason).
- **Checks** (pure functions in `engine/`, unit-tested): run status is `ok` | `error` | `waiting`; state field equals,
  contains, does not contain, matches regex, is empty, is not empty; node ran / did not run (from the run's
  `node_finished` events); duration at most N s; cost at most $X (not evaluated when `cost_usd` is NULL). A check on a
  missing field or node fails with that reason. A run that ends in error marks the other checks "not evaluated".
  Validation of a case: known check kinds, a regex that compiles, numbers where numbers are needed.
- **Test run mode** (DEC-0044). A run with `source="test"`:
  - Email node: builds the message and records it in the trace and its output field (`{"sent": false, "test": true,
    "message": …}`) without connecting to SMTP;
  - Human node: no channel request, no waiting step in the inbox, no `run_waiting` notification; the suite resumes it
    with the next scripted answer for that node through the job queue; no answer left -> the case fails
    ("waited at <node> with no answer");
  - no `callback_url` delivery, no run notifications;
  - optional mock model: every LLM node uses `mock_llm` whatever credential is set.
  Tool, HTTP, MCP and Code nodes run as usual.
- **Suite runs** (`TestService`): run one case or all cases against the current saved version; each case is a queued
  run (`RunWorker`), at most `STUDIO_TEST_PARALLEL` (default 4) at a time per suite; one running suite per workflow
  (compare-and-set), a second is refused; cancel stops queued and running cases; a worker restart recovers queued test
  runs like other queued runs and the suite finishes.
- **Limits:** at most `STUDIO_TEST_CASES_MAX` (default 50) cases per workflow.
- **Permissions:** view the workflow -> list cases and results; edit the workflow -> create, change, delete and run.
  Runs use the workflow owner's resources (DEC-0023) and the same node policy as other runs.
- **API:** `GET/POST /api/workflows/{id}/tests`, `PUT/DELETE /api/workflows/{id}/tests/{tid}`,
  `POST /api/workflows/{id}/tests/run` (`{test_ids?, mock?}`), `GET /api/workflows/{id}/tests/runs/{sid}`,
  `POST /api/workflows/{id}/tests/runs/{sid}/cancel`. Shared envelope; new codes (e.g. `TEST_NOT_FOUND`,
  `TEST_SUITE_RUNNING`, `TEST_CASES_LIMIT`, `TEST_CHECK_INVALID`) in `CATALOG`, `docs/api-errors.md` and both locales.
- **Run history:** test runs are left out of the run history and the run panel by default; a "Tests" filter shows them.
- **UI:** a **Tests** tab next to the run panel in the editor (shadcn): list of cases with the last result; add / edit /
  duplicate / delete (delete uses `ConfirmDeleteDialog`); a case editor with input fields like the Run dialog, Human
  answers per Human node, and checks with field and node pickers; **Run all**, run one, cancel, "Use the offline mock
  model" switch; results per case with each check's expected and actual value and an "Open run" link. Viewers see it
  read-only.
- **Docs:** API reference (en, vi) for the new routes.

### Out Of Scope

- Comparison with earlier versions, Run against version, Save as test case, marking stale checks (TASK-0068).
- Test cases on built-in templates and the handbook page (TASK-0069).
- CI runs with an API token, scheduled suites, LLM-judged checks, faked tool calls (REQ-0042 out of scope).
- Imported LangGraph repositories: the Tests tab is hidden for them.

## Inputs

- REQ-0042.
- `backend/app/services/run_service.py` (`plan`, `plan_resume`, `record`: notifications and `approvals.on_waiting` on
  `waiting`, `settled`: callback), `run_worker.py` (`run_job`, `resume_job`), `job_queue.py`.
- `backend/app/engine/emails.py` (SMTP send), `engine/llm.py` (`mock_llm`), the run ports / resolver.
- `backend/app/services/schedule_service.py` (a service that queues runs: pattern to follow).
- `frontend/src/components/editor/editor-run-panel.tsx`, the Run dialog input fields, `human-panel.tsx`.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0042-workflow-tests.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009), `docs/ui-conventions.md` (DEC-0008)
- Decisions: DEC-0013 (human in the loop), DEC-0023 (run resources), DEC-0036 (job queue and worker), DEC-0044 (new:
  test runs and their side effects)
- Discovery: run sources today are `ui`, `api`, `schedule`; notifications and channel requests start from
  `RunService.record` when a run waits.
- Clarifications: none

## Expected Outputs

- Models, migration, repository, `TestService`, checks module, routes, error codes
- Test run mode in the engine and run service (e-mail dry run, no channel / notification / callback, mock model option)
- DEC-0044
- Tests panel UI and locales (en, vi); API docs (en, vi)
- Backend tests and e2e

## Implementation Notes

- Keep the engine unaware of suites: the run carries a `test` flag (and `mock`) in its plan / ports; the Email node and
  the LLM node read it. Everything else (Human answers, suite bookkeeping) lives in `TestService`.
- The suite reacts to a test run settling (`RunService.settled`) to record its result, queue the next case and resume a
  waiting test run with its next answer. Use compare-and-set on result rows so recovery never records a case twice.
- A suite runs on the saved version (not unsaved edits); the result stores that version number.

## Constraints

- Layers (DEC-0009); SQLAlchemy + Alembic, no raw SQL; `tests/test_layers.py` passes.
- No new process: the job queue and worker only.
- shadcn and theme tokens; en/vi keys identical; no UI text in components; delete confirmation by name (DEC-0025).
- SQLite and Postgres, with and without Redis. Mock mode works offline.

## Dependencies

- None. TASK-0068 and TASK-0069 build on this task.

## Acceptance Criteria

- Test cases with inputs, Human answers and every check type save, validate (bad regex, unknown kind) and reload.
- Run all and run one report pass / fail per case and per check, with expected and actual values and the run id.
- A waiting test run is resumed with its scripted answers in order; with no answer left the case fails with the reason.
- A test run sends no e-mail (with a configured SMTP credential), no channel message (with a connected channel), no
  notification and no callback; the trace and output show the e-mail it would have sent.
- The mock option runs every LLM node with the mock.
- One running suite per workflow; cancel stops it; limits apply; a recovered test run is recorded once.
- Viewers see cases and results and cannot change or run them; other users get `WORKFLOW_NOT_FOUND`.
- Test runs are hidden from the run history unless the "Tests" filter is on.
- pytest (SQLite and Postgres), `npm run build`, lint, vitest and e2e pass.

## Validation Plan

- pytest: every check kind (unit); case validation; suite with a Human node (approve, reject, text, no answer left);
  side effects with SMTP and a mocked Slack channel; mock option; one-suite-at-a-time and cancel; permissions; limits;
  recovery of a queued test run; history filter; `tests/test_api_envelope.py` for the new codes.
- E2E: add a case with a check, Run all, see pass; break the check, see fail with expected and actual.
- `docs/ui-conventions.md` checklist.

## Assumptions

- The defaults in REQ-0042 (50 cases, 4 in parallel, real models unless the mock option is on) stand.

## Open Questions

- None.

## Activity Log

- 2026-10-21: planned from REQ-0042.

## Handoff Notes
