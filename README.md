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
- **Nhánh song song** (TASK-0011): node (không phải Condition) có nhiều cạnh ra → các nhánh chạy cùng superstep. Trường state được nhiều
  nhánh ghi cần `reducer`: `append` (list, gom mọi kết quả), `merge` (object), `add` (number/integer); mặc định `replace`. Thiếu reducer → lỗi validate.
- **Join**: chờ mọi nhánh đi vào rồi chạy một lần (cạnh chờ của LangGraph); cần ≥ 2 cạnh vào, không nhận trực tiếp từ Condition.
- **Subgraph**: `workflow_id` của một workflow đã lưu (của bạn). Workflow con được nhúng inline: node bên trong hiện trong trace dạng
  `Subgraph › node` (id `sub/node`), dừng ở Human, checkpoint và khôi phục như node thường. State dùng chung theo tên trường; vòng tham chiếu,
  workflow không tồn tại / import, lồng quá 5 cấp đều bị báo lỗi khi lưu và khi chạy (`WORKFLOW_INVALID`). Thiết kế: DEC-0020.
- **MCP tool** (TASK-0013): `server_id`, `tool`, `arguments` (object; chuỗi là template, đúng `{{state.x}}` thì giữ kiểu), `output_field`.
- **Retriever** (TASK-0012): `knowledge_base_id`, `query` (template), `top_k` (1–20), `output_field` → list `{text, score, filename, …}`.

## Máy chủ MCP & node MCP tool (TASK-0013)
- Cài đặt → **Máy chủ MCP**: thêm máy chủ Streamable HTTP (URL + header bí mật) hoặc stdio (lệnh + tham số + biến môi trường bí mật), **Tìm công cụ**,
  xem danh sách công cụ. Phạm vi *Cá nhân* (chỉ bạn) hoặc *Tổ chức* (admin quản lý, mọi người dùng). Không có máy chủ dựng sẵn.
- Secret được mã hoá (khoá Fernet như credential), API chỉ trả tên + giá trị che. Node MCP tool chọn máy chủ, công cụ và nhập tham số theo schema của công cụ.
- **stdio** tắt mặc định: `STUDIO_MCP_STDIO=1` để admin đăng ký. Tiến trình chạy trên máy/container API với môi trường sạch (không kế thừa `JWT_SECRET`,
  `DATABASE_URL`…), thư mục home tạm rỗng, timeout `STUDIO_MCP_TIMEOUT` (30 s) và bị kill cả process group; ngoài ra **không** cô lập thêm → chỉ thêm lệnh tin cậy,
  hoặc chạy máy chủ MCP trong container riêng qua HTTP.
- **HTTP**: URL phải là địa chỉ công khai (chống SSRF, kết nối ghim vào IP đã kiểm tra) trừ khi `STUDIO_MCP_ALLOW_PRIVATE=1` (vd. sidecar trong compose).
- Thiết kế: DEC-0022.

## Vai trò, chia sẻ workflow & "Add to Slack" (TASK-0014)
- **Vai trò** (toàn studio): `admin` (quản lý người dùng, kênh/máy chủ MCP của tổ chức, toàn quyền mọi workflow), `editor` (mặc định: tạo
  workflow, credential, kho tri thức, máy chủ MCP, kênh riêng), `viewer` (chỉ mở và chạy workflow được chia sẻ). Không có SSO.
- Cài đặt → **Người dùng** (admin): đổi vai trò, vô hiệu hoá tài khoản (có hiệu lực ngay, kể cả token và WebSocket đang mở), bảng quyền.
  Không thể tự đổi vai trò / tự vô hiệu hoá, và luôn còn ít nhất một admin.
- `STUDIO_ADMIN_EMAILS` chỉ còn là **bootstrap**: email trong danh sách thành admin khi đăng ký, và khi khởi động **chỉ khi không còn admin
  nào hoạt động** (khôi phục khi bị khoá). Tài khoản đầu tiên (user demo) là admin. `STUDIO_DEFAULT_ROLE=viewer` để tài khoản mới chỉ xem.
- **Chia sẻ**: nút **Chia sẻ** trong editor (chủ sở hữu hoặc admin) → thêm email với quyền *Người xem* (mở, chạy) hoặc *Người chỉnh sửa*
  (thêm sửa, lưu). Chỉ chủ sở hữu / admin xoá, chia sẻ, tạo API token. Người xem thấy editor chỉ đọc; vai trò `viewer` giới hạn mọi chia sẻ ở mức xem.
- Lần chạy workflow được chia sẻ dùng **credential, kho tri thức, máy chủ MCP và subgraph của chủ sở hữu**; người không có quyền sửa chỉ chạy
  bản đã lưu. Lịch sử chạy: chủ sở hữu / admin thấy mọi lần chạy, người khác chỉ thấy lần chạy của mình.
