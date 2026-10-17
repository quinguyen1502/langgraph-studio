"""Settings read from environment variables (names and defaults unchanged from the MVP).

Values that tests or operators may change at runtime are functions; the rest are read once.
"""
import os

BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- database ---
STUDIO_DB = os.environ.get("STUDIO_DB", os.path.join(BACKEND_DIR, "studio.db"))
# DATABASE_URL overrides STUDIO_DB (e.g. postgresql+psycopg://user:pw@host/db); default is the SQLite file.
def normalise_db_url(url: str) -> str:
    """Accept the common `postgres://` / `postgresql://` forms and pin them to the psycopg (v3) driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix): return "postgresql+psycopg://" + url[len(prefix):]
    return url

DATABASE_URL = normalise_db_url(os.environ.get("DATABASE_URL") or f"sqlite:///{STUDIO_DB}")

# --- redis (TASK-0009): optional; unset = in-memory run bus (single process) ---
REDIS_URL = os.environ.get("REDIS_URL") or None

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
def allow_private_callbacks() -> bool: return os.environ.get("STUDIO_ALLOW_PRIVATE_CALLBACKS") == "1"
def worker_enabled() -> bool: return os.environ.get("STUDIO_WORKER", "1") != "0"  # run queued jobs in this API process
def worker_concurrency() -> int: return max(1, _int("STUDIO_WORKER_CONCURRENCY", 2))
def wait_ttl() -> float: return max(0.0, float(os.environ.get("STUDIO_WAIT_TTL", 7 * 86400)))  # waiting runs expire (0 = never)
def sync_wait_max() -> float: return max(0.0, float(os.environ.get("STUDIO_SYNC_WAIT_MAX", 30)))  # sync trigger: then 202 + poll URL
def trigger_rate_limit() -> int: return max(0, _int("STUDIO_TRIGGER_RATE_LIMIT", 60))  # runs per token per window (0 = off)
def trigger_rate_window() -> int: return max(1, _int("STUDIO_TRIGGER_RATE_WINDOW", 60))  # seconds
def version_keep() -> int: return max(0, _int("STUDIO_VERSION_KEEP", 0))  # keep last N versions (0 = all)
# --- TASK-0020 ---
def webhook_max_attempts() -> int: return max(1, _int("STUDIO_WEBHOOK_MAX_ATTEMPTS", 5))
def webhook_backoff_base() -> float: return max(0.0, float(os.environ.get("STUDIO_WEBHOOK_BACKOFF_BASE", 2)))  # s; delay = base * 2^(n-1)
def webhook_backoff_max() -> float: return max(0.0, float(os.environ.get("STUDIO_WEBHOOK_BACKOFF_MAX", 300)))
def secret_grace() -> float: return max(0.0, float(os.environ.get("STUDIO_SECRET_GRACE", 24 * 3600)))  # old signing secret stays valid
def job_visibility() -> int: return max(3, _int("STUDIO_JOB_VISIBILITY_TIMEOUT", 30))  # lease of a taken job
def job_reap_every() -> float: return max(0.2, float(os.environ.get("STUDIO_JOB_REAP_EVERY", 15)))
def public_url() -> str: return (os.environ.get("STUDIO_PUBLIC_URL") or "").rstrip("/")  # links in e-mails
def smtp() -> dict | None:
    """SMTP settings for notification e-mail; None (no-op) when SMTP_HOST is unset."""
    host = os.environ.get("SMTP_HOST", "").strip()
    if not host: return None
    return {"host": host, "port": _int("SMTP_PORT", 587), "user": os.environ.get("SMTP_USER") or None,
            "password": os.environ.get("SMTP_PASSWORD") or None, "sender": os.environ.get("SMTP_FROM") or "studio@localhost",
            "starttls": os.environ.get("SMTP_STARTTLS", "1") != "0", "ssl": os.environ.get("SMTP_SSL") == "1"}
def notify_webhook() -> tuple[str, str | None] | None:
    url = os.environ.get("STUDIO_NOTIFY_WEBHOOK_URL", "").strip()
    return (url, os.environ.get("STUDIO_NOTIFY_WEBHOOK_SECRET") or None) if url else None
def otel_metrics() -> bool: return os.environ.get("STUDIO_OTEL_METRICS", "").lower() in ("1", "true", "yes", "on")
# --- TASK-0022: approval through external channels ---
def approval_ttl() -> float: return max(60.0, float(os.environ.get("STUDIO_APPROVAL_TTL", 24 * 3600)))  # approval buttons expire (s)
def slack_api_url() -> str: return (os.environ.get("SLACK_API_URL") or "https://slack.com/api").rstrip("/")
def telegram_api_url() -> str: return (os.environ.get("TELEGRAM_API_URL") or "https://api.telegram.org").rstrip("/")
def llm_mode() -> str: return "openai" if os.environ.get("OPENAI_API_KEY") else "mock"
# --- TASK-0022 follow-up: identity verification codes sent by the bot ---
def identity_code_ttl() -> float: return max(60.0, float(os.environ.get("STUDIO_IDENTITY_CODE_TTL", 600)))  # a code is valid (s)
def identity_code_attempts() -> int: return max(1, _int("STUDIO_IDENTITY_CODE_ATTEMPTS", 5))  # wrong codes before a new one is needed
def identity_code_resend() -> int: return max(0, _int("STUDIO_IDENTITY_CODE_RESEND", 30))     # min seconds between two codes
# --- TASK-0022 follow-up: org-wide approval channels ---
def admin_emails() -> set[str]: return {e.strip().lower() for e in (os.environ.get("STUDIO_ADMIN_EMAILS") or "").split(",") if e.strip()}
# --- TASK-0022 follow-up: rate limits of the public approval callbacks (fixed window, shared via Redis) ---
def callback_rate_limit_ip() -> int: return max(0, _int("STUDIO_CALLBACK_RATE_LIMIT_IP", 60))        # per client IP and window (0 = off)
def callback_rate_limit_channel() -> int: return max(0, _int("STUDIO_CALLBACK_RATE_LIMIT_CHANNEL", 300))  # per connection / Slack team
def callback_rate_window() -> int: return max(1, _int("STUDIO_CALLBACK_RATE_WINDOW", 60))
# --- TASK-0013: MCP servers ---
def mcp_stdio_enabled() -> bool: return os.environ.get("STUDIO_MCP_STDIO") == "1"  # stdio servers run processes on the API host: off by default
def mcp_allow_private() -> bool: return os.environ.get("STUDIO_MCP_ALLOW_PRIVATE") == "1"  # HTTP servers on private/loopback addresses
def mcp_timeout() -> float: return max(1.0, float(os.environ.get("STUDIO_MCP_TIMEOUT", 30)))  # per MCP session (s)
