# Test Evidence Document

This document records automated test execution results for the Evidence-Based Privilege/Access Review Prototype. The test suite is organized into two distinct directories: `tests/normal/` (functional API and flow verification) and `tests/adversarial/` (security controls, failure cases, and policy configurability).

---

## Test Execution Summary

- **Execution Timestamp**: 2026-09-07
- **Test Framework**: `pytest 9.1.1` (Python 3.14.6)
- **Total Tests Executed**: 11
- **Passed**: 11
- **Failed**: 0
- **Pass Rate**: 100%

---

## Detailed Test Case Breakdown

### 1. Normal Test Suite (`tests/normal/`)

| Test File | Test Function Name | Objective / Assertion | Result |
|-----------|--------------------|-----------------------|--------|
| `test_identity_api.py` | `test_list_identities` | Verifies `/api/identities` returns populated identity list ($\ge 150$ records). | ✅ PASSED |
| `test_identity_api.py` | `test_filter_identities_by_department` | Verifies filtering identities by department (e.g. `Biology`) returns scoped subset. | ✅ PASSED |
| `test_rules_engine.py` | `test_evaluate_clean_entitlement` | Confirms clean entitlement assigned to active student receives low risk score ($< 50$) and clean status. | ✅ PASSED |
| `test_review_flow.py` | `test_prototype_review_flow_approval_with_evidence` | Verifies prototype approval records full `evidence_shown` JSON snapshot without rubber-stamp flag. | ✅ PASSED |
| `test_review_flow.py` | `test_baseline_review_flow_bulk_approve` | Confirms baseline "Approve All" flow marks decisions as `is_rubber_stamp = 1` and `evidence_provided = false`. | ✅ PASSED |

---

### 2. Adversarial Test Suite (`tests/adversarial/`)

| Test File | Test Function Name | Edge / Failure Case Covered | Objective / Assertion | Result |
|-----------|--------------------|-----------------------------|-----------------------|--------|
| `test_edge_cases.py` | `test_edge_case_1_no_usage_history` | **Edge Case 1: No Usage History** | Verifies newly onboarded researcher access is labeled `INSUFFICIENT_DATA` rather than false positive dormant alert. | ✅ PASSED |
| `test_edge_case_2_offboarded_active_access` | **Edge Case 2: Offboarded Active Access** | Verifies offboarded identity holding live access triggers critical `OFFBOARDED_ACTIVE_ACCESS` flag (+50 risk), overriding usage recency. | ✅ PASSED |
| `test_edge_cases.py` | `test_edge_case_3_adversarial_rubber_stamping_rejection` | **Edge Case 3: Rubber-Stamping Override** | Asserts approving flagged anomaly without reason raises HTTP 400. Direct API bypass forces `is_rubber_stamp = 1` and audit log flag. | ✅ PASSED |
| `test_edge_cases.py` | `test_edge_case_4_peer_baseline_collapse` | **Edge Case 4: Baseline Collapse ($N \le 2$)** | Confirms department with single faculty member sets `peer_baseline_collapsed: true` and suppresses false deviation alerts. | ✅ PASSED |
| `test_edge_cases.py` | `test_edge_case_5_conflicting_duplicate_entitlements` | **Edge Case 5: Duplicate Entitlement Conflict** | Verifies identity holding multi-source duplicate access (`primary_iam` and `legacy_hr`) triggers `DUPLICATE_ENTITLEMENT_CONFLICT` flag. | ✅ PASSED |
| `test_rules_configurability.py` | `test_rules_engine_runtime_configurability` | **Policy Configurability** | Modifies `unused_threshold_days` dynamically at runtime and proves flagged set changes accordingly without code redeployment. | ✅ PASSED |

---

## Pytest Console Output

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- C:\project\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\project
plugins: anyio-4.15.1
collecting ... collected 11 items

tests/adversarial/test_edge_cases.py::test_edge_case_1_no_usage_history PASSED [  9%]
tests/adversarial/test_edge_cases.py::test_edge_case_2_offboarded_active_access PASSED [ 18%]
tests/adversarial/test_edge_cases.py::test_edge_case_3_adversarial_rubber_stamping_rejection PASSED [ 27%]
tests/adversarial/test_edge_cases.py::test_edge_case_4_peer_baseline_collapse PASSED [ 36%]
tests/adversarial/test_edge_cases.py::test_edge_case_5_conflicting_duplicate_entitlements PASSED [ 45%]
tests/adversarial/test_rules_configurability.py::test_rules_engine_runtime_configurability PASSED [ 54%]
tests/normal/test_identity_api.py::test_list_identities PASSED           [ 63%]
tests/normal/test_identity_api.py::test_filter_identities_by_department PASSED [ 72%]
tests/normal/test_review_flow.py::test_prototype_review_flow_approval_with_evidence PASSED [ 81%]
tests/normal/test_review_flow.py::test_baseline_review_flow_bulk_approve PASSED [ 90%]
tests/normal/test_rules_engine.py::test_evaluate_clean_entitlement PASSED [100%]

======================= 11 passed, 4 warnings in 4.85s ========================
```
