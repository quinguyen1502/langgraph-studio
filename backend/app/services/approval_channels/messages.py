"""Chat texts of approval requests, outcomes and identity codes in English and Vietnamese (TASK-0022 follow-up).

The request and the edited message follow the run owner's language (users.lang, set by the studio's language
switcher); a private answer to the person who pressed a button follows theirs. Unknown / unset: English.
"""
from typing import Optional

LANGS = ("en", "vi")
TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "title": "Approval needed", "workflow": "Workflow: {v}", "step": "Step: {v}", "question": "Question: {v}", "run": "Run: {v}",
        "expires": "Expires: {v}", "open": "Open in LangGraph Studio", "approve": "Approve", "reject": "Reject",
        "approved_by": "✅ Approved by {who}", "rejected_by": "❌ Rejected by {who}", "at": "{text} at {when}",
        "answered": "Answered in LangGraph Studio", "cancelled": "The run was cancelled", "expired": "The request expired",
        "finished": "The run went on without this request",
        "code": "LangGraph Studio verification code: {code}\nIt expires in {minutes} min. If you did not ask for it, ignore this message.",
        "APPROVAL_TOKEN_INVALID": "Invalid approval button", "APPROVAL_TOKEN_EXPIRED": "This approval request has expired",
        "APPROVAL_ALREADY_DECIDED": "This request was already answered",
        "APPROVAL_IDENTITY_UNKNOWN": "Link and verify your {kind} account in LangGraph Studio (Settings → My accounts) to approve",
        "APPROVAL_FORBIDDEN": "You are not allowed to approve this run",
    },
    "vi": {
        "title": "Cần phê duyệt", "workflow": "Workflow: {v}", "step": "Bước: {v}", "question": "Câu hỏi: {v}", "run": "Lượt chạy: {v}",
        "expires": "Hết hạn: {v}", "open": "Mở trong LangGraph Studio", "approve": "Duyệt", "reject": "Từ chối",
        "approved_by": "✅ {who} đã duyệt", "rejected_by": "❌ {who} đã từ chối", "at": "{text} lúc {when}",
        "answered": "Đã trả lời trong LangGraph Studio", "cancelled": "Lượt chạy đã bị huỷ", "expired": "Yêu cầu đã hết hạn",
        "finished": "Lượt chạy đã tiếp tục mà không cần yêu cầu này",
        "code": "Mã xác minh LangGraph Studio: {code}\nMã hết hạn sau {minutes} phút. Nếu bạn không yêu cầu, hãy bỏ qua tin nhắn này.",
        "APPROVAL_TOKEN_INVALID": "Nút phê duyệt không hợp lệ", "APPROVAL_TOKEN_EXPIRED": "Yêu cầu phê duyệt này đã hết hạn",
        "APPROVAL_ALREADY_DECIDED": "Yêu cầu này đã được trả lời",
        "APPROVAL_IDENTITY_UNKNOWN": "Hãy liên kết và xác minh tài khoản {kind} trong LangGraph Studio (Cài đặt → Tài khoản của tôi) để phê duyệt",
        "APPROVAL_FORBIDDEN": "Bạn không có quyền phê duyệt lượt chạy này",
    },
}


def lang_of(user) -> str:
    """A user's chat language (None / unknown -> en)."""
    v = getattr(user, "lang", None)
    return v if v in LANGS else "en"


def text(lang: Optional[str], key: str, **kw) -> str:
    t = TEXTS.get(lang or "en", TEXTS["en"]).get(key) or TEXTS["en"].get(key) or key
    return t.format(**kw) if kw else t