- **Add to Slack**: đặt `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, `SLACK_SIGNING_SECRET` (trang *Basic Information* của Slack app) và
  `STUDIO_PUBLIC_URL`; trong Slack app thêm Redirect URL `{STUDIO_PUBLIC_URL}/api/approvals/slack/oauth/callback`, bật *Manage Distribution*.
  Thẻ Slack trong Cài đặt → Kênh phê duyệt hiện nút **Add to Slack** (cá nhân, hoặc tổ chức cho admin); dán bot token vẫn dùng được.
- Thiết kế: DEC-0023.

## Nhóm, chuyển quyền sở hữu, nhật ký & xoá người dùng (TASK-0029)
- Cài đặt → **Nhóm** (admin): tạo nhóm, thêm thành viên. Trong hộp **Chia sẻ** chọn *Nhóm* để chia sẻ workflow với cả nhóm (xem / chỉnh sửa);
  quyền hiệu lực là quyền cao nhất giữa chia sẻ trực tiếp và các nhóm.
- **Chuyển quyền sở hữu** (chủ sở hữu hoặc admin, trong hộp Chia sẻ): người nhận phải là editor/admin. Credential, kho tri thức, máy chủ MCP
  mà người nhận không dùng được có thể gán lại sang tài nguyên của họ, hoặc giữ và được **đánh dấu** cần sửa.
- Cài đặt → **Hoạt động** (admin): nhật ký đổi vai trò, kích hoạt, chia sẻ, nhóm, chuyển quyền, xoá tài khoản, chính sách; lọc theo loại, thời gian, từ khoá.
- **Xoá người dùng** (Cài đặt → Người dùng): *Ẩn danh hoá* (giữ lịch sử chạy) hoặc *Xoá* (xoá cả lần chạy); workflow họ sở hữu phải chuyển cho người khác trước.
- **Tài nguyên tổ chức khi chạy**: admin chọn vai trò được dùng kênh phê duyệt và máy chủ MCP *Toàn tổ chức* (mặc định editor + admin).
- Subgraph: lỗi kiểm tra ghi `Cha › Node con`; xoá workflow đang được dùng làm subgraph sẽ bị chặn kèm danh sách (có *Vẫn xoá*); danh sách phiên bản báo khi subgraph đã đổi.
- Ngoài phạm vi: Slack Enterprise Grid (cài đặt toàn Grid). Thiết kế: DEC-0024.

## Kho tri thức & node Retriever (TASK-0012)
- Cài đặt → **Kho tri thức**: tạo kho, tải `.txt` / `.md` / `.pdf` (≤ 10 MB), xem số đoạn, thử tìm kiếm, đổi model/khoá, lập chỉ mục lại.
- Embedding: credential OpenAI(-compatible) của kho → `OPENAI_API_KEY` → mock offline cố định (`mock:512`, không cần khoá). Mặc định
  `text-embedding-3-small`. Đổi model/khoá thì tài liệu được lập chỉ mục lại; nếu embedder thay đổi ngoài UI, tìm kiếm báo `KB_EMBEDDER_CHANGED`.
- Lưu trữ: Postgres có pgvector (image compose `pgvector/pgvector:pg17`) → cột `vector`, tìm bằng SQL; Postgres thường hoặc SQLite → JSON + so cosine
  trong Python (cùng kết quả). API: `/api/knowledge-bases…` (xem `docs/api-errors.md` cho mã `KB_*`). Thiết kế: DEC-0021.

## Nhà cung cấp LLM: Ollama, LM Studio, OpenAI-compatible, OpenRouter (TASK-0030)
Mở **Credentials** (thanh trên) → chọn provider. Mỗi provider là một lớp nhỏ trong `backend/app/engine/providers.py` (registry, DEC-0032):

| Provider | Base URL mặc định | API key | Danh sách model |
| --- | --- | --- | --- |
| Ollama | `http://localhost:11434` | không cần | `/api/tags` |
| LM Studio | `http://localhost:1234/v1` | không cần | `/v1/models` |
| OpenAI-compatible (vLLM, llama.cpp `server`, LocalAI) | `http://localhost:8000/v1` | tuỳ server | `/v1/models` |
| OpenRouter | `https://openrouter.ai/api/v1` | **bắt buộc** (+ header tuỳ chọn `HTTP-Referer`, `X-Title`) | `/api/v1/models` |
| OpenAI / Anthropic | như trước | bắt buộc | `/models`, `/v1/models` |

- **Test connection** gọi danh sách model của provider (trước hoặc sau khi lưu); lỗi trả mã `PROVIDER_UNREACHABLE`, `PROVIDER_AUTH_FAILED`, `PROVIDER_BAD_RESPONSE`, `MODEL_NOT_FOUND` (`docs/api-errors.md`).
- Trong node LLM, ô **Model** có nút tải danh sách model từ credential đã chọn; không tải được thì vẫn gõ tay.
- Chạy bằng LangChain: `ChatOllama` (langchain-ollama) và `ChatOpenAI(base_url=…)` cho LM Studio / OpenRouter / OpenAI-compatible, nên streaming và `bind_tools` (tool calling) dùng được nếu model hỗ trợ (`engine.llm.chat_model(cred, model)`).
- Cài đặt: Ollama `ollama serve` + `ollama pull llama3.2`; LM Studio: tab *Developer* → *Start server* và tải một model; OpenRouter: tạo key tại https://openrouter.ai/keys.
- **Xem trực tiếp (streaming):** khi chạy, node LLM gửi từng đoạn văn bản qua WebSocket (`node_token`), và tab Logs hiện chữ đang sinh ở dòng của node và trong tab Output. Kết quả cuối không đổi, và các đoạn này không lưu vào lịch sử run.
- **Embedding cho kho tri thức:** chọn credential Ollama / LM Studio / OpenAI-compatible / OpenRouter / OpenAI trong *Cài đặt → Kho tri thức*. Model mặc định theo provider (Ollama: `nomic-embed-text`, cần `ollama pull nomic-embed-text`). Nút **Kiểm tra embedding** cho biết số chiều. Mỗi kho lưu số chiều (`dims`). Nếu model trả vector khác số chiều, API báo `KB_EMBEDDING_DIMENSION_MISMATCH` và bạn chỉ cần bấm index lại.
- **Sửa credential:** bấm biểu tượng bút ở dòng credential. Để trống ô key thì giữ key cũ (chỉ hiện dạng che), nhập key mới thì thay. Provider không đổi được.
- **Docker Compose:** trong container, `localhost` là chính container. `api` và `worker` có `extra_hosts: host.docker.internal:host-gateway`, nên đặt base URL là `http://host.docker.internal:11434` (Ollama) hoặc `http://host.docker.internal:1234/v1` (LM Studio). Trên Linux, Ollama cần nghe trên mọi interface (`OLLAMA_HOST=0.0.0.0 ollama serve`), LM Studio bật *Serve on Local Network*; tường lửa có thể phải cho phép subnet Docker (vd. `sudo iptables -I INPUT -i br-+ -j ACCEPT` / `-i docker0`).

