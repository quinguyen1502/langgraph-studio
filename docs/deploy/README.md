# Deploy Superstep to a PaaS

[Tiếng Việt](README.vi.md) · [Environment variables](env-vars.md)

Superstep ships an **all-in-one image** (the root `Dockerfile`, published as `ghcr.io/quinguyen1502/superstep`).
One container serves the UI, `/api` and the `/ws/run` WebSocket on `$PORT`, so it fits platforms that route one
port per service. The repository's `docker-compose.yml` (Postgres, Redis, api, worker, nginx) is still the
full-featured setup for your own server.

| | All-in-one image (PaaS) | `docker-compose.yml` (own server) |
|---|---|---|
| Database | SQLite in `/data` (needs a persistent volume), or Postgres via `DATABASE_URL` | Postgres 17 + pgvector |
| Worker + Redis | Optional (off by default, runs are executed in the web process) | On |
| Code nodes | On, **Runs on host** (subprocess runtime, Python + TypeScript/Deno) | Docker sandbox (after you build the images) |
| Demo account | None (production mode) | `admin@example.com` / `admin123` in dev mode |

## Before you deploy

- **First admin.** Production mode has no demo account. Set `STUDIO_ADMIN_EMAILS` to your email. At the
  first start that account is created as an admin. Its one-time password is printed **once** in the service log
  (`Created the admin account ... (sign in and change it now): <password>`). To choose it yourself, set
  `STUDIO_ADMIN_PASSWORD` (8+ characters, a letter and a digit). Change the password after the first sign-in.
- **Secrets.** `JWT_SECRET` and `STUDIO_SECRET_KEY` are required. The templates below generate both.
  `STUDIO_SECRET_KEY` encrypts stored credentials: if you change or lose it, they cannot be decrypted again.
- **Code nodes run on the host.** Code nodes are on, using the subprocess runtime. Code runs directly on the
  server, without Docker limiting its access: it can use the network and read what the server process can read
  (environment variables and `/data` included). Use it only with trusted users and trusted code, or set
  `STUDIO_ENABLE_CODE_NODES=0`. A separate sandbox service is planned.
- **Public URL.** Set `STUDIO_PUBLIC_URL` to the https address of the service. Links in emails and
  Slack/Telegram callbacks need it.
- **Free plans sleep.** Sleeping services drop open WebSockets and delay schedules and webhooks. Use an always-on
  instance for anything beyond a trial.

## Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep)

| Blueprint | What it creates | Button |
|---|---|---|
| [`render.yaml`](../../render.yaml) (default) | Web service + 1 GB disk at `/data` (SQLite) | [Deploy](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep) |
| [`deploy/render/render.postgres.yaml`](../../deploy/render/render.postgres.yaml) | Web service + Render Postgres 17 | [Deploy](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep&path=deploy/render/render.postgres.yaml) |
| [`deploy/render/render.full.yaml`](../../deploy/render/render.full.yaml) | Web + worker + Render Postgres + Render Key Value | [Deploy](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep&path=deploy/render/render.full.yaml) |

1. Click a button, sign in to Render and fill in `STUDIO_ADMIN_EMAILS` (and optionally `STUDIO_PUBLIC_URL`,
   `OPENAI_API_KEY`). `JWT_SECRET` and `STUDIO_SECRET_KEY` are generated.
2. When the deploy is live, open **Logs** and copy the one-time admin password.
3. Set `STUDIO_PUBLIC_URL` to `https://<service>.onrender.com` (or your domain) if you skipped it.

Notes: a disk needs a paid instance type (Starter or above), and a service with a disk cannot scale beyond one
instance. Free Render Postgres databases are deleted after 30 days. The blueprints set `autoDeployTrigger: off`,
so your copy does not redeploy whenever this repository changes; use **Manual Deploy** to update.

## Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy?template=https://github.com/quinguyen1502/superstep)

[`app.json`](../../app.json) + [`heroku.yml`](../../heroku.yml) build the image on the container stack and add
**Heroku Postgres** (Essential 0). Heroku has no persistent disk, so SQLite is not an option there.

