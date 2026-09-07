import pytest
from backend.app.models.schemas import IdentitySchema, EntitlementSchema
from backend.app.services.rules_engine import RulesEngine

def test_evaluate_clean_entitlement(db_conn, rules_engine):
    # Fetch an active student entitlement
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
               i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
        FROM entitlements e
        JOIN identities i ON e.identity_id = i.id
        WHERE i.role_type = 'student' AND i.status = 'active' AND e.resource = 'library_catalog'
        LIMIT 1
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
    assert snapshot is not None
    assert snapshot.user_status == "active"
    assert snapshot.risk_score < 50
