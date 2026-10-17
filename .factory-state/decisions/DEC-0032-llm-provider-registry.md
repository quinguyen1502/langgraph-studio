# Decision

## Metadata

- Decision ID: DEC-0032
- Status: Proposed
- Date: 2026-10-17
- Related: TASK-0030, TASK-0005, DEC-0009 (layers), DEC-0010 (envelope)

## Context
LLM support was two hard-coded branches (OpenAI-compatible, Anthropic) in `engine/llm.py` plus a `PROVIDERS` dict. The owner wants Ollama, LM Studio, a generic OpenAI-compatible endpoint and OpenRouter, each with its own defaults, optional key, model list and connection test, using LangChain integrations so streaming and tool calling work.

## Decision
- **Registry/strategy** in `engine/providers.py`: `Provider` base with class attributes (`id`, `label`, `default_base_url`, `default_model`, `key_required`, `header_fields`, `local`, `models_path`) and three behaviours: `list_models(cred)`, `chat_model(cred, model)` (LangChain), `invoke(prompt, model, cred)`. `OpenAICompatible` → `LMStudio`, `OpenRouter` are a few lines each; `Ollama` overrides model parsing and the chat model. `REGISTRY` is the single source of truth for the API (`GET /api/providers`), the credential service and `call_llm`.
- **OpenAI and Anthropic** keep their plain-HTTP `invoke` (no behaviour change, existing tests untouched apart from the patch point) but are registry members too.
- **Credentials** stay the storage mechanism: key now optional per provider (`key_required`), `headers` JSON column (migration 0023) restricted to the provider's `header_fields` (OpenRouter `HTTP-Referer`, `X-Title`). Keys stay Fernet-encrypted; headers are not secret and are returned.
- **Test connection = list models**. One code path proves reachability and authorisation and feeds the model picker: `POST /api/providers/{id}/test` for unsaved form values (needs `resources.manage`), `GET /api/credentials/{id}/models` for saved ones (owner only).
- **Errors**: `ProviderError(code, …)` in the engine (catalog codes), converted to `AppError` by the service; the run engine already copies `.code` into the error event. `PROVIDER_AUTH_FAILED` is 400, not 401, so the SPA does not mistake it for an expired session.
- **No SSRF block** on provider URLs: local providers are private addresses by design, and only users with `resources.manage` can point the server at a URL (same as the existing OpenAI base URL).
- **Pin `openai>=2.45,<3`**: openai 3.x moved to `httpx2`, which respx cannot intercept; 2.x is supported by langchain-openai 1.x. Revisit when respx supports httpx2.
- **Docker**: `extra_hosts: host.docker.internal:host-gateway` on `api` and `worker`; users enter `http://host.docker.internal:<port>` (UI hint + README).

## Consequences
- Adding a provider = one class + one `REGISTRY` entry + an en/vi label (`creds.providers.<id>`; falls back to the API label).
- `engine.llm.chat_model(cred, model)` gives any future agent/tool node a streaming, tool-capable model for every provider.
- Open: stream LLM node tokens into the trace; Ollama/LM Studio embeddings for knowledge bases; editing credentials in place.
