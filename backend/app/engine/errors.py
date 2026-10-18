"""Engine-level errors (no web/HTTP knowledge)."""
from __future__ import annotations
from typing import List


class ValidationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


class Interrupt(Exception):
    """Raised by a Human node that has no response yet: the run pauses (status `waiting`) at `node` (TASK-0006)."""
    def __init__(self, node: str, prompt: str):
        super().__init__(f"Waiting for a human response at {node}")
        self.node, self.prompt = node, prompt
