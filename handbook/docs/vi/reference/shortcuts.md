# Phím tắt

Trên macOS, ++ctrl++ là ++cmd++. ++question++ hoặc ++ctrl+slash++ hiện danh sách
này trong trình soạn thảo. Danh sách gốc nằm ở `frontend/src/lib/shortcuts.ts`,
dùng chung cho bộ xử lý phím, bảng phím tắt và bảng lệnh.

| Nhóm | Thao tác | Phím | Khi đang gõ |
| --- | --- | --- | --- |
| Chung | Lưu | ++ctrl+s++ | có |
| Chung | Bảng lệnh | ++ctrl+k++ | có |
| Chung | Bảng phím tắt | ++question++, ++ctrl+slash++ | |
| Chung | Bỏ chọn / đóng panel | ++esc++ | |
| Chạy | Chạy | ++ctrl+enter++ | có |
| Chạy | Dừng | ++ctrl+period++ | có |
| Lịch sử | Undo | ++ctrl+z++ | |
| Lịch sử | Redo | ++ctrl+shift+z++, ++ctrl+y++ | |
| Clipboard | Copy, cut, paste node | ++ctrl+c++, ++ctrl+x++, ++ctrl+v++ | |
| Clipboard | Nhân bản | ++ctrl+d++ | |
| Canvas | Xoá phần đang chọn | ++delete++, ++backspace++ | |
| Canvas | Chọn tất cả | ++ctrl+a++ | |
| Canvas | Vừa khung nhìn | ++shift+1++ | |
| Canvas | Phóng to, thu nhỏ | ++ctrl+equal++, ++ctrl+minus++ | |
| Canvas | Tự sắp xếp bố cục | ++shift+l++ | |

Khi đang gõ trong một ô, các phím tắt khác ngoài lưu, chạy, dừng và bảng lệnh
đều bị bỏ qua; hộp thoại đang mở cũng tắt chúng. Ô nhập văn bản giữ undo và
copy riêng của trình duyệt.
