"""Deterministic relevance gate: avoid unrelated LLM spend (keywords only, zero model calls)."""

from __future__ import annotations

OFF_TOPIC_NOTICE = (
    "此助理僅能協助 Advisor Flow AI 營運工作區內的議題——例如會議紀錄與摘要、客戶資料與後續行動、"
    "文件上傳與解讀、工作流程與任務進度，以及與合規、簽核或稽核有關的諮詢。"
    "\n您剛才的問題與本平台場景無關，為節約運算資源恕無法回覆；請改為圍繞會議／客戶／文件／流程／"
    "合規等實際工作情境提問。"
    "\n\nThis assistant only covers this platform's advisor operations (meetings, clients, "
    "documents, workflows, compliance, and approvals). Please ask something within that scope."
)


def _haystack(payload: str) -> str:
    """Lower ASCII for insensitive match; preserves CJK and other Unicode."""
    return "".join(ch.lower() if ch.isascii() else ch for ch in payload)


# Substrings intentionally multi-char where short English tokens could false-positive (e.g. "in").
_IN_SCOPE_NEEDLES = frozenset(
    (
        # Product / UX
        "advisor flow",
        "advisorflow",
        "這個平台",
        "本平台",
        "工作區",
        "應用",
        # English domain
        "meeting",
        "transcript",
        "workflow",
        "client",
        "document",
        "compliance",
        "approval",
        "audit trail",
        "audit",
        "portfolio",
        "wealth",
        "onboarding",
        "follow-up",
        "follow up",
        "action item",
        "summary",
        "summarize",
        "financial",
        "investment",
        "pdf",
        "upload",
        "embedding",
        "vector",
        "crm",
        "kyc",
        "regulation",
        "advisory",
        "fiduciary",
        # Chinese domain
        "會議",
        "會面",
        "客戶",
        "檔案",
        "文件",
        "報告",
        "合規",
        "稽核",
        "簽核",
        "審批",
        "顧問",
        "理財",
        "投資",
        "資產",
        "組合",
        "摘要",
        "逐字稿",
        "上傳",
        "流程",
        "法遵",
    )
)


def user_message_covers_workspace_scope(payload: str) -> bool:
    """Return True only when deterministic signals suggest an advisor-ops question."""
    if not isinstance(payload, str):
        return False
    condensed = "".join(payload.split())
    if len(condensed) < 4:
        return False
    hay = _haystack(payload)
    return any(n in hay for n in _IN_SCOPE_NEEDLES)
