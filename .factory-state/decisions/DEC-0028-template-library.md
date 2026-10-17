# Decision

## Metadata

- Decision ID: DEC-0028
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0025, REQ-0015, PLAN-0001

## Decisions
- **Built-ins live in code** (`engine/templates.py`: Chatbot, RAG Q&A, Approval flow, Router; ids `builtin-*`), not in the database: always read-only, updated with releases, nothing to seed or migrate.
- **Stored templates** (`workflow_templates`, migration `0023_templates`, SQLite + Postgres): `scope` is `user` (owner only) or `org` (everyone; create/delete needs `org.manage`). Personal templates are purged with the user's personal data (TASK-0029 deletion); org templates are kept.
- **One sanitiser** for save-as, import and use: keeps state/nodes/edges only; blanks `credential_id`, `knowledge_base_id`, `server_id`, `channel_id`, `workflow_id`; drops `headers`, `api_key`, `secret`, `token`, `password`, `authorization` and runtime `_` fields. Templates therefore never carry secrets or another user's resources; the RAG starter intentionally needs "choose a knowledge base" after creation.
- **Portable file** `{"format":"langgraph-studio/template","version":1,name,description,workflow}`. Import checks structure (format, version, Start + End, unique ids, edges between existing nodes) and returns `TEMPLATE_INVALID` with the problems in `details`; full graph validation happens in the editor as for any workflow.
- **Save as template copies the last saved version** (server-side, access-checked by `WorkflowService.get`); the dialog warns (warning token) when there are unsaved changes, instead of silently saving the workflow.
- **Use** goes through `WorkflowService.save` (new id, unique name, `workflows.create` permission), so a template workflow is an ordinary, independent workflow.
- **List payload** carries only node ids/types/positions and edge endpoints for the SVG preview (node colours from the `--node-*` tokens).
- **Codes:** `TEMPLATE_NOT_FOUND`, `TEMPLATE_READ_ONLY`, `TEMPLATE_INVALID`, `TEMPLATE_NAME_REQUIRED`, `TEMPLATE_SCOPE_FORBIDDEN` (catalog, docs/api-errors.md, en+vi). Another user's personal template answers NOT_FOUND (no existence leak).
- **UI:** "New workflow" opens the gallery (Blank is the first card); deleting a template uses ConfirmDeleteDialog (UI-only, DEC-0025).

## Consequences
- No template versioning or editing in place (save a new one and delete the old). No marketplace.
