"""Tool node Code mode (TASK-0053, REQ-0039, DEC-0041): user Python runs in a sandbox, never in this process.

`run_code` sends {source, state} to `sandbox/code_runner.py` on stdin and reads one JSON result line. The server only
parses the source (`problems`); it never executes it. Docker is the runtime: no network, no mounts, an empty
environment, and memory, CPU and process limits. A call is killed at its time limit or when the run is cancelled."""
from __future__ import annotations
import ast, json, os, subprocess, threading, time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from ..core import config
from ..core.errors import AppError
from .sandbox import container

RUNNER = os.path.join(os.path.dirname(__file__), "sandbox", "code_runner.py")
SOURCE_MAX = 64 * 1024
STATE_MAX = 1024 * 1024
RESULT_MAX = 1024 * 1024
STDOUT_MAX = 64 * 1024
STARTER = 'def main(state):\n    """Return the value for the output field."""\n    return state.get("message", "")\n'
_slots: Dict[int, threading.BoundedSemaphore] = {}
_checked: Dict[str, tuple[float, Optional[str]]] = {}  # image -> (when, problem or None)
CHECK_TTL = 30.0


@dataclass
class CodeResult:
    value: Any
    stdout: str = ""
    runtime: str = "docker"
    duration_ms: float = 0.0

    def trace(self) -> Dict[str, Any]:
        return {"stdout": self.stdout, "runtime": self.runtime, "duration_ms": self.duration_ms}


class CodeFailure(AppError):
    """An AppError that also carries what the code printed and its traceback, for the trace."""

    def __init__(self, code: str, output: Dict[str, Any], **params):
        AppError.__init__(self, code, **params); self.output = output


def problems(source: Any) -> List[str]:
    """Why this source cannot run, from parsing alone (it is never executed here). Empty when it can."""
    if not isinstance(source, str) or not source.strip(): return ["the code is empty"]
    if len(source.encode()) > SOURCE_MAX: return [f"the code is larger than {SOURCE_MAX // 1024} KB"]
    try: tree = ast.parse(source, "<code>")
    except SyntaxError as e: return [f"syntax error on line {e.lineno}: {e.msg}"]
    mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
    if not mains: return ["define a top-level function main(state)"]
    a = mains[-1].args
    if len(a.posonlyargs) + len(a.args) < 1 and a.vararg is None: return ["main must take the state as its argument: main(state)"]
    return []


def unavailable() -> Optional[str]:
    """Why Code nodes cannot run here right now, or None. Docker and the image are checked at most every 30 s."""
    if config.code_runtime() == "off": return "off"
    image = config.code_image()
    hit = _checked.get(image)
    if hit and time.monotonic() - hit[0] < CHECK_TTL: return hit[1]
    try:
        r = subprocess.run([container.docker_exe(), "image", "inspect", image], stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, text=True, timeout=15)
        problem = None if r.returncode == 0 else (
            f"the image {image} is missing (build it: docker build -t {image} docker/studio-code)" if "No such image" in (r.stderr or "")
            else f"Docker is not running ({(r.stderr or '').strip()[:200]})")
    except FileNotFoundError: problem = "Docker is not installed"
    except subprocess.TimeoutExpired: problem = "Docker did not answer"
    _checked[image] = (time.monotonic(), problem)
    return problem


def runtime_error() -> Optional[AppError]:
    why = unavailable()
    if why is None: return None
    return AppError("CODE_RUNTIME_OFF") if why == "off" else AppError("CODE_RUNTIME_UNAVAILABLE", reason=why)


def _slot() -> threading.BoundedSemaphore:
    n = config.code_concurrency()
    return _slots.setdefault(n, threading.BoundedSemaphore(n))


def _command() -> List[str]:
    with open(RUNNER, encoding="utf-8") as fh: return ["python", "-I", "-c", fh.read()]


