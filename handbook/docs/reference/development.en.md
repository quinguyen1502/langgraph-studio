# Development

## Repository layout

| Path | Contents |
| --- | --- |
| `backend/app/` | FastAPI app, layered `core / models / schemas / repositories / services / api / engine` |
| `backend/tests/` | pytest suite, including layer, envelope and catalogue checks |
| `frontend/` | React, TypeScript, Vite, React Flow, Tailwind v4, shadcn/ui |
| `frontend/e2e/` | Playwright specs |
| `docker/studio-code/` | The Code mode sandbox image |
| `handbook/` | This site (MkDocs Material) |
| `scripts/` | Compose smoke test, the intro video renderer |
| `docs/` | Error catalogue, backend architecture and UI conventions |
| `.env.example` | Every Compose and runtime variable |
| `.factory/`, `.factory-state/` | The delivery workflow: requirements, decisions, tasks, reviews and QA |

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q
cd frontend && npm run build && npm run lint && npm test
```

Install the backend with `pip install -e "backend[dev]"`. Postgres and Redis
locally:

```bash
cd backend
DATABASE_URL=postgresql://… TEST_DATABASE_URL=postgresql://… \
  REDIS_URL=redis://localhost:6379/0 .venv/bin/python -m pytest -q
```

The Postgres tests need a role with `CREATEDB`.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs pytest on Python 3.12 (also on
Postgres 17 and Redis 7), the frontend build on Node 20 and 22, and a Compose
smoke test. `handbook.yml` builds this handbook strictly and publishes it from
`main`. `factory-verify.yml` checks the factory metadata. End-to-end tests are
not on CI.

## End-to-end tests

Playwright starts its own API on port 8100 (with a temporary database), Vite
on 5190, a fake chat API and an SMTP sink.

```bash
cd frontend && npx playwright install chromium
npm run e2e
```

| Variable | Effect |
| --- | --- |
| `PW_CHROME` | Use an installed Chrome instead of Playwright's Chromium |
| `E2E_UVICORN`, `E2E_PYTHON` | Override the backend binaries |
| `E2E_API_PORT`, `E2E_UI_PORT` | Run two checkouts side by side |
| `E2E_CODE_RUNTIME=subprocess` | Run the Code mode specs without Docker |

## Handbook screenshots

```bash
cd frontend && HANDBOOK_SHOTS=1 npm run e2e -- handbook
```

`e2e/handbook.spec.ts` seeds sample workflows, runs them, and writes
`handbook/docs/images/<en|vi>/*.png` at 1440 × 900. The Code mode shot needs
Docker and the `studio-code:1` image.

## The handbook

```bash
cd handbook
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve -a 127.0.0.1:8001
```

English is the default (`/`), Vietnamese is `/vi/` (`*.en.md` and `*.vi.md`
side by side). `mkdocs.yml` sets `strict: true`, so `mkdocs build` fails on a
broken link. [Error codes](errors.md) is included from `docs/api-errors.md`.

## The intro video

`scripts/promo/` renders the intro video on the home page from the handbook
screenshots: an HTML timeline that Chrome renders frame by frame and ffmpeg
encodes with a generated music bed. See `scripts/promo/README.md`.

## Contribution workflow

Work follows the AI Software Factory in `.factory/` (see `AGENTS.md`):
requirements, decisions and tasks live in `.factory-state/`, each task gets a
branch `factory/task-<id>-<name>`, and a merge needs a human approval. Backend
changes keep the layers; schema changes go through Alembic; new error codes go
into the catalogue, `docs/api-errors.md` and both locales; UI strings go into
both locale files.