## API
Mọi endpoint trả về envelope: `{"success": true, "data": …, "error": null}` hoặc `{"success": false, "data": null, "error": {"code": "AUTH_INVALID_CREDENTIALS", "message": "…", "details": …}}`. Danh mục mã lỗi: `docs/api-errors.md` (DEC-0010).

## Ngôn ngữ (i18n)
UI có tiếng Anh và tiếng Việt (react-i18next, `frontend/src/locales/en.json` / `vi.json`). Mặc định theo ngôn ngữ trình duyệt; đổi bằng nút ngôn ngữ (màn hình đăng nhập và thanh trên cùng), lựa chọn lưu ở `localStorage.lang`. Lỗi API được dịch theo `error.code`; mã chưa có bản dịch thì hiện message tiếng Anh của server.

- `GET/POST /api/credentials`, `DELETE /api/credentials/{id}`, `GET /api/providers` (secret không bao giờ được trả về)
- `POST /api/auth/register`, `POST /api/auth/login` → `{token, user}`, `GET /api/me`
- `PATCH /api/workflows/{id}` (đổi tên), `POST /api/workflows/{id}/duplicate`, `DELETE /api/workflows/{id}`
- `GET/POST /api/workflows`, `GET /api/workflows/{id}`, `POST /api/validate`, `GET /api/tools`
- `GET /api/workflows/{id}/runs` – lịch sử chạy
- `WS /ws/run?token=...` – gửi `{"workflow_id":"example","input":{...}}` (hoặc `workflow` inline); nhận `run_started`, `node_started`, `node_finished{duration_ms,delta}`, `run_finished{state}`, `error`.

## Ví dụ có sẵn
`example` – Customer Support: Start → Classify intent (LLM) → Route (Condition theo `intent`) → `order_status`: Lookup order (tool) → Reply / `general`: General answer → End. Thử input `{"message":"Đơn A100 đâu rồi?"}` hoặc `{"message":"Giờ mở cửa?"}`.

## Giới hạn MVP
Auth đơn giản (không refresh token, không reset mật khẩu, không phân quyền chia sẻ), không có undo, mock LLM chỉ dùng heuristic từ khoá.

## Cấu trúc backend & database (TASK-0017)
Backend chia lớp `core / models / schemas / repositories / services / api / engine` — sơ đồ và quy tắc import ở `docs/backend-architecture.md` (DEC-0009).

- ORM: SQLAlchemy 2.0; migration: Alembic (`backend/app/migrations`). Server tự chạy `alembic upgrade head` khi khởi động; DB SQLite cũ được nhận nguyên dữ liệu.
- `DATABASE_URL` (tuỳ chọn) ghi đè `STUDIO_DB`, ví dụ `postgresql://user:pw@localhost/studio` (driver `psycopg` đã có sẵn trong dependencies). Mặc định vẫn là SQLite `backend/studio.db`.
- `REDIS_URL` (tuỳ chọn), ví dụ `redis://localhost:6379/0`: trạng thái run, tín hiệu huỷ và pub/sub sự kiện (`run:{id}:events`) qua Redis, nên có thể huỷ run từ API worker khác bằng `POST /api/runs/{id}/cancel`. Bỏ trống = bộ nhớ trong tiến trình (DEC-0011).
- Tạo migration mới: `cd backend && .venv/bin/alembic revision --autogenerate -m "mô tả"`, rồi `.venv/bin/alembic upgrade head`.

## Triển khai với Docker Compose (TASK-0009)
Stack gồm `postgres` (17 + pgvector, image `pgvector/pgvector:pg17`), `redis` (7), `api` (FastAPI, tự chạy `alembic upgrade head` + seed khi khởi động) và `web` (nginx phục vụ bản build Vite, proxy `/api` và `/ws`). Cả bốn service đều có healthcheck; dữ liệu nằm trong các volume `pgdata`, `redisdata`, `apidata`.

```bash
cp .env.example .env      # đặt JWT_SECRET và POSTGRES_PASSWORD (bắt buộc); không commit .env
docker compose up --build # UI: http://localhost:8080 (đổi bằng WEB_PORT)
python scripts/compose_smoke.py http://localhost:8080   # kiểm tra: health, đăng nhập demo, chạy ví dụ qua /ws/run
```

