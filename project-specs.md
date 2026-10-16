# Project Specs

Statements marked `Approved` are owner decisions. `Preferred`, `Proposed`, and `Unknown` items require confirmation or discovery.

## Summary

### Project Name

- langgraph-studio

### One-Line Description

- Internal drag-and-drop builder that designs, compiles, runs and imports LangGraph workflows from a browser.

### Problem Statement

Building and debugging LangGraph agents currently requires writing Python by hand; the team wants a visual, internal tool to design graphs, run them with live per-node feedback, and inspect existing LangGraph repositories, both for internal use and for learning LangGraph concepts.

### Intended Outcome

Team members can sign in, visually compose a workflow (Start, LLM, Tool/API, Condition, End), run it with live per-node status over WebSocket, review run history, and import an existing LangGraph repo to visualise and run its original graph.

### Starter Preset

- Web App [Input aid; not an architectural decision]

## Vision

### Goals

- Visual design of LangGraph StateGraphs without hand-written boilerplate
- Deterministic offline demo (mock LLM) so the tool works without API keys
- Live per-node execution feedback and persisted run history
- Import and visualise existing LangGraph repos and run their original code
- Serve as a learning aid for LangGraph concepts

### Non-Goals

- Public multi-tenant SaaS
- Replacing the official LangGraph Platform / Studio for production deployments
- Editing imported repo source code from the canvas

### Success Metrics

- Unknown; define measurable product and delivery outcomes before MVP approval.

## Users And Stakeholders

### Primary Users

- Internal developers and learners (Vietnamese-speaking team) building or studying LangGraph agents; the project owner as administrator.

## Scope

### MVP Scope

- Implemented (observed in repository at commit 2c2d401):
- React Flow canvas with drag-drop palette (Start, LLM, Tool/API, Condition, End), connect/delete, config panel, state schema editor
- Tailwind CSS v4 + shadcn/ui UI, dark mode toggle
- FastAPI backend: workflow JSON {nodes, edges, state} CRUD in SQLite, graph validation, compiler to langgraph StateGraph (add_node/add_edge/add_conditional_edges on state-field value vs edge labels)
- LLM node (OpenAI-compatible via OPENAI_API_KEY, deterministic mock otherwise), Tool node (HTTP request or registered Python function, example lookup_order)
- WebSocket run streaming with per-node started/finished, duration and state delta; run history persisted
- Email/password auth (PBKDF2 hashing, JWT), register/login/me, per-user workflow ownership, seeded demo user
- Workflow list page (search, create, rename, duplicate, delete with confirm), login/register pages, react-router guards
- Import LangGraph repo (GitHub URL or zip): per-import venv, langgraph.json / StateGraph scan, subprocess inspection via get_graph(xray), conversion to read-only Code nodes with dagre auto-layout, run of original graph in subprocess with streamed events and clear missing-key errors
- Seeded customer-support example workflow; pytest suite (19 tests) and npm build

### Post-MVP Scope

- Real LLM provider configuration (OpenAI, Anthropic, others) with per-workflow credentials
- Human-in-the-loop (interrupts, approval nodes, resume)
- API / webhook triggers for workflows
- Workflow versioning and diff/rollback
- Subgraphs and parallel branches (fan-out/fan-in) in the builder
- RAG nodes (retriever / vector store)
- MCP tool integration
- Postgres + Redis + Docker Compose deployment
- Container-sandboxed repo imports
- Observability (tracing, LangSmith/OpenTelemetry, metrics)
- RBAC and workflow sharing

### Out Of Scope

- Public internet exposure without hardening
- Billing / multi-tenant isolation
- Mobile apps

## Roadmap

### P0

- Implemented (observed in repository at commit 2c2d401):
- React Flow canvas with drag-drop palette (Start, LLM, Tool/API, Condition, End), connect/delete, config panel, state schema editor
- Tailwind CSS v4 + shadcn/ui UI, dark mode toggle
- FastAPI backend: workflow JSON {nodes, edges, state} CRUD in SQLite, graph validation, compiler to langgraph StateGraph (add_node/add_edge/add_conditional_edges on state-field value vs edge labels)
- LLM node (OpenAI-compatible via OPENAI_API_KEY, deterministic mock otherwise), Tool node (HTTP request or registered Python function, example lookup_order)
- WebSocket run streaming with per-node started/finished, duration and state delta; run history persisted
- Email/password auth (PBKDF2 hashing, JWT), register/login/me, per-user workflow ownership, seeded demo user
- Workflow list page (search, create, rename, duplicate, delete with confirm), login/register pages, react-router guards
- Import LangGraph repo (GitHub URL or zip): per-import venv, langgraph.json / StateGraph scan, subprocess inspection via get_graph(xray), conversion to read-only Code nodes with dagre auto-layout, run of original graph in subprocess with streamed events and clear missing-key errors
- Seeded customer-support example workflow; pytest suite (19 tests) and npm build

