"""All-in-one image: the built frontend (Vite `dist/`) served by the API on the same origin, so one port carries the UI,
/api and /ws (PaaS platforms route one port per service). Unknown non-API paths get index.html (SPA routes); unknown
/api and /ws paths keep the API's 404 envelope."""
import os
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

API_PREFIXES = ("api/", "ws/")


class SPAStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":  # an unknown WebSocket path: refuse instead of StaticFiles' http-only assert
            await send({"type": "websocket.close", "code": 1008}); return
        await super().__call__(scope, receive, send)

    async def get_response(self, path: str, scope):
        try: return await super().get_response(path, scope)
        except HTTPException as e:
            if e.status_code != 404 or path.startswith(API_PREFIXES) or path in ("api", "ws"): raise
            return await super().get_response("index.html", scope)


def mount_frontend(app: FastAPI, directory: str) -> None:
    if directory and os.path.isfile(os.path.join(directory, "index.html")):
        app.mount("/", SPAStaticFiles(directory=directory, html=True), name="frontend")
