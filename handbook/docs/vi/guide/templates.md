# Mẫu workflow

**Workflow mới** mở thư viện mẫu.

![Thư viện mẫu](../images/templates.png)

| Nhóm | Nội dung |
| --- | --- |
| Workflow trống | Chỉ có Start và End. |
| Có sẵn | Mười hai mẫu ở dưới. |
| Chỉ mình tôi | Các mẫu bạn đã lưu. |
| Toàn tổ chức | Các mẫu chia sẻ cho mọi người. |

Mỗi thẻ có bản xem trước của graph và logo của từng kênh duyệt mà mẫu dùng.
Tạo từ mẫu sẽ chép nó thành một workflow mới do bạn sở hữu. Tên và mô tả của
mẫu có sẵn hiện theo ngôn ngữ giao diện.

## Mẫu có sẵn

| Mẫu | Làm gì |
| --- | --- |
| **Chatbot** | Một LLM trả lời tin nhắn của người dùng. |
| **Hỏi đáp RAG** | Tìm các đoạn liên quan trong kho tri thức rồi trả lời dựa trên đó. |
| **Quy trình duyệt** | Soạn câu trả lời, nhờ người duyệt trong studio, rồi chỉnh lại hoặc dừng. |
| **Định tuyến** | Phân loại yêu cầu rồi chuyển tới nhánh chuyên trách. |
| **Duyệt qua Slack** | Quy trình duyệt, với nút Approve / Reject trong Slack. |
| **Duyệt qua Telegram** | Như trên, với nút trong Telegram. |
| **Duyệt qua WhatsApp** | Như trên, với nút trả lời trong WhatsApp. |
| **Duyệt qua e-mail** | Xin duyệt qua e-mail, rồi node Send email gửi kết quả cho người yêu cầu. |
| **Duyệt qua Microsoft Teams** | Như trên, với Adaptive Card trong Teams. |
| **Duyệt hai cấp** | Trưởng nhóm duyệt trên Slack, sau đó quản lý duyệt qua e-mail. |
| **Hỗ trợ có chuyển cấp** | Trả lời từ kho tri thức; node Decision chuyển câu trả lời chưa chắc chắn cho người xem lại. |
| **Xử lý hàng loạt** | Vòng For each tóm tắt từng mục trong danh sách, rồi một LLM gộp các bản tóm tắt. |

Mẫu theo kênh chỉ ghi loại kênh. Sau khi tạo, chọn kết nối, người nhận và
người duyệt trên node Human (xem [Kênh duyệt](../operate/channels.md)). Trước
đó, run sẽ dừng chờ ở node Human và có thể duyệt ngay trong studio. **Hỏi đáp
RAG** và **Hỗ trợ có chuyển cấp** cần một kho tri thức trước khi chạy.

## Lưu thành mẫu

**⋯ → Lưu thành mẫu** chép **phiên bản đã lưu gần nhất** của workflow (muốn có
các sửa đổi chưa lưu thì lưu trước). Chọn tên, mô tả và ai được thấy. Phạm vi
tổ chức cần quyền `org.manage`.

Mẫu không bao giờ mang theo credential, kho tri thức, máy chủ MCP, kết nối kênh
duyệt, người nhận hay người duyệt, liên kết subgraph, header hay API key. Các
field đó được để trống, sau khi tạo bạn tự chọn lại. Node Human chỉ giữ loại kênh
mà nó dùng.

## Xuất và nhập

**Xuất** trên một thẻ ghi ra file `*.template.json`:

```json
{"format": "superstep/template", "version": 1,
 "name": "…", "description": "…", "workflow": {"state": [], "nodes": [], "edges": []}}
```

**Nhập mẫu** trong thư viện đọc lại file đó. Mẫu có node Code cần quyền
`code.write` để nhập hoặc dùng.

Xoá mẫu cần gõ đúng tên mẫu. Các workflow đã tạo từ mẫu không bị ảnh hưởng.
