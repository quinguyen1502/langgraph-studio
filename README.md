# LangGraph Studio (MVP nội bộ)

Công cụ kéo-thả để xây dựng workflow LangGraph: vẽ graph trên canvas, cấu hình node, lưu JSON vào SQLite, backend compile thành `StateGraph` và chạy với streaming qua WebSocket.

## Chạy nhanh
```bash
./dev.sh            # tự tạo venv + npm install lần đầu
```
- UI: http://localhost:5173 (Vite proxy `/api` và `/ws` sang backend)
- API: http://localhost:8000/docs

Dùng LLM thật (2 cách):
1. **Credentials trong app** (khuyến nghị): trang Workflows → **Credentials** → thêm OpenAI / OpenAI-compatible (base URL tuỳ chọn) hoặc Anthropic. Trong editor, chọn credential ở config của LLM node. API key được **mã hoá khi lưu** (Fernet, khoá từ `STUDIO_SECRET_KEY` hoặc file `~/.langgraph-studio/secret.key` tự tạo với quyền 0600, đổi bằng `STUDIO_SECRET_KEY_FILE`) và không bao giờ trả về trình duyệt; chỉ hiển thị 4 ký tự cuối. Mất khoá → credential cũ không giải mã được (báo lỗi rõ khi chạy).
2. `export OPENAI_API_KEY=sk-...` (tuỳ chọn `OPENAI_BASE_URL`) — dùng cho LLM node không chọn credential.

Không có credential/key → **mock LLM** xác định (deterministic), chạy offline. Lỗi provider (401, timeout…) hiện thành event `error` của node, không làm sập server.

## Đăng nhập & tài khoản demo
- Tài khoản demo (tự seed khi khởi động): **admin@example.com / admin123**
- Mật khẩu hash bằng PBKDF2-SHA256 (200k vòng, salt riêng); đăng nhập trả JWT (HS256, hạn 24h). Đặt `JWT_SECRET` khi chạy thật.
- Mọi API workflow/run cần header `Authorization: Bearer <token>`; WebSocket dùng `ws://.../ws/run?token=<token>`.
- Workflow thuộc về user tạo ra nó; user mới đăng ký được tặng 1 bản workflow ví dụ.

### Quy tắc mật khẩu & phiên đăng nhập (TASK-0003)
- Đăng ký: mật khẩu ≥ 8 ký tự, có cả chữ và số (tối đa 128). Tài khoản demo `admin123` được seed sẵn nên không bị áp quy tắc này.
- Email được chuẩn hoá (trim + chữ thường). Lỗi đăng nhập luôn là "Sai email hoặc mật khẩu" (không lộ email nào tồn tại).
- Token hết hạn hoặc không hợp lệ → tự đăng xuất, chuyển tới `/login?expired=1&next=…` kèm thông báo, đăng nhập lại sẽ quay về trang cũ. Frontend cũng tự đăng xuất đúng lúc token hết hạn.
- `JWT_TTL_SECONDS` (mặc định 86400). Khi `JWT_SECRET` còn là giá trị placeholder, backend log cảnh báo; với `STUDIO_ENV=production` thì backend từ chối khởi động.
- Giới hạn số lần đăng nhập sai / khoá tài khoản: **chưa làm** (hoãn, ngoài phạm vi TASK-0003).

## Các màn hình
- `/login`, `/register`: form shadcn Card, báo lỗi (sai mật khẩu, email trùng…), link qua lại.
- `/workflows`: bảng workflow (tên, số node, thời gian cập nhật, trạng thái lần chạy cuối), ô tìm kiếm, nút **New workflow**, menu ⋯ để đổi tên / nhân bản / xoá (có Dialog xác nhận).
- `/workflows/:id`: editor (nút ← về danh sách, menu user có Đăng xuất).
- Chưa đăng nhập → tự chuyển về `/login`; token hết hạn (401) → tự đăng xuất.