- Đăng nhập demo: `admin@example.com` / `admin123`.
- `GET /api/health` cho biết `database` (`postgresql`/`sqlite`) và `run_bus` (`redis`/`memory`).
- `STUDIO_SECRET_KEY` (khoá Fernet cho credential) để trống thì được sinh một lần vào volume `apidata` (`/data/secret.key`); muốn chạy production hãy đặt cố định và `STUDIO_ENV=production`.
- Mỗi stack chạy một container `api` (migration lúc khởi động không khoá chống chạy song song).
- Test backend trên Postgres + Redis tại máy: `DATABASE_URL=postgresql://… TEST_DATABASE_URL=postgresql://… REDIS_URL=redis://localhost:6379/0 .venv/bin/python -m pytest -q` (role cần quyền `CREATEDB` cho `tests/test_db_postgres.py`).

## Tracing & số liệu run (TASK-0010)
Mỗi run có số liệu tóm tắt (thời gian, token vào/ra, chi phí USD, số lỗi). Chúng hiện ở thanh tóm tắt của tab Logs, ở từng span LLM (rê chuột để xem model và token) và trong tab Lịch sử.

- Chế độ mock: token là ước tính, chi phí `$0`, không cần key.
- Model không có trong bảng giá (`backend/app/engine/usage.py`) hiển thị chi phí `—`.

Trace theo chuẩn OpenTelemetry: một trace cho mỗi run, một span cho mỗi node (thời gian, trạng thái, lỗi, `gen_ai.usage.*`, chi phí). Không cấu hình exporter thì tracing tắt hẳn (no-op).

| Đích | Biến môi trường |
|---|---|
| OTLP (Jaeger, Tempo, OTel Collector…) | `OTEL_EXPORTER_OTLP_ENDPOINT` (+ các biến `OTEL_*` chuẩn, ví dụ `OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_SERVICE_NAME`) |
| LangSmith (tuỳ chọn) | `LANGSMITH_API_KEY` **và** `LANGSMITH_TRACING=true` (+ `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`) |
| Link "Mở trace" trong UI | `STUDIO_TRACE_URL`, ví dụ `http://localhost:16686/trace/{trace_id}` |

Xem trace bằng Jaeger trong compose:
```bash
# trong .env:
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
STUDIO_TRACE_URL=http://localhost:16686/trace/{trace_id}
docker compose --profile tracing up --build   # Jaeger UI: http://localhost:16686 (service "langgraph-studio")
```
Chạy dev không dùng compose: `docker run -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one`, rồi chạy backend với `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`.

## Human-in-the-loop (TASK-0006)
Node **Human** tạm dừng run để chờ người duyệt hoặc nhập liệu:

- **Cấu hình**: `prompt` (template `{{state.field}}`) và `output_field`.
- **Khi chạy tới node**: run chuyển sang trạng thái `waiting`. Tab Logs hiện khung trả lời với các nút **Duyệt** (`approved`), **Từ chối** (`rejected`) hoặc gửi văn bản tự do. Phản hồi được ghi vào `output_field`, nên có thể dùng Condition để rẽ nhánh theo `approved` / `rejected`.
- **Danh sách chờ**: trang danh sách workflow có thẻ "Đang chờ bạn" liệt kê các run đang chờ; bấm **Phản hồi** để mở đúng run đó.
- **Lưu trạng thái**: checkpoint lưu trong DB, nên vẫn tiếp tục được sau khi khởi động lại server.
- **Quyền**: chỉ chủ của run mới được duyệt hoặc huỷ (DEC-0013).
- **API**:
  - `GET /api/runs/pending`: danh sách run đang chờ.
  - WebSocket `/ws/run` gửi `{"resume_run_id": "...", "response": "approved"}` để tiếp tục.
  - `POST /api/runs/{id}/cancel` để huỷ run đang chờ.

## Kích hoạt workflow qua API / webhook (TASK-0007)
1. Mở workflow, bấm **API** trên thanh công cụ, tạo token (dạng `wft_…`; token chỉ hiện **một lần**). Có thể thu hồi bất kỳ lúc nào.
2. Gọi:
```bash
curl -X POST http://localhost:8080/api/hooks/workflows/<wid>/runs \
  -H "Authorization: Bearer wft_..." -H "Content-Type: application/json" \
  -d '{"input": {"message": "hi"}, "mode": "sync"}'
```
- **Các chế độ**:
  - `mode: "sync"`: chờ và trả `final_state`.
  - `"async"` (mặc định): trả `202 {run_id, status: "queued"}`, rồi xem kết quả bằng `GET /api/hooks/workflows/<wid>/runs/<run_id>`.
  - `callback_url`: nhận kết quả bằng POST (header `X-Studio-Event: run.finished`). Địa chỉ nội bộ bị chặn trừ khi `STUDIO_ALLOW_PRIVATE_CALLBACKS=1`.
- **Lỗi**: token sai, thiếu hoặc đã thu hồi trả về `401 TRIGGER_TOKEN_INVALID`.
- **Lịch sử**: run qua API hiện trong tab Lịch sử với nhãn **API**.
- **Hàng đợi**: run được đưa vào hàng đợi rồi do worker thực thi.
  - Mặc định worker chạy ngay trong tiến trình API (`STUDIO_WORKER=1`).
  - Khi có `REDIS_URL`, hàng đợi là Redis nên có thể chạy worker riêng bằng `python -m app.worker`.
  - Compose có sẵn service `worker`; mở rộng bằng `docker compose up --scale worker=3`.
- **Chưa hỗ trợ**: lịch chạy định kỳ (cron), xem DEC-0014.

### Phiên bản workflow (TASK-0008)

