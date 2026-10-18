# LangGraph Studio

**English** · [Tiếng Việt](README.vi.md)

Internal tool for designing LangGraph workflows in the browser. Draw a graph, configure nodes, save the JSON, and run it with live per-node events. The FastAPI backend compiles that JSON into a LangGraph `StateGraph`. You can also import an existing Python LangGraph repo and run the original graph inside a Docker sandbox.

This is for internal use and learning. It does not replace LangGraph Platform.

## Quick start

```bash
./dev.sh
```

The first run creates `backend/.venv`, installs the backend, and runs `npm install` in `frontend/`.

- UI: http://localhost:5173 (Vite proxies `/api` and `/ws` to the backend)
- API docs: http://localhost:8000/docs
- Demo account, seeded on startup: `admin@example.com` / `admin123`

To use a real model, open **Credentials** on the workflow list and add a provider. A node with no credential and no `OPENAI_API_KEY` uses the deterministic offline mock. Provider failures (401, timeout, and so on) become a node `error` event. They do not crash the server.

`export OPENAI_API_KEY=sk-...` (optional `OPENAI_BASE_URL`) is the fallback for an LLM node that has no credential selected.

## Accounts

Passwords are hashed with PBKDF2-SHA256 (200k rounds, a unique salt). Login returns an HS256 JWT that lasts 24 hours (`JWT_TTL_SECONDS`, default 86400). Set `JWT_SECRET` for any shared or production process. If that value is still the placeholder, the backend logs a warning. With `STUDIO_ENV=production` it refuses to start.

Registration requires a password of 8–128 characters with at least one letter and one digit. The seeded `admin123` password is exempt. Email is trimmed and lower-cased. A bad login always says the email or password is wrong.

Send `Authorization: Bearer <token>` on workflow and run APIs. The run socket is `ws://…/ws/run?token=<token>`. An expired or invalid token signs the UI out and returns to `/login?expired=1&next=…`. A new account receives a copy of the example workflow. Workflows belong to the user who created them.

There is no login lockout and no password reset.

## Editor

| Area | What it does |
| --- | --- |
| Top bar | Name, Save, Run / Stop, undo and redo. Everything else is in the **⋯** menu. |
| Left | Node palette and the state-schema editor. |
| Centre | React Flow canvas. Drag from the right handle to the left handle. Delete removes the selection. Start and End cannot be deleted. |
| Right | Config for the selection, and run history. |
| Bottom | JSON input and the live log. |

`?` or `Ctrl/⌘+/` opens the shortcut sheet (`frontend/src/lib/shortcuts.ts`). `Ctrl/⌘+S` saves, `Ctrl/⌘+Enter` runs, `Ctrl/⌘+.` stops, `Ctrl/⌘+A` selects all, `Shift+1` fits the view, `Ctrl/⌘` plus `+`/`-` zooms. Shortcuts other than save, run, and stop are ignored while typing. An open dialog disables them.

`Ctrl/⌘+Z` undoes and `Ctrl/⌘+Shift+Z` or `Ctrl/⌘+Y` redoes, up to 100 steps. One drag is one step. Continuous typing in the same node is one step. Text fields keep the browser's own undo. The unsaved badge clears when you undo back to the saved graph.

`Ctrl/⌘+K` opens the command palette on every page, including from a text field. It fuzzy-finds editor actions, **Add node**, **Go to node**, **Open workflow**, **New workflow**, and Settings pages. English keywords such as `retriever` and `mcp` match too.

`Ctrl/⌘+C`, `Ctrl/⌘+X`, `Ctrl/⌘+V`, and `Ctrl/⌘+D` copy, cut, paste, and duplicate. Start and End are never copied. Only edges between selected nodes travel with them. Pasted nodes get new ids. The clipboard is `localStorage` (`langgraph-studio/nodes` v1), so you can paste into another workflow in the same browser. A credential you cannot use is cleared on paste.

**Arrange** or `Shift+L` lays the graph out with dagre at the real node size. The arrow beside it picks left-to-right or top-to-bottom. The top-left of the graph stays put. One arrange is one undo step.

