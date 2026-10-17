from . import approvals, auth, credentials, imports, knowledge, mcp, meta, notifications, runs, runs_ws, triggers, workflows

ROUTERS = [auth.router, meta.router, workflows.router, credentials.router, imports.router, runs.router, runs_ws.router, triggers.router,
           notifications.router, notifications.ws_router, approvals.router, knowledge.router, mcp.router]