- **Tạo phiên bản**: mỗi lần lưu có thay đổi (lưu, đổi tên, nhân bản, import) sẽ tạo một phiên bản bất biến, ghi kèm tác giả và thời điểm. Lưu mà không thay đổi gì thì không tạo phiên bản mới. Workflow có sẵn trước khi nâng cấp trở thành **v1**.
- **Xem lịch sử**: bấm **Phiên bản** trên thanh công cụ.
  - Danh sách: vN, tác giả, thời gian, số nút.
  - So sánh hai phiên bản bất kỳ: nút, cạnh và state được thêm, xoá, sửa hoặc di chuyển, kèm before/after.
  - **Khôi phục**: có bước xác nhận. Phiên bản cũ được chép thành một **phiên bản mới nhất** nên lịch sử không bị ghi đè; tên hiện tại được giữ lại.
- **Tab Lịch sử**: mỗi run có nhãn `vN` cho phiên bản đã chạy. Nếu chạy với thay đổi chưa lưu, nhãn là **chưa lưu**. Việc chỉ kéo nút sang chỗ khác không tính là thay đổi.
- **API**:
  - `GET /api/workflows/{wid}/versions`
  - `GET …/versions/{n}`
  - `GET …/versions/diff?a=1&b=2`
  - `POST …/versions/{n}/restore`
  - Lỗi `404 VERSION_NOT_FOUND`.
- Xem DEC-0015.

## Hardening phase 2 (TASK-0019)

### Human-in-the-loop
- **Thời lượng run** chỉ tính thời gian chạy thực tế. Khoảng thời gian chờ người phản hồi không được tính.
- **Hết hạn**: run chờ lâu hơn `STUDIO_WAIT_TTL` giây (mặc định 7 ngày, `0` = không bao giờ) sẽ chuyển sang trạng thái `expired`, kèm sự kiện `run_expired`.
  - Server quét mỗi 60 giây và kiểm tra thêm khi có người truy cập run.
  - Resume một run đã hết hạn trả về `410 RUN_EXPIRED`.
- **Badge trên thanh tiêu đề**: hiện số run đang chờ bạn phản hồi. Bấm vào để tới danh sách chờ.

### Webhook & API trigger
- **Chữ ký**: khi tạo token sẽ nhận thêm **signing secret** `whsec_…`, chỉ hiện một lần.
  - Mỗi callback có header `X-Studio-Signature: t=<unix ts>,v1=<hex>`, trong đó `v1 = HMAC-SHA256(secret, "<t>.<raw body>")`.
  - Bên nhận cần kiểm tra chữ ký và từ chối nếu `t` lệch quá 5 phút:
```python
import hashlib, hmac, time
def verify(secret: str, header: str, body: bytes, tolerance=300) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    if abs(time.time() - int(parts["t"])) > tolerance: return False
    mac = hmac.new(secret.encode(), f'{parts["t"]}.'.encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, parts["v1"])
```
  - Token tạo trước TASK-0019 không có secret nên callback của chúng không được ký. Tạo token mới để có chữ ký.
- **Giới hạn tần suất**: mỗi token được `STUDIO_TRIGGER_RATE_LIMIT` lần chạy mỗi `STUDIO_TRIGGER_RATE_WINDOW` giây (mặc định 60/60).
  - Vượt giới hạn trả về `429 RATE_LIMITED`, kèm header `Retry-After`.
  - Bộ đếm dùng chung qua Redis; không có Redis thì mỗi tiến trình tự đếm.
  - Việc poll kết quả không bị giới hạn.
- **Chế độ sync** chờ tối đa `STUDIO_SYNC_WAIT_MAX` giây (mặc định 30). Hết thời gian chờ thì trả về `202` kèm `poll_url` và header `Location`. Chế độ async cũng trả `poll_url`.
- **Hàng đợi tin cậy (Redis)**:
  - Worker chuyển job sang danh sách "processing" của riêng nó (`BLMOVE`), và chỉ xoá job (ack) sau khi run đã được ghi lại.
  - Job mất lease được đưa trở lại hàng đợi (xem TASK-0020 bên dưới).
  - **Hàng đợi in-memory chỉ dùng cho dev**, vì job bị mất khi tiến trình khởi động lại.
- **SSRF / DNS rebinding**: tên miền chỉ được phân giải **một lần** lúc gửi.
  - Mọi địa chỉ phân giải ra đều được kiểm tra, rồi kết nối thẳng tới IP đó. Header `Host` và chứng chỉ TLS (SNI) vẫn theo tên miền gốc.
  - Webhook không đi theo redirect.

### Phiên bản
- **Phân trang**: `GET …/versions?limit=50&offset=0` trả về `{items, total, limit, offset}`. Hộp thoại Phiên bản có nút "Tải thêm".
- **Giới hạn số phiên bản**: `STUDIO_VERSION_KEEP=N` chỉ giữ N phiên bản mới nhất. Phiên bản mà một run đã chạy thì không bao giờ bị xoá.
- **Khôi phục**:
  - Khôi phục phiên bản có nội dung giống hệt hiện tại thì không làm gì (`unchanged: true`), và giao diện có thông báo.
  - Hộp xác nhận khôi phục cảnh báo nếu editor đang có thay đổi chưa lưu.
- **Lưu đồng thời**: hai lần lưu cùng lúc trùng số phiên bản thì tự thử lại.

### Migration & Redis
- **Migration khi khởi động** được khoá để nhiều API/worker khởi động cùng lúc không đụng nhau:
  - Postgres dùng `pg_advisory_xact_lock`.
  - SQLite dùng file `<db>.migrate.lock` (`fcntl`).
