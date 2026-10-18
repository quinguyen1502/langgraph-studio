# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0002
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-19
- Source: project-specs.md (Post-MVP Scope)

## Summary

Real LLM providers with per-workflow credentials. LLM nodes can call real providers (OpenAI, Anthropic, OpenAI-compatible) using credentials managed in the app, while mock mode remains the default without keys.

## Problem Or Opportunity

LLM nodes can call real providers (OpenAI, Anthropic, OpenAI-compatible) using credentials managed in the app, while mock mode remains the default without keys.

## Scope

### In Scope

- Provider + model selection on LLM nodes
- Encrypted credential storage per user or workspace
- Fallback to mock when no credential is configured

### Out Of Scope

- Fine-tuning, embeddings (see REQ-0007)

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- `backend/app/compiler.py` `call_llm` uses env OPENAI_API_KEY only

## Desired Behavior

LLM nodes can call real providers (OpenAI, Anthropic, OpenAI-compatible) using credentials managed in the app, while mock mode remains the default without keys.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- An LLM node configured with a stored OpenAI or Anthropic credential returns the provider response during a run
- Credentials are never returned by any API response or written to logs
- Without credentials the existing mock behaviour and tests are unchanged
- Provider errors surface as a node `error` event, not a server crash

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Resolved 2026-10-16 (DEC-0006, delivered by TASK-0005): credentials belong to a user and are chosen per LLM node, so each workflow picks its own; a shared workflow runs with its owner's credentials (DEC-0023). No global admin credential besides the `OPENAI_API_KEY` fallback.
- Resolved: OpenAI and OpenAI-compatible base URLs, and Anthropic, first (DEC-0006); the provider registry later added Ollama, LM Studio, OpenRouter and generic OpenAI-compatible servers (DEC-0032, TASK-0030).

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
- Delivered by `.factory-state/tasks/done/TASK-0005-configure-real-llm-providers-with-per-workflow-credentials.md`, merged to `develop`.
