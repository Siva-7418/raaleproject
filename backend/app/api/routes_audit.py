import json
from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from backend.app.db.database import get_connection

router = APIRouter(prefix="/api/audit", tags=["Audit & Metrics"])

@router.get("/decisions")
def get_audit_decisions(
    mode: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT d.id, d.entitlement_id, d.reviewer_id, d.review_mode, d.decision,
                   d.evidence_shown, d.reason_text, d.is_rubber_stamp, d.timestamp,
                   e.resource, e.privilege_level, i.name as identity_name, i.role_type, i.department
            FROM review_decisions d
            JOIN entitlements e ON d.entitlement_id = e.id
            JOIN identities i ON e.identity_id = i.id
        """
        params = []
        if mode:
            query += " WHERE d.review_mode = ?"
            params.append(mode)

        query += " ORDER BY d.timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result = []
        for r in rows:
            record = dict(r)
            try:
                record["evidence_shown"] = json.loads(record["evidence_shown"])
            except Exception:
                pass
            record["is_rubber_stamp"] = bool(record["is_rubber_stamp"])
            result.append(record)

        return result
    finally:
        conn.close()

@router.get("/metrics")
def get_audit_metrics():
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Count per review mode
        cursor.execute("""
            SELECT review_mode,
                   COUNT(*) as total_decisions,
                   SUM(CASE WHEN is_rubber_stamp = 1 THEN 1 ELSE 0 END) as rubber_stamp_count,
                   SUM(CASE WHEN decision = 'approve' THEN 1 ELSE 0 END) as approved_count,
                   SUM(CASE WHEN decision = 'revoke' THEN 1 ELSE 0 END) as revoked_count,
                   SUM(CASE WHEN decision = 'flag_for_follow_up' THEN 1 ELSE 0 END) as flagged_count
            FROM review_decisions
            GROUP BY review_mode
        """)
        rows = cursor.fetchall()

        metrics = {}
        for r in rows:
            m_mode = r["review_mode"]
            total = r["total_decisions"]
            rubber = r["rubber_stamp_count"]
            pct = round((rubber / total * 100.0), 2) if total > 0 else 0.0
            metrics[m_mode] = {
                "total_decisions": total,
                "rubber_stamp_count": rubber,
                "blanket_approval_rate_pct": pct,
                "approved_count": r["approved_count"],
                "revoked_count": r["revoked_count"],
                "flagged_count": r["flagged_count"]
            }

        return metrics
    finally:
        conn.close()
