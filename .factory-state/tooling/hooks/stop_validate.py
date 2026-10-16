#!/usr/bin/env python3
"""Run report-only factory validation when an agent turn stops."""
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
commands = [["factory", "validate", str(root)]]
commands.extend(json.loads("[]"))
for command in commands:
    try:
        result = subprocess.run(
            command if isinstance(command, list) else command,
            cwd=root,
            shell=isinstance(command, str),
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        output = (result.stdout + result.stderr).strip()
        if output:
            print(output, file=sys.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Factory validation hook warning: {exc}", file=sys.stderr)
# Report-only: validation findings must not trap the agent in a Stop hook loop.
print("{}")
raise SystemExit(0)
