# Chế độ Code

Node Tool ở chế độ **Code Python** chạy đoạn Python bạn viết ngay trong node.
Code định nghĩa hàm `main(state)`; giá trị trả về được ghi vào `output_field`
của node.

```python
def main(state):
    print("seen:", state["message"])   # hiện trong trace, không lưu vào state
    return state["message"].upper()
```

![Chế độ Code với kết quả chạy thử](../images/code-node.png)

!!! info "Trước khi bắt đầu"
    Chế độ Code tắt cho tới khi server đặt `STUDIO_ENABLE_CODE_NODES=1` và có
    image sandbox. Việc này do admin làm: xem
    [Môi trường chạy Code](../operate/code-runtime.md). Khi còn tắt, workflow
    có node Code sẽ không qua được kiểm tra và báo rõ lý do.

## Viết và chạy thử

1. Chọn một node Tool, đặt **Chế độ** là **Code Python**. Ô code bắt đầu bằng
   khung `main(state)` và tô màu cú pháp Python.
2. Dưới ô code, node liệt kê các package có trong image và các giới hạn.
3. Đặt input mẫu vào tab **Input** của panel run.
4. Bấm **Chạy thử với state mẫu**. Nút này chạy `main(state)` một lần với
   input đó và không lưu gì. Kết quả hiện giá trị trả về, phần đã in ra, và
   khi lỗi thì có traceback chỉ gồm các frame trong code của bạn.
5. Lưu và chạy như bình thường.

Chạy thử đi qua `POST /api/code/test`, tối đa
`STUDIO_CODE_TEST_PER_MINUTE` lần mỗi phút cho mỗi người (mặc định 20).

## Quy ước

| Quy tắc | Chi tiết |
| --- | --- |
| Điểm vào | Hàm tên `main` nhận một tham số là state. |
| Input | Bản sao JSON của state. Sửa nó không làm thay đổi run. |
| Output | Giá trị trả về, phải là JSON: dict, list, string, số, bool hoặc `None`. |
| Phần in ra | `print()` và stderr hiện trong trace, tối đa 64 KB (dài hơn bị cắt). |
| Kích thước | Mã nguồn tối đa 64 KB; state và kết quả mỗi thứ tối đa 1 MB. |
| Package | Thư viện chuẩn cộng các package trong image: `pydantic` và `python-dateutil` với image mặc định. |
| Mạng, file | Không có. Container không có mạng, root chỉ đọc, `/tmp` 64 MB. |
| Thời gian | Timeout của node, không vượt quá mức tối đa của server (mặc định 30 giây). |

Code chỉ ảnh hưởng tới run qua giá trị trả về.

## Lỗi

| Mã | Khi nào |
| --- | --- |
| `CODE_INVALID` | Lỗi cú pháp, hoặc không có hàm `main` gọi được. |
| `CODE_FAILED` | `main` ném lỗi. Trace hiện traceback. |
| `CODE_RESULT_NOT_JSON` | Giá trị trả về không phải JSON. |
| `CODE_TIMEOUT` | Chạy quá giới hạn thời gian. |
| `CODE_MEMORY` | Container chạm giới hạn bộ nhớ. |
| `CODE_TOO_LARGE` | Mã nguồn, state hoặc kết quả vượt giới hạn kích thước. |
| `CODE_RUNTIME_OFF`, `CODE_RUNTIME_UNAVAILABLE` | Chế độ Code đang tắt, hoặc thiếu Docker hay image. |
| `CODE_WRITE_FORBIDDEN` | Bạn không có quyền `code.write`. |

Cấu hình retry của node áp dụng cho các lỗi này. Huỷ run sẽ kill container
của nó.

## Ai được viết code

Chỉ vai trò có `code.write` (mặc định là admin) mới được thêm node Code hoặc
sửa code của nó, dù qua lưu, khôi phục phiên bản, hay nhập và dùng mẫu. Editor
vẫn mở, chạy, di chuyển, đổi tên, xoá node Code và nhân bản workflow có node
Code; với họ, code chỉ đọc và nút chạy thử bị ẩn.

## Trong trace

Dòng của node có `code_output`: phần in ra, runtime và thời gian chạy. Khi lỗi
thì có traceback. Mỗi lần gọi mất khoảng 0,3 giây khi image đã sẵn.
