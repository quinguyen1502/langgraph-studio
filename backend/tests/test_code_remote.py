"""STUDIO_CODE_RUNTIME=remote: Code calls go to the sandbox service (app.sandbox_service) over HTTP with a token."""
import shutil, threading, time
import httpx, pytest
from app import sandbox_service
from app.core.errors import AppError
from app.engine import code_runtime as cr
from app.engine.sandbox import remote

TOKEN = "test-sandbox-token-0123456789"
UPPER = 'def main(state):\n    print("got", state["message"])\n    return state["message"].upper()\n'


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv("STUDIO_CODE_NO_NETWORK", "1")  # as in the sandbox image
    srv = sandbox_service.make_server("127.0.0.1", 0, TOKEN)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    monkeypatch.setenv("STUDIO_ENABLE_CODE_NODES", "1"); monkeypatch.setenv("STUDIO_CODE_RUNTIME", "remote")
    monkeypatch.setenv("STUDIO_SANDBOX_URL", url.removeprefix("http://"))  # a bare host:port gets http://
    monkeypatch.setenv("STUDIO_SANDBOX_TOKEN", TOKEN); remote.forget()
    yield url
    srv.shutdown(); remote.forget()


def test_runs_python_remotely(service):
    assert cr.unavailable() is None
    r = cr.run_code(UPPER, {"message": "hi"})
    assert r.value == "HI" and r.stdout == "got hi\n" and r.runtime == "remote"


def test_code_errors_come_back_as_code_failures(service):
    with pytest.raises(cr.CodeFailure) as e: cr.run_code('def main(state):\n    return 1 / 0\n', {})
    assert e.value.code == "CODE_FAILED" and "ZeroDivisionError" in e.value.message


@pytest.mark.parametrize("code", [
    'import socket\ndef main(state):\n    socket.create_connection(("1.1.1.1", 53), timeout=2)\n',
    'import subprocess\ndef main(state):\n    return subprocess.run(["id"]).returncode\n',
    'import os\ndef main(state):\n    return os.system("id")\n',
    'import ctypes\ndef main(state):\n    return ctypes.CDLL(None).getpid()\n',
])
def test_no_network_and_no_processes(service, code):
    with pytest.raises(cr.CodeFailure) as e: cr.run_code(code, {})
    assert "PermissionError" in e.value.message and "no network" in e.value.message


def test_time_limit_is_enforced_by_the_service(service, monkeypatch):
    monkeypatch.setenv("STUDIO_CODE_MAX_SECONDS", "1")
    t0 = time.monotonic()
    with pytest.raises(AppError) as e: cr.run_code('def main(state):\n    while True: pass\n', {})
    assert e.value.code == "CODE_TIMEOUT" and time.monotonic() - t0 < 10


def test_cancel_is_forwarded(service):
    t0 = time.monotonic(); flag = {"stop": False}
    threading.Timer(0.5, lambda: flag.update(stop=True)).start()
    with pytest.raises(AppError) as e: cr.run_code('import time\ndef main(state):\n    time.sleep(20)\n', {}, cancelled=lambda: flag["stop"])
    assert "cancelled" in e.value.message and time.monotonic() - t0 < 10


def test_wrong_token_and_unreachable_service(service, monkeypatch):
    monkeypatch.setenv("STUDIO_SANDBOX_TOKEN", "a-different-token-000000"); remote.forget()
    assert "refused STUDIO_SANDBOX_TOKEN" in cr.unavailable()
    with pytest.raises(AppError) as e: cr.run_code(UPPER, {"message": "x"})
    assert e.value.code == "CODE_RUNTIME_UNAVAILABLE"
    monkeypatch.setenv("STUDIO_SANDBOX_TOKEN", ""); remote.forget()
    assert "STUDIO_SANDBOX_TOKEN is not set" in cr.unavailable()
    monkeypatch.setenv("STUDIO_SANDBOX_TOKEN", TOKEN); monkeypatch.setenv("STUDIO_SANDBOX_URL", "http://127.0.0.1:1"); remote.forget()
    assert "did not answer" in cr.unavailable()


def test_service_api_requires_the_token_and_uses_the_envelope(service):
    assert httpx.get(service + "/healthz").json()["data"] == {"ok": True}
    r = httpx.get(service + "/v1/info"); assert r.status_code == 401 and r.json()["error"]["code"] == "AUTH_TOKEN_INVALID"
    h = {"Authorization": f"Bearer {TOKEN}"}
    info = httpx.get(service + "/v1/info", headers=h).json()["data"]; assert "python" in info["languages"]
    r = httpx.post(service + "/v1/run", headers=h, json={"id": "x", "language": "cobol", "payload": "{}"})
    assert r.json()["error"]["code"] == "CODE_LANGUAGE_UNSUPPORTED"
    r = httpx.post(service + "/v1/runs/nope/cancel", headers=h, json={}); assert r.status_code == 404
    r = httpx.post(service + "/v1/run", headers=h, content=b"x" * (sandbox_service.BODY_MAX + 1))
    assert r.status_code == 413


def test_service_refuses_a_short_token():
    with pytest.raises(SystemExit): sandbox_service.Sandbox("short")


@pytest.mark.skipif(not shutil.which("deno"), reason="Deno is not installed")
def test_runs_typescript_remotely(service, monkeypatch):
    monkeypatch.setenv("STUDIO_CODE_TS_PACKAGES", "")  # no package cache in this test
    r = cr.run_code('export function main(state: { message: string }) { return state.message.length }\n', {"message": "four"}, language="typescript")
    assert r.value == 4 and r.runtime == "remote"
