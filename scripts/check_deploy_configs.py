"""CI check for the PaaS deploy files (docs/deploy): each one parses and keeps the facts the all-in-one image needs
(port 8000, the /api/health check, the required secrets). Usage: python scripts/check_deploy_configs.py"""
import json, pathlib, sys, tomllib
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SECRETS = ("JWT_SECRET", "STUDIO_SECRET_KEY", "STUDIO_ADMIN_EMAILS")
# file -> (loader, text that must appear; secrets set elsewhere are listed in the docs instead)
CHECKS = {
    "render.yaml": (yaml.safe_load, ["/api/health", "/data", *SECRETS]),
    "deploy/render/render.postgres.yaml": (yaml.safe_load, ["/api/health", "DATABASE_URL", *SECRETS]),
    "deploy/render/render.full.yaml": (yaml.safe_load, ["/api/health", "DATABASE_URL", "REDIS_URL", "app.worker", "STUDIO_SANDBOX_TOKEN", "pserv", *SECRETS]),
    "app.json": (json.loads, ["heroku-postgresql", "container", *SECRETS]),
    "heroku.yml": (yaml.safe_load, ["Dockerfile", "app.worker"]),
    "railway.json": (json.loads, ["Dockerfile", "/api/health"]),
    "fly.toml": (tomllib.loads, ["8000", "/api/health", "/data", "ghcr.io/quinguyen1502/superstep"]),
    ".do/deploy.template.yaml": (yaml.safe_load, ["8000", "/api/health", "DATABASE_URL", "superstep", *SECRETS]),
    "deploy/zeabur/template.yaml": (yaml.safe_load, ["8000", "/data", "ghcr.io/quinguyen1502/superstep", *SECRETS]),
    "deploy/compose/docker-compose.single.yml": (yaml.safe_load, ["8000", "/data", *SECRETS]),
    "deploy/fly/sandbox.fly.toml": (tomllib.loads, ["superstep-sandbox", "STUDIO_SANDBOX_TOKEN", "::"]),
    "docker-compose.yml": (yaml.safe_load, ["studio-sandbox", "internal: true", "STUDIO_SANDBOX_TOKEN"]),
}


def main() -> int:
    bad = []
    for name, (load, needles) in CHECKS.items():
        text = (ROOT / name).read_text()
        try: load(text)
        except Exception as e: bad.append(f"{name}: does not parse ({e})"); continue
        bad += [f"{name}: missing {n!r}" for n in needles if n not in text]
    docs = "".join(p.read_text() for p in (ROOT / "docs/deploy").glob("*.md"))
    bad += [f"docs/deploy: {name} is not documented" for name in CHECKS if name not in docs and not name.startswith("deploy/render/") and name not in ("heroku.yml", "docker-compose.yml")]
    print("\n".join(bad) or f"{len(CHECKS)} deploy files OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
