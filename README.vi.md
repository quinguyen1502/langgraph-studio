# LangGraph Studio

[English](README.md) · **Tiếng Việt**

Công cụ nội bộ để thiết kế workflow LangGraph trên trình duyệt. Vẽ graph, cấu hình node, lưu JSON, rồi chạy và xem sự kiện từng node. Backend FastAPI biên dịch JSON đó thành `StateGraph` của LangGraph. Có thể import một repo LangGraph viết bằng Python và chạy graph gốc trong sandbox Docker.

Dùng nội bộ và để học. Không thay LangGraph Platform.

## Chạy nhanh

```bash
./dev.sh
```

Lần đầu script tạo `backend/.venv`, cài backend, và chạy `npm install` trong `frontend/`.

- UI: http://localhost:5173 (Vite chuyển `/api` và `/ws` sang backend)
- API: http://localhost:8000/docs
- Tài khoản demo, tự seed khi khởi động (trừ production): `admin@example.com` / `admin123`

Muốn model thật, mở **Credentials** trên trang danh sách workflow và thêm provider. Node không chọn credential và không có `OPENAI_API_KEY` thì dùng mock offline, kết quả xác định. Lỗi provider (401, timeout, …) thành event `error` của node, không làm sập server.

`export OPENAI_API_KEY=sk-...` (tuỳ chọn `OPENAI_BASE_URL`) là lối dự phòng khi node LLM không chọn credential.

## Tài khoản

Mật khẩu hash bằng PBKDF2-SHA256 (200 nghìn vòng, salt riêng). Đăng nhập trả JWT HS256, hạn 24 giờ (`JWT_TTL_SECONDS`, mặc định 86400). Đặt `JWT_SECRET` khi chạy chung hoặc production. Giá trị còn là placeholder thì backend ghi cảnh báo. `STUDIO_ENV=production` thì từ chối khởi động. `STUDIO_CORS_ORIGINS` (phân tách bằng dấu phẩy) liệt kê các origin trình duyệt được gọi API. Khi chưa đặt, môi trường dev cho phép `*`, production không cho origin nào, vì UI chạy cùng origin. Trình duyệt giữ phiên trong cookie HttpOnly (`studio_session`, `SameSite=Lax`; `Secure` khi production, hoặc đặt `STUDIO_COOKIE_SECURE`), nên script trên trang không đọc được. Các thao tác ghi dựa vào cookie phải gửi `X-Requested-With: studio`, và `lib/api.ts` đã gửi sẵn. Socket từ UI dùng cùng cookie và phải đến từ đúng host của server. API client vẫn có thể truyền `?token=`; log của uvicorn ghi thành `token=***`.

Đăng ký: mật khẩu 8–128 ký tự, có ít nhất một chữ và một số. Mật khẩu demo `admin123` không bị quy tắc này. Email được cắt khoảng trắng và đưa về chữ thường. Đăng nhập sai luôn báo email hoặc mật khẩu không đúng.

Đăng nhập và đăng ký vẫn trả `token` và `expires_at` trong body. API client gửi `Authorization: Bearer <token>` (không cần header CSRF) và mở socket bằng `ws://…/ws/run?token=<token>`. `POST /api/auth/logout` xoá cookie. Token hết hạn hoặc không hợp lệ thì UI tự đăng xuất và về `/login?expired=1&next=…`. Tài khoản mới được tặng một bản workflow ví dụ. Workflow thuộc về người tạo.

Sai mật khẩu 5 lần trong 15 phút thì e-mail đó bị khoá 15 phút, kể cả khi nhập đúng mật khẩu (`AUTH_LOCKED`; `STUDIO_LOGIN_MAX_FAILURES`, `STUDIO_LOGIN_WINDOW`, `STUDIO_LOGIN_LOCK`). E-mail không tồn tại cũng bị đếm như vậy, nên việc bị khoá không cho biết tài khoản có tồn tại hay không.

Để đặt lại mật khẩu, admin mở **Settings → Users**, tạo link một lần (biểu tượng chìa khoá) rồi gửi cho người dùng. Khi đã đặt `SMTP_HOST` và `STUDIO_PUBLIC_URL`, nút **Quên mật khẩu?** ở trang đăng nhập sẽ gửi link qua e-mail; nút này trả lời giống nhau với mọi địa chỉ. Link dùng được một lần, trong `STUDIO_PASSWORD_RESET_TTL` giây (mặc định 3600). Đặt mật khẩu mới sẽ đăng xuất mọi phiên cũ của tài khoản và gỡ khoá.

Khi production (`STUDIO_ENV=production`), tài khoản demo không được tạo. Nếu tài khoản này đã có sẵn và còn dùng mật khẩu demo, nó bị vô hiệu hoá lúc khởi động; dùng `STUDIO_ADMIN_EMAILS` để có admin đầu tiên.

## Trình soạn thảo

| Vùng | Việc |
| --- | --- |
| Thanh trên | Tên, Lưu, Chạy / Dừng, hoàn tác và làm lại. Phần còn lại nằm trong menu **⋯**. |
| Trái | Palette node và trình sửa state schema. |
| Giữa | Canvas React Flow. Kéo từ handle phải sang handle trái. Delete xoá phần đang chọn. Start và End không xoá được. |
| Phải | Cấu hình phần đang chọn, và lịch sử chạy. |
| Dưới | Input JSON và log trực tiếp. |

Kéo viền của panel trái, phải hoặc dưới để đổi kích thước. Tối thiểu là 180px, 260px và 140px, canvas giữ ít nhất 280×160px. Kích thước lưu trong trình duyệt này (`localStorage.lgs.editorPanels`), không lưu trên workflow. Xoá dữ liệu trang sẽ trả về 250px, 320px và 300px.

`?` hoặc `Ctrl/⌘+/` mở bảng phím tắt (`frontend/src/lib/shortcuts.ts`). `Ctrl/⌘+S` lưu, `Ctrl/⌘+Enter` chạy, `Ctrl/⌘+.` dừng, `Ctrl/⌘+A` chọn tất cả, `Shift+1` vừa khung nhìn, `Ctrl/⌘` với `+`/`-` phóng to hoặc thu nhỏ. Khi đang gõ, chỉ lưu, chạy và dừng còn tác dụng. Hộp thoại đang mở thì phím tắt editor tắt.

