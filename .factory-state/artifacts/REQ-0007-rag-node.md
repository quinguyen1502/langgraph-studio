# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0007
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-18
- Source: project-specs.md (Post-MVP Scope)

## Summary

RAG retriever node. Users can attach documents to a knowledge base and use a Retriever node that writes relevant chunks into state.

## Problem Or Opportunity

Users can attach documents to a knowledge base and use a Retriever node that writes relevant chunks into state.

## Scope

### In Scope

- Document upload, chunking, embedding, vector store, Retriever node

### Out Of Scope

- Web crawling

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- No embedding or vector store exists

## Desired Behavior

Users can attach documents to a knowledge base and use a Retriever node that writes relevant chunks into state.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- Uploading a document and running a Retriever node returns top-k chunks into the configured state field
- Works offline with a deterministic mock embedding

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Resolved 2026-10-17 (owner): pgvector on Postgres, brute-force fallback on SQLite, mock embedding offline, OpenAI `text-embedding-3-small` by default; txt/md/pdf ≤ 10 MB. See DEC-0021.

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
- Delivered by `.factory-state/tasks/done/TASK-0012-add-rag-retriever-node.md`, merged to `develop`.
