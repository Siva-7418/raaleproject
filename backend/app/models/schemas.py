from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class IdentitySchema(BaseModel):
    id: str
    name: str
    role_type: str
    department: str
    start_date: str
    end_date: Optional[str] = None
    status: str

class EntitlementSchema(BaseModel):
    id: str
    identity_id: str
    resource: str
    privilege_level: str
    granted_date: str
    granted_by: str
    justification: Optional[str] = None
    source_system: str = "primary_iam"

class UsageEventSchema(BaseModel):
    id: str
    entitlement_id: str
    timestamp: str
    action_type: str

class PeerRoleBaselineSchema(BaseModel):
    id: Optional[int] = None
    role_type: str
    department: str
    resource: str
    privilege_level: str
    total_peers: int
    peers_holding_count: int
    peer_holding_pct: float
    is_collapsed: bool = False

class EvidenceSnapshot(BaseModel):
    days_since_last_use: Optional[int] = None
    last_used_timestamp: Optional[str] = None
    usage_status: str # "ACTIVE", "UNUSED", "INSUFFICIENT_DATA"
    user_status: str # "active", "offboarded"
    peer_holding_pct: float
    peer_sample_size: int
    peer_baseline_collapsed: bool = False
    is_high_risk_resource: bool = False
    is_missing_justification: bool = False
    risk_score: int # 0 to 100
    flagged_anomalies: List[str] = []
    source_system_conflict: bool = False
    conflict_details: Optional[str] = None

class EntitlementReviewItem(BaseModel):
    entitlement_id: str
    identity: IdentitySchema
    entitlement: EntitlementSchema
    evidence: Optional[EvidenceSnapshot] = None # None in Baseline mode!

class DecisionSubmission(BaseModel):
    entitlement_id: str
    reviewer_id: str = "rev-admin-01"
    review_mode: str # "baseline" or "prototype"
    decision: str # "approve", "revoke", "flag_for_follow_up"
    reason_text: Optional[str] = None
    bypass_reason_check: bool = False # Used for adversarial rubber-stamp simulation

class ReviewDecisionRecord(BaseModel):
    id: str
    entitlement_id: str
    reviewer_id: str
    review_mode: str
    decision: str
    evidence_shown: Dict[str, Any]
    reason_text: Optional[str] = None
    is_rubber_stamp: bool = False
    timestamp: str

class RulesConfigSchema(BaseModel):
    unused_threshold_days: int = 90
    peer_deviation_threshold_pct: float = 10.0
    high_risk_resources: List[str] = ["finance_system", "student_records", "research_data_vault", "payroll_system"]
    require_reason_on_override: bool = True
    require_reason_on_revoke: bool = True
    minimum_peer_sample_size: int = 2

class BulkDecisionSubmission(BaseModel):
    entitlement_ids: List[str]
    reviewer_id: str = "rev-admin-01"
    review_mode: str = "baseline"
    decision: str = "approve"
    reason_text: Optional[str] = None
