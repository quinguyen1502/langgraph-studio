# Môi trường chạy Code

[Chế độ Code](../guide/code-mode.md) cho admin viết Python trong node Tool.
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
- một cảnh báo trong cấu hình Code, và nhãn **Không cách ly** trên node và
  trong ô chọn chế độ;
- `runtime: subprocess` trên các dòng trace, kèm một cảnh báo cho mỗi run;
- một dấu trong lịch sử run (`code_runtime` trên mỗi run);
- thẻ Code nodes ở **Cài đặt → Người dùng**;
- một mục nhật ký `system.code_runtime_subprocess` ở lần gọi đầu tiên sau mỗi
  lần khởi động.

Chế độ này không bao giờ tự bật: với runtime `docker` mặc định mà không có
Docker, node Code không qua được kiểm tra. Giá trị runtime không hợp lệ sẽ tắt
node Code.
