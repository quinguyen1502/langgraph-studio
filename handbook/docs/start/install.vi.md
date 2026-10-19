# Cài đặt

## Yêu cầu

| Cho | Cần |
| --- | --- |
| Phát triển | Python 3.12 trở lên, Node 20 hoặc 22, Git |
| Bộ Compose | Docker có Compose v2 |
| Chế độ Code, import repo | Docker trên máy chạy API |

## Phát triển ở máy

```bash
git clone https://github.com/quinguyen1502/langgraph-studio.git
cd langgraph-studio
./dev.sh
```

Lần chạy đầu tạo `backend/.venv`, cài backend kèm phần dev, và chạy
`npm install` trong `frontend/`. Sau đó script khởi động:

| Dịch vụ | URL |
| --- | --- |
| UI (Vite) | <http://localhost:5173>, chuyển `/api` và `/ws` sang backend |
| Tài liệu API (OpenAPI) | <http://localhost:8000/docs> |

Đăng nhập bằng tài khoản demo `admin@example.com` / `admin123`. Tài khoản này
được tạo khi khởi động (trừ môi trường production), cùng với workflow ví dụ
**Customer Support**.

Khi phát triển, dữ liệu nằm trong SQLite (`backend/studio.db`) và run bus nằm
trong bộ nhớ. Không cần chạy thêm dịch vụ nào.

!!! tip "Chưa có key của model?"
    Node LLM không có credential và không có `OPENAI_API_KEY` sẽ dùng bản mock
    offline cho kết quả cố định, nên mọi ví dụ đều chạy được khi chưa có nhà
    cung cấp. Muốn dùng model thật, xem [Nhà cung cấp LLM](../operate/providers.md).

## Docker Compose

Compose chạy Postgres 17 có pgvector, Redis 7, API (tự chạy migration Alembic
và seed khi khởi động), một worker, và nginx phục vụ bản build của UI.

```bash
cp .env.example .env   # đặt JWT_SECRET và POSTGRES_PASSWORD; không commit .env
docker compose up --build
python scripts/compose_smoke.py http://localhost:8080
```

UI ở <http://localhost:8080> (`WEB_PORT`). Script smoke (cần `httpx` và `websockets`) kiểm tra health, đăng nhập bằng
tài khoản demo và chạy workflow ví dụ qua `/ws/run`.

Cấu hình production, tăng số worker và trace có ở
[Triển khai bằng Compose](../operate/deploy.md).

## Kiểm tra

```bash
curl -s http://localhost:8000/api/health
```

`data` cho biết `llm_mode`, `database` (`sqlite` hoặc `postgresql`), `run_bus`
(`memory` hoặc `redis`), `tracing` và `import_enabled`.

## Tiếp theo

[Làm workflow đầu tiên](first-workflow.md).
