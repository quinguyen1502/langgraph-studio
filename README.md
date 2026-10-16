# LangGraph Studio (MVP nội bộ)

Công cụ kéo-thả để xây dựng workflow LangGraph: vẽ graph trên canvas, cấu hình node, lưu JSON vào SQLite, backend compile thành `StateGraph` và chạy với streaming qua WebSocket.

## Chạy nhanh
```bash
./dev.sh            # tự tạo venv + npm install lần đầu
```
- UI: http://localhost:5173 (Vite proxy `/api` và `/ws` sang backend)
- API: http://localhost:8000/docs

Dùng LLM thật: `export OPENAI_API_KEY=sk-...` (tuỳ chọn `OPENAI_BASE_URL` cho endpoint tương thích OpenAI) trước khi chạy. Không có key → **mock LLM** xác định (deterministic), chạy offline.

## Đăng nhập & tài khoản demo
- Tài khoản demo (tự seed khi khởi động): **admin@example.com / admin123**
- Mật khẩu hash bằng PBKDF2-SHA256 (200k vòng, salt riêng); đăng nhập trả JWT (HS256, hạn 24h). Đặt `JWT_SECRET` khi chạy thật.
- Mọi API workflow/run cần header `Authorization: Bearer <token>`; WebSocket dùng `ws://.../ws/run?token=<token>`.
- Workflow thuộc về user tạo ra nó; user mới đăng ký được tặng 1 bản workflow ví dụ.

## Các màn hình
- `/login`, `/register`: form shadcn Card, báo lỗi (sai mật khẩu, email trùng…), link qua lại.
- `/workflows`: bảng workflow (tên, số node, thời gian cập nhật, trạng thái lần chạy cuối), ô tìm kiếm, nút **New workflow**, menu ⋯ để đổi tên / nhân bản / xoá (có Dialog xác nhận).
- `/workflows/:id`: editor (nút ← về danh sách, menu user có Đăng xuất).
- Chưa đăng nhập → tự chuyển về `/login`; token hết hạn (401) → tự đăng xuất.

## Import LangGraph repo
Trên trang `/workflows` bấm **Import repo** → tab *GitHub URL* (repo public, tuỳ chọn branch/subdir) hoặc *Zip upload*. Dialog hiển thị tiến trình (fetching → installing → inspecting → ready), log và lỗi; nếu repo có nhiều graph thì chọn một graph rồi **Tạo workflow**.

Backend (`backend/app/importer.py`, `backend/app/sandbox/runner.py`):
1. Clone (`git clone --depth 1`) hoặc giải nén zip (chặn zip-slip) vào `~/.langgraph-studio/imports/<job_id>/` (đổi bằng biến `STUDIO_IMPORT_DIR`; nằm ngoài repo để không lẫn vào git/Factory scan). Workflow import trước đây (ở `backend/imports/`) vẫn chạy được vì lưu đường dẫn tuyệt đối.
2. Tạo venv riêng (`uv venv`, fallback `python -m venv`) và cài deps: `pip install -e .` nếu có pyproject/setup.py, hoặc `-r requirements.txt` (+ `langgraph`, `python-dotenv`).
3. Tìm graph từ `langgraph.json` → `graphs`; fallback: quét file `.py` có `StateGraph` và biến `x = ....compile(...)`.
4. Chạy `runner.py inspect` **trong subprocess bằng python của venv import** (timeout 120s): `graph.get_graph(xray=True)` → nodes/edges (kể cả conditional), JSON schema input/output → state fields, `inspect.getsource` của từng node → module:function + source. Node có dấu hiệu gọi LLM (ChatOpenAI, init_chat_model, bind_tools…) được gắn badge “LLM” (best-effort).
5. Chuyển thành workflow: `__start__`/`__end__` → Start/End, các node khác → node **Code** (read-only, xem source ở panel phải), conditional edge có label + nét đứt. Auto-layout bằng dagre ở frontend. Lưu thành workflow mới của user, kèm `source` metadata (repo, branch, ref, import id).

Chạy workflow import: WebSocket như cũ, nhưng backend chạy **graph gốc** bằng `runner.py run` trong venv của repo (`graph.astream(stream_mode=["debug","values"])`), chuyển các sự kiện task/task_result thành `node_started`/`node_finished` (duration, delta). Input là JSON state (key `__context__` để truyền runtime context; context dataclass có default sẽ tự tạo). Thiếu API key → lỗi rõ ràng kèm danh sách biến khai báo trong `.env.example`. Timeout chạy 300s (`STUDIO_RUN_TIMEOUT`).

Đã thử: `langchain-ai/new-langgraph-project` (chạy được không cần key), `langchain-ai/react-agent` (import + hiển thị conditional edge/loop; chạy cần ANTHROPIC/OPENAI/TAVILY key → báo lỗi thiếu key).