def _exchange(argv: List[str], name: str, payload: str, seconds: float,
              cancelled: Optional[Callable[[], bool]]) -> tuple[str, str, int, str]:
    """Run to completion, or kill at the deadline or on cancel. Returns (stdout, stderr, returncode, stopped)."""
    try: proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError: raise AppError("CODE_RUNTIME_UNAVAILABLE", reason="Docker is not installed") from None
    box: Dict[str, Any] = {}
    t = threading.Thread(target=lambda: box.update(zip(("out", "err"), proc.communicate(payload))), daemon=True)
    t.start(); deadline = time.monotonic() + seconds; stopped = ""
    while t.is_alive():
        t.join(0.25)
        if not t.is_alive(): break
        if time.monotonic() >= deadline: stopped = "timeout"
        elif cancelled is not None and cancelled(): stopped = "cancelled"
        if stopped:
            try: subprocess.run([container.docker_exe(), "kill", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            except (OSError, subprocess.TimeoutExpired): pass  # the local kill below still ends the client
            if proc.poll() is None: proc.kill()
            t.join(5); break
    return box.get("out") or "", box.get("err") or "", proc.returncode if proc.returncode is not None else -9, stopped


def run_code(source: str, state: Dict[str, Any], *, node: str = "code", timeout: Optional[float] = None,
             cancelled: Optional[Callable[[], bool]] = None) -> CodeResult:
    """Call main(state) of `source` once in the sandbox. Raises AppError (CodeFailure when the code itself failed)."""
    if (err := runtime_error()) is not None: raise err
    if (why := problems(source)): raise AppError("CODE_INVALID", node=node, reason=why[0])
    data = json.dumps(state, ensure_ascii=False, default=str)
    if len(data.encode()) > STATE_MAX: raise AppError("CODE_TOO_LARGE", node=node, what="state", max_kb=STATE_MAX // 1024)
    limit = min(float(timeout), config.code_max_seconds()) if timeout else float(config.code_max_seconds())
    payload = json.dumps({"source": source, "stdout_max": STDOUT_MAX, "state": json.loads(data)}, ensure_ascii=False)
    name = container.container_name()
    argv = container.build_code(name=name, image=config.code_image(), command=_command(),
                                memory=config.code_memory(), cpus=config.code_cpus(), pids=config.code_pids())
    slot = _slot(); t0 = time.perf_counter()
    if not slot.acquire(timeout=limit): raise AppError("CODE_TIMEOUT", node=node, seconds=f"{limit:g}")
    try: out, err, code, stopped = _exchange(argv, name, payload, limit, cancelled)
    finally: slot.release()
    ms = round((time.perf_counter() - t0) * 1000, 2)
    if stopped == "timeout": raise CodeFailure("CODE_TIMEOUT", {"runtime": "docker"}, node=node, seconds=f"{limit:g}")
    if stopped == "cancelled": raise AppError("CODE_FAILED", node=node, error="the run was cancelled")
    line = next((x for x in reversed(out.splitlines()) if x.strip()), "")
    if code == 137 and not line: raise CodeFailure("CODE_MEMORY", {"runtime": "docker"}, node=node, limit=config.code_memory())
    if len(line.encode()) > RESULT_MAX + STDOUT_MAX: raise AppError("CODE_TOO_LARGE", node=node, what="result", max_kb=RESULT_MAX // 1024)
    try: res = json.loads(line)
    except ValueError:
        reason = (err or out).strip().splitlines()[-1:] or [f"exit code {code}"]
        if "Unable to find image" in err or "No such image" in err: _checked.pop(config.code_image(), None)
        raise AppError("CODE_RUNTIME_UNAVAILABLE", reason=reason[0][:300]) from None
    output = {"stdout": res.get("stdout") or "", "runtime": "docker", "duration_ms": ms}
    if res.get("ok"): return CodeResult(res.get("value"), output["stdout"], "docker", ms)
    output["traceback"] = res.get("traceback") or ""
    kind = res.get("kind")
    if kind == "not_json": raise CodeFailure("CODE_RESULT_NOT_JSON", output, node=node, type=res.get("type") or "?")
    if kind == "invalid": raise CodeFailure("CODE_INVALID", output, node=node, reason=res.get("error") or "invalid code")
    raise CodeFailure("CODE_FAILED", output, node=node, error=(res.get("error") or "an error")[:300])