- **Redis trên event loop** (run bus `start/finish/publish`, rate limit) dùng client `redis.asyncio`. Các lệnh chặn (lấy job, kiểm tra huỷ trong luồng chạy run) chạy trong thread.

### Tracing
- **Bảng giá**: `STUDIO_PRICES='{"my-model": [1.0, 2.0]}'` hoặc `STUDIO_PRICES_FILE=/path/prices.json` (đơn vị USD / 1 triệu token), ghi đè hoặc bổ sung bảng có sẵn. Tiền tố dài nhất được ưu tiên.
- **Span được tạo khi run kết thúc**, dựng lại từ timestamp của các sự kiện; run đang chạy chưa có trace. Run đang chờ (HITL) chỉ có trace khi đã kết thúc.
- **Tránh trace trùng trên LangSmith**: khi bật exporter LangSmith của Studio (`LANGSMITH_API_KEY` + `LANGSMITH_TRACING=true`), tracer LangSmith riêng của LangChain bị tắt (`LANGSMITH_TRACING_V2=false` + `langsmith.configure(enabled=False)`). Nhờ vậy mỗi lần gọi LLM chỉ xuất hiện một lần.

## Hardening bổ sung (TASK-0020)

### Thông báo khi run chờ người phản hồi
- **Chuông thông báo** trên thanh tiêu đề hiện số thông báo chưa đọc. Bấm vào một thông báo để mở run và đánh dấu đã đọc. Có nút "Đánh dấu tất cả đã đọc".
  - API: `GET /api/notifications?unread=1`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`.
- **E-mail**: đặt `SMTP_HOST` (cùng `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS`/`SMTP_SSL`). Không đặt `SMTP_HOST` thì không gửi e-mail. Link trong e-mail dùng `STUDIO_PUBLIC_URL`.
  - Thử ở máy local: `python -m aiosmtpd -n -l 127.0.0.1:1025` rồi đặt `SMTP_HOST=127.0.0.1 SMTP_PORT=1025 SMTP_STARTTLS=0`.
- **Notify webhook** (tuỳ chọn): `STUDIO_NOTIFY_WEBHOOK_URL` nhận JSON cho mỗi run `waiting`/`expired`, được ký bằng `STUDIO_NOTIFY_WEBHOOK_SECRET` nếu có.

### Webhook kết quả
- **Nhật ký gửi (deliveries)**: mỗi callback được lưu với trạng thái, số lần thử, mã HTTP và độ trễ. Xem ở tab **Deliveries** trong hộp thoại API, có nút **Gửi lại**.
- **Thử lại**: lỗi mạng và mọi phản hồi không phải 2xx được thử lại qua hàng đợi (địa chỉ bị chặn bởi SSRF guard thì thất bại ngay) với độ trễ tăng dần `min(STUDIO_WEBHOOK_BACKOFF_BASE^n, STUDIO_WEBHOOK_BACKOFF_MAX)`, tối đa `STUDIO_WEBHOOK_MAX_ATTEMPTS` lần. Bên nhận nên khử trùng lặp theo `run_id` + event.
- **Đổi signing secret**: nút xoay khoá trên mỗi token. Secret mới chỉ hiện một lần. Secret cũ vẫn hợp lệ thêm `STUDIO_SECRET_GRACE` giây (mặc định 1 ngày): trong thời gian này header có hai giá trị `v1=`, bên nhận chấp nhận nếu một trong hai khớp.

### Hàng đợi & khôi phục
- Mỗi job đang chạy giữ một **lease** (TTL `STUDIO_JOB_VISIBILITY_TIMEOUT`, tự gia hạn). Một vòng quét định kỳ (`STUDIO_JOB_REAP_EVERY`) đưa lại hàng đợi các job mất lease, thay cho heartbeat.
- Job được khôi phục **chạy tiếp từ checkpoint cuối** (sự kiện `run_recovered`) thay vì chạy lại từ đầu. Node đang chạy lúc sập có thể chạy lại, nên node có side effect (HTTP, tool) cần idempotent. Chi tiết: DEC-0017.

### Telemetry
- Span được xuất **ngay khi từng node xong**, không đợi hết run. Không cấu hình thì vẫn là no-op.
- `STUDIO_OTEL_METRICS=1` cùng `OTEL_EXPORTER_OTLP_ENDPOINT`: xuất metrics `studio.runs`, `studio.run.duration`, `studio.tokens`, `studio.cost`, `studio.errors`.

## Effectively-once & thông báo trực tiếp (TASK-0021)

### Side effect "effectively-once"
- Mỗi lần chạy node LLM/Tool có một **idempotency key** cố định theo (run, node, lần lặp). Node Tool HTTP gửi header `Idempotency-Key` (kèm `X-Studio-Run-Id`, `X-Studio-Attempt`). Tool Python nhận key nếu khai báo tham số `idempotency_key`. Khi job được khôi phục và chạy lại đúng node đó, key **giữ nguyên**, nên bên nhận hỗ trợ idempotency chỉ áp dụng một lần.
- **Sổ kết quả node (ledger)**: kết quả của node có side effect được lưu lại. Khi khôi phục, node đã xong được dùng lại kết quả (`reused` trong trace) thay vì chạy lại. Ledger được xoá khi run kết thúc.
- **Fencing token**: mỗi lần worker nhận một run, `runs.lease_gen` tăng lên. Mọi lần ghi (checkpoint, ledger, kết quả) phải mang đúng số này. Worker cũ (mất lease) bị từ chối ghi và tự dừng run của nó.

### Checkpoint
- Checkpoint lấy trực tiếp từ LangGraph theo từng superstep, nên bước **song song (fan-out)** cũng khôi phục được.
- Workflow **import** (chạy trong subprocess): nếu graph không có checkpointer riêng, runner gắn một saver trong bộ nhớ và gửi checkpoint đã serialize về server; khi khôi phục, subprocess mới tiếp tục từ đó. Giới hạn: không có ledger/idempotency key bên trong code của repo; state không serialize được hoặc lớn hơn 2 MB thì chạy lại từ đầu.

### Trace
- Khi khôi phục, root span của đoạn bị mất được xuất với **đúng span id cũ** (các node span đã xuất có cha), trạng thái lỗi "worker lost"; đoạn khôi phục là con và có link tới nó.

### Thông báo
- Chuông nhận thông báo **trực tiếp** qua WebSocket `/ws/notifications` (Redis pub/sub giữa các tiến trình, hoặc trong bộ nhớ). Mất kết nối thì quay về poll 30 giây.
- E-mail có cả bản text và **HTML**.
- **Cài đặt thông báo** (trong menu chuông): bật/tắt chuông trong ứng dụng và e-mail cho riêng bạn. API: `GET/PUT /api/notifications/preferences`.

Chi tiết và các giới hạn còn lại: DEC-0018.

## Phê duyệt qua Slack / Telegram (TASK-0022)

Node **Human** có thể gửi yêu cầu phê duyệt (nút **Approve / Reject**) sang Slack hoặc Telegram. Người bấm nút được ánh xạ sang
user của studio qua **tài khoản chat đã xác minh**; chỉ **chủ run** hoặc **người duyệt được liệt kê** trên node mới phê duyệt được.
Token trong nút được ký (HMAC), dùng **một lần** và **hết hạn** (`STUDIO_APPROVAL_TTL`, mặc định 86400 s). Sau khi quyết định, tin nhắn
gốc được sửa (bỏ nút, ghi ai duyệt lúc nào). Tin nhắn và nút theo **ngôn ngữ** (en/vi) của chủ run; câu trả lời riêng cho người bấm
theo ngôn ngữ của họ (ngôn ngữ chọn trong studio được lưu vào tuỳ chọn tài khoản). Mọi yêu cầu / quyết định / lần bấm bị từ chối nằm
trong **Cài đặt → Nhật ký** (`/settings/audit`, lọc theo nội dung, quyết định, nền tảng). Không cấu hình kênh thì không có gì thay đổi (no-op). Thiết kế: DEC-0019.

**Yêu cầu chung: URL công khai.** Slack và Telegram gọi về studio qua HTTPS công khai. Đặt `STUDIO_PUBLIC_URL=https://studio.example.com`
(cũng dùng cho link trong tin nhắn). Ở máy dev có thể dùng tunnel (`cloudflared tunnel --url http://localhost:8090` hoặc `ngrok http 8090`).
Endpoint callback:
- Slack: **URL chung** `POST {STUDIO_PUBLIC_URL}/api/approvals/callback/slack`, định tuyến theo `team_id` của workspace, nên một người
  có thể kết nối **nhiều workspace** (mỗi workspace một kết nối; lưu lại cùng workspace = thay thế). URL riêng
  `/api/approvals/callback/slack/{channel_id}` vẫn dùng được.
