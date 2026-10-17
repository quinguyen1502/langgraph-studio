# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0015
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-17
- Source: owner request 2026-10-17 (Phase 5: Editor UX)

## Summary

Starter workflow templates, save a workflow as a template, and import/export templates.

## Problem Or Opportunity

New users start from an empty canvas; teams cannot share reusable starting points.

## Scope

### In Scope

- Built-in starter templates (e.g. chatbot, RAG Q&A, approval flow, router with conditions) seeded read-only
- New workflow → pick a template (gallery with name, description, node preview) or blank
- Save as template from the editor (name, description; personal, or org-wide for admins)
- Import/export a template as JSON (validated against the workflow schema; credentials and secrets never exported)
- API with the response envelope and English error codes (catalog, docs/api-errors.md, en+vi); Alembic migration that works on SQLite and Postgres

### Out Of Scope

- Public template marketplace
- Versioning of templates

## Stakeholders Or Users

- Workflow authors using the LangGraph Studio editor

## Current Context

- React Flow editor (`frontend/src/pages/Editor.tsx`), shadcn/Tailwind UI, en/vi i18n

## Desired Behavior

Starter workflow templates, save a workflow as a template, and import/export templates.

## Business Rules

- Strict shadcn (tokens only), en/vi texts, keyboard and screen-reader accessible

## Constraints

- Mock/offline mode must keep working without API keys.

## Acceptance Criteria

- Creating from a template produces an independent workflow that runs in mock mode
- Export → import round-trips a template; invalid files get a translated error code
- Exported files contain no credential ids or secrets
- Backend tests (SQLite + Postgres), e2e for gallery, save-as-template and import

## Open Questions

- None yet
