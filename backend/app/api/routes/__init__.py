from . import approvals, auth, code, users, credentials, imports, knowledge, mcp, meta, notifications, runs, runs_ws, templates, triggers, workflow_tests, workflows

ROUTERS = [auth.router, meta.router, workflows.router, credentials.router, imports.router, runs.router, runs_ws.router, triggers.router,
           notifications.router, notifications.ws_router, approvals.router, knowledge.router, mcp.router, users.router, templates.router, code.router, workflow_tests.router]
