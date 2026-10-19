# Câu hỏi thường gặp

**Cần key của model mới thử được không?**
Không. Khi không có credential và không có `OPENAI_API_KEY`, node LLM dùng bản
mock offline cho kết quả cố định, node Decision trả câu trả lời mẫu, embedding
dùng `mock:512`, và node Send email chạy thử. Mọi ví dụ và mẫu khởi đầu đều
chạy được.

**JSON của workflow có bị gắn chặt với studio không?**
JSON là định dạng riêng của studio. Khi chạy, backend biên dịch nó thành một
`StateGraph` bình thường của LangGraph; trang [Khái niệm](../start/concepts.md)
có mô tả định dạng.

**Chạy được project LangGraph có sẵn không?**
Được, bằng [import repo](../operate/import.md): graph Python gốc chạy trong
Docker sandbox và các bước của nó hiện trong cùng một trace. Node được import
chỉ đọc trên canvas.

**Khác gì các sản phẩm của LangChain?**
Superstep là một project riêng, tự host, không do LangChain làm. Nó dựng graph
trực quan dưới dạng JSON, biên dịch sang LangGraph, và có sẵn duyệt, lịch chạy,
trigger, phiên bản và phân quyền. LangSmith Studio (trước đây là LangGraph
Studio) dùng để xem graph bạn viết bằng code, còn LangSmith Deployment (trước
đây là LangGraph Platform) dùng để host chúng. Tới v0.1.0, Superstep có tên là
LangGraph Studio.

**Vì sao run dừng với lỗi recursion?**
Một vòng lặp không bao giờ đi qua Condition dẫn ra ngoài, hoặc graph chạy quá
`STUDIO_RECURSION_LIMIT` bước (mặc định 25). Vòng For each không tính vào giới
hạn này. Xem [Run và trace](../run/traces.md#gioi-han).

**Hai nhánh cùng ghi một field và Lưu bị lỗi.**
Đặt reducer cho field đó (`append`, `merge` hoặc `add`), hoặc ghi vào các field
khác nhau. Xem [State và tham chiếu](../guide/state.md#reducer).

**Node LLM chạy trong Docker không gọi được Ollama.**
Trong Compose, `localhost` là chính container. Dùng
`http://host.docker.internal:11434`. Xem
[Triển khai bằng Compose](../operate/deploy.md#model-chay-o-may-khi-dung-compose).

**Vì sao node Code của tôi chỉ đọc?**
Viết code cần quyền `code.write`, mặc định chỉ admin có. Xem
[Chế độ Code](../guide/code-mode.md#ai-uoc-viet-code).

**Run được khôi phục có gửi e-mail hai lần không?**
Không. Node có side effect đã xong được phát lại từ sổ kết quả, và `Message-ID`
của e-mail lấy từ idempotency key của node. Xem
[Kiến trúc](architecture.md#side-effect-gan-nhu-ung-mot-lan).

**Run được lưu ở đâu, bao lâu?**
Trong database, kèm sự kiện (giới hạn bởi `STUDIO_RUN_MAX_BYTES`), state cuối
và phiên bản đã dùng. Khi xoá người dùng, có thể giữ run của họ (đã ẩn danh)
hoặc xoá luôn.

**Giao diện có những ngôn ngữ nào?**
Tiếng Anh và tiếng Việt. Mặc định theo trình duyệt; nút ngôn ngữ lưu lựa chọn.