### P1

- Real LLM provider configuration (OpenAI, Anthropic, others) with per-workflow credentials
- Human-in-the-loop (interrupts, approval nodes, resume)
- API / webhook triggers for workflows
- Workflow versioning and diff/rollback
- Subgraphs and parallel branches (fan-out/fan-in) in the builder
- RAG nodes (retriever / vector store)
- MCP tool integration
- Postgres + Redis + Docker Compose deployment
- Container-sandboxed repo imports
- Observability (tracing, LangSmith/OpenTelemetry, metrics)
- RBAC and workflow sharing

### P2

- Unknown

## Core User Flows

- 1. Sign in (or register) -> workflow list
- 2. Create / open workflow -> drag nodes, connect, configure, edit state schema -> Save
- 3. Run with JSON input -> live node highlighting and logs -> run saved to history
- 4. Import repo (URL or zip) -> progress log -> pick graph -> imported read-only workflow -> run original graph
- 5. Rename / duplicate / delete workflows; logout

### Required Flow States

- Loading, empty, error, permission, and completion states: Unknown.

## Features

### Candidate MVP Requirements

- [Proposed] Implemented (observed in repository at commit 2c2d401):
- [Proposed] React Flow canvas with drag-drop palette (Start, LLM, Tool/API, Condition, End), connect/delete, config panel, state schema editor
- [Proposed] Tailwind CSS v4 + shadcn/ui UI, dark mode toggle
- [Proposed] FastAPI backend: workflow JSON {nodes, edges, state} CRUD in SQLite, graph validation, compiler to langgraph StateGraph (add_node/add_edge/add_conditional_edges on state-field value vs edge labels)
- [Proposed] LLM node (OpenAI-compatible via OPENAI_API_KEY, deterministic mock otherwise), Tool node (HTTP request or registered Python function, example lookup_order)
- [Proposed] WebSocket run streaming with per-node started/finished, duration and state delta; run history persisted
- [Proposed] Email/password auth (PBKDF2 hashing, JWT), register/login/me, per-user workflow ownership, seeded demo user
- [Proposed] Workflow list page (search, create, rename, duplicate, delete with confirm), login/register pages, react-router guards
- [Proposed] Import LangGraph repo (GitHub URL or zip): per-import venv, langgraph.json / StateGraph scan, subprocess inspection via get_graph(xray), conversion to read-only Code nodes with dagre auto-layout, run of original graph in subprocess with streamed events and clear missing-key errors
- [Proposed] Seeded customer-support example workflow; pytest suite (19 tests) and npm build

### Acceptance Criteria

- Unknown; refine each approved requirement into verifiable acceptance criteria.

## UX/UI Direction

### Product Experience

- Unknown

### Screens Or Surfaces

- Derive from approved user flows.

### Accessibility Requirements

- Unknown; define keyboard, screen-reader, contrast, and responsive expectations where applicable.

## Data And Domain Model

### Main Entities And Relationships

- Unknown; derive from approved requirements without treating draft nouns as decisions.

### Data Lifecycle, Privacy, And Compliance

- Unknown

## Technical Direction

### Technology Stack

- Frontend: React + TypeScript (Vite) with @xyflow/react, Tailwind CSS v4, shadcn/ui [Preferred]; Factory automation: specification only
- Mobile: Unknown [Unknown]; Factory automation: specification only
- Backend: FastAPI (Python 3.13) + langgraph [Preferred]; Factory automation: specification only
- Database: SQLite (MVP); PostgreSQL + Redis on roadmap [Preferred]; Factory automation: specification only
- Infrastructure: Local dev script (dev.sh); Docker Compose on roadmap [Proposed]; Factory automation: specification only
- Ci Cd: GitHub Actions [Approved]; Factory automation: configuration
- Deployment: Internal host (undecided) [Unknown]; Factory automation: specification only
- Testing: pytest (backend), tsc + vite build (frontend); Playwright screenshots [Preferred]; Factory automation: specification only

### Expected Commands

