import yaml
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import sqlite3

from backend.app.models.schemas import RulesConfigSchema, EvidenceSnapshot, EntitlementSchema, IdentitySchema

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = BASE_DIR / "config" / "rules.yaml"

class RulesEngine:
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or CONFIG_PATH
        self.config = self.load_config()

    def load_config(self) -> RulesConfigSchema:
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return RulesConfigSchema(**data)
        return RulesConfigSchema()

    def update_config(self, new_config: RulesConfigSchema) -> RulesConfigSchema:
        self.config = new_config
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(new_config.model_dump(), f)
        return self.config

    def evaluate_entitlement(
        self,
        conn: sqlite3.Connection,
        identity: IdentitySchema,
        entitlement: EntitlementSchema
    ) -> EvidenceSnapshot:
        cfg = self.config
        flags: List[str] = []
        risk_score = 0

        # 1. Fetch usage logs for entitlement
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp FROM usage_events
            WHERE entitlement_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (entitlement.id,))
        last_usage_row = cursor.fetchone()

        now = datetime.datetime.now(datetime.timezone.utc)
        days_since_last_use = None
        last_used_ts = None
        usage_status = "INSUFFICIENT_DATA"

        if last_usage_row:
            last_used_ts = last_usage_row["timestamp"]
            # Parse ISO 8601 string
            dt_use = datetime.datetime.fromisoformat(last_used_ts.replace("Z", "+00:00"))
            if dt_use.tzinfo is None:
                dt_use = dt_use.replace(tzinfo=datetime.timezone.utc)
            days_since_last_use = max(0, (now - dt_use).days)

            if days_since_last_use > cfg.unused_threshold_days:
                usage_status = "UNUSED"
                flags.append(f"UNUSED_ENTITLEMENT ({days_since_last_use} days dormant > {cfg.unused_threshold_days}d threshold)")
                risk_score += 30
            else:
                usage_status = "ACTIVE"
        else:
            # EDGE CASE 1: No usage history at all
            usage_status = "INSUFFICIENT_DATA"
            flags.append("INSUFFICIENT_USAGE_DATA (No activity logs recorded since grant)")
            risk_score += 10 # Mild uncertainty bump, not false positive alert

        # 2. Check Identity Status (EDGE CASE 2: Offboarded Identity Active Access)
        user_status = identity.status
        if user_status == "offboarded":
            flags.append("OFFBOARDED_ACTIVE_ACCESS (User offboarded but privilege remains active)")
            risk_score += 50 # Critical severity flag!

        # 3. Fetch Peer Role Baseline Data (EDGE CASE 4: Baseline Collapse Guard)
        cursor.execute("""
            SELECT total_peers, peers_holding_count, peer_holding_pct, is_collapsed
            FROM peer_role_baselines
            WHERE role_type = ? AND department = ? AND resource = ? AND privilege_level = ?
        """, (identity.role_type, identity.department, entitlement.resource, entitlement.privilege_level))
        peer_row = cursor.fetchone()

        peer_holding_pct = 0.0
        peer_sample_size = 0
        peer_collapsed = False

        if peer_row:
            peer_sample_size = peer_row["total_peers"]
            peer_holding_pct = peer_row["peer_holding_pct"]
            peer_collapsed = bool(peer_row["is_collapsed"]) or (peer_sample_size <= cfg.minimum_peer_sample_size)
        else:
            # Fallback peer count if missing in baseline table
            cursor.execute("""
                SELECT COUNT(DISTINCT id) FROM identities
                WHERE role_type = ? AND department = ? AND status = 'active'
            """, (identity.role_type, identity.department))
            peer_sample_size = cursor.fetchone()[0]
            peer_collapsed = (peer_sample_size <= cfg.minimum_peer_sample_size)

        if peer_collapsed:
            flags.append(f"PEER_BASELINE_COLLAPSED (Small peer sample size n={peer_sample_size} <= {cfg.minimum_peer_sample_size}; peer deviation suppressed)")
        else:
            if peer_holding_pct < cfg.peer_deviation_threshold_pct:
                flags.append(f"UNUSUAL_FOR_ROLE (Held by only {peer_holding_pct:.1f}% of {identity.role_type} peers in {identity.department})")
                risk_score += 25

        # 4. Check Resource Risk Classification
        is_high_risk = entitlement.resource in cfg.high_risk_resources
        if is_high_risk:
            flags.append(f"HIGH_RISK_RESOURCE (Target system '{entitlement.resource}' is classified high-risk)")
            risk_score += 20

        # 5. Check Missing Justification
        is_missing_justification = not bool(entitlement.justification and entitlement.justification.strip())
        if is_missing_justification:
            flags.append("MISSING_JUSTIFICATION (No business/academic rationale was provided at grant time)")
            risk_score += 15

        # 6. Check Conflicting/Duplicate Entitlements (EDGE CASE 5)
        cursor.execute("""
            SELECT id, resource, source_system FROM entitlements
            WHERE identity_id = ? AND resource = ? AND id != ?
        """, (identity.id, entitlement.resource, entitlement.id))
        conflicts = cursor.fetchall()
        
        has_conflict = False
        conflict_details = None
        if conflicts:
            has_conflict = True
            other_sources = ", ".join([c["source_system"] for c in conflicts])
            conflict_details = f"Identity holds duplicate access to '{entitlement.resource}' across systems: {entitlement.source_system} and {other_sources}"
            flags.append(f"DUPLICATE_ENTITLEMENT_CONFLICT ({conflict_details})")
            risk_score += 25

        # Bound risk score between 0 and 100
        final_risk_score = min(100, risk_score)

        return EvidenceSnapshot(
            days_since_last_use=days_since_last_use,
            last_used_timestamp=last_used_ts,
            usage_status=usage_status,
            user_status=user_status,
            peer_holding_pct=peer_holding_pct,
            peer_sample_size=peer_sample_size,
            peer_baseline_collapsed=peer_collapsed,
            is_high_risk_resource=is_high_risk,
            is_missing_justification=is_missing_justification,
            risk_score=final_risk_score,
            flagged_anomalies=flags,
            source_system_conflict=has_conflict,
            conflict_details=conflict_details
        )
