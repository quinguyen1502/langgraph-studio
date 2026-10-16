# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0006
- Status: Proposed (agent decision within TASK-0005; owner confirms in PR review)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0002
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0005

## Context

REQ-0002 left open the credential scope and first providers. Credentials must be encrypted at rest.

## Decision

- Credentials are owned per user (`credentials` table) and selected per LLM node (`data.credential_id`), so each workflow chooses its own credentials.
- First providers: OpenAI (and OpenAI-compatible via base URL) and Anthropic.
- Encryption: Fernet (`cryptography`), key from `STUDIO_SECRET_KEY` or a 0600 key file (`STUDIO_SECRET_KEY_FILE`, default `~/.langgraph-studio/secret.key`) generated on first use.
- API returns only name, provider, base URL and a masked hint; secrets are decrypted only inside the run worker.
- Nodes without a credential keep the previous behaviour (env `OPENAI_API_KEY`, else deterministic mock).

## Rationale

Smallest model that satisfies per-workflow selection without adding workspaces/RBAC (REQ-0012 later).

## Alternatives Considered

- Option: Workflow-level single credential
  - Benefits: simpler UI
  - Tradeoffs: cannot mix providers in one graph
  - Reason Not Chosen: node-level selection is more flexible at equal cost
- Option: Global admin credentials
  - Benefits: central control
  - Tradeoffs: needs RBAC
  - Reason Not Chosen: deferred to REQ-0012

## Impacts

- New endpoints: `GET/POST /api/credentials`, `DELETE /api/credentials/{id}`, `GET /api/providers`
- Losing the secret key makes stored credentials undecryptable (clear error on run)

## Risks

- Key file on the same host as the DB; production should inject `STUDIO_SECRET_KEY` from a secret manager.

## Approval

- Approved By: pending (owner review on TASK-0005 PR)
- Approved On:
- Scope And Limits: langgraph-studio backend

## Review Or Revisit Trigger

- REQ-0012 (RBAC/sharing) or a move to a managed secret store.
