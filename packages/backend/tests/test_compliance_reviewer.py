"""Deterministic compliance reviewer — Step 7.1."""

from app.services.compliance.reviewer import ComplianceRiskLevel, review_meeting_summary_draft


def test_clean_draft_is_low_risk():
    r = review_meeting_summary_draft(
        summary="Discussed goals and next steps; no product recommendations finalized.",
        action_items=[{"task": "Send disclosure packet", "owner": None, "due": None}],
    )
    assert r.risk_level == ComplianceRiskLevel.LOW
    assert not r.findings


def test_risk_free_language_is_high_risk():
    r = review_meeting_summary_draft(
        summary="We described the strategy as risk-free for the client.",
        action_items=[],
    )
    assert r.risk_level == ComplianceRiskLevel.HIGH
    assert r.prohibited_hits


def test_forward_looking_without_disclosure_is_medium():
    r = review_meeting_summary_draft(
        summary="We believe this allocation will double in five years.",
        action_items=[],
    )
    assert r.risk_level == ComplianceRiskLevel.MEDIUM
    assert r.disclosure_gaps


def test_forward_looking_with_disclosure_is_low():
    r = review_meeting_summary_draft(
        summary=(
            "Hypothetical illustration only — past performance does not guarantee future results; "
            "risk of loss applies. We discussed possible scenarios."
        ),
        action_items=[],
    )
    assert r.risk_level == ComplianceRiskLevel.LOW
