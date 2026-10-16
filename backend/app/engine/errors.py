"""Engine-level errors (no web/HTTP knowledge)."""
from __future__ import annotations
from typing import List


class ValidationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors
