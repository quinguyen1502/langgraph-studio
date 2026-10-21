# Task

## Metadata

- Project: superstep
- Task ID: TASK-0069
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Requirement IDs: REQ-0042
- Design IDs: none (UX direction set in REQ-0042)
- Architecture IDs: DEC-0009, DEC-0044

## Objective

Give every built-in template test cases that show what it is for and pass offline, copy them to workflows made from a
built-in template, and document workflow tests in the handbook.

## Scope

### In Scope

- **Built-in template cases.** Each template in `engine/templates.py` `BUILTINS` gets one to three test cases (input,
  Human answers, checks) that pass with the mock model, for example the leave request: "Approved leave" (answer
  approved, node `notify` ran, `decision` equals `approved`) and "Rejected leave". Cases on templates with a Human node
  cover both answers where the graph branches on them.
- **Copy on use.** Creating a workflow from a built-in template (`TemplateService`) copies its cases to the new
  workflow, within the case limit.
- **Saved templates carry no cases.** Saving a workflow as a template does not include its test cases (owner,
  2026-10-21); `sanitize` and the template format stay as they are.
- **Template test:** `tests/test_templates.py` runs every built-in template's cases in mock mode and expects them to
  pass, so a template change that breaks its own cases fails CI.
- **Handbook (en, vi):** a "Workflow tests" page: what a test case is, check kinds, Human answers, Run all, the mock
  option, what a test run does not send (e-mail, channel messages, notifications, callbacks) and what it still runs
  (tools, HTTP, MCP, Code), comparison with earlier versions, Run against version, Save as test case, permissions and
  limits. Screenshots from e2e like the other pages. The quickstart's "Next steps" links to it; the templates page
  says built-in templates come with test cases.

### Out Of Scope

- Test cases in templates users save (REQ-0042 out of scope).
- New templates.

## Inputs

- REQ-0042, TASK-0067 (cases and suite runs), TASK-0068 (comparison, Save as test case, for the docs).
- `backend/app/engine/templates.py` (`BUILTINS`), `services/template_service.py` (use template), `tests/test_templates.py`.
- Handbook: `handbook/docs/{en,vi}/`, `frontend/e2e/handbook.spec.ts` (screenshots), `check_images.py`.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0042-workflow-tests.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0044
- Discovery: built-in templates run offline with the mock model (`test_new_builtins_run_offline`).
- Clarifications: none

## Expected Outputs

- Test cases on every built-in template; copy on use
- Template test that runs them
- Handbook page (en, vi) with screenshots; quickstart and templates page links

## Implementation Notes

- Keep template cases next to the template definition in `engine/templates.py`, in the same JSON shape the API uses.
- Mock answers are deterministic (`mock_llm`): write checks on branches, statuses and fields the mock fills
  predictably, not on free LLM text.

## Constraints

- en and vi handbook pages identical in structure (CI checks it); both strict builds and the image check pass.
- SQLite and Postgres. Mock mode works offline.

## Dependencies

- TASK-0067 and TASK-0068.

## Acceptance Criteria

- Every built-in template has one to three test cases, and they all pass in mock mode (`tests/test_templates.py`).
- A workflow made from a built-in template has its cases; a template saved by a user has none.
- The handbook "Workflow tests" page (en, vi) covers the scope above, with screenshots; both builds and the image check
  pass.
- pytest (SQLite and Postgres), `npm run build`, lint, vitest and e2e pass.

## Validation Plan

- pytest: template cases pass offline; copy on use; saved template without cases.
- E2E: create a workflow from a template, open Tests, Run all, all pass; handbook screenshots.
- Handbook builds (en, vi) and `check_images.py`.

## Assumptions

- One to three cases per template is enough to show its purpose.

## Open Questions

- None.

## Activity Log

- 2026-10-21: planned from REQ-0042.

## Handoff Notes
