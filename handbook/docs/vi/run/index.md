# Chạy

Workflow chạy được theo bốn cách. Cách nào cũng đi qua cùng một engine, tạo
cùng một kiểu trace và hiện trong **Lịch sử**.

| Bắt đầu bởi | Cách | Nhãn trong Lịch sử |
| --- | --- | --- |
| Trình soạn thảo | **Chạy**, **Một bước** hoặc **Chạy tới đây**, qua `/ws/run` | — |
| Dịch vụ khác | `POST /api/hooks/workflows/{wid}/runs` với token của workflow | **API** |
| Lịch | Lịch cron gắn với workflow | **Lịch** |
| Người tiếp tục run | Duyệt, từ chối hoặc trả lời node Human đang chờ | — |

<div class="grid cards" markdown>

-   :material-chart-gantt:{ .lg .middle } **[Run và trace](traces.md)**

    ---

    Timeline Logs, chạy từng bước, huỷ, giới hạn và chi phí.

-   :material-account-check:{ .lg .middle } **[Duyệt bởi người](human-approval.md)**

    ---

    Run đang chờ, thông báo và duyệt qua chat.

-   :material-api:{ .lg .middle } **[API trigger và webhook](api-triggers.md)**

    ---

    Token, run sync và async, callback có chữ ký, worker.

-   :material-calendar-clock:{ .lg .middle } **[Lịch chạy](schedules.md)**

    ---

    Cron, múi giờ và các mốc bị lỡ.

-   :material-flask-outline:{ .lg .middle } **[Kiểm thử workflow](tests.md)**

    ---

    Test case, Chạy tất cả, so sánh với version trước.

</div>
