#!/usr/bin/env python3
"""Block obvious writes to owner-controlled factory configuration."""
import json
import re
import sys

payload = json.load(sys.stdin)
tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
tool_input = payload.get("tool_input") or payload.get("toolInput") or payload.get("input") or {}
serialized = json.dumps(tool_input, ensure_ascii=False)
command = (
    str(tool_input.get("command") or tool_input.get("cmd") or "")
    if isinstance(tool_input, dict)
    else ""
)
protected = re.compile(
    r"(?<![\w-])(?:\.factory(?:/|(?=[\"'\s]|$))|"
    r"\.factory-state/tooling(?:/|(?=[\"'\s]|$)))"
)
path_write = bool(protected.search(serialized)) and tool_name.lower() in {
    "write", "edit", "multiedit", "apply_patch"
}
destructive = bool(
    protected.search(command)
    and re.search(
        r"(?:rm\s+(?:-[^ ]*r[^ ]*f|-[^ ]*f[^ ]*r)|git\s+(?:clean|reset\s+--hard)|(?:>|tee\s+))",
        command,
    )
)
if path_write or destructive:
    print("Factory guardrail blocked a write to owner-controlled factory assets.", file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(0)
