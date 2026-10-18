"""Roles and permissions (TASK-0014, DEC-0023). Fixed in code: the single source for the API, the admin UI matrix and tests.

Global role (users.role): what a user may do in the studio.
Workflow access: owner, or a share (viewer | editor); admins act as owner on every workflow."""

ROLES = ("admin", "editor", "viewer")
DEFAULT_ROLE = "editor"

# global permissions
USERS_MANAGE = "users.manage"          # list users, change roles, (de)activate accounts
ORG_MANAGE = "org.manage"              # org-wide approval channels and MCP servers, stdio MCP servers
WORKFLOWS_ALL = "workflows.all"        # owner-level access to every workflow
WORKFLOWS_CREATE = "workflows.create"  # create, import and duplicate workflows
RESOURCES_MANAGE = "resources.manage"  # own credentials, knowledge bases, personal MCP servers, API tokens

PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset({USERS_MANAGE, ORG_MANAGE, WORKFLOWS_ALL, WORKFLOWS_CREATE, RESOURCES_MANAGE}),
    "editor": frozenset({WORKFLOWS_CREATE, RESOURCES_MANAGE}),
    "viewer": frozenset(),  # opens and runs workflows shared with them; creates nothing
}

# workflow actions
VIEW, RUN, EDIT, DELETE, SHARE, TRANSFER = "view", "run", "edit", "delete", "share", "transfer"
SHARE_ROLES = ("viewer", "editor")
WORKFLOW_ACTIONS: dict[str, frozenset[str]] = {
    "owner": frozenset({VIEW, RUN, EDIT, DELETE, SHARE, TRANSFER}),
    "editor": frozenset({VIEW, RUN, EDIT}),
    "viewer": frozenset({VIEW, RUN}),
}


def best_share(roles) -> str | None:
    """The strongest share role among direct and team shares (editor > viewer)."""
    rs = [r for r in roles if r in SHARE_ROLES]
    return "editor" if "editor" in rs else ("viewer" if rs else None)


# org-wide approval channels and MCP servers at run time (admin policy, TASK-0029); admins always may
ORG_RESOURCE_DEFAULT = ("admin", "editor")


def can(role: str | None, permission: str) -> bool:
    return permission in PERMISSIONS.get(role or "", frozenset())


def workflow_role(user_role: str | None, is_owner: bool, share_role: str | None) -> str | None:
    """Effective access to one workflow: owner | editor | viewer | None. A global viewer never edits (share capped)."""
    if is_owner or can(user_role, WORKFLOWS_ALL): return "owner"
    if share_role not in SHARE_ROLES: return None
    return "viewer" if user_role == "viewer" else share_role


def matrix() -> dict:
    """For the admin UI: every role with its permissions, and the workflow access levels."""
    perms = [USERS_MANAGE, ORG_MANAGE, WORKFLOWS_ALL, WORKFLOWS_CREATE, RESOURCES_MANAGE]
    return {"roles": [{"role": r, "permissions": sorted(PERMISSIONS[r])} for r in ROLES], "permissions": perms,
            "workflow_access": [{"access": a, "actions": sorted(WORKFLOW_ACTIONS[a], key=[VIEW, RUN, EDIT, DELETE, SHARE, TRANSFER].index)} for a in WORKFLOW_ACTIONS]}
