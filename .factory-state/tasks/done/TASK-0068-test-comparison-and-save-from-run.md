# Task

## Metadata

- Project: superstep
- Task ID: TASK-0068
- Status: done (PR #90, REV-0062, QA-0062)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Requirement IDs: REQ-0042
- Design IDs: none (UX direction set in REQ-0042)
- Architecture IDs: DEC-0009, DEC-0044

## Objective

Show whether a version behaves better or worse than an earlier one, let the author run the suite on an earlier
version, and turn a good run into a test case in one click.

## Scope

### In Scope

- **Comparison.** A suite result is compared with the latest finished suite run on an earlier version of the same
  workflow. Per case: **Regression** (passed before, fails now), **Fixed** (failed before, passes now), still failing,
  still passing, **New** (no earlier result). The suite header shows the counts and the version it was compared with.
  With no earlier result, the panel says so and offers **Run against version …**.
- **Run against version …** runs the suite on a stored earlier version (its snapshot from `workflow_versions`), with the
  same test run mode as TASK-0067. The result names that version. Only for users who can edit the workflow.
- **Suite history:** the last suite runs of the workflow (version, who, when, passed / failed), each one openable.
- **Save as test case** from a run in the run history or the run panel: a new case with the run's input, the Human
  answers it was given (from its `run_resumed` events, in order), and checks filled in: status equals the run's status,
  each node that ran "ran", and each output field of the final state "equals" its value (long values as "contains" the
  first 200 characters). The editor opens on the new case so the author removes what they do not need before saving.
  Allowed for users who can edit the workflow; hidden for imported LangGraph repositories.
- **Stale checks.** When the graph no longer has a field or a node a check names, the Tests panel marks the check, and
  the run fails it with that reason (as in TASK-0067).
- **API:** `GET /api/workflows/{id}/tests/runs` (history), the comparison in the suite run result,
  `POST /api/workflows/{id}/tests/run` accepts `version`, `POST /api/workflows/{id}/tests/from-run/{run_id}` returns a
  draft case (not saved). New error codes, if any, in `CATALOG`, `docs/api-errors.md` and both locales.
- **Docs:** API reference (en, vi) for the changed and new routes.

### Out Of Scope

- Text diff of two versions' outputs (REQ-0042 out of scope).
- Built-in template cases and the handbook page (TASK-0069).

## Inputs

- REQ-0042, TASK-0067 (tables, `TestService`, Tests panel).
- `backend/app/services/workflow_service.py` (`get_version`, `list_versions`), `run_service.py` (`plan`).
- `frontend/src/components/editor/editor-run-panel.tsx` (run history rows), the version history dialog.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0042-workflow-tests.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0044 (test runs, from TASK-0067)
- Discovery: a run stores the version that ran (`Run.workflow_version`); version snapshots are immutable.
- Clarifications: none

## Expected Outputs

- Comparison and suite history in the service, API and Tests panel
- Run against version
- Save as test case (API draft + UI in the run history and run panel)
- Stale check marking
- Locales (en, vi), API docs, tests

## Implementation Notes

- Compare by test id: a case edited after the earlier run is still the same case; a case created after it is **New**.
- Running an older version plans the run from that version's snapshot, as a saved run of the workflow (resources,
  policy and permissions of the workflow), tagged with that version number.
- Save as test case reads only what the user may already see in the run (owner or workflow access).

## Constraints

- Layers (DEC-0009); SQLAlchemy + Alembic if a column is needed; `tests/test_layers.py` passes.
- shadcn and theme tokens; new status colours as CSS variables (`--success`, `--warning`); en/vi keys identical; no UI
  text in components.
- SQLite and Postgres. Mock mode works offline.

## Dependencies

- TASK-0067.

## Acceptance Criteria

- A suite run on version N shows Regression, Fixed, still failing, still passing and New against the latest earlier
  suite run, with the version it was compared with.
- Run against version runs the stored snapshot and names that version in the result.
- Save as test case creates a draft with the run's input, its Human answers in order and the prefilled checks; saving it
  and running it passes on the same version.
- A check naming a removed node or field is marked in the panel and fails with that reason.
- Viewers see the comparison and history but cannot run against a version or save a case from a run.
- pytest (SQLite and Postgres), `npm run build`, lint, vitest and e2e pass.

## Validation Plan

- pytest: comparison states (including New and a case edited in between); run against an older version; draft from a
  run with and without Human answers; stale checks; permissions.
- E2E: save a case from a run, change the graph so it fails, see **Regression** against the previous version.
- `docs/ui-conventions.md` checklist.

## Assumptions

- Comparing pass / fail per case is enough; values are visible in each case's result.

## Open Questions

- None.

## Activity Log

- 2026-10-21: planned from REQ-0042.
- 2026-10-21: started after PR #89 merged, and implemented. DEC-0044 item 8 added. Review REV-0062, QA QA-0062.
- 2026-10-21: the owner reported the check result icons sitting off the text line; fixed. CI green on PR #90
  (Postgres included); the owner approved the merge.

## Handoff Notes

- Every test run plans from its suite's version snapshot (job `version`), including Run all on the latest version
  and a recovered test run that restarts.
- The comparison is computed on read against the newest finished suite run on a lower version, so running against
  an older version later changes what a newer suite is compared with.
- A draft from a run leaves out Start and End node checks and fields equal to the input; its name is `Run <id>`.
- TASK-0069 can give template cases the same shape as `POST …/tests/from-run/{run_id}` returns.
