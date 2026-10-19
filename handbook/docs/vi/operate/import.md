# Import repo LangGraph

Import biến một project LangGraph viết bằng Python thành workflow chạy và xem
trace được trong studio. Graph chạy bằng chính **code gốc**, bên trong Docker
sandbox.

!!! warning "Thử nghiệm, mặc định tắt"
    Import tắt cho tới khi `STUDIO_ENABLE_IMPORT=1`. Khi còn tắt, `/api/import*`
    trả về `404 IMPORT_DISABLED` và nút **Import repo** bị ẩn. `GET /api/health`
    cho biết `import_enabled`.

## Import

Ở trang **Workflows**, **Import repo** nhận một URL GitHub công khai (kèm
branch và thư mục con nếu cần) hoặc một file zip. Hộp thoại hiện các bước tải
về, cài đặt, kiểm tra và sẵn sàng. Chọn một graph rồi tạo workflow.

Những gì diễn ra (`backend/app/engine/repo_import.py`,
`backend/app/engine/sandbox/container.py`, `backend/app/engine/sandbox/runner.py`):

1. `git clone --depth 1`, hoặc giải nén zip có chặn đường dẫn zip-slip, vào
   `~/.langgraph-studio/imports/<job_id>/` (`STUDIO_IMPORT_DIR`). Bước này chạy
   trong process API; image API có sẵn `git`.
2. `python -m venv` và `pip` chạy **trong Docker** (`STUDIO_IMPORT_IMAGE`, mặc
   định `python:3.12-slim`). Package lấy từ `pyproject.toml` / `setup.py`
   (`pip install -e .`) hoặc `requirements.txt`, luôn cộng thêm `langgraph` và
   `python-dotenv`.
3. Graph lấy từ `langgraph.json`, hoặc từ việc quét tìm `StateGraph` và
   `x = ….compile(…)`. Việc quét chỉ đọc file.
4. `runner.py inspect` gọi `graph.get_graph(xray=True)` với `--network none`
   (120 giây, `STUDIO_INSPECT_TIMEOUT`).
5. `__start__` / `__end__` thành Start / End. Các node khác thành node Code chỉ
   đọc, được dàn bằng dagre.

## Chạy

Run chạy graph gốc qua `runner.py run` (`graph.astream`). Sự kiện được chuyển
thành `node_started` / `node_finished`. Đặt runtime context vào input dưới key
`__context__`. Thiếu key nào có tên trong `.env.example` sẽ được báo trong lỗi.
Hết giờ hoặc hết bộ nhớ (exit 137) thành một sự kiện `error`, ví dụ
`Sandbox stopped (time limit (12s)).`

Nếu graph import không có checkpointer, runner gắn một saver trong bộ nhớ và
gửi checkpoint đã serialise về server, nên run được khôi phục sẽ khởi động
container mới từ checkpoint đó. State không serialise được, hoặc lớn hơn 2 MB,
sẽ chạy lại từ đầu. Repo import không có sổ kết quả node.

## Sandbox

| Kiểm soát | Cấu hình |
| --- | --- |
| Hệ thống file | Root chỉ đọc; chỉ thư mục job được gắn đọc-ghi; bản sao chỉ đọc của `runner.py` ở `/opt/studio-runner`; `/tmp` tmpfs |
| Quyền | Bỏ mọi capability, `no-new-privileges` |
| Bộ nhớ | `STUDIO_IMPORT_MEMORY` (mặc định `1g`, swap bằng bộ nhớ) |
| CPU | `STUDIO_IMPORT_CPUS` (mặc định `1`) |
| Process | `STUDIO_IMPORT_PIDS` (mặc định 256) |
| Mạng | Cài đặt: `bridge`. Kiểm tra: `none`. Chạy: `STUDIO_IMPORT_NETWORK` (`bridge` hoặc `none`, mặc định `bridge`) |
| Môi trường | Không dùng môi trường của server. Chỉ các tên khai báo trong `.env.example` mà server có, cộng `STUDIO_IMPORT_SECRETS`. `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL` và mọi tên `STUDIO_*` không bao giờ được truyền vào. |
| Thời gian | `STUDIO_RUN_TIMEOUT`, đọc khi process khởi động (mặc định 300 giây cho run import) |

`localhost` trong sandbox là chính container. Khi runtime là Docker, không có
chuyện âm thầm chuyển sang subprocess. `STUDIO_IMPORT_RUNTIME=subprocess` chỉ để
chạy test và cho máy không có Docker; nó chạy cùng user hệ điều hành với API và
không phải sandbox.

## Với Compose

Compose gắn `/var/run/docker.sock` vào `api` và `worker`, socket này tương
đương quyền root trên máy chạy Docker. Đừng bật import trên máy bạn không tin.
Trước khi `docker compose up`:

```bash
export STUDIO_ENABLE_IMPORT=1
export STUDIO_IMPORT_HOST_DIR="$PWD/.imports"   # đường dẫn tuyệt đối trên host của bind mount
mkdir -p "$STUDIO_IMPORT_HOST_DIR"
```

Không có `STUDIO_IMPORT_HOST_DIR` thì daemon sẽ gắn đường dẫn bên trong
container và sandbox lỗi. Trên Linux, nếu user của container không mở được
socket, đặt `STUDIO_DOCKER_GID="$(stat -c %g /var/run/docker.sock)"`. Nếu
`docker` không có trong `PATH`, API dùng CLI của Docker Desktop ở
`/Applications/Docker.app/Contents/Resources/bin/docker`.

## Dọn dẹp

Job được lưu thành `job.json`. Khi khởi động lại, job đang dở mà pid không còn
sẽ được đánh dấu `Import interrupted by a restart`. Workflow tạo từ job được
gắn `keep` và không bị dọn. Các thư mục job khác cũ hơn
`STUDIO_IMPORT_MAX_AGE_HOURS` (mặc định 72, `0` là không dọn) bị xoá khi lần
import tiếp theo bắt đầu. Mã nguồn lớn hơn `STUDIO_IMPORT_MAX_BYTES` (mặc định
200 MB, không tính `.git`) bị từ chối.

## Chưa hỗ trợ

Repo private, monorepo JS, file `langgraph.json` phức tạp, gVisor và
Firecracker.

Đã kiểm tra với `langchain-ai/new-langgraph-project` (chạy được không cần key)
và `langchain-ai/react-agent` (import được và hiện vòng lặp; khi chạy thì báo
thiếu key của nhà cung cấp).