- Telegram: `POST {STUDIO_PUBLIC_URL}/api/approvals/callback/telegram/{channel_id}` (nút **Đăng ký webhook** tự đặt).

**Kết nối cá nhân và toàn tổ chức.** Mỗi user có thể tạo kết nối riêng (*Cá nhân*), chỉ dùng trên workflow của mình. **Admin**
(vai trò `admin`, quản lý ở Cài đặt → **Người dùng**; xem mục RBAC) tạo thêm kết nối *Toàn tổ chức* mà mọi user đều chọn được trên node Human; chỉ admin sửa / xoá được kết nối này.

**Xác minh tài khoản chat.** Trong **Kênh phê duyệt → Tài khoản của tôi**, nhập Slack member ID / Telegram user ID → **Liên kết & gửi mã**:
bot nhắn riêng (DM) một mã 6 số; nhập mã → **Xác minh**. Chưa xác minh thì nút bấm trong chat bị từ chối (`APPROVAL_IDENTITY_UNKNOWN`).
Mã hết hạn sau `STUDIO_IDENTITY_CODE_TTL` (600 s), tối đa `STUDIO_IDENTITY_CODE_ATTEMPTS` (5) lần nhập sai, gửi lại cách nhau ít nhất
`STUDIO_IDENTITY_CODE_RESEND` (30 s). Mã được gửi qua kết nối cá nhân của bạn, nếu không có thì qua kết nối toàn tổ chức (Telegram: bấm
**Start** trong chat với bot trước). Liên kết tạo trước bản này phải xác minh lại.

