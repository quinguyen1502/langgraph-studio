# State và tham chiếu

## State schema

Khai báo state ở mục **State schema** của panel trái. Mỗi field có tên và
kiểu:

| Kiểu | Giá trị JSON | Reducer |
| --- | --- | --- |
| `string` | văn bản | `replace` |
| `number` | số thực | `replace`, `add` |
| `integer` | số nguyên | `replace`, `add` |
| `boolean` | `true` / `false` | `replace` |
| `object` | object JSON | `replace`, `merge` |
| `list` | mảng JSON | `replace`, `append` |

Input của run là state ban đầu.

## Reducer

Reducer quyết định một lần ghi kết hợp với giá trị đang có trong field thế
nào. `replace` (mặc định) ghi đè. Các reducer khác có tác dụng khi nhiều node
ghi trong cùng một superstep, hoặc khi vòng lặp gom kết quả:

| Reducer | Tác dụng |
| --- | --- |
| `append` | Thêm phần tử (hoặc các phần tử) mới vào list. |
| `merge` | Gộp các key mới vào object. |
| `add` | Cộng thêm số. |

Các nhánh song song cùng ghi một field mà không có reducer sẽ không qua được
kiểm tra, vì LangGraph không biết lần ghi nào thắng.

## Tham chiếu

Prompt, câu hỏi của Human, URL và body của HTTP Tool, query của Retriever,
các ô của Send email và arguments của MCP đều là template. Một tham chiếu có
dạng `{{state.field}}`, kèm đường dẫn và filter nếu cần:

```text
{{state.order.items.0.sku}}        đi vào object theo key và list theo chỉ số
{{state.name | trim | upper}}      filter áp dụng từ trái sang phải
{{state.tags | join(", ")}}        filter nhận được một tham số
{{state.note | default("none")}}   giá trị thay thế khi rỗng
```

Thiếu một bước trên đường dẫn thì kết quả rỗng.

| Filter | Kết quả |
| --- | --- |
| `upper`, `lower`, `trim` | Chữ hoa/thường và khoảng trắng |
| `json` | Giá trị dạng JSON |
| `length` | Độ dài của list, object hoặc văn bản |
| `first`, `last` | Phần tử đầu hoặc cuối của list |
| `default("text")` | `text` khi giá trị rỗng |
| `join(", ")` | Nối các phần tử list bằng dấu phân cách |
| `truncate(80)` | Cắt văn bản còn 80 ký tự |

Argument của MCP (và `text` của Decision) đúng bằng một tham chiếu thì giữ
nguyên kiểu của giá trị, nên `{{state.items | length}}` truyền đi một số.

## Trong trình soạn thảo

Tham chiếu hiện thành tag. Gõ `{{` để chọn field của state, gõ `|` bên trong
tham chiếu để chọn filter. Nhấp đúp vào tag để sửa dạng văn bản. Field không
có trong state hoặc filter không tồn tại sẽ đỏ, và Lưu sẽ liệt kê chúng. Run
từ chối tham chiếu sai với `TEMPLATE_REF_INVALID`.
