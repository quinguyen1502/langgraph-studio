# Triển khai Superstep lên PaaS

[English](README.md) · [Biến môi trường](env-vars.vi.md)

Superstep có một **image all-in-one** (`Dockerfile` ở thư mục gốc, phát hành tại `ghcr.io/quinguyen1502/superstep`).
Một container phục vụ giao diện, `/api` và WebSocket `/ws/run` trên `$PORT`, nên phù hợp với các nền tảng chỉ định
tuyến một cổng cho mỗi dịch vụ. `docker-compose.yml` của repo (Postgres, Redis, api, worker, nginx) vẫn là cách
triển khai đầy đủ tính năng trên máy chủ của bạn.

| | Image all-in-one (PaaS) | `docker-compose.yml` (máy chủ riêng) |
|---|---|---|
| Cơ sở dữ liệu | SQLite trong `/data` (cần volume lưu trữ lâu dài), hoặc Postgres qua `DATABASE_URL` | Postgres 17 + pgvector |
| Worker + Redis | Tuỳ chọn (mặc định tắt, run được thực thi trong process web) | Bật |
| Node Code | Bật, **Chạy trực tiếp trên server** (runtime subprocess, Python + TypeScript/Deno) | Sandbox Docker (sau khi bạn build image) |
| Tài khoản demo | Không có (chế độ production) | `admin@example.com` / `admin123` ở chế độ dev |

## Trước khi triển khai

- **Admin đầu tiên.** Chế độ production không có tài khoản demo. Đặt `STUDIO_ADMIN_EMAILS` là email của bạn. Ở lần
  khởi động đầu, tài khoản này được tạo với quyền admin. Mật khẩu dùng một lần được in **một lần** trong log của dịch
  vụ (`Created the admin account ... (sign in and change it now): <mật khẩu>`). Muốn tự chọn mật khẩu, đặt
  `STUDIO_ADMIN_PASSWORD` (từ 8 ký tự, có chữ và số). Hãy đổi mật khẩu sau lần đăng nhập đầu tiên.
- **Khoá bí mật.** Bắt buộc có `JWT_SECRET` và `STUDIO_SECRET_KEY`. Các mẫu bên dưới tự sinh cả hai.
  `STUDIO_SECRET_KEY` mã hoá các credential đã lưu: nếu đổi hoặc mất khoá này, chúng không giải mã được nữa.
- **Node Code chạy trực tiếp trên server.** Node Code được bật với runtime subprocess. Code đang chạy trực tiếp trên
  máy chủ, không có Docker giới hạn quyền: code có thể dùng mạng và đọc những gì process máy chủ đọc được (kể cả biến
  môi trường và `/data`). Chỉ nên dùng cho người dùng và code tin cậy, hoặc đặt `STUDIO_ENABLE_CODE_NODES=0`. Một dịch
  vụ sandbox riêng đang được lên kế hoạch.
- **URL công khai.** Đặt `STUDIO_PUBLIC_URL` là địa chỉ https của dịch vụ. Link trong email và callback
  Slack/Telegram cần giá trị này.
- **Gói miễn phí sẽ ngủ.** Dịch vụ ngủ sẽ ngắt WebSocket đang mở và làm trễ lịch chạy, webhook. Ngoài mục đích dùng
  thử, hãy dùng instance luôn bật.

## Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep)