`Ctrl/⌘+Z` hoàn tác, `Ctrl/⌘+Shift+Z` hoặc `Ctrl/⌘+Y` làm lại, tối đa 100 bước. Một lần kéo là một bước. Gõ liên tục trong cùng một node gộp thành một bước. Ô nhập giữ hoàn tác của trình duyệt. Huy hiệu chưa lưu mất khi hoàn tác về đúng bản đã lưu.

`Ctrl/⌘+K` mở bảng lệnh trên mọi trang, kể cả khi đang gõ. Tìm gần đúng thao tác editor, **Thêm node**, **Đến node**, **Mở workflow**, **Workflow mới**, và các trang Cài đặt. Từ khoá tiếng Anh như `retriever` và `mcp` cũng khớp.

`Ctrl/⌘+C`, `Ctrl/⌘+X`, `Ctrl/⌘+V`, `Ctrl/⌘+D` sao chép, cắt, dán, nhân bản. Start và End không bao giờ được sao chép. Chỉ cạnh nối giữa các node đang chọn đi cùng. Node dán ra có id mới. Bộ nhớ là `localStorage` (`langgraph-studio/nodes` v1), nên dán sang workflow khác trong cùng trình duyệt được. Credential bạn không có quyền dùng sẽ bị bỏ trống khi dán.

**Sắp xếp** hoặc `Shift+L` xếp graph bằng dagre theo kích thước thật của node. Mũi tên bên cạnh chọn trái sang phải hoặc trên xuống dưới. Góc trên-trái của graph giữ nguyên. Một lần sắp xếp là một bước hoàn tác. Chuột phải trên canvas và chọn **Thêm ghi chú** để đặt một mảnh giấy. Nó được lưu cùng workflow, Sắp xếp không đổi vị trí của nó, và lần chạy không thực thi nó.

**Workflow mới** mở thư viện mẫu: graph trống, bốn mẫu sẵn (Chatbot, RAG Q&A, Approval flow, Router), và mẫu của bạn hoặc của tổ chức. Mỗi mẫu có ảnh xem trước. **Lưu thành mẫu** chép bản đã lưu. Phạm vi toàn tổ chức cần `org.manage`. Xuất và nhập dùng `*.template.json` (`{"format": "langgraph-studio/template", "version": 1, ...}`). Mẫu không chứa credential, kho tri thức, máy chủ MCP, kênh phê duyệt, liên kết subgraph, header, hay API key. Các trường đó được làm trống. Xoá mẫu phải gõ đúng tên.

Nút mặt trăng / mặt trời trên mọi màn hình lưu theme trong `localStorage`. `?theme=dark` ép dark mode. Màu lấy từ theme Tailwind v4 và shadcn, không dùng mã màu cố định.

UI có tiếng Anh và tiếng Việt (`frontend/src/locales/en.json` và `vi.json`). Mặc định theo trình duyệt. Nút ngôn ngữ ở màn hình đăng nhập và thanh trên lưu lựa chọn trong `localStorage.lang`. Lỗi API dịch theo `error.code`. Mã chưa có bản dịch thì hiện message tiếng Anh của server.

## Node

```json
{"name": "...", "state": [{"name": "message", "type": "string"}],
 "nodes": [{"id": "n1", "type": "llm", "position": {"x": 0, "y": 0},
            "data": {"label": "..", "model": "gpt-4o-mini", "prompt": "Hi {{state.message}}", "output_field": "answer"}}],
 "edges": [{"id": "e1", "source": "a", "target": "b"}]}
```

