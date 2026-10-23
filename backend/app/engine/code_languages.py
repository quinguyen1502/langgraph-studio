"""Languages of the Tool node Code mode (TASK-0079, DEC-0048): one strategy per language, one shared runner.

`code_runtime` owns everything every language shares: the payload on stdin, the limits, the deadline and cancel, the
one-line JSON result and the error codes. A `CodeLanguage` only says how to check a source without running it, which
command runs the language's runner (inside the container and on the host) and which image and packages it has.
Adding a language = one class here + one entry in `LANGUAGES`; nothing else branches on the language."""
from __future__ import annotations
import ast, os, sys
from typing import Dict, List, Optional
from ..core import config
from ..core.errors import AppError

SANDBOX = os.path.join(os.path.dirname(__file__), "sandbox")
DEFAULT = "python"


def _read(name: str) -> str:
    with open(os.path.join(SANDBOX, name), encoding="utf-8") as fh: return fh.read()


class CodeLanguage:
    """The interface. Subclasses set `id`, `starter` and implement the four methods."""
    id: str = ""
    starter: str = ""

    def problems(self, source: str) -> List[str]:
        """Why `source` cannot run, from reading it alone (never executed on the server). Empty when it can."""
        raise NotImplementedError

    def command(self) -> List[str]:
        """argv inside the container (the runner travels on the command line; nothing is mounted)."""
        raise NotImplementedError

    def host_command(self, workdir: str) -> List[str]:
        """argv for the host subprocess runtime."""
        raise NotImplementedError

    def host_env(self, workdir: str) -> Dict[str, str]:
        """Extra environment for the host subprocess (on top of the empty base environment)."""
        return {}

    def image(self) -> str: raise NotImplementedError
    def packages(self) -> List[str]: raise NotImplementedError

    def host_problem(self) -> Optional[str]:
        """Why the host subprocess runtime cannot run this language (e.g. its binary is missing), or None."""
        return None


class Python(CodeLanguage):
    id = "python"
    starter = 'def main(state):\n    """Return the value for the output field."""\n    return state.get("message", "")\n'

    def problems(self, source: str) -> List[str]:
        try: tree = ast.parse(source, "<code>")
        except SyntaxError as e: return [f"syntax error on line {e.lineno}: {e.msg}"]
        mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
        if not mains: return ["define a top-level function main(state)"]
        a = mains[-1].args
        if len(a.posonlyargs) + len(a.args) < 1 and a.vararg is None: return ["main must take the state as its argument: main(state)"]
        return []

    def command(self) -> List[str]: return ["python", "-I", "-c", _read("code_runner.py")]
    def host_command(self, workdir: str) -> List[str]: return [sys.executable, "-I", "-c", _read("code_runner.py")]
    def host_env(self, workdir: str) -> Dict[str, str]: return {"PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    def image(self) -> str: return config.code_image()
    def packages(self) -> List[str]: return config.code_packages()


LANGUAGES: Dict[str, CodeLanguage] = {"python": Python()}


def language_of(data: Optional[dict]) -> str:
    """The language of a Code-mode node's data; graphs saved before TASK-0079 have none and are Python."""
    return str((data or {}).get("language") or DEFAULT)


def enabled() -> List[str]:
    """Languages this server offers: STUDIO_CODE_LANGUAGES (comma-separated) filtered to the known ones."""
    return [x for x in config.code_languages() if x in LANGUAGES]


def get(language: Optional[str], node: str = "code") -> CodeLanguage:
    """The strategy for `language`, or CODE_LANGUAGE_UNSUPPORTED when it is unknown or not enabled here."""
    lang = language or DEFAULT
    if lang not in enabled(): raise AppError("CODE_LANGUAGE_UNSUPPORTED", node=node, language=lang)
    return LANGUAGES[lang]
