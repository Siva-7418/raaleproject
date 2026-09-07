import json
import uuid
import datetime
import sqlite3
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from backend.app.models.schemas import (
    EntitlementReviewItem, IdentitySchema, EntitlementSchema,
    DecisionSubmission, ReviewDecisionRecord, BulkDecisionSubmission
)
from backend.app.services.rules_engine import RulesEngine

class ReviewService:
    def __init__(self, rules_engine: Optional[RulesEngine] = None):
        self.rules_engine = rules_engine or RulesEngine()

    def get_review_items(
        self,
        conn: sqlite3.Connection,
        mode: str = "prototype",
        department_filter: Optional[str] = None
    ) -> List[EntitlementReviewItem]:
        cursor = conn.cursor()

        query = """
            SELECT
                e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
                i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
            FROM entitlements e
            JOIN identities i ON e.identity_id = i.id
            LEFT JOIN review_decisions d ON e.id = d.entitlement_id AND d.review_mode = ?
            WHERE d.id IS NULL
        """
        params = [mode]

        if department_filter:
            query += " AND i.department = ?"
            params.append(department_filter)

        query += " ORDER BY e.id ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        items: List[EntitlementReviewItem] = []

        for r in rows:
            identity = IdentitySchema(
                id=r["ident_id"],
                name=r["name"],
                role_type=r["role_type"],
                department=r["department"],
                start_date=r["start_date"],
                end_date=r["end_date"],
                status=r["status"]
            )
            entitlement = EntitlementSchema(
                id=r["ent_id"],
                identity_id=r["ident_id"],
                resource=r["resource"],
                privilege_level=r["privilege_level"],
                granted_date=r["granted_date"],
                granted_by=r["granted_by"],
                justification=r["justification"],
                source_system=r["source_system"]
            )

            evidence = None
            if mode == "prototype":
                evidence = self.rules_engine.evaluate_entitlement(conn, identity, entitlement)

            items.append(EntitlementReviewItem(
                entitlement_id=entitlement.id,
                identity=identity,
                entitlement=entitlement,
                evidence=evidence
            ))

        if mode == "prototype":
            items.sort(key=lambda x: (x.evidence.risk_score if x.evidence else 0), reverse=True)

        return items

    def submit_decision(
        self,
        conn: sqlite3.Connection,
        submission: DecisionSubmission
    ) -> ReviewDecisionRecord:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.id as ent_id, e.resource, e.privilege_level, e.granted_date, e.granted_by, e.justification, e.source_system,
                   i.id as ident_id, i.name, i.role_type, i.department, i.start_date, i.end_date, i.status
            FROM entitlements e
            JOIN identities i ON e.identity_id = i.id
            WHERE e.id = ?
        """, (submission.entitlement_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Entitlement {submission.entitlement_id} not found")

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

        cfg = self.rules_engine.config
        is_rubber_stamp = False
        reason_text = submission.reason_text

        if submission.review_mode == "prototype":
            evidence = self.rules_engine.evaluate_entitlement(conn, identity, entitlement)
            evidence_shown_dict = evidence.model_dump()
            has_anomalies = len(evidence.flagged_anomalies) > 0 or evidence.risk_score > 0

            if submission.decision == "revoke" and cfg.require_reason_on_revoke:
                if not reason_text or not reason_text.strip():
                    if not submission.bypass_reason_check:
                        raise HTTPException(status_code=400, detail="Reason text is required when revoking access.")
                    else:
                        is_rubber_stamp = True
                        reason_text = "[BYPASSED_REASON] Revoked without required justification."

            elif submission.decision == "approve" and has_anomalies and cfg.require_reason_on_override:
                if not reason_text or not reason_text.strip():
                    if not submission.bypass_reason_check:
                        raise HTTPException(status_code=400, detail=f"Reason text is required when approving an entitlement with flagged anomalies: {', '.join(evidence.flagged_anomalies)}")
                    else:
                        is_rubber_stamp = True
                        reason_text = "[BYPASSED_REASON] Approved flagged anomaly without required justification."
        else:
            evidence_shown_dict = {
                "mode": "baseline_spreadsheet",
                "evidence_provided": False,
                "note": "Spreadsheet baseline review mode - zero evidence or risk context displayed to reviewer."
            }
            if submission.decision == "approve" and (not reason_text or not reason_text.strip()):
                is_rubber_stamp = True

        decision_id = f"DEC-{uuid.uuid4().hex[:10].upper()}"
        ts_now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO review_decisions (id, entitlement_id, reviewer_id, review_mode, decision, evidence_shown, reason_text, is_rubber_stamp, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id,
            submission.entitlement_id,
            submission.reviewer_id,
            submission.review_mode,
            submission.decision,
            json.dumps(evidence_shown_dict),
            reason_text,
            1 if is_rubber_stamp else 0,
            ts_now
        ))

        conn.commit()

        return ReviewDecisionRecord(
            id=decision_id,
            entitlement_id=submission.entitlement_id,
            reviewer_id=submission.reviewer_id,
            review_mode=submission.review_mode,
            decision=submission.decision,
            evidence_shown=evidence_shown_dict,
            reason_text=reason_text,
            is_rubber_stamp=is_rubber_stamp,
            timestamp=ts_now
        )

    def bulk_submit_baseline(
        self,
        conn: sqlite3.Connection,
        bulk: BulkDecisionSubmission
    ) -> List[ReviewDecisionRecord]:
        records = []
        for ent_id in bulk.entitlement_ids:
            sub = DecisionSubmission(
                entitlement_id=ent_id,
                reviewer_id=bulk.reviewer_id,
                review_mode="baseline",
                decision=bulk.decision,
                reason_text=bulk.reason_text,
                bypass_reason_check=True
            )
            records.append(self.submit_decision(conn, sub))
        return records