- Install: ./dev.sh (first run: creates backend/.venv, pip install -e "backend[dev]", npm install) [Expected]
- Run: ./dev.sh (backend :8000, frontend :5173) [Expected]
- Test: cd backend && .venv/bin/python -m pytest -q [Expected]
- Build: cd frontend && npm run build [Expected]
- Lint: Unknown
- Typecheck: cd frontend && npx tsc -b [Expected]
- Format: Unknown
- Migration: Alembic (`backend/app/migrations`), applied on startup (DEC-0009) [Observed]

### Constraints

- Internal use only; single SQLite file for MVP
- Must run offline in mock mode without API keys
- Imported repo code is arbitrary and must only run in a subprocess with its own venv (not the server process)
- UI copy primarily Vietnamese

### Integrations

- OpenAI-compatible chat completions API (optional, via OPENAI_API_KEY / OPENAI_BASE_URL)
- GitHub (public clone) for repo import
- uv / pip for per-import virtualenvs

### Architecture And Compatibility Insights

- [Info] **Frontend/API boundary inferred:** Separate frontend and backend technologies imply at least two runtime boundaries.
  - Recommendation: Record API style, authentication ownership, and local development orchestration.

### Explicit Technical Decisions

- Only technology choices marked `Approved` may generate decision records.

## Quality Attributes

### Performance

- Unknown

### Reliability

- Unknown

### Security And Privacy

- Unknown

### Maintainability And Observability

- Unknown

## Delivery And Operations

### Environments And Release Expectations

- Unknown

### Monitoring, Rollback, And Recovery

- Unknown

## Risks And Assumptions

### Assumptions

- Technology choices not marked `Approved` are not binding decisions.
- Commands marked `Expected` are not observed until source files confirm them.

### Risks And Blockers

- Unknown

### Open Questions

- Confirm every `Preferred`, `Proposed`, or `Unknown` technology choice before implementation requires it.

## Validation Strategy

- Confirm project artifacts preserve the statuses and constraints in this specification.
- Discover actual install, run, test, build, lint, typecheck, format, and migration commands from source files.
- Define requirement-level automated tests, manual QA, and acceptance evidence before implementation completion.

## Initial Work Breakdown

### Suggested Tasks

- [Proposed] Implemented (observed in repository at commit 2c2d401):
- [Proposed] React Flow canvas with drag-drop palette (Start, LLM, Tool/API, Condition, End), connect/delete, config panel, state schema editor
- [Proposed] Tailwind CSS v4 + shadcn/ui UI, dark mode toggle
- [Proposed] FastAPI backend: workflow JSON {nodes, edges, state} CRUD in SQLite, graph validation, compiler to langgraph StateGraph (add_node/add_edge/add_conditional_edges on state-field value vs edge labels)
- [Proposed] LLM node (OpenAI-compatible via OPENAI_API_KEY, deterministic mock otherwise), Tool node (HTTP request or registered Python function, example lookup_order)
- [Proposed] WebSocket run streaming with per-node started/finished, duration and state delta; run history persisted
- [Proposed] Email/password auth (PBKDF2 hashing, JWT), register/login/me, per-user workflow ownership, seeded demo user
- [Proposed] Workflow list page (search, create, rename, duplicate, delete with confirm), login/register pages, react-router guards
- [Proposed] Import LangGraph repo (GitHub URL or zip): per-import venv, langgraph.json / StateGraph scan, subprocess inspection via get_graph(xray), conversion to read-only Code nodes with dagre auto-layout, run of original graph in subprocess with streamed events and clear missing-key errors
- [Proposed] Seeded customer-support example workflow; pytest suite (19 tests) and npm build

## Decision And Confidence Summary

### Owner-Confirmed Technology

- Ci Cd: GitHub Actions

### Items Requiring Attention

- Frontend: React + TypeScript (Vite) with @xyflow/react, Tailwind CSS v4, shadcn/ui [Preferred]
- Mobile: Unknown [Unknown]
- Backend: FastAPI (Python 3.13) + langgraph [Preferred]
- Database: SQLite (MVP); PostgreSQL + Redis on roadmap [Preferred]
- Infrastructure: Local dev script (dev.sh); Docker Compose on roadmap [Proposed]
- Deployment: Internal host (undecided) [Unknown]
- Testing: pytest (backend), tsc + vite build (frontend); Playwright screenshots [Preferred]

### Evidence State

- Technology values are declared owner inputs, not repository observations.
- Populated commands are `Expected` until verified against repository evidence.