1. Click the button, enter `STUDIO_ADMIN_EMAILS`, deploy.
2. `heroku logs --app <app> | grep "admin account"` shows the one-time password.
3. `heroku config:set STUDIO_PUBLIC_URL=https://<app>.herokuapp.com --app <app>`

Optional worker: `heroku addons:create heroku-redis:mini --app <app>` (sets `REDIS_URL`), then
`heroku ps:scale worker=1 --app <app>`. Optionally `heroku config:set STUDIO_WORKER=0` so queued runs only go to the
worker dyno (the worker process ignores this variable).

## Railway

[`railway.json`](../../railway.json) builds the root `Dockerfile` with a health check. There is no published
template yet; deploy from the repository:

1. **New Project → Deploy from GitHub repo**, pick your fork or `quinguyen1502/superstep`.
2. **Variables**: `JWT_SECRET` and `STUDIO_SECRET_KEY` (random values, e.g. `openssl rand -hex 32`), `STUDIO_ADMIN_EMAILS`,
   `RAILWAY_RUN_UID=0` (Railway volumes are owned by root; the image runs as a non-root user otherwise).
3. SQLite: **add a volume** to the service, mounted at `/data`. Postgres instead: add the Postgres database and set
   `DATABASE_URL=${{Postgres.DATABASE_URL}}` (use a pgvector-enabled Postgres if you need vector search).
4. **Settings → Networking → Generate Domain**, then set `STUDIO_PUBLIC_URL` to it.

Optional worker: add Redis (`REDIS_URL=${{Redis.REDIS_URL}}` on both services) and a second service from the same
repository with the start command `python -m app.worker`.

## Coolify and Dokploy (self-hosted)

These run on your own server, so you have two choices:

- **All-in-one image.** Create a Docker Compose resource from
  [`deploy/compose/docker-compose.single.yml`](../../deploy/compose/docker-compose.single.yml) (or a Docker image
  resource with `ghcr.io/quinguyen1502/superstep:latest`, port 8000, a volume at `/data`). Set `JWT_SECRET`,
  `STUDIO_SECRET_KEY` and `STUDIO_ADMIN_EMAILS` in the environment. For Postgres, create a database resource and
  set `DATABASE_URL`.
- **Full stack with the Docker sandbox.** Create a Docker Compose resource from the repository's
  `docker-compose.yml` (set `JWT_SECRET`, `POSTGRES_PASSWORD`, `STUDIO_SECRET_KEY`, `STUDIO_ENV=production`,
  `STUDIO_ADMIN_EMAILS`). Code nodes then run in Docker containers through the host's Docker socket: build
  `docker/studio-code` and `docker/studio-code-ts` on the server and set `STUDIO_ENABLE_CODE_NODES=1`.
  Mounting the Docker socket gives the api container root-equivalent access to the host.

Both tools put a reverse proxy (Traefik or Caddy) in front of the service; WebSockets work without extra settings.
Point the domain at port 8000 (all-in-one) or 80 of the `web` service (full stack).

## Any other Docker host

```sh
export JWT_SECRET=$(openssl rand -hex 32) STUDIO_SECRET_KEY=$(openssl rand -hex 32)
echo "$STUDIO_SECRET_KEY"
docker run -d -p 8000:8000 -v superstep-data:/data -e JWT_SECRET -e STUDIO_SECRET_KEY \
  -e STUDIO_ADMIN_EMAILS=you@example.com ghcr.io/quinguyen1502/superstep:latest
docker logs <container> | grep "admin account"
```

Store the printed `STUDIO_SECRET_KEY` somewhere safe: you need the same value on every start.

## Images

`.github/workflows/image.yml` builds the image on every pull request, boots it on SQLite and on Postgres, scans it
with Trivy (fails on fixable critical vulnerabilities) and publishes it to GHCR from `develop` (`:develop`,
`:sha-<commit>`) and from release tags (`:1.2.3`, `:1.2`, `:latest`; `:1` from 1.0 on). No secret is baked into the
image.
