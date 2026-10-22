# Requirement

## Metadata

- Project: superstep
- Requirement ID: REQ-0042
- Status: Implemented (TASK-0067 PR #89, TASK-0068 PR #90, TASK-0069 PR #91)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-22
- Source: owner request in chat, 2026-10-21. After REQ-0041 (proposals 1 and 2), the owner asked to continue with the
  feature proposals. This is proposal 3: saved test cases for a workflow, run all at once after each edit and compared
  with the previous version.

## Summary

- A workflow can have **test cases**. Each test case has an input, the answers to give at Human nodes, and **checks**,
  for example "the output contains …", "the run went through the approved branch" or "the run took less than 30 s".
- **Run all** runs every test case against the current version and shows which cases pass and which fail, with the
  expected and actual value of each check.
- The result is **compared with the last result on an earlier version**, so a regression shows at a glance: cases that
  passed before and fail now.
- **Save as test case** from a run in the history turns a good run into a test case in one click.

## Problem Or Opportunity

- The vision names debugging agents as a main goal. Today an author checks a change by running the workflow by hand
  with one input at a time and reading the trace. Nothing remembers which inputs mattered or what the right result was.
- A prompt or routing change can break a case that worked last week, and nobody sees it until a real run goes wrong.
  Versioning (REQ-0005) keeps every graph, but there is no way to tell whether a version behaves better or worse.
- The 12 built-in templates have no example inputs that show what each one is for and prove they still work.

## Scope

### In Scope

- **Test cases on a workflow** (stored with the workflow, not inside the graph JSON, so editing a test does not create a
  new workflow version):
  - name and input (the Start fields, as in the Run dialog);
  - Human node answers: for each Human node, the answers to give in order (Approve, Reject or a text reply). A run that
    waits at a Human node with no answer left fails that case with a clear message;
  - checks, all of which must pass:
    - run status is `ok`, `error` or `waiting`;
    - a state field equals, contains, does not contain or matches a pattern (regex), or is empty or not empty;
    - a node ran, or did not run (this is how a branch is checked);
    - the run took at most N seconds; the run cost at most $X (only when the models have a known price).
- **Tests panel** in the editor, next to the run panel: list, add, edit, duplicate and delete test cases; **Run all** and
  run one; cancel a suite run.
- **Running.** Each test case is a normal run with the source `test`, tagged with the workflow version, queued through
  the job queue like API and scheduled runs, a few at a time. Runs use the workflow owner's resources, as other runs do
  (DEC-0023).
- **Side effects of a test run.** A test run does not send e-mail (the Email node records the message it would have
  sent, in the trace and in its output field), does not send approval channel messages or notifications, and does not
  call the API callback URL. Tool, HTTP, MCP and Code nodes run for real; the handbook says so.
- **Model.** By default a test run uses the models the workflow is set up with. A suite option "Use the offline mock
  model" runs every LLM node with the mock: free and the same every time, useful for checking branches and structure.
- **Results:**
  - per case: pass or fail, each check with expected and actual value, duration, cost, and a link to the run trace;
  - per suite run: version, who ran it, when, passed / failed counts;
  - **comparison** with the latest suite run on an earlier version: newly failing (regression), newly passing, still
    failing, and cases added since;
  - **Run against version …** runs the suite on an earlier version (from its stored snapshot) to get a baseline.
- **Save as test case** from a run in the history or the run panel: the input and the Human answers of that run, with
  checks filled in from it (status, nodes that ran, output fields equal to their value). The author edits them.
- **Run history.** Test runs are hidden from the run history by default, with a "Tests" filter to show them.
- **Validation.** A check that names a state field or a node that no longer exists is marked in the panel, and the case
  fails with that reason instead of an unclear error.
- **Built-in templates** come with one to three test cases each that pass offline with the mock model. A workflow made
  from a built-in template gets a copy of them. A template a user saves does not carry test cases.
- **Permissions.** Users who can view the workflow see its test cases and results. Users who can edit it add, change and
  run them (a run can cost model credits).
- **API.** Routes for test cases and suite runs (create, list, run, result), with the shared envelope and new error codes
  in the catalogue, `docs/api-errors.md` and both locales.
- **Docs.** A handbook page (en, vi) on workflow tests, with screenshots. The quickstart mentions it in "Next steps".

### Out Of Scope

- Checks judged by an LLM ("the answer is polite"), similarity scores, or datasets of hundreds of inputs (evaluation).
- Running a suite on a schedule or on every save.
- Running a suite from CI with a workflow API token (the owner chose later, 2026-10-21).
- Test cases in templates that users save: a saved template does not carry the workflow's test cases, since their
  inputs may hold personal data, as approvers and escalation addresses are dropped today (owner, 2026-10-21).
- Faking a tool, HTTP, MCP or Code node with a canned response.
- Tests for imported LangGraph repositories (`source.kind == "langgraph_import"`).
- Checks inside a subgraph: a Subgraph node is checked as one node, by its output fields.
- Comparing the text of two versions' outputs side by side (only pass / fail per check is compared).

## Stakeholders Or Users

- Workflow authors who change prompts, routing or models and want to know nothing broke.
- People learning LangGraph, who see what each template is meant to do through its test cases.
- Reviewers of a workflow change, who read the suite result of the new version.

## Current Context

- Versions: `models/workflow_version.py`, `WorkflowService.list_versions / get_version / diff_versions /
  restore_version` (REQ-0005, TASK-0008). A run stores the version that ran (`Run.workflow_version`).
- Runs: `models/run.py` (`input`, `events`, `final_state`, `status`, `duration_ms`, `cost_usd`, `source` = `ui` | `api`
  | `schedule`). `RunService.plan` and `execute`; queued runs go through `JobQueue` and `RunWorker` (API, schedules).
- Human node: waits with status `waiting`; `RunService.plan_resume` continues with an answer (REQ-0003, DEC-0013).
  Channel requests and inbox: `ApprovalService.on_waiting`, REQ-0041, DEC-0043.
- Email node: `engine/emails.py` sends through the SMTP credential (REQ-0037).
- Mock model: `engine/llm.py` `mock_llm`, deterministic; `config.llm_mode()`.
- Run one step and Test with sample state: REQ-0024, TASK-0055 (Code node).
- Templates: `engine/templates.py` (`BUILTINS`, `sanitize`), `services/template_service.py` (REQ-0015, REQ-0040).
- Run history UI: `frontend/src/components/editor/editor-run-panel.tsx`.

## Desired Behavior

- An author opens the Leave request workflow and its **Tests** tab: three test cases from the template, "Approved
  leave", "Rejected leave" and "Missing dates". They click **Run all**: 3 passed, in a few seconds, with the mock model.
- They change the extract prompt and save (version 8). **Run all** shows 2 passed, 1 failed, marked **Regression**
  against version 7: the "Missing dates" check "details contains 'dates'" failed, expected "dates", actual "…". The
  author opens the run trace from the row.
- From a real run that went well, the author clicks **Save as test case**, keeps the checks "status is ok" and "node
  notify ran", and names it.
- A test case with an Email node passes without any e-mail being sent; the trace shows the message it would have sent.

## Business Rules

- A test run never sends e-mail, approval channel messages, notifications or callbacks, whatever the workflow is set up
  with.
- A test case runs against one version; the result always names that version.
- One suite run at a time per workflow; a second **Run all** is refused until the first ends or is cancelled.
- Test cases run as the workflow owner's resources, with the same org policy and node permissions as other runs.
- Deleting a workflow deletes its test cases and suite results; the test runs follow the existing run retention.

## Constraints

- Backend layers (DEC-0009): routers → services → repositories; SQLAlchemy models and an Alembic migration for new
  tables; no raw SQL. `tests/test_layers.py` passes.
- No new process: suite runs use the existing job queue and worker.
- The engine does not know about tests beyond a run option that turns off external sends (and the mock model option).
- shadcn components and theme tokens; en and vi locale keys identical; no UI text in components.
- SQLite and Postgres, with and without Redis. Everything works offline in mock mode.
- A limit on test cases per workflow (50 by default) and on parallel test runs (4 by default), configurable.

## Acceptance Criteria

- Test cases with inputs, Human answers and every check type save, validate and survive a reload.
- **Run all** runs every case against the current version and reports pass / fail per case and per check, with expected
  and actual values and a link to the run.
- A case that waits at a Human node uses its scripted answers; with no answer left it fails with a clear reason.
- A suite run on version N is compared with the latest suite run on an earlier version; regressions are marked.
- **Run against version …** runs the suite on a stored older version.
- **Save as test case** from a run creates a case with that run's input, Human answers and prefilled checks.
- Test runs send no e-mail, channel message, notification or callback (tested with a configured SMTP credential and a
  channel), and the trace shows the e-mail that would have been sent.
- The mock-model option runs every LLM node offline.
- Test runs are hidden from the run history unless the "Tests" filter is on.
- Viewers see test cases and results but cannot change or run them.
- Every built-in template has test cases that pass offline; a workflow made from a built-in template gets them; a
  template saved by a user carries none.
- Backend tests cover checks, Human answers, side effects, comparison, permissions and limits; e2e covers the Tests
  panel and Save as test case. The handbook pages (en, vi) build.

## Edge Cases

- The graph changes so a check names a node or field that no longer exists: the case fails with that reason.
- A run errors before any check: the status check reports it, the other checks are marked not evaluated.
- A run reaches the run time limit or is cancelled: the case fails with that status.
- A loop that passes a Human node several times: the answers are used in order.
- Two editors press **Run all** at the same time: one suite run starts, the other is refused.
- A suite run while the worker restarts: queued test runs recover like other queued runs, and the suite result
  completes.
- A regex check with an invalid pattern: reported when the case is saved.
- No earlier suite result exists: the comparison says so and offers **Run against version …**.

## Assumptions

- Test runs use the same run time limits and node policies as other runs.
- The cost check uses the cost the run already records (`cost_usd`); with no known price, the check is reported as not
  evaluated, not as failed.
- The defaults above (50 cases, 4 in parallel) are acceptable.
- Test runs use the workflow's real models unless the mock option is on (owner, 2026-10-21).

## Open Questions

- None. The owner accepted the requirement on 2026-10-21: real models by default (mock as a suite option), CI runs
  later, and only built-in templates carry test cases.

## Related Artifacts

- REQ-0005 workflow versioning (TASK-0008), REQ-0024 run one step, REQ-0003 and DEC-0013 human in the loop
- REQ-0033 scheduled runs and DEC-0036 (job queue, worker), DEC-0023 (whose resources a run uses)
- REQ-0037 send e-mail node, REQ-0034 approval channels, REQ-0041 approval deadlines and inbox
- REQ-0015 and REQ-0040 templates
- `docs/backend-architecture.md` (DEC-0009), `docs/ui-conventions.md` (DEC-0008)