| Blueprint | Tạo ra | Nút |
|---|---|---|
| [`render.yaml`](../../render.yaml) (mặc định) | Web service + ổ đĩa 1 GB tại `/data` (SQLite) | [Deploy](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep) |
| [`deploy/render/render.postgres.yaml`](../../deploy/render/render.postgres.yaml) | Web service + Render Postgres 17 | [Deploy](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep&path=deploy/render/render.postgres.yaml) |
| [`deploy/render/render.full.yaml`](../../deploy/render/render.full.yaml) | Web + worker + Render Postgres + Render Key Value | [Deploy](https://render.com/deploy?repo=https://github.com/quinguyen1502/superstep&path=deploy/render/render.full.yaml) |

1. Bấm một nút, đăng nhập Render và điền `STUDIO_ADMIN_EMAILS` (tuỳ chọn thêm `STUDIO_PUBLIC_URL`,
   `OPENAI_API_KEY`). `JWT_SECRET` và `STUDIO_SECRET_KEY` được tự sinh.
2. Khi deploy xong, mở **Logs** và sao chép mật khẩu admin dùng một lần.
3. Đặt `STUDIO_PUBLIC_URL` là `https://<service>.onrender.com` (hoặc tên miền của bạn) nếu bạn đã bỏ qua.

Lưu ý: ổ đĩa cần instance trả phí (Starter trở lên), và dịch vụ có ổ đĩa chỉ chạy được một instance. Render xoá
database Postgres miễn phí sau 30 ngày. Các blueprint đặt `autoDeployTrigger: off` để bản của bạn không tự deploy lại
mỗi khi repo này thay đổi; dùng **Manual Deploy** để cập nhật.

## Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy?template=https://github.com/quinguyen1502/superstep)

[`app.json`](../../app.json) + [`heroku.yml`](../../heroku.yml) build image trên container stack và thêm
**Heroku Postgres** (Essential 0). Heroku không có ổ đĩa lưu trữ lâu dài nên không dùng được SQLite.

1. Bấm nút, nhập `STUDIO_ADMIN_EMAILS`, deploy.
2. `heroku logs --app <app> | grep "admin account"` hiện mật khẩu dùng một lần.
3. `heroku config:set STUDIO_PUBLIC_URL=https://<app>.herokuapp.com --app <app>`

Worker tuỳ chọn: `heroku addons:create heroku-redis:mini --app <app>` (đặt `REDIS_URL`), rồi
`heroku ps:scale worker=1 --app <app>`. Có thể thêm `heroku config:set STUDIO_WORKER=0` để run trong hàng đợi chỉ do
dyno worker xử lý (process worker bỏ qua biến này).

## Railway

[`railway.json`](../../railway.json) build `Dockerfile` ở thư mục gốc kèm health check. Hiện chưa có template công
khai; hãy deploy từ repo:

1. **New Project → Deploy from GitHub repo**, chọn bản fork của bạn hoặc `quinguyen1502/superstep`.
2. **Variables**: `JWT_SECRET` và `STUDIO_SECRET_KEY` (giá trị ngẫu nhiên, ví dụ `openssl rand -hex 32`),
   `STUDIO_ADMIN_EMAILS`, `RAILWAY_RUN_UID=0` (volume của Railway thuộc root; nếu không đặt, image chạy bằng user
   không phải root và không ghi được).
3. SQLite: **thêm volume** cho dịch vụ, gắn tại `/data`. Hoặc Postgres: thêm database Postgres và đặt
   `DATABASE_URL=${{Postgres.DATABASE_URL}}` (dùng Postgres có pgvector nếu bạn cần tìm kiếm vector).
4. **Settings → Networking → Generate Domain**, rồi đặt `STUDIO_PUBLIC_URL` bằng địa chỉ đó.

Worker tuỳ chọn: thêm Redis (`REDIS_URL=${{Redis.REDIS_URL}}` cho cả hai dịch vụ) và một dịch vụ thứ hai từ cùng
repo với lệnh khởi động `python -m app.worker`.

## Coolify và Dokploy (tự host)

Hai công cụ này chạy trên máy chủ của bạn, nên có hai lựa chọn:

- **Image all-in-one.** Tạo resource Docker Compose từ
  [`deploy/compose/docker-compose.single.yml`](../../deploy/compose/docker-compose.single.yml) (hoặc resource Docker
  image với `ghcr.io/quinguyen1502/superstep:latest`, cổng 8000, volume tại `/data`). Đặt `JWT_SECRET`,
  `STUDIO_SECRET_KEY` và `STUDIO_ADMIN_EMAILS` trong phần biến môi trường. Muốn dùng Postgres, tạo resource database
  và đặt `DATABASE_URL`.
- **Toàn bộ stack với sandbox Docker.** Tạo resource Docker Compose từ `docker-compose.yml` của repo (đặt
  `JWT_SECRET`, `POSTGRES_PASSWORD`, `STUDIO_SECRET_KEY`, `STUDIO_ENV=production`, `STUDIO_ADMIN_EMAILS`). Khi đó node
  Code chạy trong container Docker qua Docker socket của máy chủ: build `docker/studio-code` và `docker/studio-code-ts`
  trên máy chủ và đặt `STUDIO_ENABLE_CODE_NODES=1`. Gắn Docker socket cho container api quyền tương đương root trên
  máy chủ.

Cả hai đặt một reverse proxy (Traefik hoặc Caddy) trước dịch vụ; WebSocket hoạt động mà không cần cấu hình thêm.
Trỏ tên miền vào cổng 8000 (all-in-one) hoặc cổng 80 của dịch vụ `web` (toàn bộ stack).

## Máy chủ Docker bất kỳ

```sh
export JWT_SECRET=$(openssl rand -hex 32) STUDIO_SECRET_KEY=$(openssl rand -hex 32)
echo "$STUDIO_SECRET_KEY"
docker run -d -p 8000:8000 -v superstep-data:/data -e JWT_SECRET -e STUDIO_SECRET_KEY \
  -e STUDIO_ADMIN_EMAILS=you@example.com ghcr.io/quinguyen1502/superstep:latest
docker logs <container> | grep "admin account"
```

Hãy lưu `STUDIO_SECRET_KEY` vừa in ra ở nơi an toàn: mọi lần khởi động đều cần đúng giá trị này.

## Image

`.github/workflows/image.yml` build image ở mọi pull request, khởi động image trên SQLite và trên Postgres, quét bằng
Trivy (thất bại khi có lỗ hổng nghiêm trọng đã có bản vá) và phát hành lên GHCR từ `develop` (`:develop`,
`:sha-<commit>`) và từ tag phát hành (`:1.2.3`, `:1.2`, `:latest`; `:1` từ bản 1.0). Không có khoá bí mật nào nằm
trong image.
