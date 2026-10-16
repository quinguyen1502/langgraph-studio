from . import auth, credentials, imports, meta, runs, runs_ws, workflows

ROUTERS = [auth.router, meta.router, workflows.router, credentials.router, imports.router, runs.router, runs_ws.router]
