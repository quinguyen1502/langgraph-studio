# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0044
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Related Requirements: REQ-0042
- Related Architecture: DEC-0009 (layers), DEC-0013 (human in the loop), DEC-0023 (run resources), DEC-0036 (job queue
  and worker), DEC-0043 (waiting steps)
- Related Tasks: TASK-0067, TASK-0068, TASK-0069

## Context

REQ-0042 adds workflow test cases: an input, scripted answers for Human nodes and checks. A suite runs them after each
edit. A test run must behave like a real run so that it tests something, but it must not reach real people: no e-mail,
no approval channel message, no notification and no API callback. It also has to answer its own Human nodes without a
person, and the owner chose a per-suite option to run every LLM node with the offline mock.

## Decision

1. **A test run is an ordinary run with `source = "test"`.** It is queued through the job queue and executed by the
   run worker with `RunService.execute`, so it has the same validation, node policy, run time limit, resources of the
   workflow owner (DEC-0023), checkpoints, recovery and trace as any queued run. The run belongs to the user who started
   the suite.
2. **The queue job carries `test: {"mock": bool}`.** `RunService.apply_test` turns it into run-time ports flags. The
   flag is on every job of the run (first segment, resumes, recovered jobs), so no segment loses it.
3. **What a test run does not do:**
   - Send email nodes always do the existing dry run (`sent: false, dry_run: true` and the message preview), even with
     an SMTP credential; the hourly e-mail quota is not used;
   - no `run_waiting` / `run_expired` notification, no approval channel request and no waiting step in the Approvals
     inbox (`RunService.record` skips them for `source = "test"`);
   - no `callback_url` delivery: `RunService.settled` hands a test run to the suite instead.
   Tool (built-in, HTTP, Code), MCP and Retriever nodes run for real. The handbook says so.
4. **Mock option.** With `mock`, LLM and Decision nodes use the offline mocks (`mock_llm`, the JEV mock) whatever
   credential or environment key is set.
5. **Human answers.** When a test run settles as `waiting`, the suite queues a `resume` job with the next scripted
   answer for that node (`by: {"channel": "test"}`), the same path channel answers use; the worker's claim makes each
   resume happen once. With no answer left, the run is cancelled and the case fails with `no_answer`.
6. **Suites.** A suite stores a copy of each case as it ran and one result row per case; status changes are
   compare-and-set, and a partial unique index allows one running suite per workflow. At most `STUDIO_TEST_PARALLEL`
   cases of a suite run at once; each settled test run starts the next queued case.
7. **History.** Test runs are left out of the run history, the last-run column of the workflow list and the waiting
   list; `GET /api/workflows/{id}/runs?tests=true` lists them.

## Rationale

- Reusing the run path means a test checks the code that real runs use, and recovery, fencing and tracing come for
  free. A separate in-process executor would drift from it.
- Turning off sends at the edges (e-mail node, record, settled) keeps the engine unaware of suites: the engine only
  sees two port flags.
- Answering through the resume job keeps "first answer wins" and fencing unchanged.

## Alternatives Considered

- **Run test cases synchronously in the request.** Blocks the request for minutes with real models, and loses
  recovery. Rejected.
- **Fake every side-effect node.** Would hide real failures of tools the author wants to test; faking tool responses
  is out of scope (REQ-0042). Only sends that reach people are turned off.
- **A separate `test` flag column on runs.** `source` already says where a run came from. Rejected.

## Consequences

- Test runs count as runs of the user who started the suite and cost model credits unless the mock option is on.
- A suite needs the job worker (`STUDIO_WORKER`, on by default). With the in-memory queue, queued cases are lost on a
  restart; such a suite stays running until someone cancels it.
- Tools with side effects (HTTP calls, Code, MCP) do run in tests.
