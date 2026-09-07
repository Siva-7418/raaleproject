import pytest
from fastapi import HTTPException
from backend.app.models.schemas import DecisionSubmission, IdentitySchema, EntitlementSchema

def test_edge_case_1_no_usage_history(db_conn, rules_engine):
    """EDGE CASE 1: No usage history at all (e.g. newly onboarded temp researcher).
    System must label usage as INSUFFICIENT_DATA and avoid false positive dormant alerts."""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
               i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
        FROM entitlements e
        JOIN identities i ON e.identity_id = i.id
        WHERE i.id = 'USER-EDGE-01'
    """)
    row = cursor.fetchone()
    assert row is not None

    identity = IdentitySchema(
        id=row["ident_id"], name=row["name"], role_type=row["role_type"],
        department=row["department"], start_date=row["start_date"],
        end_date=row["end_date"], status=row["status"]
    )
    entitlement = EntitlementSchema(
        id=row["ent_id"], identity_id=row["ident_id"], resource=row["resource"],
        privilege_level=row["privilege_level"], granted_date=row["granted_date"],
        granted_by=row["granted_by"], justification=row["justification"],
        source_system=row["source_system"]
    )

    snapshot = rules_engine.evaluate_entitlement(db_conn, identity, entitlement)
    assert snapshot.usage_status == "INSUFFICIENT_DATA"
    assert snapshot.days_since_last_use is None
    # Must NOT have UNUSED_ENTITLEMENT flag
    assert not any("UNUSED_ENTITLEMENT" in f for f in snapshot.flagged_anomalies)
    assert any("INSUFFICIENT_USAGE_DATA" in f for f in snapshot.flagged_anomalies)

def test_edge_case_2_offboarded_active_access(db_conn, rules_engine):
    """EDGE CASE 2: Offboarded identity holding active access.
    Must trigger a critical high-severity flag regardless of usage recency."""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
               i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
        FROM entitlements e
        JOIN identities i ON e.identity_id = i.id
        WHERE i.id = 'USER-EDGE-02'
    """)
    row = cursor.fetchone()
    assert row is not None

    identity = IdentitySchema(
        id=row["ident_id"], name=row["name"], role_type=row["role_type"],
        department=row["department"], start_date=row["start_date"],
        end_date=row["end_date"], status=row["status"]
    )
    entitlement = EntitlementSchema(
        id=row["ent_id"], identity_id=row["ident_id"], resource=row["resource"],
        privilege_level=row["privilege_level"], granted_date=row["granted_date"],
        granted_by=row["granted_by"], justification=row["justification"],
        source_system=row["source_system"]
    )

    snapshot = rules_engine.evaluate_entitlement(db_conn, identity, entitlement)
    assert snapshot.user_status == "offboarded"
    assert any("OFFBOARDED_ACTIVE_ACCESS" in f for f in snapshot.flagged_anomalies)
    assert snapshot.risk_score >= 50

def test_edge_case_3_adversarial_rubber_stamping_rejection(db_conn, review_service):
    """EDGE CASE 3: Adversarial rubber-stamping - approving a flagged item without reason.
    System must reject the decision with HTTP 400. If forced via API bypass, decision must be logged as rubber stamp."""
    # Attempt approving offboarded entitlement without reason
    sub = DecisionSubmission(
        entitlement_id="ENT-EDGE-02",
        reviewer_id="rev-adversary",
        review_mode="prototype",
        decision="approve",
        reason_text=None,
        bypass_reason_check=False
    )

    # 1. Verify API Rejection
    with pytest.raises(HTTPException) as exc_info:
        review_service.submit_decision(db_conn, sub)
    assert exc_info.value.status_code == 400
    assert "Reason text is required" in exc_info.value.detail

    # 2. Verify Forced Bypass Audit Trail Logging
    sub_bypassed = DecisionSubmission(
        entitlement_id="ENT-EDGE-02",
        reviewer_id="rev-adversary",
        review_mode="prototype",
        decision="approve",
        reason_text=None,
        bypass_reason_check=True
    )
    record = review_service.submit_decision(db_conn, sub_bypassed)
    assert record.is_rubber_stamp is True
    assert "[BYPASSED_REASON]" in record.reason_text

def test_edge_case_4_peer_baseline_collapse(db_conn, rules_engine):
    """EDGE CASE 4: Peer baseline collapse (n <= 2 in small department/role).
    System must suppress raw peer deviation alert and mark baseline as collapsed."""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
               i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
        FROM entitlements e
        JOIN identities i ON e.identity_id = i.id
        WHERE i.id = 'USER-EDGE-04'
    """)
    row = cursor.fetchone()
    assert row is not None

    identity = IdentitySchema(
        id=row["ident_id"], name=row["name"], role_type=row["role_type"],
        department=row["department"], start_date=row["start_date"],
        end_date=row["end_date"], status=row["status"]
    )
    entitlement = EntitlementSchema(
        id=row["ent_id"], identity_id=row["ident_id"], resource=row["resource"],
        privilege_level=row["privilege_level"], granted_date=row["granted_date"],
        granted_by=row["granted_by"], justification=row["justification"],
        source_system=row["source_system"]
    )

    snapshot = rules_engine.evaluate_entitlement(db_conn, identity, entitlement)
    assert snapshot.peer_baseline_collapsed is True
    assert any("PEER_BASELINE_COLLAPSED" in f for f in snapshot.flagged_anomalies)
    # Must NOT have raw UNUSUAL_FOR_ROLE flag based on n=1
    assert not any("UNUSUAL_FOR_ROLE" in f for f in snapshot.flagged_anomalies)

def test_edge_case_5_conflicting_duplicate_entitlements(db_conn, rules_engine):
    """EDGE CASE 5: Conflicting / Duplicate entitlements across source systems.
    System must flag duplicate entitlement conflict."""
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
               i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
        FROM entitlements e
        JOIN identities i ON e.identity_id = i.id
        WHERE i.id = 'USER-EDGE-05' AND e.id = 'ENT-EDGE-05A'
    """)
    row = cursor.fetchone()
    assert row is not None

    identity = IdentitySchema(
        id=row["ident_id"], name=row["name"], role_type=row["role_type"],
        department=row["department"], start_date=row["start_date"],
        end_date=row["end_date"], status=row["status"]
    )
    entitlement = EntitlementSchema(
        id=row["ent_id"], identity_id=row["ident_id"], resource=row["resource"],
        privilege_level=row["privilege_level"], granted_date=row["granted_date"],
        granted_by=row["granted_by"], justification=row["justification"],
        source_system=row["source_system"]
    )

    snapshot = rules_engine.evaluate_entitlement(db_conn, identity, entitlement)
    assert snapshot.source_system_conflict is True
    assert any("DUPLICATE_ENTITLEMENT_CONFLICT" in f for f in snapshot.flagged_anomalies)
