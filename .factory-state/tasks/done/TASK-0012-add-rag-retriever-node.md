# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0012
- Previous ID: TASK-0011 (renumbered 2026-10-16, DEC-0007)
- Status: done
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-17
- Requirement IDs: REQ-0007
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0007: Add RAG retriever node.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0007-rag-node.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0007

## Inputs

- `.factory-state/artifacts/REQ-0007-rag-node.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0007-rag-node.md`
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

- Uploading a document and running a Retriever node returns top-k chunks into the configured state field
- Works offline with a deterministic mock embedding

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Vector store choice (pgvector vs. Chroma) depends on REQ-0008

## Activity Log

- 2026-10-17: Implemented (DEC-0021, REV-0018, QA-0018); moved to review. Open question resolved by the owner: pgvector + SQLite brute-force fallback.
- 2026-10-16: Renumbered TASK-0011 -> TASK-0012 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0018. QA QA-0018.

## Handoff Notes

- Use branch `factory/task-0012-add-rag-retriever-node` when implementation begins.