**New workflow** opens the template gallery: a blank graph, four starters (Chatbot, RAG Q&A, Approval flow, Router), and your templates or the organisation's. Each template has a preview. **Save as template** copies the saved graph. Organisation scope needs `org.manage`. Export and import use `*.template.json` (`{"format": "langgraph-studio/template", "version": 1, ...}`). Templates never contain credentials, knowledge bases, MCP servers, approval channels, subgraph links, headers, or API keys. Those fields are emptied. Deleting a template requires typing its name.

The moon/sun control on every screen stores the theme in `localStorage`. `?theme=dark` forces dark mode. Colours come from the Tailwind v4 and shadcn theme, not hard-coded palette values.

The UI is English and Vietnamese (`frontend/src/locales/en.json` and `vi.json`). The default follows the browser. The language button on the login screen and the top bar stores the choice in `localStorage.lang`. API errors are translated by `error.code`. An unknown code shows the server's English message.

## Nodes

```json
{"name": "...", "state": [{"name": "message", "type": "string"}],
 "nodes": [{"id": "n1", "type": "llm", "position": {"x": 0, "y": 0},
            "data": {"label": "..", "model": "gpt-4o-mini", "prompt": "Hi {{state.message}}", "output_field": "answer"}}],
 "edges": [{"id": "e1", "source": "a", "target": "b"}]}
```

