# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0009
- Previous ID: TASK-0008 (renumbered 2026-10-16, DEC-0007)
- Status: review
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0008
- Design IDs: DEC-0011
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0008: Move to Postgres and Redis with Docker Compose.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0008-postgres-redis-compose.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0008

## Inputs

- `.factory-state/artifacts/REQ-0008-postgres-redis-compose.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0008-postgres-redis-compose.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`

## Expected Outputs

- Implementation, tests, README update
- Design/architecture artifact if the requirement changes boundaries

## Constraints

- Mock mode and existing tests must keep passing

## Dependencies

- TASK-0002 (CI) recommended first

## Acceptance Criteria

- `docker compose up` starts the full stack and the seeded example runs end to end
- Schema managed by migrations (e.g. Alembic)
- Existing tests run against Postgres in CI

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch for phase 2 is `develop`; this PR targets `develop`.

## Open Questions

- Keep SQLite as a supported dev mode? **Resolved: yes, SQLite stays the dev default (DEC-0011).**

## Delivered

- Postgres via `DATABASE_URL` (psycopg 3); Alembic revisions unchanged and verified on Postgres 17.
- `RunBus` interface (`services/run_bus.py`): in-memory default, Redis when `REDIS_URL` is set (registry, cancel flag, event pub/sub). `POST /api/runs/{id}/cancel`, error code `RUN_NOT_FOUND` (en/vi).
- `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf.template`, `docker-compose.yml`, `.env.example`, `scripts/compose_smoke.py`.
- CI: `backend-postgres` job (services postgres + redis), `compose` build + smoke job; CI also runs for `develop`.
- Docs: DEC-0011, ARCH-0001, `docs/backend-architecture.md`, README deploy section, roadmap, REV-0008, QA-0008.

## Activity Log

- 2026-10-16: Implemented on `factory/task-0009-move-to-postgres-and-redis-with-docker-compose` (from `develop`); moved to review.

- 2026-10-16: Renumbered TASK-0008 -> TASK-0009 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0009-move-to-postgres-and-redis-with-docker-compose` when implementation begins.
