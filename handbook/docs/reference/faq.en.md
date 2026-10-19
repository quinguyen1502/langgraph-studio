# FAQ

**Do I need a model key to try it?**
No. With no credential and no `OPENAI_API_KEY`, LLM nodes use a deterministic
offline mock, Decision nodes return sample answers, embeddings use `mock:512`,
and Send email nodes run dry. Every example and starter template runs.

**Is the workflow JSON tied to the studio?**
The JSON is the studio's own format. The backend compiles it into a regular
LangGraph `StateGraph` at run time; the [Concepts](../start/concepts.md) page
shows the format.

**Can I run an existing LangGraph project?**
Yes, with [repo import](../operate/import.md): the original Python graph runs
in a Docker sandbox and its steps show in the same trace. Imported nodes are
read-only on the canvas.

**How is this different from LangGraph Platform?**
LangGraph Studio is a separate, self-hosted project. It builds graphs visually
as JSON, with approvals, schedules, triggers, versions and roles built in. It
does not replace LangGraph Platform.

**Why did my run stop with a recursion error?**
A loop never passed a Condition that leads out, or the graph took more than
`STUDIO_RECURSION_LIMIT` steps (default 25). For each loops do not count
toward that limit. See [Runs and traces](../run/traces.md#limits).

**Two branches write the same field and Save fails.**
Give the field a reducer (`append`, `merge` or `add`), or write to different
fields. See [State and references](../guide/state.md#reducers).

**My LLM node in Docker cannot reach Ollama.**
Inside Compose, `localhost` is the container. Use
`http://host.docker.internal:11434`. See
[Deploy with Compose](../operate/deploy.md#local-models-from-compose).

**Why is my Code node read-only?**
Writing code needs `code.write`, which only admins have by default. See
[Code mode](../guide/code-mode.md#who-may-write-code).

**Will a recovered run send the e-mail twice?**
No. Finished side-effect nodes are replayed from the ledger, and the e-mail's
`Message-ID` comes from the node's idempotency key. See
[Architecture](architecture.md#effectively-once-side-effects).

**Where are runs stored, and for how long?**
In the database, with their events (capped by `STUDIO_RUN_MAX_BYTES`), the
final state and the version they used. Deleting a user can keep their runs
(anonymised) or delete them.

**Which languages does the UI support?**
English and Vietnamese. The default follows the browser; the language button
stores the choice.