## Import LangGraph repo
Trên trang `/workflows` bấm **Import repo** → tab *GitHub URL* (repo public, tuỳ chọn branch/subdir) hoặc *Zip upload*. Dialog hiển thị tiến trình (fetching → installing → inspecting → ready), log và lỗi; nếu repo có nhiều graph thì chọn một graph rồi **Tạo workflow**.

Backend (`backend/app/engine/repo_import.py`, `backend/app/engine/sandbox/runner.py`):
1. Clone (`git clone --depth 1`) hoặc giải nén zip (chặn zip-slip) vào `~/.langgraph-studio/imports/<job_id>/` (đổi bằng biến `STUDIO_IMPORT_DIR`; nằm ngoài repo để không lẫn vào git/Factory scan). Workflow import trước đây (ở `backend/imports/`) vẫn chạy được vì lưu đường dẫn tuyệt đối.
2. Tạo venv riêng (`uv venv`, fallback `python -m venv`) và cài deps: `pip install -e .` nếu có pyproject/setup.py, hoặc `-r requirements.txt` (+ `langgraph`, `python-dotenv`).
3. Tìm graph từ `langgraph.json` → `graphs`; fallback: quét file `.py` có `StateGraph` và biến `x = ....compile(...)`.
4. Chạy `runner.py inspect` **trong subprocess bằng python của venv import** (timeout 120s): `graph.get_graph(xray=True)` → nodes/edges (kể cả conditional), JSON schema input/output → state fields, `inspect.getsource` của từng node → module:function + source. Node có dấu hiệu gọi LLM (ChatOpenAI, init_chat_model, bind_tools…) được gắn badge “LLM” (best-effort).
5. Chuyển thành workflow: `__start__`/`__end__` → Start/End, các node khác → node **Code** (read-only, xem source ở panel phải), conditional edge có label + nét đứt. Auto-layout bằng dagre ở frontend. Lưu thành workflow mới của user, kèm `source` metadata (repo, branch, ref, import id).

Chạy workflow import: WebSocket như cũ, nhưng backend chạy **graph gốc** bằng `runner.py run` trong venv của repo (`graph.astream(stream_mode=["debug","values"])`), chuyển các sự kiện task/task_result thành `node_started`/`node_finished` (duration, delta). Input là JSON state (key `__context__` để truyền runtime context; context dataclass có default sẽ tự tạo). Thiếu API key → lỗi rõ ràng kèm danh sách biến khai báo trong `.env.example`. Timeout chạy 300s (`STUDIO_RUN_TIMEOUT`).

Đã thử: `langchain-ai/new-langgraph-project` (chạy được không cần key), `langchain-ai/react-agent` (import + hiển thị conditional edge/loop; chạy cần ANTHROPIC/OPENAI/TAVILY key → báo lỗi thiếu key).

> ⚠️ **Bảo mật**: import = thực thi code tuỳ ý của repo (lúc cài đặt và lúc load/chạy graph). Code chỉ chạy trong subprocess + venv riêng với env rút gọn (chỉ PATH/HOME/… và các biến `*_API_KEY`, không có `JWT_SECRET`), có timeout — nhưng **không phải sandbox**: cùng user OS, có network và quyền đọc ghi file. Chỉ import repo tin cậy; nếu cần cách ly thật hãy chạy trong container/VM riêng.

Giới hạn: graph import là read-only (sửa trên canvas không ảnh hưởng code gốc); subgraph chỉ hiển thị khi xray hoạt động, sự kiện run chỉ ở cấp graph cha; job import lưu trong memory (restart server thì mất job đang chạy, workflow đã tạo vẫn còn); không hỗ trợ repo private, monorepo JS, hay `langgraph.json` dạng phức tạp.

