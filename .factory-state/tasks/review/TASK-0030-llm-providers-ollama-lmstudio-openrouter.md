# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0030
- Status: review
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: (owner request 2026-10-17; extends TASK-0005)
- Design IDs: DEC-0032
- Architecture IDs: ARCH-0001

## Objective

Let LLM nodes use local models (Ollama, LM Studio, any OpenAI-compatible server such as vLLM / llama.cpp / LocalAI) and OpenRouter, configured through the existing credentials mechanism, with a model list and a connection test.

## Scope

### In Scope

- Provider registry/strategy in `backend/app/engine/providers.py`; one small class per provider (defaults, key requirement, accepted extra headers, model listing, LangChain chat model).
- Credentials: optional API key for local providers (required for OpenRouter/OpenAI/Anthropic), base URL defaults (`http://localhost:11434`, `http://localhost:1234/v1`, `http://localhost:8000/v1`, `https://openrouter.ai/api/v1`), OpenRouter `HTTP-Referer` / `X-Title` headers stored on the credential (migration 0023).
- `POST /api/providers/{id}/test` (unsaved settings) and `GET /api/credentials/{id}/models` (saved credential): model list from Ollama `/api/tags`, OpenAI-compatible `/v1/models`, OpenRouter `/api/v1/models`.
- LangChain: `ChatOllama` (langchain-ollama), `ChatOpenAI(base_url=…)` (langchain-openai); streaming and `bind_tools` available via `engine.llm.chat_model()`.
- Error codes `PROVIDER_UNREACHABLE`, `PROVIDER_AUTH_FAILED`, `PROVIDER_BAD_RESPONSE`, `MODEL_NOT_FOUND`, `CREDENTIAL_HEADER_UNSUPPORTED` (catalog, docs/api-errors.md, en/vi); run error events carry the same codes.
- UI: provider list from the API, per-provider form (key optional label, default URL placeholder, Docker hint, header fields), "Test connection" on the form and on saved rows, LLM node model picker (fetched list + manual entry, warning on failure); deletes keep `ConfirmDeleteDialog`.
- Docker Compose: `extra_hosts: host.docker.internal:host-gateway` on `api` and `worker`; README section.

### Out Of Scope

- Token-by-token streaming of LLM node output into the run trace (the node still returns the final text; streaming is available to code using `chat_model()`).
- Tool-calling agent node (no such node exists yet); embeddings for Ollama/LM Studio in knowledge bases.
- Editing an existing credential (delete + re-add, as before).

## Acceptance Criteria

- Backend tests with mocked HTTP (respx) for all four providers: model list, chat, usage, streaming, tool calls, error mapping, API envelope.
- Backend suite on SQLite and on Postgres 17 + Redis 7 (Compose, `--env-file`), migration 0023 applied on both.
- e2e `e2e/llm-providers.spec.ts` (fake providers in `backend/tests/fixtures/mock_chat_api.py`) and the full e2e suite; frontend build.
- Screenshots light/dark × en/vi in `/workspace/ss-review/55-llm-*`.

## Evidence

- SQLite: 249 passed, 10 skipped. Postgres 17 (pgvector) + Redis 7 via `docker compose -p lgs-llm --env-file …`: 258 passed, 1 skipped.
- e2e: 28 passed, 4 skipped (all specs). `npm run build` OK.
- Compose: api/worker resolve `host.docker.internal` (172.17.0.1) and list models from a fake Ollama on the host; `http://localhost:11434` from the container returns `PROVIDER_UNREACHABLE` as documented. Needed `iptables-legacy -I FORWARD -i br-<net> -o br-<net> -j ACCEPT` on this box for the new compose network.