**Giới hạn tần suất callback.** Endpoint công khai bị giới hạn theo IP (`STUDIO_CALLBACK_RATE_LIMIT_IP`, 60) và theo kết nối / workspace
(`STUDIO_CALLBACK_RATE_LIMIT_CHANNEL`, 300) trong cửa sổ `STUDIO_CALLBACK_RATE_WINDOW` (60 s); vượt quá → `429 RATE_LIMITED`. Sau reverse
proxy, đặt `STUDIO_TRUSTED_PROXIES` (danh sách CIDR của proxy): `X-Forwarded-For` được đọc từ phải sang trái, bỏ qua các hop tin cậy,
và chỉ khi peer trực tiếp là proxy tin cậy (Compose mặc định là các dải private vì nginx của `web` đứng trước `api`; nginx này là edge nên
ghi đè `X-Forwarded-For` bằng IP nó thấy. Có load balancer phía trước: đổi sang `$proxy_add_x_forwarded_for` và thu hẹp danh sách CIDR). `STUDIO_TRUST_PROXY=1`
(cũ) vẫn dùng được, tương đương tin đúng một hop.

**Tài khoản theo workspace.** Liên kết Slack được lưu theo (workspace, member ID): cùng một member ID ở workspace khác cần xác minh riêng.
Mỗi tài khoản chat chỉ có một người dùng đã xác minh (ràng buộc unique trong DB, kể cả khi hai người xác minh cùng lúc → `IDENTITY_TAKEN`).

### Tạo Slack app
1. https://api.slack.com/apps → **Create New App** → *From scratch*, chọn workspace.
2. **OAuth & Permissions** → Bot Token Scopes: `chat:write`, `im:write` (DM mã xác minh); thêm `chat:write.public` nếu muốn gửi vào kênh public mà bot chưa được mời → **Install to Workspace** → copy **Bot User OAuth Token** (`xoxb-…`).
3. **Basic Information** → copy **Signing Secret**.
4. Studio: menu người dùng → **Cài đặt** → **Kênh** (`/settings/channels`) → thẻ **Slack** → tab *Cá nhân* hoặc *Toàn tổ chức* → dán bot token + signing secret → **Lưu** (nút **Kiểm tra kết nối** gọi lại `auth.test` / `getMe`). Studio gọi `auth.test` để lấy tên và `team_id` của workspace. Copy **Request URL (mọi workspace)**.
5. Slack app → **Interactivity & Shortcuts** → bật, **Request URL** = URL vừa copy → Save. Workspace khác: lặp lại 1–5 (cùng Request URL).
6. Mời bot vào kênh (`/invite @tên-bot`) và lấy **Channel ID** (chi tiết kênh → cuối trang, dạng `C0123ABCD`).
7. Mỗi người duyệt: **Cài đặt → Tài khoản của tôi** (hoặc ngay trong thẻ Slack) → Slack member ID (hồ sơ → ⋮ → *Copy member ID*) → nhận mã qua DM → xác minh.

Callback được xác thực bằng `X-Slack-Signature` (HMAC-SHA256 của `v0:{timestamp}:{body}` với signing secret), timestamp lệch tối đa 5 phút.

### Tạo Telegram bot
1. Chat với **@BotFather** → `/newbot` → copy token (`123456:AA…`).
2. Studio → **Cài đặt → Kênh** → thẻ **Telegram** → tab *Cá nhân* / *Toàn tổ chức* → dán token (webhook secret để trống thì studio tự sinh) → **Lưu** → **Đăng ký webhook**
   (gọi `setWebhook` với URL callback + `secret_token`; cần `STUDIO_PUBLIC_URL` dạng https).
3. Thêm bot vào group (hoặc nhắn riêng cho bot) và lấy **chat ID** (group thường dạng `-100…`; ví dụ gửi một tin vào group rồi mở
   `https://api.telegram.org/bot<token>/getUpdates` *trước khi* đăng ký webhook, hoặc dùng @RawDataBot).
4. Mỗi người duyệt: bấm **Start** trong chat với bot, rồi **Tài khoản của tôi** → Telegram user ID (nhắn @userinfobot) → nhận mã → xác minh.

Webhook được xác thực bằng header `X-Telegram-Bot-Api-Secret-Token`.

### Cấu hình trên node Human
Chọn node → **Kênh phê duyệt**: *Chỉ trong Studio* (mặc định) hoặc một **kết nối** (cá nhân hoặc toàn tổ chức), **Channel ID / chat ID**,
**Người duyệt** (e-mail của user studio, phân tách bằng dấu phẩy). Trả lời ngay trong studio vẫn được; khi đó nút trong chat bị vô hiệu
và tin nhắn ghi "Answered in LangGraph Studio" / "Đã trả lời trong LangGraph Studio". Run bị huỷ / hết hạn cũng đóng yêu cầu. Run khởi
chạy qua API có `callback_url` mà được tiếp tục (từ studio, Slack, Telegram hoặc sau khi khôi phục) sẽ gửi webhook `callback_url` đúng một
lần cho mỗi lần dừng/kết thúc, qua pipeline giao nhận (ký, retry, mục Deliveries).

Biến môi trường: `STUDIO_PUBLIC_URL`, `STUDIO_APPROVAL_TTL`, `STUDIO_ADMIN_EMAILS`, `STUDIO_TRUSTED_PROXIES` (`STUDIO_TRUST_PROXY`), `STUDIO_CALLBACK_RATE_LIMIT_IP`,
`STUDIO_CALLBACK_RATE_LIMIT_CHANNEL`, `STUDIO_CALLBACK_RATE_WINDOW`, `STUDIO_IDENTITY_CODE_TTL` / `_ATTEMPTS` / `_RESEND`,
`SLACK_API_URL` / `TELEGRAM_API_URL` (chỉ để test với API giả, xem `backend/tests/fixtures/mock_chat_api.py`).