## Run trace (tab Logs)
- Mỗi lần node chạy là 1 dòng: trạng thái, tên + loại node, thời lượng, thanh waterfall, tokens (nếu có). Vòng lặp hiện #2, #3…
- Bấm dòng (hoặc bấm node trên canvas) → chi tiết: Input (state trước), Output, State diff, Raw; JSON gập/mở được, có nút copy.
- "Raw events" hiện luồng sự kiện gốc; tab History replay dùng cùng timeline.
- `STUDIO_RECURSION_LIMIT` (mặc định 25) giới hạn số bước mỗi run để vòng lặp vô hạn dừng sớm; mỗi payload trong event bị cắt ở 16 000 ký tự JSON.

## Giới hạn runtime, huỷ & timeout (TASK-0004)
| Biến môi trường | Mặc định | Ý nghĩa |
|---|---|---|
| `STUDIO_RECURSION_LIMIT` | 25 | Số bước tối đa mỗi run (vòng lặp qua Condition sẽ dừng với lỗi) |
| `STUDIO_RUN_TIMEOUT` | 120 (giây) | Thời gian tối đa mỗi run → trạng thái `timeout` |
| `STUDIO_EVENT_MAX_BYTES` | 262144 (256 KB) | Kích thước tối đa 1 event (gửi + lưu); trường quá lớn thay bằng `{"_truncated": true, ...}` |
| `STUDIO_RUN_MAX_BYTES` | 2097152 (2 MB) | Tổng event lưu cho 1 run; phần giữa bị bỏ, thay bằng event `{"type":"truncated","dropped":n}` |
| `STUDIO_INPUT_MAX_BYTES` | 262144 | Kích thước input của run |
| `STUDIO_WORKFLOW_MAX_BYTES` | 1048576 | Kích thước workflow JSON (HTTP 413 nếu vượt) |

Ngoài ra trường `input`/`delta` trong timeline được cắt ở 16 000 ký tự JSON (TASK-0016) để giao diện nhẹ — lớp cắt nhỏ hơn, nằm trong giới hạn 256 KB/event.
- Nút **Cancel** (khi đang chạy) gửi `{"type":"cancel"}`; đóng tab/mất kết nối cũng huỷ run. Huỷ là *cooperative*: dừng giữa các bước, một lời gọi LLM/HTTP đang chạy có thể chạy xong ở nền. Trạng thái lưu: `ok`, `error`, `cancelled`, `timeout`.
- Lỗi trả về chỉ là 1 dòng, không có stack trace; khoá dạng `sk-…`, `Bearer …`, `api_key=…` bị che.
- Validator từ chối: edge trỏ node không tồn tại, trùng id, nhiều Start, node tự nối (trừ Condition), vòng lặp không đi qua Condition, node không đi tới được.
- `STUDIO_ENABLE_DEMO_TOOLS=1` bật tool `sleep_demo` (ngủ 1.5 s) chỉ để thử cancel/timeout (E2E dùng).

