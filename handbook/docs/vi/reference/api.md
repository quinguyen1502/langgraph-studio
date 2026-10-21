# HTTP API

UI dùng cùng API với mọi client khác. Trang OpenAPI tương tác nằm ở `/docs` của
API (<http://localhost:8000/docs> khi phát triển).

## Envelope

Mọi response REST đều là một envelope:

```jsonc
// success
{"success": true, "data": <payload>, "error": null}
// error
{"success": false, "data": null, "error": {"code": "AUTH_INVALID_CREDENTIALS", "message": "Incorrect email or password", "details": null}}
```

`code` dạng `UPPER_SNAKE` ổn định và là hợp đồng giữa hai bên; `message` là
tiếng Anh, cho người đọc và log. Client dịch theo `code` và dùng `message` khi
không có bản dịch. Danh sách mã ở [Mã lỗi](errors.md).

## Xác thực

| Client | Cách |
| --- | --- |
| API client | `POST /api/auth/login` → `data.token`; then `Authorization: Bearer <token>` |
| Trình duyệt | Cookie `studio_session`, cộng `X-Requested-With: studio` cho request ghi |
| WebSocket | Cookie, hoặc `?token=<token>` |
| Trigger workflow | `Authorization: Bearer wft_…`, chỉ cho `/api/hooks/*` |

## Chạy workflow qua WebSocket

```text
WS /ws/run
→ {"workflow_id": "…", "input": {…}}             chạy một workflow đã lưu
→ {"resume_run_id": "…", "response": "approved"}  trả lời node Human đang chờ
→ {"workflow_id": "…", "workflow": {…}, …}       chạy graph chưa lưu của trình soạn thảo
→ {"workflow_id": "…", "input": {…}, "steps": 1}  dừng sau một superstep
→ {"workflow_id": "…", "input": {…}, "until": "node_id"}  dừng sau node đó
→ {"type": "cancel"}                              huỷ run hiện tại
← {"type": "run_started", …} {"type": "node_started", …} {"type": "node_token", …}
  {"type": "node_finished", …} … {"type": "run_finished", …}
```

## Endpoint

??? abstract "Xác thực và tài khoản"

    ```text
    POST   /api/auth/register
    POST   /api/auth/login
    POST   /api/auth/logout
    GET    /api/auth/options
    POST   /api/auth/password-reset
    POST   /api/auth/password-reset/confirm
    GET    /api/me
    POST   /api/me/password
    ```

??? abstract "Workflow, phiên bản, chia sẻ"

    ```text
    GET    /api/workflows                       POST   /api/workflows
    GET    /api/workflows/{wid}                 PATCH  /api/workflows/{wid}
    DELETE /api/workflows/{wid}                 POST   /api/workflows/{wid}/duplicate
    GET    /api/workflows/{wid}/dependents      POST   /api/validate
    GET    /api/workflows/{wid}/versions        GET    /api/workflows/{wid}/versions/{n}
    GET    /api/workflows/{wid}/versions/diff   POST   /api/workflows/{wid}/versions/{n}/restore
    GET    /api/workflows/{wid}/shares          PUT    /api/workflows/{wid}/shares
    DELETE /api/workflows/{wid}/shares/{target}
    PUT    /api/workflows/{wid}/team-shares     DELETE /api/workflows/{wid}/team-shares/{tid}
    GET    /api/workflows/{wid}/transfer        POST   /api/workflows/{wid}/transfer
    ```

??? abstract "Runs"

    ```text
    GET    /api/workflows/{wid}/runs          (?tests=true: các run test)
    GET    /api/runs/pending
    POST   /api/runs/{run_id}/cancel
    WS     /ws/run
    ```

??? abstract "API trigger và lần gửi"

    ```text
    GET    /api/workflows/{wid}/tokens          POST   /api/workflows/{wid}/tokens
    DELETE /api/workflows/{wid}/tokens/{tid}    POST   /api/workflows/{wid}/tokens/{tid}/rotate-secret
    POST   /api/hooks/workflows/{wid}/runs      GET    /api/hooks/workflows/{wid}/runs/{run_id}
    GET    /api/workflows/{wid}/deliveries      POST   /api/workflows/{wid}/deliveries/{did}/redeliver
    ```

??? abstract "Lịch chạy"

    ```text
    GET    /api/workflows/{wid}/schedules       POST   /api/workflows/{wid}/schedules
    PATCH  /api/workflows/{wid}/schedules/{sid} DELETE /api/workflows/{wid}/schedules/{sid}
    POST   /api/schedules/preview
    ```

??? abstract "Kiểm thử workflow"

    ```text
    GET    /api/workflows/{wid}/tests          POST   /api/workflows/{wid}/tests
    PUT    /api/workflows/{wid}/tests/{tid}    DELETE /api/workflows/{wid}/tests/{tid}
    POST   /api/workflows/{wid}/tests/run      GET    /api/workflows/{wid}/tests/runs/{sid}
    POST   /api/workflows/{wid}/tests/runs/{sid}/cancel
    ```

??? abstract "Mẫu"

    ```text
    GET    /api/templates                       POST   /api/templates
    POST   /api/templates/import                DELETE /api/templates/{tid}
    GET    /api/templates/{tid}/export          POST   /api/templates/{tid}/use
    ```

??? abstract "Credential và nhà cung cấp"

    ```text
    GET    /api/providers                       POST   /api/providers/{pid}/test
    GET    /api/credentials                     POST   /api/credentials
    PUT    /api/credentials/{cid}               DELETE /api/credentials/{cid}
    GET    /api/credentials/{cid}/models        POST   /api/credentials/{cid}/embeddings/test
    ```

??? abstract "Kho tri thức"

    ```text
    GET    /api/knowledge-bases                 POST   /api/knowledge-bases
    GET    /api/knowledge-bases/{kid}           PUT    /api/knowledge-bases/{kid}
    DELETE /api/knowledge-bases/{kid}           POST   /api/knowledge-bases/{kid}/documents
    DELETE /api/knowledge-bases/{kid}/documents/{did}
    POST   /api/knowledge-bases/{kid}/reindex   POST   /api/knowledge-bases/{kid}/search
    ```

??? abstract "Máy chủ MCP"

    ```text
    GET    /api/mcp/servers                     POST   /api/mcp/servers
    PUT    /api/mcp/servers/{sid}               DELETE /api/mcp/servers/{sid}
    POST   /api/mcp/servers/{sid}/discover
    ```

??? abstract "Duyệt và danh tính"

    ```text
    GET    /api/approvals/channels              POST   /api/approvals/channels
    PUT    /api/approvals/channels/{cid}        DELETE /api/approvals/channels/{cid}
    POST   /api/approvals/channels/{cid}/test   POST   /api/approvals/channels/{cid}/register-webhook
    POST   /api/approvals/callback/{kind}       GET|POST /api/approvals/callback/{kind}/{cid}
    GET    /api/approvals/identities            PUT    /api/approvals/identities
    POST   /api/approvals/identities/{kind}/send-code
    POST   /api/approvals/identities/{kind}/verify
    GET    /api/approvals/link                  POST   /api/approvals/link
    GET    /api/approvals/audit
    GET    /api/approvals/inbox                 POST   /api/approvals/inbox/{run_id}
    GET    /api/approvals/slack/oauth           POST   /api/approvals/slack/oauth/start
    GET    /api/approvals/slack/oauth/callback
    ```

??? abstract "Thông báo"

    ```text
    GET    /api/notifications                   POST   /api/notifications/{nid}/read
    POST   /api/notifications/read-all
    GET    /api/notifications/preferences       PUT    /api/notifications/preferences
    WS     /ws/notifications
    ```

??? abstract "Người dùng, nhóm, quản trị"

    ```text
    GET    /api/roles
    GET    /api/admin/users                     PATCH  /api/admin/users/{target}
    DELETE /api/admin/users/{target}            POST   /api/admin/users/{target}/password-reset
    GET    /api/admin/policy                    PUT    /api/admin/policy
    GET    /api/admin/audit
    GET    /api/teams                           POST   /api/teams
    PATCH  /api/teams/{tid}                     DELETE /api/teams/{tid}
    POST   /api/teams/{tid}/members             DELETE /api/teams/{tid}/members/{member}
    ```

??? abstract "Import, code, meta"

    ```text
    POST   /api/import                          GET    /api/import/{jid}
    POST   /api/import/{jid}/finalize
    POST   /api/code/test
    GET    /api/health                          GET    /api/meta/runtime
    GET    /api/tools
    ```
