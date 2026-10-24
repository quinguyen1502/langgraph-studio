# Self-hosted with Coolify or Dokploy

[Tiếng Việt](self-hosted.vi.md) · [Deploy guide](README.md)

This is the full-feature path: the repository's `docker-compose.yml` (Postgres 17 + pgvector, Redis, api, worker,
nginx) on a server you control. Code nodes run in throwaway Docker containers (no network, no mounts, memory, CPU and
process limits) through the host's Docker socket, which a managed PaaS cannot offer.

## Server requirements

- A Linux server with 2 GB RAM or more, Docker Engine 24+, and Coolify or Dokploy installed.
- A domain pointing at the server (both tools issue the TLS certificate).
- Shell access, to build the two sandbox images once.

## 1. Build the sandbox images on the server

The api and worker start Code containers from these local tags:

```sh
git clone https://github.com/quinguyen1502/superstep && cd superstep
docker build -t studio-code:1 docker/studio-code
docker build -t studio-code-ts:1 docker/studio-code-ts
stat -c %g /var/run/docker.sock   # the socket's group id, for STUDIO_DOCKER_GID below
```

Rebuild them when you update Superstep and these Dockerfiles changed.

## 2. Create the resource

**Coolify:** **+ New → Public Repository** (or your fork via the GitHub App), build pack **Docker Compose**,
compose file `/docker-compose.yml`, branch `main`.

**Dokploy:** **Create Service → Compose**, provider **GitHub** or **Git**, compose path `./docker-compose.yml`,
branch `main`.

## 3. Environment

Set these in the resource's environment variables (Coolify: **Environment Variables**; Dokploy: **Environment**):

```sh
JWT_SECRET=<openssl rand -hex 32>
STUDIO_SECRET_KEY=<openssl rand -hex 32>   # keep it: stored credentials need the same key
POSTGRES_PASSWORD=<openssl rand -hex 24>
STUDIO_ENV=production
STUDIO_ADMIN_EMAILS=you@example.com
STUDIO_PUBLIC_URL=https://studio.example.com
STUDIO_ENABLE_CODE_NODES=1
STUDIO_DOCKER_GID=<the group id from step 1>
OPENAI_API_KEY=                            # optional
```

In production there is no demo account: the first start creates the `STUDIO_ADMIN_EMAILS` admin and prints its
one-time password in the **api** logs (or set `STUDIO_ADMIN_PASSWORD`).

## 4. Domain and deploy

Attach the domain to the **web** service, port **80** (Coolify: the service's **Domains** field as
`https://studio.example.com:80`; Dokploy: **Domains → Add Domain**, service `web`, port 80, HTTPS on). The built-in
proxy (Traefik or Caddy) handles WebSockets. Do not publish the api, Postgres or Redis ports.

Deploy, then open the domain and sign in. The **Code nodes** card in **Settings → Users** should show the Docker
runtime for Python and TypeScript.

## 5. Operate

- **Scale runs:** API triggers, schedules and recovered runs go to the `worker` service. Add replicas in the tool's
  UI (or `docker compose up --scale worker=3`).
- **Tracing:** set `OTEL_EXPORTER_OTLP_ENDPOINT` to your collector, or enable the compose `tracing` profile for Jaeger.
- **Backups:** back up the `langgraph-studio_pgdata` volume, or schedule `pg_dump` (Coolify and Dokploy both have
  scheduled database backups if you move Postgres to their database resource and set `DATABASE_URL`).
- **Updates:** redeploy the resource; migrations run when the api starts.

## Security model

- Mounting `/var/run/docker.sock` gives the api and worker containers root-equivalent control of the host. Only
  run Superstep on a server dedicated to it, and keep the api off the public network (only nginx is exposed).
- Code containers have no network (`--network none`), no mounts, an empty environment, a read-only root file
  system and memory, CPU and process limits (`STUDIO_CODE_MEMORY`, `STUDIO_CODE_CPUS`, `STUDIO_CODE_PIDS`). They
  share the host kernel: container isolation, not a virtual machine.
- `docker-compose.yml` names its Postgres volume `langgraph-studio_pgdata` for upgrades from v0.1. Two Superstep
  stacks on one Docker host would share it: run one stack per host, or rename the volume before the first deploy.

## Without the Docker socket

If you cannot mount the socket, use the all-in-one image instead
([`deploy/compose/docker-compose.single.yml`](../../deploy/compose/docker-compose.single.yml)). Code nodes then run
on the host, without Docker limiting their access.
