# Discovery: Import Assessment

## Project

- Name: langgraph-studio
- Integration branch: `main` (repository created 2026-10-16 with a single `main` branch)
- Remote: https://github.com/quinguyen1502/langgraph-studio (private)

## Observed Manifests

- `backend/requirements.txt` (fastapi, uvicorn, langgraph, httpx, pytest, pyjwt, python-multipart)
- `frontend/package.json` (react 19, @xyflow/react 12, tailwindcss 4, shadcn/radix, react-router-dom, @dagrejs/dagre, lucide-react)

## Observed Source Directories

- `backend/app/` (FastAPI service, compiler, auth, importer, sandbox runner)
- `frontend/src/` (pages, components, lib)

## Observed Test Directories

- `backend/tests/` (test_compiler.py, test_auth.py, test_import.py; fixtures under `backend/tests/fixtures/`)

## Existing AI Instructions

- None before Factory import.

## Commands Inferred From Repository Evidence

- Install/Run: `./dev.sh` — observed working 2026-10-16
- Test: `cd backend && .venv/bin/python -m pytest -q` — observed 19 passed 2026-10-16
- Build + typecheck: `cd frontend && npm run build` (`tsc -b && vite build`) — observed passing 2026-10-16
- Lint/format: not configured (Unknown)

## Findings

- Factory linked by copy (`factory_link_mode: copy`); the framework repo is private, a submodule would require collaborator credentials for every clone.
- Stack recorded as `Preferred` rather than `Approved`: Factory `ready` requires a published scaffold for an Approved source stack, and scaffolding an existing codebase would only produce conflicts. Owner decision needed.
- Security: imported repo code runs on the host in a subprocess (REQ-0009 tracks containerisation).
- Demo credentials and default JWT secret are local-only placeholders; no real secrets found in a repository scan (2026-10-16).

## Constraints

- Inferred commands must be validated before they become project standards.
- Manifest presence is evidence of a tool or ecosystem, not approval of an architecture.

## Related Artifacts

- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/REQ-0001-mvp-baseline.md` … `REQ-0012-rbac-sharing.md`