> ⚠️ **Bảo mật**: import = thực thi code tuỳ ý của repo (lúc cài đặt và lúc load/chạy graph). Code chỉ chạy trong subprocess + venv riêng với env rút gọn (chỉ PATH/HOME/… và các biến `*_API_KEY`, không có `JWT_SECRET`), có timeout — nhưng **không phải sandbox**: cùng user OS, có network và quyền đọc ghi file. Chỉ import repo tin cậy; nếu cần cách ly thật hãy chạy trong container/VM riêng.

Giới hạn: graph import là read-only (sửa trên canvas không ảnh hưởng code gốc); subgraph chỉ hiển thị khi xray hoạt động, sự kiện run chỉ ở cấp graph cha; job import lưu trong memory (restart server thì mất job đang chạy, workflow đã tạo vẫn còn); không hỗ trợ repo private, monorepo JS, hay `langgraph.json` dạng phức tạp.

## Dark mode
Nút mặt trăng/mặt trời trên thanh trên cùng (mọi màn hình). Lựa chọn được lưu trong localStorage; có thể ép bằng `?theme=dark`. Giao diện dùng Tailwind CSS v4 + shadcn/ui (theme neutral mặc định), icon lucide-react.

## Test & CI
```bash
cd backend && .venv/bin/python -m pytest -q   # cấu hình trong backend/pyproject.toml
cd frontend && npm run build && npm run lint
```
GitHub Actions: `.github/workflows/ci.yml` (pytest Python 3.12; npm ci + build trên Node 20/22, có cache) và `factory-verify.yml` (sinh bởi `factory stack apply`). Cài backend thủ công: `pip install -e "backend[dev]"`.

## Giao diện
- **Top bar**: tên workflow, Save, Run.
- **Trái**: palette node (Start, LLM, Tool/API, Condition, End) – kéo thả vào canvas; editor state schema (tên field + kiểu).
- **Giữa**: canvas React Flow – nối node bằng cách kéo từ handle phải sang handle trái; chọn rồi nhấn Delete để xoá.
- **Phải**: cấu hình node/edge đang chọn + lịch sử chạy (bấm để xem lại log).
- **Dưới**: input JSON + log từng node (started/finished, thời gian, state delta). Node đang chạy sáng vàng, xong chuyển xanh.

## Định dạng workflow
```json
{"name": "...", "state": [{"name":"message","type":"string"}],
 "nodes": [{"id":"n1","type":"llm","position":{"x":0,"y":0},
            "data":{"label":"..","model":"gpt-4o-mini","prompt":"Hi {{state.message}}","output_field":"answer"}}],
 "edges": [{"id":"e1","source":"a","target":"b","label":"(chỉ cho cạnh ra từ Condition)"}]}
```
- **LLM**: `model`, `prompt` (biến `{{state.field}}`), `output_field`.
- **Tool**: `mode=function` + `function` (đăng ký bằng `@register_tool` trong `backend/app/compiler.py`, ví dụ `lookup_order`) hoặc `mode=http` + `method`, `url`, `body` (template).
- **Condition**: `field`; giá trị field được so khớp với `label` của các cạnh ra (chính xác → không phân biệt hoa thường → chứa chuỗi), `default` tuỳ chọn → `add_conditional_edges`.

## API
- `POST /api/auth/register`, `POST /api/auth/login` → `{token, user}`, `GET /api/me`
- `PATCH /api/workflows/{id}` (đổi tên), `POST /api/workflows/{id}/duplicate`, `DELETE /api/workflows/{id}`
- `GET/POST /api/workflows`, `GET /api/workflows/{id}`, `POST /api/validate`, `GET /api/tools`
- `GET /api/workflows/{id}/runs` – lịch sử chạy
- `WS /ws/run?token=...` – gửi `{"workflow_id":"example","input":{...}}` (hoặc `workflow` inline); nhận `run_started`, `node_started`, `node_finished{duration_ms,delta}`, `run_finished{state}`, `error`.

## Ví dụ có sẵn
`example` – Customer Support: Start → Classify intent (LLM) → Route (Condition theo `intent`) → `order_status`: Lookup order (tool) → Reply / `general`: General answer → End. Thử input `{"message":"Đơn A100 đâu rồi?"}` hoặc `{"message":"Giờ mở cửa?"}`.

## Giới hạn MVP
Auth đơn giản (không refresh token, không reset mật khẩu, không phân quyền chia sẻ), không chạy song song/loop phức tạp (mỗi LLM/Tool chỉ 1 cạnh ra), không có undo, mock LLM chỉ dùng heuristic từ khoá.
