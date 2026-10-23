# Tự host với Coolify hoặc Dokploy

[English](self-hosted.md) · [Hướng dẫn triển khai](README.vi.md)

Đây là cách triển khai đầy đủ tính năng: `docker-compose.yml` của repo (Postgres 17 + pgvector, Redis, api, worker,
nginx) trên máy chủ do bạn quản lý. Node Code chạy trong các container Docker dùng một lần (không mạng, không mount,
có giới hạn bộ nhớ, CPU và số process) qua Docker socket của máy chủ, điều mà PaaS được quản lý không cung cấp được.

## Yêu cầu máy chủ

- Máy chủ Linux có từ 2 GB RAM, Docker Engine 24+, đã cài Coolify hoặc Dokploy.
- Một tên miền trỏ về máy chủ (cả hai công cụ đều tự cấp chứng chỉ TLS).
- Quyền truy cập shell để build hai image sandbox một lần.

## 1. Build image sandbox trên máy chủ

api và worker khởi chạy container Code từ các tag cục bộ này:

```sh
git clone https://github.com/quinguyen1502/superstep && cd superstep
docker build -t studio-code:1 docker/studio-code
docker build -t studio-code-ts:1 docker/studio-code-ts
stat -c %g /var/run/docker.sock   # group id của socket, dùng cho STUDIO_DOCKER_GID bên dưới
```

Hãy build lại khi bạn cập nhật Superstep và các Dockerfile này thay đổi.

## 2. Tạo resource

**Coolify:** **+ New → Public Repository** (hoặc bản fork của bạn qua GitHub App), build pack **Docker Compose**,
file compose `/docker-compose.yml`, nhánh `main`.

**Dokploy:** **Create Service → Compose**, provider **GitHub** hoặc **Git**, đường dẫn compose `./docker-compose.yml`,
nhánh `main`.

## 3. Biến môi trường

Đặt các biến sau trong phần biến môi trường của resource (Coolify: **Environment Variables**; Dokploy:
**Environment**):

```sh
JWT_SECRET=<openssl rand -hex 32>
STUDIO_SECRET_KEY=<openssl rand -hex 32>   # hãy giữ lại: credential đã lưu cần đúng khoá này
POSTGRES_PASSWORD=<openssl rand -hex 24>
STUDIO_ENV=production
STUDIO_ADMIN_EMAILS=you@example.com
STUDIO_PUBLIC_URL=https://studio.example.com
STUDIO_ENABLE_CODE_NODES=1
STUDIO_DOCKER_GID=<group id ở bước 1>
OPENAI_API_KEY=                            # tuỳ chọn
```

Ở production không có tài khoản demo: lần khởi động đầu tạo admin `STUDIO_ADMIN_EMAILS` và in mật khẩu dùng một lần
trong log của **api** (hoặc đặt `STUDIO_ADMIN_PASSWORD`).

## 4. Tên miền và deploy

Gắn tên miền vào dịch vụ **web**, cổng **80** (Coolify: trường **Domains** của dịch vụ, dạng
`https://studio.example.com:80`; Dokploy: **Domains → Add Domain**, dịch vụ `web`, cổng 80, bật HTTPS). Proxy có sẵn
(Traefik hoặc Caddy) xử lý WebSocket. Đừng mở cổng của api, Postgres hay Redis ra ngoài.

Deploy, rồi mở tên miền và đăng nhập. Thẻ **Node Code** trong **Cài đặt → Người dùng** phải hiện runtime Docker cho
Python và TypeScript.

## 5. Vận hành

- **Mở rộng run:** API trigger, lịch chạy và run được khôi phục đi tới dịch vụ `worker`. Thêm bản sao trong giao diện
  của công cụ (hoặc `docker compose up --scale worker=3`).
- **Tracing:** đặt `OTEL_EXPORTER_OTLP_ENDPOINT` trỏ tới collector của bạn, hoặc bật profile `tracing` của compose để
  dùng Jaeger.
- **Sao lưu:** sao lưu volume `langgraph-studio_pgdata`, hoặc lên lịch `pg_dump` (Coolify và Dokploy đều có sao lưu
  database theo lịch nếu bạn chuyển Postgres sang resource database của chúng và đặt `DATABASE_URL`).
- **Cập nhật:** deploy lại resource; migration chạy khi api khởi động.

## Mô hình bảo mật

- Gắn `/var/run/docker.sock` cho container api và worker quyền điều khiển máy chủ tương đương root. Chỉ chạy
  Superstep trên máy chủ dành riêng cho nó, và không mở api ra mạng công cộng (chỉ nginx được mở).
- Container Code không có mạng (`--network none`), không mount, môi trường rỗng, hệ thống file gốc chỉ đọc và có giới
  hạn bộ nhớ, CPU và số process (`STUDIO_CODE_MEMORY`, `STUDIO_CODE_CPUS`, `STUDIO_CODE_PIDS`). Chúng dùng chung kernel
  với máy chủ: đây là cách ly bằng container, không phải máy ảo.
- `docker-compose.yml` đặt tên volume Postgres là `langgraph-studio_pgdata` để nâng cấp từ v0.1. Hai stack Superstep
  trên cùng một máy chủ Docker sẽ dùng chung volume này: hãy chạy một stack cho mỗi máy chủ, hoặc đổi tên volume trước
  lần deploy đầu.

## Không có Docker socket

Nếu không thể gắn socket, hãy dùng image all-in-one
([`deploy/compose/docker-compose.single.yml`](../../deploy/compose/docker-compose.single.yml)). Khi đó node Code chạy
trực tiếp trên server, không có Docker giới hạn quyền.
