# Môi trường chạy Code

[Chế độ Code](../guide/code-mode.md) cho admin viết Python hoặc TypeScript trong node Tool.
Trang này nói về phía server: cách bật và cái gì cách ly nó.

## Bật lên

```bash
docker build -t studio-code:1 docker/studio-code
export STUDIO_ENABLE_CODE_NODES=1
```

Image là `python:3.12-slim` có `pydantic` và `python-dateutil`.
`STUDIO_CODE_IMAGE` chọn image khác; liệt kê package của nó trong
`STUDIO_CODE_PACKAGES` (cách nhau bằng dấu phẩy) để trình soạn thảo hiện ra.
Khi chế độ này tắt, hoặc thiếu Docker hay image, workflow có node Code sẽ không
qua được kiểm tra và báo rõ lý do. `GET /api/meta/runtime` cho biết trình soạn
thảo đang thấy gì.

Với Compose, API và worker khởi động container qua Docker socket, giống import
repo.

## Cách ly

Mỗi lần gọi có một container mới:

| Kiểm soát | Cấu hình |
| --- | --- |
| Mạng | `--network none` |
| Hệ thống file | Root chỉ đọc, `/tmp` tmpfs 64 MB, không gắn thư mục nào của host |
| Quyền | `--cap-drop ALL`, `no-new-privileges`, đúng uid và gid của API |
| Môi trường | `HOME=/tmp` và hai cờ của Python; không có biến hay credential nào của server |
| Input | Bản sao JSON của state qua stdin |

## Giới hạn

| Biến | Mặc định | Nghĩa |
| --- | --- | --- |
| `STUDIO_CODE_MEMORY` | `256m` | Bộ nhớ (swap bằng bộ nhớ) |
| `STUDIO_CODE_CPUS` | `0.5` | Phần CPU |
| `STUDIO_CODE_PIDS` | `64` | Số process |
| `STUDIO_CODE_MAX_SECONDS` | `30` | Trần cho timeout của node |
| `STUDIO_CODE_CONCURRENCY` | `4` | Số container cùng lúc trên mỗi process server |
| `STUDIO_CODE_TEST_PER_MINUTE` | `20` | Số run thử trong trình soạn thảo cho mỗi người mỗi phút |

Huỷ run sẽ kill container của nó.

## TypeScript

Node TypeScript chạy trên Deno trong image riêng, với cùng cách ly và giới
hạn. Mặc định cả hai ngôn ngữ đều được cung cấp (`STUDIO_CODE_LANGUAGES`, ví
dụ `python` để chỉ cung cấp Python).

```bash
docker build -t studio-code-ts:1 docker/studio-code-ts
```

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `STUDIO_CODE_LANGUAGES` | `python,typescript` | Các ngôn ngữ trình soạn thảo cung cấp |
| `STUDIO_CODE_TS_IMAGE` | `studio-code-ts:1` | Image Deno |
| `STUDIO_CODE_TS_PACKAGES` | `npm:zod@3,npm:date-fns@4` | Các package duy nhất code được import, mỗi package ghim theo `tên@major`; giữ đúng như `docker/studio-code-ts/deps.ts` |
| `STUDIO_DENO` | `deno` trong `PATH` | File chạy Deno cho chế độ subprocess |
| `STUDIO_CODE_TS_DENO_DIR` | trống | Cache Deno chứa các package được phép, cho chế độ subprocess |

Code phải import package với đúng bản major đã ghim trong danh sách, ví dụ
`npm:zod@3` (hoặc `npm:zod@3.25.1`, `npm:zod@3/mini`). Import `npm:zod` không
ghi phiên bản hoặc khác major bị từ chối khi lưu, với lỗi `CODE_INVALID` và lý
do ghi rõ spec được phép, vì nếu không Deno sẽ tìm bản mới nhất, mà cache không
có bản đó.

Chế độ subprocess không có image, nên bạn tự tạo cache với đúng các spec đó rồi
trỏ máy chủ tới cache này (không có `STUDIO_CODE_TS_DENO_DIR` và
`STUDIO_CODE_TS_PACKAGES` thì không package nào được phép):

```bash
export DENO_DIR=/var/lib/studio/deno-cache
printf 'import "npm:zod@3";\nimport "npm:date-fns@4";\n' > deps.ts
deno cache --no-config --no-lock deps.ts
export STUDIO_CODE_TS_DENO_DIR=$DENO_DIR STUDIO_CODE_TS_PACKAGES=npm:zod@3,npm:date-fns@4
```

Deno chạy không có cờ quyền nào, cùng `--no-remote` và `--cached-only`. Code
không đọc hay ghi được file, không dùng được mạng, không đọc được biến môi
trường và không chạy được tiến trình, kể cả ở chế độ subprocess, và chỉ
import được package đã có trong cache của image. Bộ nhớ bị giới hạn qua heap
V8 (ba phần tư `STUDIO_CODE_MEMORY`). Thẻ admin trong **Cài đặt → Người dùng**
hiện từng ngôn ngữ và cho biết ngôn ngữ đó đã sẵn sàng chưa.

## Không có Docker

`STUDIO_CODE_RUNTIME=subprocess` chạy code như process con của server, với môi
trường rỗng và thư mục tạm riêng. Trên Linux còn có giới hạn bộ nhớ, thời gian
CPU, số file mở và số process; giới hạn thời gian kill cả nhóm process.

!!! danger "Đây không phải sandbox"
    Ở chế độ subprocess, code dùng được mạng và đọc được mọi file mà user của
    server đọc được, kể cả file database và `secret.key` khi dùng SQLite. Trên
    macOS giới hạn bộ nhớ không có tác dụng. Chỉ dùng cho việc ở máy và code tin
    cậy.

Studio cho thấy điều này ở mọi nơi:

- một dòng `WARNING` trong log khi khởi động;
- `code_runtime: "subprocess"` trong `GET /api/meta/runtime`;
- một cảnh báo trong cấu hình Code, và nhãn **Chạy trực tiếp trên server** trong ô chọn
  chế độ và **Chạy trên server** trên node, kèm tooltip giải thích;
- `runtime: subprocess` trên các dòng trace, kèm một cảnh báo cho mỗi run;
- một dấu trong lịch sử run (`code_runtime` trên mỗi run);
- thẻ Code nodes ở **Cài đặt → Người dùng**;
- một mục nhật ký `system.code_runtime_subprocess` ở lần gọi đầu tiên sau mỗi
  lần khởi động.

Chế độ này không bao giờ tự bật: với runtime `docker` mặc định mà không có
Docker, node Code không qua được kiểm tra. Giá trị runtime không hợp lệ sẽ tắt
node Code.
