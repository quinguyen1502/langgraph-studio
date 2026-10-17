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
- **Credentials** stay the storage mechanism: key now optional per provider (`key_required`), `headers` JSON column (migration 0024_credential_headers, renumbered after 0023_templates) restricted to the provider's `header_fields` (OpenRouter `HTTP-Referer`, `X-Title`). Keys stay Fernet-encrypted; headers are not secret and are returned.
- **Test connection = list models**. One code path proves reachability and authorisation and feeds the model picker: `POST /api/providers/{id}/test` for unsaved form values (needs `resources.manage`), `GET /api/credentials/{id}/models` for saved ones (owner only).
- **Errors**: `ProviderError(code, …)` in the engine (catalog codes), converted to `AppError` by the service; the run engine already copies `.code` into the error event. `PROVIDER_AUTH_FAILED` is 400, not 401, so the SPA does not mistake it for an expired session.
- **No SSRF block** on provider URLs: local providers are private addresses by design, and only users with `resources.manage` can point the server at a URL (same as the existing OpenAI base URL).
- **Pin `openai>=2.45,<3`**: openai 3.x moved to `httpx2`, which respx cannot intercept; 2.x is supported by langchain-openai 1.x. Revisit when respx supports httpx2.
- **Docker**: `extra_hosts: host.docker.internal:host-gateway` on `api` and `worker`; users enter `http://host.docker.internal:<port>` (UI hint + README).

## Consequences
- Adding a provider = one class + one `REGISTRY` entry + an en/vi label (`creds.providers.<id>`; falls back to the API label).
- `engine.llm.chat_model(cred, model)` gives any future agent/tool node a streaming, tool-capable model for every provider.
- The three follow-ups below (formerly open) are implemented in the same PR.

## Follow-up decisions (2026-10-17, same PR)

### Live LLM output in the run trace
- LLM nodes stream through `Provider.invoke(..., on_token)` (LangChain `.stream()`; usage from the aggregated chunks, `stream_usage=True` for OpenAI-compatible servers). OpenAI/Anthropic stay on plain HTTP (`PlainHTTP`) and send the whole answer as one delta; the offline mock streams word by word.
- Transport: LangGraph's `custom` stream mode (`get_stream_writer()` inside the node). The runtime turns it into `node_token {node, iteration, delta}` events on the existing WebSocket. A `TokenBuffer` coalesces deltas (~50 ms) so a fast model does not flood the socket.
- `node_token` events are **live only**: they are not stored in the run's event log, telemetry or history. `node_finished` still carries the final text, which stays exactly the same (the concatenated deltas equal it, tested).
- UI: `buildTrace` adds the deltas to the running span's `live` text. The row shows the tail of that text, and the detail panel's Output tab shows it as it grows. Once the node finishes, the normal output replaces it.
- Not streamed: LLM nodes inside subgraphs (LangGraph needs `subgraphs=True`; left out to keep the event model flat) and imported code (sandbox).

### Embeddings through the registry
- `Provider.embed(texts, model, cred)`: OpenAI-style `POST {base}/embeddings` by default (OpenAI, LM Studio, generic, OpenRouter). Ollama overrides it with `POST /api/embed`. Anthropic has `supports_embeddings = False` (`PROVIDER_EMBEDDINGS_UNSUPPORTED`). Plain HTTP rather than LangChain `OpenAIEmbeddings`, because that one tokenises with tiktoken by default, and local servers reject token arrays.
- Embedder id `<provider>:<model>` (e.g. `ollama:nomic-embed-text`; existing `openai:*` / `mock:512` ids unchanged). An empty model takes the provider's `default_embedding_model`.
- **Dimension per knowledge base**: `knowledge_bases.dims` (migration 0025_kb_dims) is written on the first upload and on re-index. Legacy knowledge bases have NULL, and the service reads the size from one stored chunk the first time (`vector_dims()` on pgvector) and saves it. The pgvector column stays dimension-less (`vector`), as in TASK-0012, so knowledge bases with different models share it safely. A vector whose size differs from `dims` under the same embedder name (e.g. a re-pulled local model) is refused with `KB_EMBEDDING_DIMENSION_MISMATCH` (409) on upload and search; re-index adopts the new size. Changing the model or credential re-indexes automatically, as before.
- Provider failures during embedding surface their own codes (`PROVIDER_UNREACHABLE`, `MODEL_NOT_FOUND`, ...) instead of the generic `KB_EMBEDDING_FAILED`.
- `POST /api/credentials/{id}/embeddings/test {model}` embeds a probe text and returns `{model, dims, latency_ms}`; the knowledge-base form uses it ("Test embedding") and reuses the model picker (model list from the credential, manual entry).

### Edit a credential in place
- `PUT /api/credentials/{id} {name, base_url, headers, api_key?, clear_key?}` (owner, `resources.manage`). The provider is fixed. An empty `api_key` keeps the stored secret, and a new one replaces it (re-encrypted, new mask). `clear_key` removes it only where a key is optional (`CREDENTIAL_KEY_REQUIRED` otherwise). Validation is the same `_clean` as on create.
- `POST /api/providers/{id}/test` accepts `credential_id`. While editing, an empty key field tests with the stored key, which is never sent to the browser.
- UI: the add form doubles as the edit form (pencil button per row). It has a disabled provider, a placeholder saying the masked key is kept, a "Remove the stored key" switch for optional-key providers, and Cancel/Save. Delete stays on `ConfirmDeleteDialog`.
