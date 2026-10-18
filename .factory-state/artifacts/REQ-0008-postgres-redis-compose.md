# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0008
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-19
- Source: project-specs.md (Post-MVP Scope)

## Summary

Postgres + Redis with Docker Compose. Replace SQLite with PostgreSQL, add Redis for run queue/pubsub, and provide Docker Compose for local and internal deployment.

## Problem Or Opportunity

Replace SQLite with PostgreSQL, add Redis for run queue/pubsub, and provide Docker Compose for local and internal deployment.

## Scope

### In Scope

- DB abstraction + migrations
- Redis-backed run queue/event fan-out
- docker-compose.yml for backend, frontend, postgres, redis

### Out Of Scope

- Kubernetes manifests

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- SQLite file `backend/studio.db`; schema created inline in `main.py`

## Desired Behavior

Replace SQLite with PostgreSQL, add Redis for run queue/pubsub, and provide Docker Compose for local and internal deployment.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- `docker compose up` starts the full stack and the seeded example runs end to end
- Schema managed by migrations (e.g. Alembic)
- Existing tests run against Postgres in CI

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Resolved 2026-10-16: yes. SQLite stays the development default; Postgres is used when `DATABASE_URL` is set, with the same Alembic revisions (DEC-0011).

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
- Delivered by `.factory-state/tasks/done/TASK-0009-move-to-postgres-and-redis-with-docker-compose.md`, merged to `develop`.