### Kiểm thử thủ công với provider thật
1. `export OPENAI_API_KEY=sk-...` (key của bạn; không commit) rồi `./dev.sh`. Badge góc phải editor phải hiện `LLM: openai`.
2. Đăng nhập `admin@example.com / admin123`, mở **Customer Support (example)**, bấm **Run** với input mặc định.
3. Kỳ vọng: timeline đủ các bước, `Classify intent` trả `order_status`, `Reply with order info` có câu trả lời thật (không có tiền tố `[mock:`). Trạng thái `Hoàn thành`.
4. Thử lỗi: đặt key sai → run kết thúc `Lỗi` với thông báo 1 dòng `HTTPStatusError: …401…`, key bị che. Thử Cancel trong lúc chạy.
5. Ghi kết quả vào `.factory-state/artifacts/QA-0005-task-0004.md` (mục "Manual real-provider E2E").
Khi TASK-0005 (PR #2, credentials theo workflow) được merge, làm lại bước 2–4 với credential lưu trong app.

## Dark mode
Nút mặt trăng/mặt trời trên thanh trên cùng (mọi màn hình). Lựa chọn được lưu trong localStorage; có thể ép bằng `?theme=dark`. Giao diện dùng Tailwind CSS v4 + shadcn/ui (theme neutral mặc định), icon lucide-react.

## Test & CI
```bash
cd backend && .venv/bin/python -m pytest -q   # cấu hình trong backend/pyproject.toml
cd frontend && npm run build && npm run lint
```
E2E (Playwright, headless) — tự khởi động backend riêng ở :8100 (DB tạm) và Vite ở :5190:
```bash
cd frontend && npx playwright install chromium   # lần đầu; hoặc dùng Chrome có sẵn: PW_CHROME=/usr/bin/google-chrome
npm run e2e                                      # login → list → open → run, sai mật khẩu, token hết hạn, rename/duplicate/delete, 100+ workflow
SHOTS=1 npm run e2e -- screenshots               # chụp lại docs/screenshots/auth-*, list-*, editor-not-found
```
`E2E_UVICORN` cho phép chỉ định đường dẫn uvicorn khác (mặc định `backend/.venv/bin/uvicorn`). E2E chưa chạy trên CI.

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
- **Tool**: `mode=function` + `function` (đăng ký bằng `@register_tool` trong `backend/app/engine/tools.py`, ví dụ `lookup_order`) hoặc `mode=http` + `method`, `url`, `body` (template).
- **Condition**: `field`; giá trị field được so khớp với `label` của các cạnh ra (chính xác → không phân biệt hoa thường → chứa chuỗi), `default` tuỳ chọn → `add_conditional_edges`.

## API
- `GET/POST /api/credentials`, `DELETE /api/credentials/{id}`, `GET /api/providers` (secret không bao giờ được trả về)
- `POST /api/auth/register`, `POST /api/auth/login` → `{token, user}`, `GET /api/me`
- `PATCH /api/workflows/{id}` (đổi tên), `POST /api/workflows/{id}/duplicate`, `DELETE /api/workflows/{id}`
- `GET/POST /api/workflows`, `GET /api/workflows/{id}`, `POST /api/validate`, `GET /api/tools`
- `GET /api/workflows/{id}/runs` – lịch sử chạy
- `WS /ws/run?token=...` – gửi `{"workflow_id":"example","input":{...}}` (hoặc `workflow` inline); nhận `run_started`, `node_started`, `node_finished{duration_ms,delta}`, `run_finished{state}`, `error`.

## Ví dụ có sẵn
`example` – Customer Support: Start → Classify intent (LLM) → Route (Condition theo `intent`) → `order_status`: Lookup order (tool) → Reply / `general`: General answer → End. Thử input `{"message":"Đơn A100 đâu rồi?"}` hoặc `{"message":"Giờ mở cửa?"}`.

## Giới hạn MVP
Auth đơn giản (không refresh token, không reset mật khẩu, không phân quyền chia sẻ), không chạy song song/loop phức tạp (mỗi LLM/Tool chỉ 1 cạnh ra), không có undo, mock LLM chỉ dùng heuristic từ khoá.

## Cấu trúc backend & database (TASK-0017)
Backend chia lớp `core / models / schemas / repositories / services / api / engine` — sơ đồ và quy tắc import ở `docs/backend-architecture.md` (DEC-0009).

- ORM: SQLAlchemy 2.0; migration: Alembic (`backend/app/migrations`). Server tự chạy `alembic upgrade head` khi khởi động; DB SQLite cũ được nhận nguyên dữ liệu.
- `DATABASE_URL` (tuỳ chọn) ghi đè `STUDIO_DB`, ví dụ `postgresql+psycopg://user:pw@localhost/studio` (cần cài driver). Mặc định vẫn là SQLite `backend/studio.db`.
- Tạo migration mới: `cd backend && .venv/bin/alembic revision --autogenerate -m "mô tả"`, rồi `.venv/bin/alembic upgrade head`.
