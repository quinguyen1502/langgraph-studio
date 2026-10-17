# Backend API (FastAPI + LangGraph). Build context: ./backend
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    STUDIO_IMPORT_DIR=/data/imports STUDIO_SECRET_KEY_FILE=/data/secret.key STUDIO_DB=/data/studio.db
# git + uv are used by "Import LangGraph repo" (clone + per-import venv)
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* && pip install uv
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
RUN pip install . && useradd -m -u 10001 studio && mkdir -p /data && chown studio /data
USER studio
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=2).status==200 else 1)"
# Migrations (alembic upgrade head) + seed run on startup; keep one worker per container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
