"""Deterministic compliance screening for AI meeting-summary drafts — Step 7.1."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

HIGH_RISK = "high"
MEDIUM_RISK = "medium"
LOW_RISK = "low"


class ComplianceRiskLevel(str, Enum):
    LOW = LOW_RISK
    MEDIUM = MEDIUM_RISK
    HIGH = HIGH_RISK


@dataclass(frozen=True, slots=True)
class ComplianceReviewResult:
    risk_level: ComplianceRiskLevel
    findings: tuple[str, ...]
    prohibited_hits: tuple[str, ...]
    disclosure_gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "findings": list(self.findings),
            "prohibited_hits": list(self.prohibited_hits),
            "disclosure_gaps": list(self.disclosure_gaps),
        }


_FORBIDDEN: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (re.compile(r"\brisk[- ]free\b", re.I), "risk-free claim"),
    (re.compile(r"\bno risk\b", re.I), "no-risk claim"),
    (
        re.compile(r"\bguaranteed\s+(?:return|returns|profit|income|yield)\b", re.I),
        "guaranteed return language",
    ),
    (re.compile(r"\b(?:can't|cannot)\s+lose\b", re.I), "loss avoidance promise"),
    (re.compile(r"\binsider\b", re.I), "insider reference"),
)

_DISCLOSURE_MARKERS: Final[tuple[str, ...]] = (
    "past performance",
    "no guarantee",
    "not guarantee",
    "does not guarantee",
    "risk of loss",
    "hypothetical",
    "not fdic insured",
    "not insured",
)

_FORWARD_LOOKING: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bwill\s+(?:double|triple|earn)\b", re.I),
    re.compile(r"\bsure\s+thing\b", re.I),
    re.compile(r"\bguaranteed\b", re.I),
)


def review_meeting_summary_draft(
    *,
    summary: str,
    action_items: list[dict[str, Any]] | None = None,
) -> ComplianceReviewResult:
    """Score draft text using forbidden-phrase rules and disclosure heuristics."""
    parts: list[str] = [summary.strip()]
    for item in action_items or []:
        t = str(item.get("task") or "").strip()
        if t:
            parts.append(t)
    blob = "\n".join(parts)
    low = blob.lower()

    prohibited_hits: list[str] = []
    for rx, label in _FORBIDDEN:
        if rx.search(low):
            prohibited_hits.append(label)

    disclosure_gaps: list[str] = []
    has_disclosure = any(m in low for m in _DISCLOSURE_MARKERS)
    if not has_disclosure and any(p.search(blob) for p in _FORWARD_LOOKING):
        disclosure_gaps.append(
            "forward-looking or strong promise language without standard risk disclosures",
        )

    findings: list[str] = [f"Prohibited pattern: {h}" for h in prohibited_hits]
    findings.extend(f"Disclosure gap: {g}" for g in disclosure_gaps)

    if prohibited_hits:
        risk = ComplianceRiskLevel.HIGH
    elif disclosure_gaps:
        risk = ComplianceRiskLevel.MEDIUM
    else:
        risk = ComplianceRiskLevel.LOW

    return ComplianceReviewResult(
        risk_level=risk,
        findings=tuple(findings),
        prohibited_hits=tuple(prohibited_hits),
        disclosure_gaps=tuple(disclosure_gaps),
    )


__all__ = [
    "HIGH_RISK",
    "LOW_RISK",
    "MEDIUM_RISK",
    "ComplianceReviewResult",
    "ComplianceRiskLevel",
    "review_meeting_summary_draft",
]
