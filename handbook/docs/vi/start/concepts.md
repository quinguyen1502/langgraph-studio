# Khái niệm

## Workflow

Workflow là một tài liệu JSON: tên, state schema, các node và các edge.

```json
{"name": "Support triage",
 "state": [{"name": "message", "type": "string"}, {"name": "answer", "type": "string"}],
 "nodes": [{"id": "n1", "type": "llm", "position": {"x": 0, "y": 0},
            "data": {"label": "Reply", "model": "gpt-4o-mini",
                     "prompt": "Hi {{state.message}}", "output_field": "answer"}}],
 "edges": [{"id": "e1", "source": "start", "target": "n1"}]}
```

Backend biên dịch JSON này thành `StateGraph` của LangGraph: mỗi node thành
một node của graph, mỗi edge thành một bước chuyển, node Condition thành
conditional edge. JSON là nguồn sự thật duy nhất; trình soạn thảo chỉ ghi ra
JSON đó.

## State

State là một bản ghi có kiểu, dùng chung cho mọi node. Node đọc trường qua tham
chiếu `{{state.field}}` và ghi kết quả vào một `output_field`. Khi nhiều nhánh
song song cùng ghi một trường, trường đó cần **reducer**: `append` cho danh sách,
`merge` cho object, `add` cho số. Mặc định là `replace`. Xem
[State và tham chiếu](../guide/state.md).

## Node và edge

| Nhóm | Node |
| --- | --- |
| Gọi model | LLM, Decision (Jev) |
| Dữ liệu và công cụ | Tool (function, HTTP hoặc code Python), MCP tool, Retriever, Send email |
| Điều khiển luồng | Condition, For each, Join, Subgraph |
| Con người | Human |
| Biên | Start, End |

Một node có edge tới nhiều đích sẽ chạy các nhánh trong cùng một superstep.
Condition chọn một edge đi ra theo nhãn của edge. Xem
[Các loại node](../guide/nodes.md).

## Run

Run là một run graph đã lưu (hoặc chưa lưu) với input JSON. Run phát ra
các sự kiện như `run_started`, `node_started`, `node_token`, `node_finished`,
`run_waiting`, `run_paused`, `error` và `run_finished`. Trạng thái cuối là
`ok`, `error`, `cancelled`, `timeout` và `paused`; run đang chờ ở node Human
là `waiting`, chờ quá lâu thì thành `expired`.

## Superstep

LangGraph chạy graph theo từng **superstep**. Mọi node đã sẵn sàng chạy trong
cùng một superstep; phần ghi của chúng được reducer gộp lại trước superstep
kế tiếp. Nút **Một bước** trong trình soạn thảo chạy đúng một superstep rồi
dừng.

## Checkpoint

Sau mỗi superstep, state của run được lưu thành checkpoint trong database.
Node Human, một bước đang dừng, worker bị sập hay server khởi động lại đều
chạy tiếp từ checkpoint cuối, không chạy lại từ đầu.

## Side effect gần như đúng một lần

Mỗi run LLM hoặc Tool có một idempotency key cố định theo run, node và
lượt lặp. Node có side effect đã xong được ghi vào sổ kết quả, nên run được
khôi phục sẽ dùng lại kết quả (`reused` trong trace) thay vì gọi dịch vụ lần
nữa. HTTP công cụ cũng gửi `Idempotency-Key`. Xem
[Kiến trúc](../reference/architecture.md).

## Phiên bản

Mỗi lần lưu có thay đổi graph sẽ ghi một phiên bản bất biến. Run ghi lại
phiên bản nó đã dùng. Xem [Phiên bản](../guide/versions.md).
