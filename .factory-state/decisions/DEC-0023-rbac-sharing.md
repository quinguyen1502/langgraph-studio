# Decision

## Metadata

- Decision ID: DEC-0023
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0014, REQ-0012, DEC-0019 (approval channels, Slack leftover), DEC-0021, DEC-0022, ARCH-0001

## Context

REQ-0012 asked for RBAC and workflow sharing, with an open question about SSO. The owner decided (2026-10-17): roles and permissions without SSO; an admin UI for users and roles that replaces `STUDIO_ADMIN_EMAILS` as the only way to make admins, while keeping it as a bootstrap; workflow sharing; and the Slack OAuth app distribution left over from DEC-0019.

## Decisions

### Roles and permissions: fixed in code
- `core/permissions.py` is the single source of truth: three global roles (`users.role`) with fixed permissions. The API, the admin UI matrix (`GET /api/roles`, `GET /api/admin/users`) and the tests all read from it.

| Permission | admin | editor | viewer |
|---|---|---|---|
| `users.manage`: list users, change roles, (de)activate | ✓ | | |
| `org.manage`: org channels / MCP servers, stdio MCP | ✓ | | |
| `workflows.all`: owner-level access to every workflow | ✓ | | |
| `workflows.create`: create, import, duplicate, ad-hoc runs | ✓ | ✓ | |
| `resources.manage`: own credentials, knowledge bases, MCP servers, channels | ✓ | ✓ | |

- Why no custom roles: three roles cover the requirement (viewer / editor / admin). Editable permission sets would need a role table, an editor UI and migrations of their own (KISS). The matrix is code, so adding a role is one dictionary entry.
- Migration `0021_rbac` adds `users.role` (default `editor`) and `users.active`, copies `is_admin = true` to `role = 'admin'`, then drops `is_admin`. `User.is_admin` stays as a read-only property, so existing callers keep working. The migration was tested on SQLite and Postgres with a backfill test.
- New accounts get `STUDIO_DEFAULT_ROLE` (`editor`; `viewer` is allowed, `admin` never). Viewers get no copy of the example workflow.

### Workflow access
- `workflow_shares (workflow_id, user_id, role, created, shared_by)` with share roles `viewer` (open, run) and `editor` (also edit and save). The owner and admins have every action: view, run, edit, delete and share. API tokens and deliveries count as "share" because they let outsiders start runs. A global viewer is capped at viewer on every share.
- One `AccessService` (`services/access.py`) answers every check: `workflow(wid, uid, action)` returns the row or raises `WORKFLOW_NOT_FOUND` (no access, so the id is not disclosed) or `WORKFLOW_FORBIDDEN` (visible, but that action is not allowed). It replaces every `get_owned` call in the workflow, run, trigger and delivery services. The services take it as an optional dependency (`None` = the old owner-only behaviour, used by unit-test fakes).
- An editor saving a shared workflow updates it in place. The owner never changes, and response-only fields (`access`, `mine`, `owner_email`) are never stored.
- **Runs use the owner's resources.** A saved workflow resolves credentials, knowledge bases, MCP servers and subgraphs as its owner, so sharing a workflow does not require sharing its keys and a viewer cannot point it at their own. Users without edit access always run the stored graph (inline JSON is ignored). Ad-hoc graphs need `workflows.create`.
- Run history: the owner and admins see every run of a workflow; anyone else sees only their own runs (runs can contain personal inputs).
- Sharing is by e-mail of an active account. There are no groups or teams (open), no link sharing, and no transfer of ownership (open).

### Accounts: checked on every request
- `current_user` and both WebSockets now resolve the token against the database (`AuthService.current`). A deactivated or deleted account loses access immediately, including open sessions (`AUTH_ACCOUNT_DISABLED`), instead of when its JWT expires. The cost is one primary-key lookup per request.
- `/api/me` and the login/register responses carry `role`, `permissions` and `is_admin`. The UI reads `/api/me` (`lib/rbac.ts`) and does not trust the stored copy.
- Guards: an admin cannot change their own role or deactivate themselves (`USER_SELF_CHANGE`), and the last active admin cannot be demoted or deactivated (`USER_LAST_ADMIN`).

### STUDIO_ADMIN_EMAILS is now a bootstrap
- At sign-up, listed e-mails become admins. At start-up, listed accounts are promoted and reactivated **only when no active admin exists** (lockout recovery). The first account (the demo user) is created as admin. In development, the demo user is promoted again only if no admin is left. Previously every start re-promoted everyone listed, which would have silently undone demotions made in the UI.

### Add to Slack (DEC-0019 leftover)
- With `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET` and `STUDIO_PUBLIC_URL` set, the Slack card shows **Add to Slack**. `POST /api/approvals/slack/oauth/start {scope}` returns the authorize URL. The `state` is HMAC-signed (key derived from the studio secret: user, scope, 10-minute expiry, nonce). Slack redirects to `GET /api/approvals/slack/oauth/callback`, which verifies the state and that the account is still active, exchanges the code with `oauth.v2.access` (client credentials in Basic auth), and saves the workspace as a normal Slack connection: the bot token plus the app's single signing secret, through `ChannelService.create`, so validation, `auth.test`, scopes and admin rules are the same as for a pasted token. The browser lands on `/settings/channels?slack=installed` or `?slack_error=CODE`.
- Bot scopes are the same as the manual setup (`chat:write`, `chat:write.public`, `im:write`). Pasting a token still works. Enterprise Grid org-wide installs remain unsupported.

## Error codes
`AUTH_ACCOUNT_DISABLED`, `PERMISSION_DENIED`, `USER_NOT_FOUND`, `USER_ROLE_INVALID`, `USER_LAST_ADMIN`, `USER_SELF_CHANGE`, `SHARE_USER_NOT_FOUND`, `SHARE_ROLE_INVALID`, `SHARE_OWNER`, `SHARE_NOT_FOUND`, `SLACK_OAUTH_NOT_CONFIGURED`, `SLACK_OAUTH_STATE_INVALID`, `SLACK_OAUTH_FAILED`: in the catalog, `docs/api-errors.md` and en/vi.

## Consequences / open
- Resolved by TASK-0029 / DEC-0024: teams, ownership transfer, audit log, user deletion and the org-resource run-time policy (items below kept for history).
- No groups or teams, no ownership transfer, and no audit log of role and share changes.
- An org-scope resource (approval channel, MCP server) is still usable by every active account, viewers included, when a workflow they may run references it.
- Users cannot be deleted from the UI, only deactivated (their workflows and runs stay).
