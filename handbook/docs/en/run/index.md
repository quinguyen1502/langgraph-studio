# Run

A workflow runs in four ways. All of them go through the same engine,
produce the same trace, and appear in **History**.

| Started by | How | Badge in History |
| --- | --- | --- |
| The editor | **Run**, **Step** or **Run to here**, over `/ws/run` | — |
| Another service | `POST /api/hooks/workflows/{wid}/runs` with a workflow token | **API** |
| A timetable | A cron schedule on the workflow | **Schedule** |
| A person resuming | Approve, reject or answer a waiting Human node | — |

<div class="grid cards" markdown>

-   :material-chart-gantt:{ .lg .middle } **[Runs and traces](traces.md)**

    ---

    The Logs timeline, stepping, cancel, limits and cost.

-   :material-account-check:{ .lg .middle } **[Human approval](human-approval.md)**

    ---

    Waiting runs, notifications and chat approvals.

-   :material-api:{ .lg .middle } **[API triggers and webhooks](api-triggers.md)**

    ---

    Tokens, sync and async runs, signed callbacks, workers.

-   :material-calendar-clock:{ .lg .middle } **[Schedules](schedules.md)**

    ---

    Cron, time zones and missed times.

</div>