- **LLM.** `model`, `prompt` với `{{state.field}}`, `output_field`. Khi đang chạy, từng đoạn chữ tới qua event `node_token` và hiện ở dòng Logs cùng tab Output. Các đoạn này không lưu vào lịch sử run. Văn bản cuối không đổi.
- **Tool.** `mode=function` cộng tên đăng ký bằng `@register_tool` trong `backend/app/engine/tools.py` (ví dụ `lookup_order`), hoặc `mode=http` với `method`, `url`, và `body` có template. URL của HTTP Tool phải trỏ tới địa chỉ công khai: loopback, mạng riêng, link-local và địa chỉ metadata bị chặn với `HTTP_TOOL_URL_BLOCKED`, trừ khi `STUDIO_HTTP_TOOL_ALLOW_PRIVATE=1`. Request đi tới đúng IP đã kiểm tra, không theo redirect, và hết hạn sau `STUDIO_HTTP_TOOL_TIMEOUT` giây (mặc định 30).
- **Condition.** `field`. Nhãn cạnh đi ra khớp đúng chuỗi, rồi không phân biệt hoa thường sau khi bỏ khoảng trắng và dấu câu, rồi theo nguyên từ trong giá trị, nhãn dài nhất thắng. Thứ tự nhãn không ảnh hưởng: `Disapprove.` chọn `disapprove`, không chọn `approve`. Hai nhãn nguyên từ dài bằng nhau là mơ hồ. Cạnh `default` là lối còn lại khi không khớp hoặc mơ hồ.
- **Nhánh song song.** Nhiều cạnh ra từ một node không phải Condition chạy cùng superstep. Trường state bị nhiều nhánh ghi cần reducer: `append` (list), `merge` (object), hoặc `add` (số). Mặc định là `replace`. Thiếu reducer thì validate lỗi.
- **Join.** Chờ mọi nhánh đi vào rồi chạy một lần. Cần ít nhất hai cạnh vào, và không nhận cạnh thẳng từ Condition.
- **For each.** `items_field` (trường kiểu list), `item_field`, `index_field` tùy chọn (integer hoặc number), `max_items` (1–1000, mặc định 100). Node cần hai cạnh ra có nhãn `each` và `done`; editor tự gắn nhãn `each` cho cạnh đầu tiên bạn nối và `done` cho cạnh thứ hai. Nhánh `each` là phần thân vòng lặp và phải quay về node For each. Mỗi lần đi qua, node ghi phần tử tiếp theo (và số thứ tự từ 0) rồi đi theo `each`; sau phần tử cuối thì đi theo `done`. Các phần tử chạy lần lượt, nên Human, khôi phục run và idempotency key đều hoạt động theo từng phần tử. Gom kết quả bằng một trường list có reducer `append`. Vòng lặp lồng nhau được hỗ trợ; danh sách bên trong chạy lại từ đầu cho mỗi phần tử bên ngoài. Danh sách dài hơn `max_items` làm node báo lỗi. Run được cộng thêm bước LangGraph cho mỗi vòng lặp, nên `STUDIO_RECURSION_LIMIT` (mặc định 25) chỉ giới hạn các vòng lặp khác.
- **Subgraph.** `workflow_id` của một workflow đã lưu của bạn. Node bên trong hiện trên trace dạng `Subgraph › node` (id `sub/node`). State dùng chung theo tên trường. Vòng tham chiếu, workflow con không tồn tại hoặc là bản import, và lồng quá năm cấp đều lỗi khi lưu và khi chạy (`WORKFLOW_INVALID`).
- **MCP tool.** `server_id`, `tool`, `arguments` (chuỗi là template; đúng `{{state.x}}` thì giữ kiểu), `output_field`.
- **Retriever.** `knowledge_base_id`, `query`, `top_k` (1–20), `output_field`. Kết quả là danh sách `{text, score, filename, …}`.
- **Decision (Jev).** Hỏi Jev của [TypeSafe](https://typesafe.ai) các câu hỏi có kiểu về `text` (một template; nếu chỉ có đúng một `{{state.x}}` thì giá trị được gửi nguyên kiểu). Mỗi câu hỏi có `id`, `instructions` và một loại. `choice` nhận 2–255 `options` và trả về một nhãn. `score` nhận 2–10 `levels` từ thấp đến cao và trả về một số từ 0 đến chỉ số của mức cuối; số này có thể nằm giữa hai mức. `noul` trả về một số từ 0 (sai) đến 1 (đúng). `field` của câu hỏi nhận câu trả lời đó, nên Condition có thể rẽ nhánh theo lựa chọn. `output_field` (kiểu object) nhận mọi câu trả lời kèm xác suất và độ tin cậy. Node dùng credential TypeSafe, nếu không có thì dùng `TYPESAFE_API_KEY`, nếu vẫn không có thì trả câu trả lời mẫu offline: câu hỏi lựa chọn chọn phương án đầu tiên có tên xuất hiện trong văn bản. Chi phí tính $0.042 cho mỗi triệu token input; token output miễn phí. Node có cài đặt retry, timeout và cache, và run được khôi phục sẽ dùng lại câu trả lời cũ.
- **Human.** `prompt` và `output_field`. Run dừng chờ. Xem [Phê duyệt](#phê-duyệt).
- **Code.** Node chỉ đọc do import repo tạo ra. Panel phải hiện source gốc. Sửa trên canvas không đổi file đã import.

### Template

Prompt, câu hỏi Human, URL và body của HTTP Tool, query Retriever và tham số MCP là template. Một tham chiếu là `{{state.field}}`, có thể kèm đường dẫn và filter:

- `{{state.order.items.0.sku}}` đi vào object theo khoá và vào list theo chỉ số. Thiếu bước nào thì giá trị rỗng.
- `{{state.name | trim | upper}}` chạy filter từ trái sang phải: `upper`, `lower`, `trim`, `json`, `length`, `first`, `last`, `default("text")`, `join(", ")`, `truncate(80)`.
- Tham số MCP chỉ gồm đúng một tham chiếu thì giữ kiểu giá trị, nên `{{state.items | length}}` truyền một số.

Editor hiện tham chiếu thành tag. Gõ `{{` để chọn trường state, gõ `|` trong tham chiếu để chọn filter. Double-click vào tag để sửa dạng text. Trường không có trong state hoặc filter lạ có màu đỏ và Save sẽ liệt kê. Khi chạy, tham chiếu sai bị từ chối với `TEMPLATE_REF_INVALID`.

Ví dụ **Customer Support** được seed sẵn: Start → Classify intent → Route theo `intent` → `order_status` (tra cứu rồi trả lời) hoặc `general` (trả lời) → End. Thử `{"message": "Đơn A100 đâu rồi?"}` và `{"message": "Giờ mở cửa?"}`.

## Nhà cung cấp LLM trên máy

**Credentials** trên thanh trên dùng để sửa provider. Mỗi provider là một lớp nhỏ trong `backend/app/engine/providers.py`.

| Provider | Base URL mặc định | API key | Danh sách model |
| --- | --- | --- | --- |
| Ollama | `http://localhost:11434` | không cần | `/api/tags` |
| LM Studio | `http://localhost:1234/v1` | không cần | `/v1/models` |
| OpenAI-compatible (vLLM, llama.cpp, LocalAI) | `http://localhost:8000/v1` | tuỳ server | `/v1/models` |
| OpenRouter | `https://openrouter.ai/api/v1` | bắt buộc, thêm header tuỳ chọn `HTTP-Referer` và `X-Title` | `/api/v1/models` |
| OpenAI, Anthropic | như trước | bắt buộc | `/models`, `/v1/models` |
| TypeSafe (Jev), chỉ cho node Decision | `https://api.typesafe.ai` | bắt buộc | không có danh sách: **Test connection** gửi một câu hỏi nhỏ |

**Test connection** lấy danh sách model, trước hoặc sau khi lưu. Lỗi dùng `PROVIDER_UNREACHABLE`, `PROVIDER_AUTH_FAILED` (HTTP 400, để UI không coi đó là phiên hết hạn), `PROVIDER_BAD_RESPONSE`, và `MODEL_NOT_FOUND`. Xem `docs/api-errors.md`.

Key được mã hoá bằng Fernet (`STUDIO_SECRET_KEY`, hoặc file sinh sẵn `~/.langgraph-studio/secret.key` / `STUDIO_SECRET_KEY_FILE`, quyền 0600). API chỉ trả bốn ký tự cuối. Mất khoá thì credential cũ không giải được. Form sửa giữ key cũ khi ô key để trống. Provider không đổi được sau khi tạo.

Chat đi qua LangChain (`ChatOllama`, hoặc `ChatOpenAI` với `base_url`) nên streaming và tool calling chạy được khi model hỗ trợ. Chat OpenAI và Anthropic vẫn đi HTTP thường.

Trong Compose, `localhost` là chính container. `api` và `worker` có `extra_hosts: host.docker.internal:host-gateway`. Ollama đặt `http://host.docker.internal:11434`, LM Studio đặt `http://host.docker.internal:1234/v1`. Trên Linux, chạy `OLLAMA_HOST=0.0.0.0 ollama serve` và bật *Serve on Local Network* của LM Studio. Tường lửa có thể cần cầu Docker (`sudo iptables -I INPUT -i br-+ -j ACCEPT` hoặc `-i docker0`).

Embedding của kho tri thức dùng cùng credential. Model local mặc định của Ollama là `nomic-embed-text` (`ollama pull nomic-embed-text`). **Kiểm tra embedding** báo số chiều. Mỗi kho lưu `dims`. Vector khác số chiều trả `KB_EMBEDDING_DIMENSION_MISMATCH`. Lập chỉ mục lại để nhận số chiều mới. Anthropic không có embedding.

## Import repo LangGraph

Import là tính năng thử nghiệm và **tắt** cho đến khi `STUDIO_ENABLE_IMPORT=1`. Khi tắt, `POST` và `GET` `/api/import*` trả 404 `IMPORT_DISABLED` và nút **Import repo** ẩn. `GET /api/health` có `import_enabled`.

Trên `/workflows`, **Import repo** nhận URL GitHub public (tuỳ chọn nhánh và thư mục con) hoặc file zip. Hộp thoại hiện fetching, installing, inspecting, rồi ready. Chọn một graph và tạo workflow.

Backend làm các bước sau (`backend/app/engine/repo_import.py`, `backend/app/engine/sandbox/container.py`, `backend/app/engine/sandbox/runner.py`):

1. `git clone --depth 1`, hoặc giải nén zip có chặn zip-slip, vào `~/.langgraph-studio/imports/<job_id>/` (`STUDIO_IMPORT_DIR`). Clone và giải nén chạy trên process API. Image API có `git`. `python:3.12-slim` thì không.
2. Khi flag bật, `python -m venv` và `pip` chạy **trong Docker** (`STUDIO_IMPORT_IMAGE`, mặc định `python:3.12-slim`). Gói lấy từ `pyproject.toml` / `setup.py` (`pip install -e .`) hoặc `requirements.txt`, luôn kèm `langgraph` và `python-dotenv`.
3. Graph lấy từ `langgraph.json`, hoặc quét file có `StateGraph` và `x = ….compile(…)`. Bước quét chỉ đọc file.
4. `runner.py inspect` gọi `graph.get_graph(xray=True)` (120 giây, `STUDIO_INSPECT_TIMEOUT`). Inspect trong Docker dùng `--network none`.
5. `__start__` / `__end__` thành Start / End. Node còn lại thành node Code chỉ đọc. Frontend xếp bằng dagre.

Một lần chạy thực thi **graph gốc** qua `runner.py run` (`graph.astream`). Sự kiện thành `node_started` / `node_finished`. Context runtime để trong input, khoá `__context__`. Thiếu biến khai báo trong `.env.example` thì ghi trên event lỗi. Run của import đọc `STUDIO_RUN_TIMEOUT` lúc process khởi động (mặc định 300 giây). Hết giờ hoặc OOM (exit 137) là một event `error`, ví dụ `Sandbox stopped (time limit (12s)).`.

Sandbox là `docker run` với root chỉ đọc, chỉ mount thư mục job ở chế độ ghi, bản `runner.py` chỉ đọc tại `/opt/studio-runner`, bỏ mọi capability, `no-new-privileges`, tmpfs `/tmp`, và các giới hạn: memory `STUDIO_IMPORT_MEMORY` (mặc định `1g`, swap bằng memory), CPU `STUDIO_IMPORT_CPUS` (mặc định `1`), pid `STUDIO_IMPORT_PIDS` (mặc định 256). Process không nhận môi trường của server. Tên được đưa vào là biến khai báo trong `.env.example` nếu có trên server, cộng `STUDIO_IMPORT_SECRETS`. `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`, và mọi tên `STUDIO_*` không bao giờ được đưa vào. `localhost` trong sandbox là container. Lúc cài đặt mạng là `bridge`. Lúc inspect là `none`. Lúc chạy là `STUDIO_IMPORT_NETWORK` (`bridge` hoặc `none`, mặc định `bridge`). Runtime Docker không tự rơi về subprocess.

`STUDIO_IMPORT_RUNTIME=subprocess` dành cho test và máy không có Docker. Nó chạy cùng user hệ điều hành với API. Đó không phải sandbox. Khi flag tắt và không đặt runtime, graph **đã import từ trước** cũng đi lối này, nên môi trường server chỉ bị cắt bớt chứ không bị cô lập.

Compose gắn `/var/run/docker.sock` vào `api` và `worker` cả khi import đang tắt. Socket này tương đương quyền root trên daemon. Đừng bật import trên máy không tin cậy. Trước `docker compose up`, export `STUDIO_ENABLE_IMPORT=1` và `STUDIO_IMPORT_HOST_DIR="$PWD/.imports"` (đường dẫn tuyệt đối trên host, trùng bind mount) rồi `mkdir -p` thư mục đó. Trên Linux, nếu user `studio` (uid 10001) không mở được socket: `STUDIO_DOCKER_GID="$(stat -c %g /var/run/docker.sock)"`. Thiếu `STUDIO_IMPORT_HOST_DIR` thì daemon mount nhầm đường dẫn bên trong container và sandbox thất bại. `./dev.sh` trên host không cần biến này. Nếu `docker` không có trên `PATH`, API dùng CLI của Docker Desktop tại `/Applications/Docker.app/Contents/Resources/bin/docker`. gVisor và Firecracker không được hỗ trợ.

Job ghi `job.json`. Khởi động lại thì job đang dở (`queued`, `fetching`, `installing`, `inspecting`) thành `Import interrupted by a restart` khi pid không còn. Workflow tạo từ job được đánh dấu `keep` và không bị dọn. Thư mục khác cũ hơn `STUDIO_IMPORT_MAX_AGE_HOURS` (mặc định 72, `0` là không dọn) bị xoá khi bắt đầu import kế tiếp. Cây source lớn hơn `STUDIO_IMPORT_MAX_BYTES` (mặc định 200 MB, không tính `.git`) bị từ chối. Không hỗ trợ repo private, monorepo JS, và `langgraph.json` dạng phức tạp.

Nếu graph import không có checkpointer riêng, runner gắn một saver trong bộ nhớ và gửi checkpoint đã serialize về server. Khôi phục mở container mới (runtime Docker) hoặc subprocess mới (`STUDIO_IMPORT_RUNTIME=subprocess`). Bên trong repo được import không có sổ ledger. State không serialize được, hoặc lớn hơn 2 MB, thì chạy lại từ đầu.

Đã thử trước khi có sandbox: `langchain-ai/new-langgraph-project` chạy không cần key. `langchain-ai/react-agent` import được và hiện vòng lặp, còn lúc chạy thì báo thiếu key của provider.

## Run, trace, và giới hạn

Tab Logs là một dòng cho mỗi bước node: trạng thái, tên, loại, thời lượng, thanh waterfall, và token khi model báo. Vòng lặp hiện `#2`, `#3`, …. Bấm dòng, hoặc bấm node trên canvas, để xem Input, Output, State diff, và Raw. **Raw events** là luồng gốc. History phát lại cùng timeline.

**Một bước** chạy một superstep rồi dừng cùng run đó để xem kết quả. **Chạy tiếp** chạy nốt. Chọn một node rồi bấm **Chạy tới đây** để chạy đến khi node đó xong, rồi dừng. Nếu đường đi không tới node đó, run chạy hết và báo không tới. Lần dừng này có trạng thái `paused`, không phải chờ duyệt. Superstep chỉ có Start không tính là một bước.

**Cancel** gửi `{"type":"cancel"}`. Đóng tab cũng huỷ. Huỷ là hợp tác: dừng giữa các bước, nên lời gọi LLM hoặc HTTP đã gửi có thể chạy nốt. Trạng thái lưu là `ok`, `error`, `cancelled`, `timeout`, và `paused`. Lỗi là một dòng. `sk-…`, `Bearer …`, và `api_key=…` bị che.

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `STUDIO_RECURSION_LIMIT` | 25 | Số bước tối đa mỗi run. Vòng lặp không đi qua Condition thì dừng với lỗi. |
| `STUDIO_RUN_TIMEOUT` | 120 giây | Thời gian tối đa của run thường, rồi trạng thái `timeout`. Import đọc biến này lúc process khởi động và mặc định 300 giây khi chưa đặt. |
| `STUDIO_EVENT_MAX_BYTES` | 262144 | Kích thước tối đa một event. Trường quá lớn thành `{"_truncated": true, ...}`. |
| `STUDIO_RUN_MAX_BYTES` | 2097152 | Tổng event lưu cho một run. Phần giữa bị thay bằng `{"type":"truncated","dropped":n}`. |
| `STUDIO_INPUT_MAX_BYTES` | 262144 | Input tối đa của một run. |
| `STUDIO_WORKFLOW_MAX_BYTES` | 1048576 | JSON workflow tối đa. Bản lưu lớn hơn trả HTTP 413. |

Timeline còn cắt `input` và `delta` ở 16 000 ký tự JSON để trang nhẹ. Validator từ chối cạnh trỏ node không có, id trùng, nhiều Start, cạnh tự nối (trừ Condition), vòng lặp không qua Condition, và node không tới được. `STUDIO_ENABLE_DEMO_TOOLS=1` đăng ký `sleep_demo` (1,5 giây) để thử huỷ và timeout.

Mỗi run có tóm tắt thời lượng, token vào và ra, chi phí USD, và số lỗi, ở phần tóm tắt Logs, trên span LLM, và trong History. Chế độ mock ước lượng token và chi phí `$0`. Model không có trong `backend/app/engine/usage.py` hiện chi phí `—`. Ghi đè giá bằng `STUDIO_PRICES='{"my-model": [1.0, 2.0]}'` hoặc `STUDIO_PRICES_FILE` (USD / 1 triệu token). Tiền tố khớp dài nhất được chọn.

OpenTelemetry xuất một trace cho mỗi run và một span cho mỗi node (`gen_ai.usage.*` và chi phí). Không cấu hình exporter thì tracing là no-op. Span gửi đi khi từng node xong. Run đang chờ người duyệt chỉ có trace khi đã kết thúc.

| Đích | Biến |
| --- | --- |
| OTLP (Jaeger, Tempo, collector) | `OTEL_EXPORTER_OTLP_ENDPOINT` và các biến `OTEL_*` chuẩn |
| LangSmith | `LANGSMITH_API_KEY` và `LANGSMITH_TRACING=true`, thêm `LANGSMITH_PROJECT` và `LANGSMITH_ENDPOINT` nếu cần |
| "Mở trace" trên UI | `STUDIO_TRACE_URL`, ví dụ `http://localhost:16686/trace/{trace_id}` |

Khi exporter LangSmith của Studio bật, tracer LangSmith riêng của LangChain bị tắt, nên mỗi lời gọi LLM chỉ xuất một lần. `STUDIO_OTEL_METRICS=1` cùng endpoint OTLP còn xuất `studio.runs`, `studio.run.duration`, `studio.tokens`, `studio.cost`, và `studio.errors`.

```bash
# trong .env, rồi:
docker compose --profile tracing up --build   # Jaeger UI: http://localhost:16686
```

Đặt `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318` và `STUDIO_TRACE_URL=http://localhost:16686/trace/{trace_id}`. Không dùng Compose: `docker run -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one` và trỏ backend tới `http://localhost:4318`.

Side effect là effectively-once. Mỗi lần chạy LLM hoặc Tool có idempotency key cố định theo run, node, và lần lặp. Tool HTTP gửi `Idempotency-Key`, `X-Studio-Run-Id`, và `X-Studio-Attempt`. Tool Python nhận `idempotency_key` nếu khai báo tham số đó. Job được khôi phục dùng lại cùng key. Node side effect đã xong được lấy từ sổ ledger (`reused` trên trace) thay vì chạy lại. Ledger xoá khi run kết thúc. Mỗi lần worker nhận một run, `runs.lease_gen` tăng. Mọi lần ghi phải mang đúng fencing token. Worker mất lease không ghi được và tự dừng.

## Phê duyệt

Node **Human** dừng run ở trạng thái `waiting`. Tab Logs có **Duyệt** (`approved`), **Từ chối** (`rejected`), hoặc chữ tự do, ghi vào `output_field`. Condition có thể rẽ theo giá trị đó. Trang danh sách workflow hiện các run đang chờ bạn. Checkpoint nằm trong database, nên khởi động lại vẫn tiếp tục được. Chỉ chủ run được duyệt hoặc huỷ. Thời gian chờ không tính vào thời lượng run. Chờ lâu hơn `STUDIO_WAIT_TTL` giây (mặc định 7 ngày, `0` là không bao giờ) thì thành `expired` (resume trả `410 RUN_EXPIRED`).

```text
GET  /api/runs/pending
WS   /ws/run   {"resume_run_id": "...", "response": "approved"}
POST /api/runs/{id}/cancel
```

Huy hiệu trên thanh tiêu đề đếm run đang chờ bạn. Chuông liệt kê thông báo chưa đọc (`GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`) và nhận trực tiếp qua `/ws/notifications`. Mất kết nối thì poll 30 giây. Tuỳ chọn là theo từng người. Đặt `SMTP_HOST` (cùng `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS` hoặc `SMTP_SSL`) để gửi thư. Link dùng `STUDIO_PUBLIC_URL`. Để trống `SMTP_HOST` thì không gửi thư. `STUDIO_NOTIFY_WEBHOOK_URL` gửi JSON cho mỗi run `waiting` hoặc `expired`, ký bằng `STUDIO_NOTIFY_WEBHOOK_SECRET` khi biến đó được đặt.

Slack, Telegram và WhatsApp có thể mang cùng nút Duyệt / Từ chối; e-mail và Teams mang link tới studio (xem bên dưới). Lần bấm được ánh xạ qua **tài khoản chat đã xác minh**. Chỉ chủ run, hoặc email liệt kê trên node, được duyệt. Token trên nút được ký HMAC, dùng một lần, và hết hạn (`STUDIO_APPROVAL_TTL`, mặc định 86400 giây). Tin nhắn theo ngôn ngữ của chủ run. Không cấu hình kênh thì không gửi gì.

Slack và Telegram cần `STUDIO_PUBLIC_URL` là HTTPS công khai. Máy dev dùng `cloudflared tunnel --url http://localhost:8000` hoặc `ngrok http 8000`.

- Callback Slack: `POST {STUDIO_PUBLIC_URL}/api/approvals/callback/slack` (định tuyến theo `team_id`, nên một người nối được nhiều workspace). URL theo từng kênh vẫn dùng được.
- Callback Telegram: `POST {STUDIO_PUBLIC_URL}/api/approvals/callback/telegram/{channel_id}`. **Đăng ký webhook** gọi `setWebhook`.

**Slack app.** Tạo app tại https://api.slack.com/apps. Scope của bot: `chat:write`, `im:write`, và `chat:write.public` nếu bot cần gửi vào kênh public mà chưa được mời. Cài app, chép bot token (`xoxb-…`) và signing secret. Trong Studio, **Cài đặt → Kênh** (`/settings/channels`), dán cả hai rồi lưu. Chép request URL vào **Interactivity & Shortcuts**. Mời bot và dùng channel id (`C…`). Mỗi người duyệt chép Slack member id, nhận mã 6 số qua DM, rồi xác minh ở **Tài khoản của tôi**.

**Telegram bot.** `/newbot` với @BotFather, dán token, lưu, rồi **Đăng ký webhook** (`STUDIO_PUBLIC_URL` phải là https). Thêm bot vào cuộc trò chuyện và dùng chat id đó. Mỗi người duyệt bấm **Start**, rồi xác minh Telegram user id theo cách tương tự. Webhook được kiểm bằng `X-Telegram-Bot-Api-Secret-Token`.

**WhatsApp (Cloud API).** Trong một Meta app có sản phẩm WhatsApp, dán access token, phone number ID, app secret và một verify token tự chọn. Trong Meta dashboard, đặt webhook là `{STUDIO_PUBLIC_URL}/api/approvals/callback/whatsapp/{channel_id}` với verify token đó (Meta kiểm tra bằng một request GET), rồi đăng ký `messages`. Callback được kiểm tra bằng `X-Hub-Signature-256`. Yêu cầu là một tin nhắn có hai nút trả lời, gửi tới số target của node (dạng quốc tế, chỉ gồm chữ số). WhatsApp chỉ gửi tin có nút và tin văn bản trong 24 giờ kể từ tin nhắn gần nhất của người đó tới số này. Ngoài khung đó, điền **Tên template** (và ngôn ngữ) của một template đã được duyệt, có biến `{{1}}` ở phần body và hai nút trả lời nhanh (Duyệt, Từ chối). Người duyệt xác minh số của mình bằng mã như với Telegram; mã chỉ tới được trong khung 24 giờ. WhatsApp không sửa được tin đã gửi, nên kết quả là một tin trả lời vào yêu cầu.

**E-mail và Microsoft Teams** là kênh dạng link và cần `STUDIO_PUBLIC_URL`. Tin nhắn có link Duyệt và Từ chối tới `/approve?token=…`. Người nhận đăng nhập studio và xác nhận ở đó, nên không cần liên kết tài khoản chat, và việc mở link (ví dụ bởi trình quét mail) không quyết định gì. Các quy tắc vẫn như cũ: chủ run hoặc người duyệt có trong danh sách, chỉ một câu trả lời, và có hạn.
- E-mail dùng cấu hình SMTP của studio (`SMTP_HOST`, …). Target của node là một hoặc nhiều địa chỉ, cách nhau bằng dấu phẩy.
- Teams: trong kênh, thêm template Workflows "Post to a channel when a webhook request is received", rồi dán URL HTTPS của nó. Node không cần target. Yêu cầu là một Adaptive Card, và kết quả được đăng thành card thứ hai.

Lần bấm chưa xác minh bị từ chối (`APPROVAL_IDENTITY_UNKNOWN`). Mã sống `STUDIO_IDENTITY_CODE_TTL` giây (600), cho `STUDIO_IDENTITY_CODE_ATTEMPTS` lần nhập (5), và gửi lại sau `STUDIO_IDENTITY_CODE_RESEND` giây (30). Một user studio đã xác minh sở hữu một danh tính chat. Callback công khai bị giới hạn theo IP (`STUDIO_CALLBACK_RATE_LIMIT_IP`, 60) và theo kết nối (`STUDIO_CALLBACK_RATE_LIMIT_CHANNEL`, 300) trong mỗi `STUDIO_CALLBACK_RATE_WINDOW` giây (60). Phía sau nginx của Compose, `STUDIO_TRUSTED_PROXIES` là các CIDR của proxy. `X-Forwarded-For` đọc từ phải sang trái, bỏ các hop tin cậy, và chỉ khi peer trực tiếp là proxy tin cậy. Trả lời trong Studio thì nút trên chat bị tắt. Huỷ và hết hạn đóng yêu cầu.

`SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, và `SLACK_SIGNING_SECRET` bật **Add to Slack**. Redirect URL là `{STUDIO_PUBLIC_URL}/api/approvals/slack/oauth/callback`. Để trống các biến đó thì vẫn dán bot token được.

## Kích hoạt API và webhook

Mọi phản hồi HTTP là một envelope: `{"success": true, "data": …, "error": null}` hoặc `{"success": false, "data": null, "error": {"code": "…", "message": "…", "details": …}}`. Danh mục mã nằm ở `docs/api-errors.md`.

**API** trên thanh công cụ editor tạo token (`wft_…`, hiện một lần) và signing secret (`whsec_…`, hiện một lần). Thu hồi được bất kỳ lúc nào.

```bash
curl -X POST http://localhost:8080/api/hooks/workflows/<wid>/runs \
  -H "Authorization: Bearer wft_..." -H "Content-Type: application/json" \
  -d '{"input": {"message": "hi"}, "mode": "sync"}'
```

`sync` chờ `final_state`, tối đa `STUDIO_SYNC_WAIT_MAX` giây (mặc định 30), rồi trả 202 kèm `poll_url`. `async` (mặc định) trả `202 {run_id, status: "queued"}`. Xem kết quả bằng `GET /api/hooks/workflows/<wid>/runs/<run_id>`. `callback_url` nhận POST với `X-Studio-Event: run.finished`. Địa chỉ nội bộ bị chặn trừ khi `STUDIO_ALLOW_PRIVATE_CALLBACKS=1`. Token sai là `401 TRIGGER_TOKEN_INVALID`. Run qua API có huy hiệu **API** trong History.

Mỗi callback được ký. `v1` là HMAC-SHA256 của `"<t>.<raw body>"`. Từ chối nếu mốc thời gian lệch quá năm phút. Sau khi xoay secret, secret cũ còn hiệu lực `STUDIO_SECRET_GRACE` giây (mặc định một ngày) và header có hai giá trị `v1`. Chấp nhận header khi một `v1` khớp.

```python
import hashlib, hmac, time
def verify(secret: str, header: str, body: bytes, tolerance=300) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    if abs(time.time() - int(parts["t"])) > tolerance:
        return False
    mac = hmac.new(secret.encode(), f'{parts["t"]}.'.encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, parts["v1"])
```

Mỗi token được bắt đầu `STUDIO_TRIGGER_RATE_LIMIT` run trong `STUDIO_TRIGGER_RATE_WINDOW` giây (mặc định 60/60). Vượt mức thì API trả `429 RATE_LIMITED` và `Retry-After`. Việc poll không bị giới hạn. Bộ đếm dùng chung qua Redis. Không có Redis thì mỗi process tự đếm.

Mỗi lần gửi được lưu trạng thái, số lần thử, mã HTTP, và độ trễ, trong mục **Deliveries** của hộp thoại API, có nút **Gửi lại**. Lỗi mạng và phản hồi không phải 2xx được thử lại với độ trễ `min(STUDIO_WEBHOOK_BACKOFF_BASE^n, STUDIO_WEBHOOK_BACKOFF_MAX)`, tối đa `STUDIO_WEBHOOK_MAX_ATTEMPTS` lần. Địa chỉ bị SSRF guard chặn thì thất bại ngay. Bên nhận nên khử trùng theo `run_id` và event. Tên miền chỉ phân giải một lần. Mọi địa chỉ phân giải ra đều được kiểm tra, rồi kết nối thẳng tới IP đó. Không đi theo redirect.

Job chạy trên worker. `STUDIO_WORKER=1` (mặc định) chạy worker trong process API. Có `REDIS_URL` thì process riêng là `python -m app.worker`. Compose có service `worker` (`docker compose up --scale worker=3`). Hàng đợi trong bộ nhớ chỉ dành cho lúc phát triển. Job mất khi process đó khởi động lại. Trên Redis, worker giữ lease `STUDIO_JOB_VISIBILITY_TIMEOUT` giây và gia hạn. `STUDIO_JOB_REAP_EVERY` đưa lại hàng đợi các job hết lease. Job được khôi phục chạy tiếp từ checkpoint cuối (`run_recovered`). Node đang chạy lúc sập có thể chạy lại, nên node HTTP và tool nên idempotent. Không có lịch cron.

Mỗi lần lưu có thay đổi graph, đổi tên, nhân bản, hoặc import sẽ ghi một phiên bản bất biến kèm tác giả và thời điểm. Lưu không đổi thì không tạo phiên bản. Graph có từ trước khi có phiên bản là v1. **Phiên bản** liệt kê, so sánh hai bản bất kỳ, và khôi phục. Khôi phục chép graph cũ thành phiên bản mới nhất và giữ tên hiện tại. Nội dung đã trùng thì không làm gì. Mỗi run trong History có nhãn `vN`, hoặc **chưa lưu** khi editor còn sửa chưa xuất bản. Chỉ kéo node đi chỗ khác, không đổi graph, thì không tính là thay đổi.

```text
GET  /api/workflows/{wid}/versions?limit=50&offset=0
GET  /api/workflows/{wid}/versions/{n}
GET  /api/workflows/{wid}/versions/diff?a=1&b=2
POST /api/workflows/{wid}/versions/{n}/restore
```

`STUDIO_VERSION_KEEP=N` giữ N phiên bản mới nhất. Phiên bản mà một run đã dùng không bao giờ bị xoá. Thiếu phiên bản thì `404 VERSION_NOT_FOUND`.

### Lịch chạy

**⋯ → Lịch chạy** trong editor (chủ workflow) chạy workflow theo lịch cron: năm trường `phút giờ ngày-trong-tháng tháng thứ`, hỗ trợ `*`, khoảng, danh sách, bước nhảy, tên tháng và tên thứ, cùng `@hourly` / `@daily` / `@weekly` / `@monthly` / `@yearly`. Khi đặt cả hai trường ngày, một ngày khớp nếu khớp một trong hai. Mỗi lịch có múi giờ IANA (mặc định theo trình duyệt) và input JSON cho run. Giờ bị bỏ qua khi chuyển DST sẽ chạy trễ một tiếng; giờ bị lặp chỉ chạy một lần. Dialog hiện các lần chạy tiếp theo ngay khi gõ. Run chạy dưới tên người tạo lịch, đi qua cùng hàng đợi job với run từ API, và hiện trong History với nhãn **Lịch**. Lần chạy bị lỡ khi không có worker nào chạy sẽ chạy một lần khi worker lên lại. Nhiều process API cũng không chạy trùng một lần. Lịch tự tắt khi người tạo mất quyền quản lý workflow, và bị xoá vào lần đến hạn kế tiếp sau khi workflow bị xoá. Tối đa 20 lịch cho mỗi workflow. API: `GET|POST /api/workflows/{wid}/schedules`, `PATCH|DELETE …/schedules/{sid}`, `POST /api/schedules/preview`.

## Kho tri thức, MCP, và quyền

**Cài đặt → Kho tri thức** tạo kho và nhận `.txt`, `.md`, `.pdf` tối đa 10 MB. Có thể tìm, đổi model hoặc credential, và lập chỉ mục lại. Embedding dùng credential của kho, rồi `OPENAI_API_KEY`, rồi mock offline cố định (`mock:512`). Model OpenAI mặc định là `text-embedding-3-small`. Postgres của Compose là `pgvector/pgvector:pg17` và tìm bằng SQL. Postgres thường và SQLite lưu JSON rồi tính cosine trong Python. Mã lỗi là `KB_*` trong `docs/api-errors.md`.

**Cài đặt → Máy chủ MCP** đăng ký máy chủ Streamable HTTP (URL và header bí mật) hoặc lệnh stdio. **Tìm công cụ** liệt kê những gì máy chủ có. Phạm vi là cá nhân hoặc tổ chức. Secret được mã hoá. API trả tên và giá trị đã che. URL HTTP phải là địa chỉ công khai (kết nối ghim vào IP đã kiểm) trừ khi `STUDIO_MCP_ALLOW_PRIVATE=1`. Stdio tắt cho đến khi `STUDIO_MCP_STDIO=1`, và chỉ admin đăng ký được lệnh. Process nhận môi trường sạch, home tạm rỗng, và `STUDIO_MCP_TIMEOUT` (30 giây), rồi cả process group bị kill. Đó không phải sandbox. Máy chủ MCP không tin cậy nên chạy thành container HTTP riêng.

Vai trò là `admin`, `editor` (mặc định: tạo workflow, credential, kho tri thức, máy chủ MCP, và kênh cá nhân), và `viewer` (mở và chạy những gì được chia sẻ). Không có SSO. **Cài đặt → Người dùng** đổi vai trò và vô hiệu hoá tài khoản ngay, kể cả socket đang mở. Không tự đổi vai trò hoặc tự vô hiệu hoá, và phải còn ít nhất một admin đang hoạt động. `STUDIO_ADMIN_EMAILS` chỉ là bootstrap: các email đó thành admin khi đăng ký, và lúc khởi động chỉ khi không còn admin nào. `STUDIO_DEFAULT_ROLE=viewer` làm tài khoản mới chỉ được xem.

**Chia sẻ** (chủ sở hữu hoặc admin) thêm email ở mức xem hoặc sửa, hoặc chia sẻ cho cả nhóm. Quyền hiệu lực là quyền cao nhất giữa chia sẻ trực tiếp và các nhóm. Viewer thấy editor chỉ đọc. Run trên workflow được chia sẻ dùng credential, kho tri thức, máy chủ MCP, và subgraph **của chủ sở hữu**. Chủ và admin thấy mọi run. Người khác chỉ thấy run của mình. **Chuyển quyền sở hữu** yêu cầu người nhận là editor hoặc admin. Tài nguyên họ không dùng được có thể gán lại, hoặc giữ và được đánh dấu. **Cài đặt → Hoạt động** là nhật ký cho admin. Xoá người dùng thì ẩn danh và giữ các run, hoặc xoá cả run. Workflow của họ phải chuyển trước. Admin chọn vai trò nào được dùng kênh phê duyệt và máy chủ MCP của tổ chức.

## Docker Compose

Postgres 17 có pgvector, Redis 7, API (Alembic upgrade và seed lúc khởi động), worker, và nginx phục vụ bản build Vite. UI là http://localhost:8080 (`WEB_PORT`).

```bash
cp .env.example .env          # đặt JWT_SECRET và POSTGRES_PASSWORD; không commit .env
docker compose up --build
python scripts/compose_smoke.py http://localhost:8080
```

`GET /api/health` báo `database` (`postgresql` hoặc `sqlite`) và `run_bus` (`redis` hoặc `memory`). `STUDIO_SECRET_KEY` để trống thì được sinh một lần vào volume `apidata` (`/data/secret.key`). Production hãy đặt khoá cố định, cùng `STUDIO_ENV=production`. Dev tại máy để trống `DATABASE_URL` thì dùng SQLite `backend/studio.db`. Để trống `REDIS_URL` thì run bus nằm trong bộ nhớ. Danh sách biến đầy đủ ở `.env.example`.

Migration lúc khởi động có khoá để nhiều process không migrate cùng lúc (advisory lock của Postgres, hoặc `<db>.migrate.lock` với SQLite).

Backend chia lớp `core / models / schemas / repositories / services / api / engine`. Sơ đồ và quy tắc import ở `docs/backend-architecture.md`. Đổi schema thì dùng Alembic:

```bash
cd backend && .venv/bin/alembic revision --autogenerate -m "mô tả"
.venv/bin/alembic upgrade head
```

## Kiểm thử

```bash
cd backend && .venv/bin/python -m pytest -q
cd frontend && npm run build && npm run lint
```

Cài backend bằng `pip install -e "backend[dev]"`. Playwright tự bật API ở cổng 8100 và Vite ở cổng 5190:

```bash
cd frontend && npx playwright install chromium
npm run e2e
SHOTS=1 npm run e2e -- screenshots
```

`E2E_UVICORN` đổi binary uvicorn (mặc định `backend/.venv/bin/uvicorn`). `PW_CHROME` trỏ tới Chrome đã cài. E2E không chạy trên CI. GitHub Actions (`.github/workflows/ci.yml`) chạy pytest trên Python 3.12, build frontend trên Node 20 và 22, và smoke test của Compose. `factory-verify.yml` kiểm metadata của factory.

Postgres và Redis tại máy:

```bash
cd backend
DATABASE_URL=postgresql://… TEST_DATABASE_URL=postgresql://… \
  REDIS_URL=redis://localhost:6379/0 .venv/bin/python -m pytest -q
```

Test Postgres cần role có quyền `CREATEDB`.

## Bố cục

| Đường dẫn | Nội dung |
| --- | --- |
| `frontend/` | React, TypeScript, Vite, React Flow, Tailwind v4, shadcn/ui |
| `backend/app/` | App FastAPI. Router gọi service. Service gọi repository và engine. |
| `docs/api-errors.md` | Mã lỗi |
| `docs/backend-architecture.md` | Quy tắc lớp |
| `docs/ui-conventions.md` | Quy tắc UI |
| `.env.example` | Mọi biến của Compose và runtime |
| `roadmap.md` | Những gì đã giao |
