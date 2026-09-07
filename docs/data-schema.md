# Data Schema Specification

This document defines the SQLite relational database schema and Pydantic models for the Evidence-Based Privilege/Access Review Prototype.

---

## Entity Relationship Summary

- An **Identity** has 0 or more **Entitlements**.
- An **Entitlement** belongs to 1 **Identity** and has 0 or more **UsageEvents**.
- An **Entitlement** has 0 or 1 **ReviewDecisions** per review pass.
- **PeerRoleBaseline** is a precomputed or dynamic aggregate table calculated per `(role_type, department, resource, privilege_level)`.
- A **ReviewDecision** captures the decision, mandatory reason text (if applicable), and an immutable **`evidence_shown`** JSON blob.

---

## Entity Schema Definitions

### 1. `identities`
Stores demographic, institutional role, and employment lifecycle status data.

| Column Name | Data Type | Nullable | Constraints / Index | Description |
|-------------|-----------|----------|---------------------|-------------|
| `id` | TEXT / VARCHAR(64) | NO | PRIMARY KEY | Unique identity identifier (e.g. `USER-1001`) |
| `name` | TEXT | NO | - | Full name of the user |
| `role_type` | TEXT | NO | CHECK (`student`, `faculty`, `alumni`, `temp_researcher`) | Institutional population category |
| `department` | TEXT | NO | INDEX | Academic or administrative department |
| `start_date` | TEXT (ISO 8601) | NO | - | Date identity was onboarded |
| `end_date` | TEXT (ISO 8601) | YES | - | Date identity was offboarded (or null if active) |
| `status` | TEXT | NO | CHECK (`active`, `offboarded`), INDEX | Current identity lifecycle status |

---

### 2. `entitlements`
Stores specific system resource privileges assigned to identities.

| Column Name | Data Type | Nullable | Constraints / Index | Description |
|-------------|-----------|----------|---------------------|-------------|
| `id` | TEXT / VARCHAR(64) | NO | PRIMARY KEY | Unique entitlement identifier (e.g. `ENT-5001`) |
| `identity_id` | TEXT | NO | FOREIGN KEY (`identities.id`), INDEX | Associated identity |
| `resource` | TEXT | NO | INDEX | System, app, database, or vault name |
| `privilege_level` | TEXT | NO | CHECK (`read`, `write`, `admin`, `execute`) | Access level granted |
| `granted_date` | TEXT (ISO 8601) | NO | - | Date access was provisioned |
| `granted_by` | TEXT | NO | - | Identity or admin who authorized access |
| `justification` | TEXT | YES | - | Original business/academic justification (signal if null) |
| `source_system` | TEXT | NO | DEFAULT `primary_iam` | Originating identity system (used for conflict checks) |

---

### 3. `usage_events`
Stores log records of system activity associated with entitlements.

| Column Name | Data Type | Nullable | Constraints / Index | Description |
|-------------|-----------|----------|---------------------|-------------|
| `id` | TEXT / VARCHAR(64) | NO | PRIMARY KEY | Unique log entry ID |
| `entitlement_id` | TEXT | NO | FOREIGN KEY (`entitlements.id`), INDEX | Associated entitlement |
| `timestamp` | TEXT (ISO 8601) | NO | INDEX | Date and time action occurred |
| `action_type` | TEXT | NO | - | Activity classification (e.g. `login`, `query`, `update`) |

---

### 4. `peer_role_baselines`
Stores precomputed aggregate metrics for peer access distribution across role types and departments.

| Column Name | Data Type | Nullable | Constraints / Index | Description |
|-------------|-----------|----------|---------------------|-------------|
| `id` | INTEGER | NO | PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `role_type` | TEXT | NO | INDEX | Target role population |
| `department` | TEXT | NO | INDEX | Target department |
| `resource` | TEXT | NO | INDEX | Target resource |
| `privilege_level` | TEXT | NO | - | Target privilege level |
| `total_peers` | INTEGER | NO | - | Total active identities in this role+dept |
| `peers_holding_count` | INTEGER | NO | - | Count of peers holding this entitlement |
| `peer_holding_pct` | REAL | NO | - | Proportion of peers holding entitlement (0.0 - 100.0) |
| `is_collapsed` | BOOLEAN | NO | DEFAULT 0 | 1 if total_peers <= 2 (suppresses false anomaly flags) |

---

### 5. `review_decisions`
Stores immutable decisions made by reviewers, along with exact evidence shown at decision time.

| Column Name | Data Type | Nullable | Constraints / Index | Description |
|-------------|-----------|----------|---------------------|-------------|
| `id` | TEXT / VARCHAR(64) | NO | PRIMARY KEY | Unique decision ID |
| `entitlement_id` | TEXT | NO | FOREIGN KEY (`entitlements.id`), INDEX | Entitlement being reviewed |
| `reviewer_id` | TEXT | NO | - | Identity of the reviewer performing the action |
| `review_mode` | TEXT | NO | CHECK (`baseline`, `prototype`) | Review interface used when decision was submitted |
| `decision` | TEXT | NO | CHECK (`approve`, `revoke`, `flag_for_follow_up`) | Review action taken |
| `evidence_shown` | TEXT (JSON) | NO | - | Complete JSON snapshot of risk score, flags, usage, peer stats |
| `reason_text` | TEXT | YES | - | Required if decision != approve OR if approve overrides flag |
| `is_rubber_stamp` | BOOLEAN | NO | DEFAULT 0 | 1 if approved without viewing evidence or required justification |
| `timestamp` | TEXT (ISO 8601) | NO | INDEX | Time decision was executed |

---

## SQL Migration DDL Preview

```sql
CREATE TABLE IF NOT EXISTS identities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role_type TEXT NOT NULL CHECK(role_type IN ('student', 'faculty', 'alumni', 'temp_researcher')),
    department TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT NOT NULL CHECK(status IN ('active', 'offboarded'))
);

CREATE TABLE IF NOT EXISTS entitlements (
    id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL REFERENCES identities(id),
    resource TEXT NOT NULL,
    privilege_level TEXT NOT NULL,
    granted_date TEXT NOT NULL,
    granted_by TEXT NOT NULL,
    justification TEXT,
    source_system TEXT NOT NULL DEFAULT 'primary_iam'
);

CREATE TABLE IF NOT EXISTS usage_events (
    id TEXT PRIMARY KEY,
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id),
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS peer_role_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_type TEXT NOT NULL,
    department TEXT NOT NULL,
    resource TEXT NOT NULL,
    privilege_level TEXT NOT NULL,
    total_peers INTEGER NOT NULL,
    peers_holding_count INTEGER NOT NULL,
    peer_holding_pct REAL NOT NULL,
    is_collapsed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS review_decisions (
    id TEXT PRIMARY KEY,
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id),
    reviewer_id TEXT NOT NULL,
    review_mode TEXT NOT NULL CHECK(review_mode IN ('baseline', 'prototype')),
    decision TEXT NOT NULL CHECK(decision IN ('approve', 'revoke', 'flag_for_follow_up')),
    evidence_shown TEXT NOT NULL, -- JSON snapshot
    reason_text TEXT,
    is_rubber_stamp INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_identities_dept_role ON identities(department, role_type);
CREATE INDEX IF NOT EXISTS idx_entitlements_identity ON entitlements(identity_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_entitlement ON usage_events(entitlement_id);
CREATE INDEX IF NOT EXISTS idx_decisions_entitlement ON review_decisions(entitlement_id);
```
