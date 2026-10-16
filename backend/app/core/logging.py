"""Logger helper so modules share the `studio.*` namespace."""
import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"studio.{name}")
