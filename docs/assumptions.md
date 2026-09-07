# Stakeholder Assumptions & Context

## 1. Executive Context & Problem Statement
Periodic privilege and access reviews (User Access Reviews / UARs) at higher education institutions are routinely conducted using manual spreadsheet exports. Department managers and system administrators are presented with thousands of rows containing identity-to-resource mappings without context regarding whether the privilege is actively used, appropriate for the user's role, or compliant with policy.

This lack of context leads to **rubber-stamp approvals**—where reviewers approve 95%+ of requested entitlements simply to complete the administrative task. This prototype demonstrates how contextual evidence, automated peer analysis, and configurable risk rules change reviewer behavior and eliminate blanket approvals.

---

## 2. Target Stakeholder Personas

The system enforces permission boundaries and distinct workflows across two primary organizational roles:

### Persona 1: Access Reviewer (e.g., Department Head / Data Owner / Lab Director)
- **Responsibilities**: Review access entitlements for personnel within their department or project group during periodic review cycles.
- **Key Pain Point**: Overwhelmed by lists of technical permissions (e.g., `db_writer_prod_vault_v2`) with no context on whether the employee actually uses it or needs it.
- **System Capabilities**:
  - Views contextualized entitlement cards for scoped personnel.
  - Sees usage recency, peer adoption percentages, and risk severity flags.
  - Can Approve, Revoke, or Flag for Follow-up per item.
  - **Enforced Constraint**: Must provide a mandatory justification (`reason_text`) if overriding an anomaly flag or revoking access.

### Persona 2: Compliance & Security Admin (e.g., CISO / IAM Manager / Internal Auditor)
- **Responsibilities**: Oversee institution-wide access compliance, configure privilege risk thresholds, and audit decision quality.
- **Key Pain Point**: Inability to prove to external auditors what evidence a reviewer saw when making an access decision, or detecting rubber-stamp reviewers.
- **System Capabilities**:
  - Configures the runtime rules engine (`config/rules.yaml`), adjusting inactivity thresholds, high-risk resource lists, and deviation sensitivities.
  - Inspects institution-wide analytics and reviewer blanket-approval metrics.
  - Audits immutable decision records containing exact `evidence_shown` JSON snapshots captured at the moment of approval/revocation.
  - Evaluates policy bypasses and flagged overrides.

---

## 3. Data Sources & Ingestion Assumptions

In a production environment, the evidence engine aggregates data from three enterprise systems:
1. **Identity Provider (IdP) / HR System**: User status (Active vs. Offboarded), role type (Student, Faculty, Alumni, Temp Researcher), department, start/end dates.
2. **Access & Entitlement Repository**: Current entitlement grants, privilege level (read, write, admin), grant timestamp, and original justification.
3. **Application & Infrastructure Audit Logs**: Systems logs capturing user login, API calls, and data access timestamps.

*For this prototype, all data sources are synthetic and deterministically generated via `scripts/seed_data.py` to allow reproducible testing.*

---

## 4. Definition of "Evidence"

To an Access Reviewer, **Evidence** is not raw log dumps, but actionable, synthesized context presented alongside every entitlement:
1. **Usage Recency & Velocity**: Time elapsed since last action (e.g., "Last used 112 days ago" or "No usage history recorded").
2. **Peer Role Baseline Comparison**: Percentage of peers within the same `(role_type, department)` holding the same privilege (e.g., "Held by 4.2% of peers in Computer Science Faculty").
3. **Identity Lifecycle Status**: Alignment between identity status and entitlement (e.g., "CRITICAL: Identity status is OFFBOARDED as of 2026-05-01").
4. **Resource Criticality & Privilege Level**: Classification of the target system (e.g., "High-risk resource: Financial System | Admin Level").
5. **Grant History Context**: Original granting authority and justification text (or explicit signal that justification was missing at grant time).

---

## 5. Scope & Explicit Exclusions

### In Scope
- SQLite backend with FastAPI REST endpoints.
- Interactive Web UI supporting Baseline (Spreadsheet) Mode and Evidence-Based Review Mode.
- Configurable YAML rules engine evaluated dynamically.
- 5 edge/failure cases (no usage history, offboarded active access, rubber-stamping prevention, peer baseline collapse, duplicate entitlement conflict).
- Decision persistence with immutable `evidence_shown` JSON snapshots.
- Automated experiment runner comparing blanket approval rates across 150+ identities.

### Out of Scope
- Direct integration with live LDAP, Active Directory, or Okta APIs (synthetic seeded data used instead).
- OAuth2/SAML SSO authentication implementation (simulated role header/context selection used for UI role switching).
- Automated provisioning/deprovisioning webhooks back to target systems (decisions are logged to audit database).