- **LLM.** `model`, `prompt` with `{{state.field}}`, `output_field`. While a run is going, token deltas arrive as `node_token` events and show in the Logs row and the Output tab. They are not stored in run history. The final text is unchanged.
- **Tool.** `mode=function` plus a name registered with `@register_tool` in `backend/app/engine/tools.py` (for example `lookup_order`), or `mode=http` plus `method`, `url`, and a templated `body`.
- **Condition.** `field`. Outgoing edge labels are matched exactly, then case-insensitively, then as a substring. An optional `default` edge is the fallback.
- **Parallel branches.** Several outgoing edges from a node that is not a Condition run in the same superstep. A state field written by more than one branch needs a reducer: `append` (list), `merge` (object), or `add` (number). The default is `replace`. A missing reducer fails validation.
- **Join.** Waits for every incoming branch, then runs once. It needs at least two incoming edges and cannot take an edge straight from a Condition.
- **Subgraph.** `workflow_id` of one of your saved workflows. Inner nodes appear in the trace as `Subgraph › node` (id `sub/node`). State is shared by field name. Cycles, a missing or imported child, and nesting deeper than five levels fail on save and on run (`WORKFLOW_INVALID`).
- **MCP tool.** `server_id`, `tool`, `arguments` (strings are templates; an exact `{{state.x}}` keeps its type), `output_field`.
- **Retriever.** `knowledge_base_id`, `query`, `top_k` (1–20), `output_field`. The result is a list of `{text, score, filename, …}`.
- **Human.** `prompt` and `output_field`. The run waits. See [Human approval](#human-approval).
- **Code.** Read-only nodes produced by repo import. The right panel shows the original source. Editing the canvas does not change the imported file.

The seeded **Customer Support** example is Start → Classify intent → Route on `intent` → `order_status` (lookup, then reply) or `general` (answer) → End. Try `{"message": "Where is order A100?"}` and `{"message": "What are your hours?"}`.

## Local LLM providers

**Credentials** on the top bar edits providers. Each provider is a small class in `backend/app/engine/providers.py`.

| Provider | Default base URL | API key | Model list |
| --- | --- | --- | --- |
| Ollama | `http://localhost:11434` | not required | `/api/tags` |
| LM Studio | `http://localhost:1234/v1` | not required | `/v1/models` |
| OpenAI-compatible (vLLM, llama.cpp, LocalAI) | `http://localhost:8000/v1` | depends on the server | `/v1/models` |
| OpenRouter | `https://openrouter.ai/api/v1` | required, plus optional `HTTP-Referer` and `X-Title` | `/api/v1/models` |
| OpenAI, Anthropic | as before | required | `/models`, `/v1/models` |

**Test connection** lists models, before or after save. Failures use `PROVIDER_UNREACHABLE`, `PROVIDER_AUTH_FAILED` (HTTP 400, so the UI does not treat it as an expired session), `PROVIDER_BAD_RESPONSE`, and `MODEL_NOT_FOUND`. See `docs/api-errors.md`.

Keys are encrypted with Fernet (`STUDIO_SECRET_KEY`, or a generated `~/.langgraph-studio/secret.key` / `STUDIO_SECRET_KEY_FILE`, mode 0600). The API returns only the last four characters. Losing the key makes old credentials unreadable. The edit form keeps the stored key when the field is left blank. The provider cannot be changed after create.

Chat uses LangChain (`ChatOllama`, or `ChatOpenAI` with `base_url`) so streaming and tool calling work when the model supports them. OpenAI and Anthropic chat still use their plain HTTP path.

Inside Compose, `localhost` is the container. `api` and `worker` set `extra_hosts: host.docker.internal:host-gateway`. Point Ollama at `http://host.docker.internal:11434` and LM Studio at `http://host.docker.internal:1234/v1`. On Linux, run `OLLAMA_HOST=0.0.0.0 ollama serve` and enable LM Studio's *Serve on Local Network*. The firewall may need the Docker bridge (`sudo iptables -I INPUT -i br-+ -j ACCEPT` or `-i docker0`).

Knowledge-base embeddings use the same credentials. Default local model for Ollama is `nomic-embed-text` (`ollama pull nomic-embed-text`). **Test embedding** reports the vector size. Each knowledge base stores `dims`. A vector of a different size returns `KB_EMBEDDING_DIMENSION_MISMATCH`; re-index to adopt the new size. Anthropic does not support embeddings.

## Import a LangGraph repo

Import is experimental and **off** until `STUDIO_ENABLE_IMPORT=1`. While it is off, `POST` and `GET` `/api/import*` return 404 `IMPORT_DISABLED` and the **Import repo** button stays hidden. `GET /api/health` reports `import_enabled`.

On `/workflows`, **Import repo** takes a public GitHub URL (optional branch and subdirectory) or a zip. The dialog shows fetching, installing, inspecting, and ready. Pick one graph and create a workflow.

What the backend does (`backend/app/engine/repo_import.py`, `backend/app/engine/sandbox/container.py`, `backend/app/engine/sandbox/runner.py`):

1. `git clone --depth 1`, or a zip extract that rejects zip-slip paths, into `~/.langgraph-studio/imports/<job_id>/` (`STUDIO_IMPORT_DIR`). Clone and extract run on the API process. The API image includes `git`. `python:3.12-slim` does not.
2. With the flag on, `python -m venv` and `pip` run **inside Docker** (`STUDIO_IMPORT_IMAGE`, default `python:3.12-slim`). Packages come from `pyproject.toml` / `setup.py` (`pip install -e .`) or `requirements.txt`, always plus `langgraph` and `python-dotenv`.
3. Graphs come from `langgraph.json`, or from a scan for `StateGraph` and `x = ….compile(…)`. The scan only reads files.
4. `runner.py inspect` calls `graph.get_graph(xray=True)` (120s, `STUDIO_INSPECT_TIMEOUT`). Docker inspect uses `--network none`.
5. `__start__` / `__end__` become Start / End. Other nodes become read-only Code nodes. The frontend lays them out with dagre.

A run executes the **original** graph through `runner.py run` (`graph.astream`). Events become `node_started` / `node_finished`. Put runtime context in the input under `__context__`. A missing key named in `.env.example` is reported on the error. Import runs read `STUDIO_RUN_TIMEOUT` when the process starts (default 300s). A timeout or an OOM (exit 137) is one `error` event, for example `Sandbox stopped (time limit (12s)).`.

The sandbox is `docker run` with a read-only root, only the job directory mounted read-write, a read-only copy of `runner.py` at `/opt/studio-runner`, all capabilities dropped, `no-new-privileges`, a tmpfs `/tmp`, and limits: memory `STUDIO_IMPORT_MEMORY` (default `1g`, swap equal to memory), CPU `STUDIO_IMPORT_CPUS` (default `1`), pids `STUDIO_IMPORT_PIDS` (default 256). The process does not receive the server environment. Injected names are those declared in `.env.example` that exist on the server, plus `STUDIO_IMPORT_SECRETS`. `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`, and every `STUDIO_*` name are never injected. `localhost` inside the sandbox is the container. Install uses network `bridge`. Inspect uses `none`. A run uses `STUDIO_IMPORT_NETWORK` (`bridge` or `none`, default `bridge`). There is no silent fallback to a subprocess while the runtime is Docker.

`STUDIO_IMPORT_RUNTIME=subprocess` exists for tests and machines without Docker. It is the same OS user as the API. It is not a sandbox. With the flag off and the runtime unset, an **already imported** graph also runs that way, so the server environment is trimmed rather than isolated.

Compose mounts `/var/run/docker.sock` into `api` and `worker` even while import is off. That socket is root-equivalent on the daemon. Do not enable import on a host you do not trust. Before `docker compose up` export `STUDIO_ENABLE_IMPORT=1` and `STUDIO_IMPORT_HOST_DIR="$PWD/.imports"` (the absolute host path of the bind mount) and `mkdir -p` that directory. On Linux, if user `studio` (uid 10001) cannot open the socket: `STUDIO_DOCKER_GID="$(stat -c %g /var/run/docker.sock)"`. Without `STUDIO_IMPORT_HOST_DIR` the daemon mounts the in-container path and the sandbox fails. `./dev.sh` on the host does not need that variable. If `docker` is not on `PATH`, the API uses Docker Desktop's CLI at `/Applications/Docker.app/Contents/Resources/bin/docker`. gVisor and Firecracker are not supported.

Jobs persist as `job.json`. A restart marks an in-progress job (`queued`, `fetching`, `installing`, `inspecting`) as `Import interrupted by a restart` when its pid is gone. A workflow created from the job is marked `keep` and is not cleaned up. Other directories older than `STUDIO_IMPORT_MAX_AGE_HOURS` (default 72, `0` disables cleanup) are deleted when the next import starts. A source tree over `STUDIO_IMPORT_MAX_BYTES` (default 200 MB, `.git` excluded) is rejected. Private repos, JS monorepos, and complex `langgraph.json` files are not supported.

If the imported graph has no checkpointer, the runner attaches an in-memory saver and sends a serialized checkpoint to the server. Recovery starts a new container (Docker runtime) or a new subprocess (`STUDIO_IMPORT_RUNTIME=subprocess`). There is no ledger inside the imported repo. State that cannot be serialized, or is larger than 2 MB, starts again from the beginning.

Checked before the sandbox work: `langchain-ai/new-langgraph-project` runs without a key. `langchain-ai/react-agent` imports and shows its loop, and a run asks for the missing provider key.

## Runs, traces, and limits

The Logs tab is one row per node step: status, name, kind, duration, a waterfall bar, and tokens when the model reports them. Loops show `#2`, `#3`, and so on. A row, or a node on the canvas, opens Input, Output, State diff, and Raw. **Raw events** is the original stream. History replays the same timeline.

**Step** runs one superstep and pauses that same run so you can inspect it. **Continue** runs the rest. Select a node and **Run to here** runs until that node finishes, then pauses. If the path never reaches it, the run finishes and reports that. The pause is status `paused`, not a human approval. A superstep that is only Start does not use up the step.

**Cancel** sends `{"type":"cancel"}`. Closing the tab also cancels. Cancel is cooperative: it stops between steps, so an LLM or HTTP call already in flight may finish. Stored statuses are `ok`, `error`, `cancelled`, `timeout`, and `paused`. Errors are one line, with `sk-…`, `Bearer …`, and `api_key=…` redacted.

| Variable | Default | Meaning |
| --- | --- | --- |
| `STUDIO_RECURSION_LIMIT` | 25 | Max steps per run. A loop that never passes a Condition stops with an error. |
| `STUDIO_RUN_TIMEOUT` | 120 seconds | Max duration of a normal run, then status `timeout`. Import reads this at process start and defaults to 300 when unset. |
| `STUDIO_EVENT_MAX_BYTES` | 262144 | Max size of one event. Oversized fields become `{"_truncated": true, ...}`. |
| `STUDIO_RUN_MAX_BYTES` | 2097152 | Max stored events for one run. The middle is replaced by `{"type":"truncated","dropped":n}`. |
| `STUDIO_INPUT_MAX_BYTES` | 262144 | Max run input. |
| `STUDIO_WORKFLOW_MAX_BYTES` | 1048576 | Max workflow JSON. Larger saves return HTTP 413. |

The timeline also clips `input` and `delta` at 16 000 JSON characters so the page stays light. The validator rejects edges to missing nodes, duplicate ids, more than one Start, a self-edge (except on a Condition), a cycle that does not pass through a Condition, and unreachable nodes. `STUDIO_ENABLE_DEMO_TOOLS=1` registers `sleep_demo` (1.5s) for cancel and timeout tests.

Each run summary shows duration, input and output tokens, USD cost, and error count, on the Logs summary, on LLM spans, and in History. Mock mode estimates tokens and costs `$0`. A model missing from `backend/app/engine/usage.py` shows a cost of `—`. Override prices with `STUDIO_PRICES='{"my-model": [1.0, 2.0]}'` or `STUDIO_PRICES_FILE` (USD per 1M tokens). The longest matching prefix wins.

OpenTelemetry emits one trace per run and one span per node (`gen_ai.usage.*` and cost). With no exporter, tracing is a no-op. Spans go out when each node finishes. A waiting human-in-the-loop run is traced when it ends.

| Destination | Variables |
| --- | --- |
| OTLP (Jaeger, Tempo, a collector) | `OTEL_EXPORTER_OTLP_ENDPOINT` and the standard `OTEL_*` variables |
| LangSmith | `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true`, plus optional `LANGSMITH_PROJECT` and `LANGSMITH_ENDPOINT` |
| "Open trace" in the UI | `STUDIO_TRACE_URL`, for example `http://localhost:16686/trace/{trace_id}` |

When Studio's LangSmith exporter is on, LangChain's own LangSmith tracer is turned off, so each LLM call is exported once. `STUDIO_OTEL_METRICS=1` with an OTLP endpoint also exports `studio.runs`, `studio.run.duration`, `studio.tokens`, `studio.cost`, and `studio.errors`.

```bash
# .env, then:
docker compose --profile tracing up --build   # Jaeger UI: http://localhost:16686
```

Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318` and `STUDIO_TRACE_URL=http://localhost:16686/trace/{trace_id}`. Without Compose: `docker run -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one` and point the backend at `http://localhost:4318`.

Side effects are effectively-once. Each LLM or Tool execution has an idempotency key fixed by run, node, and iteration. HTTP tools send `Idempotency-Key`, `X-Studio-Run-Id`, and `X-Studio-Attempt`. A Python tool receives `idempotency_key` when it declares that parameter. A recovered job reuses the same key. Finished side-effect nodes are replayed from a ledger (`reused` in the trace) instead of running again. The ledger is deleted when the run ends. Each time a worker takes a run, `runs.lease_gen` increases. Writes must carry that fencing token. A worker that lost the lease cannot commit and stops.

## Human approval

A **Human** node pauses the run in status `waiting`. The Logs tab offers **Approve** (`approved`), **Reject** (`rejected`), or free text, written to `output_field`. A Condition can branch on that value. The workflow list shows runs waiting for you. Checkpoints live in the database, so a restart can resume. Only the run's owner can approve or cancel. Waiting time does not count toward run duration. A wait longer than `STUDIO_WAIT_TTL` seconds (default 7 days, `0` never) becomes `expired` (`410 RUN_EXPIRED` on resume).

```text
GET  /api/runs/pending
WS   /ws/run   {"resume_run_id": "...", "response": "approved"}
POST /api/runs/{id}/cancel
```

The header badge counts runs waiting for you. The bell lists unread notifications (`GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`) and receives them live on `/ws/notifications`, falling back to a 30s poll. Preferences are per user. Set `SMTP_HOST` (and `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS` or `SMTP_SSL`) to send mail. Links use `STUDIO_PUBLIC_URL`. Leave `SMTP_HOST` empty to keep mail off. `STUDIO_NOTIFY_WEBHOOK_URL` posts JSON for each `waiting` or `expired` run, signed with `STUDIO_NOTIFY_WEBHOOK_SECRET` when that is set.

Slack and Telegram can carry the same Approve / Reject buttons. The click is mapped through a **verified chat account**. Only the run owner or an email listed on the node may approve. The button token is HMAC-signed, single-use, and expires (`STUDIO_APPROVAL_TTL`, default 86400s). Messages follow the run owner's language. With no channel configured, nothing is sent.

Slack and Telegram need a public HTTPS `STUDIO_PUBLIC_URL`. For local development, `cloudflared tunnel --url http://localhost:8000` or `ngrok http 8000` is enough.

- Slack callback: `POST {STUDIO_PUBLIC_URL}/api/approvals/callback/slack` (routed by `team_id`, so one person can connect several workspaces). The per-channel URL still works.
- Telegram callback: `POST {STUDIO_PUBLIC_URL}/api/approvals/callback/telegram/{channel_id}`. **Register webhook** calls `setWebhook`.

**Slack app.** Create an app at https://api.slack.com/apps. Bot scopes: `chat:write`, `im:write`, and `chat:write.public` if the bot should post in public channels it has not joined. Install it, copy the bot token (`xoxb-…`) and the signing secret. In Studio, **Settings → Channels** (`/settings/channels`), paste both, and save. Copy the request URL into **Interactivity & Shortcuts**. Invite the bot and use the channel id (`C…`). Each approver copies their Slack member id, receives a 6-digit code by DM, and verifies it under **My accounts**.

**Telegram bot.** `/newbot` with @BotFather, paste the token, save, then **Register webhook** (`STUDIO_PUBLIC_URL` must be https). Add the bot to the chat and use that chat id. Each approver presses **Start**, then verifies their Telegram user id the same way. The webhook is checked with `X-Telegram-Bot-Api-Secret-Token`.

Unverified clicks are rejected (`APPROVAL_IDENTITY_UNKNOWN`). Codes last `STUDIO_IDENTITY_CODE_TTL` seconds (600), allow `STUDIO_IDENTITY_CODE_ATTEMPTS` tries (5), and can be resent after `STUDIO_IDENTITY_CODE_RESEND` seconds (30). One verified studio user owns a chat identity. Public callbacks are rate-limited per IP (`STUDIO_CALLBACK_RATE_LIMIT_IP`, 60) and per connection (`STUDIO_CALLBACK_RATE_LIMIT_CHANNEL`, 300) per `STUDIO_CALLBACK_RATE_WINDOW` seconds (60). Behind the Compose nginx proxy, `STUDIO_TRUSTED_PROXIES` lists the proxy CIDRs. `X-Forwarded-For` is read from the right, skipping trusted hops, and only when the direct peer is a trusted proxy. Answering in Studio disables the chat buttons. Cancel and expiry close the request.

`SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, and `SLACK_SIGNING_SECRET` enable **Add to Slack**. The redirect URL is `{STUDIO_PUBLIC_URL}/api/approvals/slack/oauth/callback`. Pasting a bot token still works when those are empty.

## API triggers and webhooks

Every HTTP response is an envelope: `{"success": true, "data": …, "error": null}` or `{"success": false, "data": null, "error": {"code": "…", "message": "…", "details": …}}`. Codes are listed in `docs/api-errors.md`.

**API** on the editor toolbar creates a token (`wft_…`, shown once) and a signing secret (`whsec_…`, shown once). Revoke either at any time.

```bash
curl -X POST http://localhost:8080/api/hooks/workflows/<wid>/runs \
  -H "Authorization: Bearer wft_..." -H "Content-Type: application/json" \
  -d '{"input": {"message": "hi"}, "mode": "sync"}'
```

`sync` waits for `final_state`, at most `STUDIO_SYNC_WAIT_MAX` seconds (default 30), then returns 202 with `poll_url`. `async` (the default) returns `202 {run_id, status: "queued"}`. Poll with `GET /api/hooks/workflows/<wid>/runs/<run_id>`. `callback_url` receives a POST with `X-Studio-Event: run.finished`. Private addresses are blocked unless `STUDIO_ALLOW_PRIVATE_CALLBACKS=1`. A bad token is `401 TRIGGER_TOKEN_INVALID`. API runs show an **API** badge in History.

Each callback is signed. `v1` is HMAC-SHA256 of `"<t>.<raw body>"`. Reject a timestamp more than five minutes off. After a secret rotation the previous secret stays valid for `STUDIO_SECRET_GRACE` seconds (default one day) and the header carries two `v1` values. Accept the header when any `v1` matches.

```python
import hashlib, hmac, time
def verify(secret: str, header: str, body: bytes, tolerance=300) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    if abs(time.time() - int(parts["t"])) > tolerance:
        return False
    mac = hmac.new(secret.encode(), f'{parts["t"]}.'.encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, parts["v1"])
```

Each token may start `STUDIO_TRIGGER_RATE_LIMIT` runs per `STUDIO_TRIGGER_RATE_WINDOW` seconds (default 60/60). Over the limit the API returns `429 RATE_LIMITED` and `Retry-After`. Polling is not limited. The counter is shared through Redis. Without Redis each process counts on its own.

Deliveries are stored with status, attempts, HTTP code, and latency, under **Deliveries** in the API dialog, with **Resend**. Network errors and non-2xx responses retry with backoff `min(STUDIO_WEBHOOK_BACKOFF_BASE^n, STUDIO_WEBHOOK_BACKOFF_MAX)`, up to `STUDIO_WEBHOOK_MAX_ATTEMPTS`. An address blocked by the SSRF guard fails immediately. Receivers should deduplicate on `run_id` plus the event. The hostname is resolved once. Every resolved address is checked, then the connection goes straight to that IP. Redirects are not followed.

Jobs run on a worker. `STUDIO_WORKER=1` (the default) runs it inside the API process. With `REDIS_URL`, a separate process is `python -m app.worker`. Compose includes a `worker` service (`docker compose up --scale worker=3`). The in-memory queue is for development only. Jobs vanish when that process restarts. On Redis the worker leases a job for `STUDIO_JOB_VISIBILITY_TIMEOUT` seconds and renews the lease. `STUDIO_JOB_REAP_EVERY` requeues jobs whose lease expired. A recovered job continues from the last checkpoint (`run_recovered`). The node that was in flight may run again, so HTTP and tool nodes should be idempotent. There is no cron scheduler.

A save that changes the graph, a rename, a duplicate, or an import writes an immutable version with author and time. A save with no change does not. Graphs that existed before versions shipped are v1. **Versions** lists them, diffs any two, and restores. Restore copies the old graph forward as a new latest version and keeps the current name. Restoring content that already matches does nothing. Each run in History is labelled `vN`, or **unsaved** when the editor had unpublished edits. Moving a node without changing the graph is not a change.

```text
GET  /api/workflows/{wid}/versions?limit=50&offset=0
GET  /api/workflows/{wid}/versions/{n}
GET  /api/workflows/{wid}/versions/diff?a=1&b=2
POST /api/workflows/{wid}/versions/{n}/restore
```

`STUDIO_VERSION_KEEP=N` keeps the newest N versions. A version that a run used is never deleted. `404 VERSION_NOT_FOUND` is the missing-version error.

## Knowledge, MCP, and access

**Settings → Knowledge** creates a base and accepts `.txt`, `.md`, and `.pdf` up to 10 MB. You can search, change the model or credential, and re-index. Embeddings use the base's credential, then `OPENAI_API_KEY`, then a fixed offline mock (`mock:512`). The default OpenAI model is `text-embedding-3-small`. Compose Postgres is `pgvector/pgvector:pg17` and searches in SQL. Plain Postgres and SQLite store JSON and score cosine similarity in Python. Codes are `KB_*` in `docs/api-errors.md`.

**Settings → MCP servers** registers a Streamable HTTP server (URL and secret headers) or a stdio command. **Find tools** lists what the server offers. Scope is personal or organisation. Secrets are encrypted. The API returns names and masked values. HTTP URLs must be public (the connection is pinned to the checked IP) unless `STUDIO_MCP_ALLOW_PRIVATE=1`. Stdio is off until `STUDIO_MCP_STDIO=1`, and only an admin can register a command. The process gets a clean environment, an empty temporary home, and `STUDIO_MCP_TIMEOUT` (30s), then the whole process group is killed. That is not a sandbox. Run untrusted MCP servers as their own HTTP container.

Roles are `admin`, `editor` (the default: create workflows, credentials, knowledge bases, MCP servers, and personal channels), and `viewer` (open and run what was shared). There is no SSO. **Settings → Users** changes roles and disables accounts immediately, including open sockets. You cannot change your own role or disable yourself, and one active admin must remain. `STUDIO_ADMIN_EMAILS` is only a bootstrap: those addresses become admin at sign-up, and at startup only when no active admin remains. `STUDIO_DEFAULT_ROLE=viewer` makes new accounts view-only.

**Share** (owner or admin) adds an email as viewer or editor, or shares with a whole team. The effective right is the highest of the direct share and the team shares. Viewers see a read-only editor. A shared run uses the **owner's** credentials, knowledge bases, MCP servers, and subgraphs. The owner and admins see every run. Everyone else sees their own. **Transfer ownership** requires the recipient to be an editor or admin. Resources they cannot use can be reassigned or kept and flagged. **Settings → Activity** is the admin audit log. Deleting a user anonymises them and keeps runs, or deletes the runs too. Their workflows must be transferred first. Admins choose which roles may use organisation approval channels and MCP servers.

## Docker Compose

Postgres 17 with pgvector, Redis 7, the API (Alembic upgrade and seed on startup), a worker, and nginx serving the Vite build. The UI is http://localhost:8080 (`WEB_PORT`).

```bash
cp .env.example .env          # set JWT_SECRET and POSTGRES_PASSWORD; do not commit .env
docker compose up --build
python scripts/compose_smoke.py http://localhost:8080
```

`GET /api/health` reports `database` (`postgresql` or `sqlite`) and `run_bus` (`redis` or `memory`). An empty `STUDIO_SECRET_KEY` is generated once into the `apidata` volume (`/data/secret.key`). Set it explicitly for production, with `STUDIO_ENV=production`. Leave `DATABASE_URL` empty in local dev to use SQLite `backend/studio.db`. Leave `REDIS_URL` empty to keep the run bus in memory. The full variable list is `.env.example`.

Startup migrations take a lock so several processes do not migrate at once (a Postgres advisory lock, or `<db>.migrate.lock` for SQLite).

The backend is layered `core / models / schemas / repositories / services / api / engine`. The diagram and import rules are in `docs/backend-architecture.md`. Schema changes go through Alembic:

```bash
cd backend && .venv/bin/alembic revision --autogenerate -m "describe"
.venv/bin/alembic upgrade head
```

## Tests

```bash
cd backend && .venv/bin/python -m pytest -q
cd frontend && npm run build && npm run lint
```

Install the backend with `pip install -e "backend[dev]"`. Playwright starts its own API on port 8100 and Vite on port 5190:

```bash
cd frontend && npx playwright install chromium
npm run e2e
SHOTS=1 npm run e2e -- screenshots
```

`E2E_UVICORN` overrides the uvicorn binary (default `backend/.venv/bin/uvicorn`). `PW_CHROME` points at an installed Chrome. End-to-end tests are not on CI. GitHub Actions (`.github/workflows/ci.yml`) runs pytest on Python 3.12, the frontend build on Node 20 and 22, and a Compose smoke test. `factory-verify.yml` checks the factory metadata.

Postgres and Redis locally:

```bash
cd backend
DATABASE_URL=postgresql://… TEST_DATABASE_URL=postgresql://… \
  REDIS_URL=redis://localhost:6379/0 .venv/bin/python -m pytest -q
```

The Postgres tests need a role with `CREATEDB`.

## Layout

| Path | Contents |
| --- | --- |
| `frontend/` | React, TypeScript, Vite, React Flow, Tailwind v4, shadcn/ui |
| `backend/app/` | FastAPI app. Routers call services. Services call repositories and the engine. |
| `docs/api-errors.md` | Error codes |
| `docs/backend-architecture.md` | Layer rules |
| `docs/ui-conventions.md` | UI rules |
| `.env.example` | Every Compose and runtime variable |
| `roadmap.md` | What has shipped |
