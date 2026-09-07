-- Database Schema DDL for Evidence-Based Access Review System

DROP TABLE IF EXISTS review_decisions;
DROP TABLE IF EXISTS usage_events;
DROP TABLE IF EXISTS entitlements;
DROP TABLE IF EXISTS identities;
DROP TABLE IF EXISTS peer_role_baselines;

CREATE TABLE identities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role_type TEXT NOT NULL CHECK(role_type IN ('student', 'faculty', 'alumni', 'temp_researcher')),
    department TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT NOT NULL CHECK(status IN ('active', 'offboarded'))
);

CREATE TABLE entitlements (
    id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    resource TEXT NOT NULL,
    privilege_level TEXT NOT NULL CHECK(privilege_level IN ('read', 'write', 'admin', 'execute')),
    granted_date TEXT NOT NULL,
    granted_by TEXT NOT NULL,
    justification TEXT,
    source_system TEXT NOT NULL DEFAULT 'primary_iam'
);

CREATE TABLE usage_events (
    id TEXT PRIMARY KEY,
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL
);

CREATE TABLE peer_role_baselines (
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

CREATE TABLE review_decisions (
    id TEXT PRIMARY KEY,
    entitlement_id TEXT NOT NULL REFERENCES entitlements(id) ON DELETE CASCADE,
    reviewer_id TEXT NOT NULL,
    review_mode TEXT NOT NULL CHECK(review_mode IN ('baseline', 'prototype')),
    decision TEXT NOT NULL CHECK(decision IN ('approve', 'revoke', 'flag_for_follow_up')),
    evidence_shown TEXT NOT NULL, -- Serialized JSON snapshot
    reason_text TEXT,
    is_rubber_stamp INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL
);

-- Optimization Indexes
CREATE INDEX idx_identities_dept_role ON identities(department, role_type);
CREATE INDEX idx_identities_status ON identities(status);
CREATE INDEX idx_entitlements_identity ON entitlements(identity_id);
CREATE INDEX idx_entitlements_resource ON entitlements(resource);
CREATE INDEX idx_usage_events_entitlement ON usage_events(entitlement_id);
CREATE INDEX idx_usage_events_timestamp ON usage_events(timestamp);
CREATE INDEX idx_baselines_role_dept ON peer_role_baselines(role_type, department, resource);
CREATE INDEX idx_decisions_entitlement ON review_decisions(entitlement_id);
