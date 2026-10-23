# Bắt đầu

Superstep gồm ba phần:

| Phần | Là gì |
| --- | --- |
| **Frontend** | React, TypeScript và Vite. React Flow vẽ canvas; giao diện dùng shadcn/ui trên Tailwind v4, có tiếng Anh và tiếng Việt. |
| **API** | FastAPI. Lưu workflow, biên dịch thành `StateGraph` của LangGraph, chạy và đẩy sự kiện qua WebSocket. |
| **Worker** | Chạy các job trong hàng đợi: run gọi qua API, lịch chạy, run được khôi phục và việc gửi webhook. Mặc định worker chạy ngay trong process API. |

Workflow là JSON gồm state schema, các node và các edge. Trình soạn thảo ghi
JSON đó, và backend kiểm tra lại mỗi lần lưu và mỗi run.

```mermaid
flowchart LR
  UI[Trình soạn thảo] -- REST + WebSocket --> API[FastAPI]
  API --> DB[(SQLite hoặc Postgres)]
  API -- job --> Q[(Bộ nhớ hoặc Redis)]
  Q --> W[Worker]
  API & W --> G[LangGraph StateGraph]
  G --> LLM[Nhà cung cấp LLM]
  G --> T[HTTP tool · MCP · SMTP]
  G --> S[Docker sandbox]
```

## Đọc tiếp

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **Cài đặt**

    ---

    Phát triển ở máy với `./dev.sh`, hoặc chạy đủ bộ bằng Compose.

    [:octicons-arrow-right-24: Cài đặt](install.md)

-   :material-vector-polyline:{ .lg .middle } **Bắt đầu nhanh**

    ---

    Dựng, chạy, duyệt và gọi một workflow qua HTTP trong mười phút.

    [:octicons-arrow-right-24: Bắt đầu nhanh](quickstart.md)

-   :material-lightbulb-outline:{ .lg .middle } **Khái niệm**

    ---

    State, node, edge, run, superstep và checkpoint.

    [:octicons-arrow-right-24: Khái niệm](concepts.md)

</div>
