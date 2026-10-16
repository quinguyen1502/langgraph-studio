"""Settings read from environment variables (names and defaults unchanged from the MVP).

Values that tests or operators may change at runtime are functions; the rest are read once.
"""
import os

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- database ---
STUDIO_DB = os.environ.get("STUDIO_DB", os.path.join(BACKEND_DIR, "studio.db"))
# DATABASE_URL overrides STUDIO_DB (e.g. postgresql+psycopg://user:pw@host/db); default is the SQLite file.
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{STUDIO_DB}"

# --- auth ---
PLACEHOLDER_SECRET = "dev-secret-change-me"
JWT_SECRET = os.environ.get("JWT_SECRET", PLACEHOLDER_SECRET)
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", 60 * 60 * 24))
IS_PROD = os.environ.get("STUDIO_ENV", "dev").lower() in ("prod", "production")
DEMO_EMAIL, DEMO_PASSWORD = "admin@example.com", "admin123"

# --- workflows ---
NAME_MAX = 120


def _int(name: str, default: int) -> int:
    try: return int(os.environ.get(name, default))
    except ValueError: return default

# --- runtime limits (TASK-0004); functions so env changes apply per run ---
def run_timeout() -> float: return float(os.environ.get("STUDIO_RUN_TIMEOUT", 120))
def event_max() -> int: return _int("STUDIO_EVENT_MAX_BYTES", 256 * 1024)
def run_max() -> int: return _int("STUDIO_RUN_MAX_BYTES", 2 * 1024 * 1024)
def input_max() -> int: return _int("STUDIO_INPUT_MAX_BYTES", 256 * 1024)
def workflow_max() -> int: return _int("STUDIO_WORKFLOW_MAX_BYTES", 1024 * 1024)
def recursion_limit() -> int: return _int("STUDIO_RECURSION_LIMIT", 25)
def llm_mode() -> str: return "openai" if os.environ.get("OPENAI_API_KEY") else "mock"
