# Dịch vụ sandbox cho node Code

[English](sandbox.md) · [Hướng dẫn triển khai](README.vi.md) · [Biến môi trường](env-vars.vi.md)

Trên PaaS được quản lý không có Docker socket, nên image all-in-one chạy node Code trực tiếp trên server, cạnh
database và các khoá bí mật. **Dịch vụ sandbox** chuyển việc thực thi đó sang một container riêng không giữ khoá bí
mật nào của studio. Studio gọi dịch vụ qua HTTP với một token dùng chung.

```
studio (web / worker)  --HTTP + Bearer STUDIO_SANDBOX_TOKEN-->  dịch vụ sandbox  -->  một process cho mỗi lần gọi
JWT_SECRET, DATABASE_URL, credential                             chỉ có token         uid riêng, env rỗng, giới hạn
```

Image: `ghcr.io/quinguyen1502/superstep-sandbox` (build từ `docker/studio-sandbox/Dockerfile`, phát hành cùng image
chính).

## Bật dịch vụ

Trên dịch vụ sandbox:

| Biến | Giá trị |
|---|---|
| `STUDIO_SANDBOX_TOKEN` | Chuỗi ngẫu nhiên từ 16 ký tự (`openssl rand -hex 32`). Không cần gì khác. |
| `PORT` | Cổng lắng nghe (mặc định 8080; Render tự đặt). |
| `STUDIO_SANDBOX_HOST` | Địa chỉ bind (mặc định `0.0.0.0`; `::` trên Fly.io). |
| `STUDIO_CODE_MAX_SECONDS`, `STUDIO_CODE_MEMORY`, `STUDIO_CODE_CONCURRENCY` | Giới hạn mỗi lần gọi và số lần gọi đồng thời (mặc định 30 s, 256m, 4). |

Trên studio (web và worker):

| Biến | Giá trị |
|---|---|
| `STUDIO_CODE_RUNTIME` | `remote` |
| `STUDIO_SANDBOX_URL` | Địa chỉ dịch vụ, ví dụ `http://sandbox:8080` (chỉ `host:port` cũng được). |
| `STUDIO_SANDBOX_TOKEN` | Cùng token đó. |

Khi đó thẻ **Node Code** trong **Cài đặt → Người dùng** hiện "Dịch vụ sandbox (remote)" và trạng thái sẵn sàng của
từng ngôn ngữ. Run ghi `remote` làm runtime Code.

### Đã được tích hợp ở đâu

- **Docker Compose:** `STUDIO_CODE_RUNTIME=remote STUDIO_SANDBOX_TOKEN=... docker compose --profile sandbox up`. Dịch
  vụ chạy trên mạng nội bộ không có internet, chỉ đọc, bỏ mọi capability trừ vài quyền cần để đổi user.
- **Render:** [`deploy/render/render.full.yaml`](../../deploy/render/render.full.yaml) thêm dịch vụ này dưới dạng
  private service với token tự sinh trong một nhóm biến riêng (sandbox chỉ nhận nhóm đó).
- **Fly.io:** [`deploy/fly/sandbox.fly.toml`](../../deploy/fly/sandbox.fly.toml) là app thứ hai, riêng tư, truy cập
  tại `http://<app>.internal:8080` (hướng dẫn trong file).
- **Nơi khác:** chạy image như một private service (không mở cổng công khai) và đặt các biến ở trên.

## Mô hình bảo mật

Với mỗi lần gọi, dịch vụ:

- Chạy code trong một process mới với **môi trường rỗng** và thư mục tạm, trong process group riêng, bị dừng khi hết
  thời gian hoặc khi run bị huỷ.
- Hạ quyền xuống **một uid riêng không có đặc quyền** (từ 61000, mỗi lần gọi đồng thời một uid), nên code không thể
  gửi tín hiệu tới dịch vụ hay đọc file của lần gọi khác.
- Áp dụng **rlimit** (không gian địa chỉ, giây CPU, số file mở, số process) và giới hạn `STUDIO_CODE_MEMORY`.
- **Python:** một audit hook mà code không gỡ được sẽ từ chối socket, process mới (`subprocess`, `os.system`, `exec`,
  `fork`, `spawn`) và `ctypes`. **TypeScript:** Deno chạy không có quyền nào: không mạng, file, biến môi trường hay
  process, và chỉ có các package đã cache.
- Bản thân dịch vụ chỉ giữ token, và container của nó không chứa gì của studio ngoài các module runtime Code.

Những gì dịch vụ **không** làm được, nói thẳng:

- **Đây là cách ly bằng process, không phải bằng container hay máy ảo.** Mọi lần gọi dùng chung kernel và hệ thống
  file của container sandbox (uid của code đọc được nhưng không ghi được). Một lỗ hổng kernel hoặc cách vượt audit
  hook của Python (ví dụ qua extension đã biên dịch) sẽ chạm tới container sandbox, nhưng không chạm tới khoá bí mật
  hay database của studio, vốn nằm ở container khác.
- **Chặn mạng của Python là lớp bảo vệ bên trong trình thông dịch.** Ranh giới mạng thật là nền tảng: với Docker
  Compose, sandbox không có đường ra internet; trên Render và Fly.io, private service vẫn ra được internet. Nếu nền
  tảng của bạn có quy tắc egress, hãy chặn lưu lượng đi ra từ sandbox.
- **Token là cách xác thực duy nhất.** Giữ dịch vụ ở chế độ riêng tư (không mở cổng công khai) và đổi token nếu bị lộ
  (đặt giá trị mới ở cả hai phía).
- Cách này yếu hơn runtime Docker trên máy chủ riêng (mỗi lần gọi một container, `--network none`), vốn vẫn là lựa
  chọn được khuyến nghị khi bạn gắn được Docker socket ([hướng dẫn tự host](self-hosted.vi.md)).

## Các backend có thể có sau này

Runtime là một interface nhỏ trong `backend/app/engine/code_runtime.py` (`CodeRunner`: `problem` và `exchange`), nên
có thể thêm backend mạnh hơn mà không phải sửa phần còn lại của studio. Các ứng viên là microVM cho mỗi lần gọi như
Fly Machines hoặc Northflank sandboxes. Chúng chưa được triển khai.
