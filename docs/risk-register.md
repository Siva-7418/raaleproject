# Risk Register & Security Assessment

This document identifies potential security, operational, privacy, and organizational risks associated with the Evidence-Based Privilege/Access Review System, along with current mitigations and residual risk ratings.

---

## Risk Matrix Summary

| Risk ID | Category | Risk Description | Severity | Likelihood | Mitigation Strategy | Residual Risk |
|---------|----------|------------------|----------|------------|---------------------|---------------|
| **RSK-01** | Security | **Reviewer Rubber-Stamp Override** (Reviewer approves flagged anomaly with dummy text like "ok") | HIGH | MEDIUM | Enforce mandatory justification strings, log rubber-stamp flags for compliance auditing, and implement minimum text length rules. | MEDIUM |
| **RSK-02** | Security | **Stale Usage Log Data** (Usage events delayed in SIEM/log collector pipeline) | MEDIUM | MEDIUM | Display log freshness timestamp explicitly in the Evidence Drawer; flag `INSUFFICIENT_DATA` if log gap exceeds 48 hours. | LOW |
| **RSK-03** | Operational | **Peer Baseline Collapse ($N \le 2$)** (False positive alerts in small departments) | MEDIUM | HIGH | Automated `PEER_BASELINE_COLLAPSED` guard suppresses raw peer deviation alerts when sample size is below threshold. | LOW |
| **RSK-04** | Privacy | **Excessive Activity Surveillance** (Detailed log visualization raising employee privacy concerns) | MEDIUM | LOW | Aggregated usage metrics (e.g. "Last active 12 days ago") displayed to reviewers rather than granular raw log payloads. | LOW |
| **RSK-05** | Security | **Historical Audit Snapshot Tampering** | CRITICAL | LOW | Storing immutable `evidence_shown` JSON blobs serialized directly on `review_decisions` table at decision execution time. | LOW |
| **RSK-06** | Compliance | **Multi-System Entitlement Desynchronization** (Duplicate grants across legacy HR and IdP) | HIGH | MEDIUM | Ingestion layer detects multi-source access and flags `DUPLICATE_ENTITLEMENT_CONFLICT` for consolidation. | MEDIUM |

---

## Detailed Risk Assessments & Controls

### RSK-01: Reviewer Rubber-Stamp Override
- **Scenario**: A department manager receives an evidence alert indicating a former temp researcher holds active admin rights to a sensitive database. Wanting to finish the review pass quickly, the reviewer enters "approved" and submits.
- **System Control**: The API requires non-empty `reason_text` on any flagged override. In compliance audit mode, decisions lacking detailed justification or forced via bypass parameters are automatically tagged as `is_rubber_stamp = 1` and flagged on the CISO compliance dashboard.

### RSK-02: Stale Usage Log Ingestion
- **Scenario**: If log collectors fail for 2 weeks, active access might be falsely categorized as dormant (`UNUSED_ENTITLEMENT`).
- **System Control**: `evidence_shown` snapshots record both log age and ingestion status. The rules engine requires a minimum observation window before triggering dormancy flags.

### RSK-05: Historical Audit Snapshot Integrity
- **Scenario**: An external auditor reviews a decision made 6 months ago. The current user status or peer baseline has changed since then.
- **System Control**: The system stores a complete JSON frozen snapshot of `evidence_shown` on the `review_decisions` database record. Auditors view exact historical evidence seen by the reviewer without relying on live state reconstructions.
