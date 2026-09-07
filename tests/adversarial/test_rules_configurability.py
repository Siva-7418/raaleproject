import pytest
from backend.app.models.schemas import RulesConfigSchema, IdentitySchema, EntitlementSchema
from backend.app.services.rules_engine import RulesEngine

def test_rules_engine_runtime_configurability(db_conn):
    engine = RulesEngine()
    
    # 1. Evaluate all active entitlements under default 90-day threshold
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
               i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
        FROM entitlements e
        JOIN identities i ON e.identity_id = i.id
        WHERE i.status = 'active'
    """)
    rows = cursor.fetchall()

    dormant_90 = 0
    for r in rows:
        ident = IdentitySchema(id=r["ident_id"], name=r["name"], role_type=r["role_type"], department=r["department"], start_date=r["start_date"], end_date=r["end_date"], status=r["status"])
        ent = EntitlementSchema(id=r["ent_id"], identity_id=r["ident_id"], resource=r["resource"], privilege_level=r["privilege_level"], granted_date=r["granted_date"], granted_by=r["granted_by"], justification=r["justification"], source_system=r["source_system"])
        snap = engine.evaluate_entitlement(db_conn, ident, ent)
        if snap.usage_status == "UNUSED":
            dormant_90 += 1

    # 2. Lower inactivity threshold to 30 days
    stricter_config = RulesConfigSchema(
        unused_threshold_days=30,
        peer_deviation_threshold_pct=10.0,
        high_risk_resources=["finance_system", "student_records", "research_data_vault"],
        require_reason_on_override=True,
        require_reason_on_revoke=True
    )
    engine.config = stricter_config

    dormant_30 = 0
    for r in rows:
        ident = IdentitySchema(id=r["ident_id"], name=r["name"], role_type=r["role_type"], department=r["department"], start_date=r["start_date"], end_date=r["end_date"], status=r["status"])
        ent = EntitlementSchema(id=r["ent_id"], identity_id=r["ident_id"], resource=r["resource"], privilege_level=r["privilege_level"], granted_date=r["granted_date"], granted_by=r["granted_by"], justification=r["justification"], source_system=r["source_system"])
        snap = engine.evaluate_entitlement(db_conn, ident, ent)
        if snap.usage_status == "UNUSED":
            dormant_30 += 1

    # 3. Assert that lowering threshold increased the number of flagged dormant entitlements
    assert dormant_30 > dormant_90, f"Expected 30-day threshold dormant count ({dormant_30}) to exceed 90-day count ({dormant_90})"
