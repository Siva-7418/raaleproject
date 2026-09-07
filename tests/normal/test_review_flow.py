import pytest
from backend.app.models.schemas import DecisionSubmission

def test_prototype_review_flow_approval_with_evidence(db_conn, review_service):
    # Fetch a low-risk entitlement item
    items = review_service.get_review_items(db_conn, mode="prototype")
    clean_item = next(i for i in items if i.evidence and i.evidence.risk_score == 0)

    sub = DecisionSubmission(
        entitlement_id=clean_item.entitlement_id,
        reviewer_id="rev-dept-head",
        review_mode="prototype",
        decision="approve"
    )

    record = review_service.submit_decision(db_conn, sub)
    assert record.decision == "approve"
    assert record.is_rubber_stamp is False
    assert record.evidence_shown["risk_score"] == 0
    assert "flagged_anomalies" in record.evidence_shown

def test_baseline_review_flow_bulk_approve(db_conn, review_service):
    items = review_service.get_review_items(db_conn, mode="baseline")
    target_ids = [i.entitlement_id for i in items[:5]]

    records = review_service.bulk_submit_baseline(
        db_conn,
        __import__("backend.app.models.schemas", fromlist=["BulkDecisionSubmission"]).BulkDecisionSubmission(entitlement_ids=target_ids)
    )
    assert len(records) == 5
    for r in records:
        assert r.review_mode == "baseline"
        assert r.is_rubber_stamp is True
        assert r.evidence_shown["evidence_provided"] is False
