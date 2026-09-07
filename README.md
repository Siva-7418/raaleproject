# Evidence-Based Privilege & Access Review Prototype

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-11%20passed-brightgreen.svg)]()

An evidence-based User Access Review (UAR) system designed for higher education institutions. This prototype shifts reviewer behavior from **uninformed blanket/rubber-stamp approvals** to **evidence-backed decisions** by surfacing usage recency, peer role baselines, offboarding indicators, and enforcing justification rules for anomalous access.

---

## 🚀 Quick Start (One-Command Setup)

### Option 1: Docker Setup (Recommended)
```bash
# Clone repository & launch container
docker-compose up --build
```
Open **`http://localhost:8000`** in your browser.

---

### Option 2: Local Python Virtual Environment Setup
```bash
# 1. Create virtualenv & install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Seed database with 154 identities & 390+ entitlements
python scripts/seed_data.py

# 3. Launch FastAPI server & Web UI
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **`http://localhost:8000`** in your browser.

---

## 📊 Re-running the Measurable Experiment

To run the automated experiment comparing the **Dumb Spreadsheet Baseline** against the **Evidence Prototype**:

```bash
python scripts/run_experiment.py
```

### Measured Result Summary
- **Baseline Blanket Approval Rate**: **100.00%** (390/390 rubber-stamped approvals)
- **Prototype Blanket Approval Rate**: **0.00%** (0 rubber-stamped approvals without evidence)
- **Absolute Reduction**: **100.00 percentage points** (Target goal of $\ge 40\%$ **EXCEEDED**).
- **Access Revocations Driven by Evidence**: **108 entitlements** (offboarded users, dormant > 90d).

*Full experiment metrics and error analysis are documented in [`docs/results.md`](docs/results.md).*

---

## 🧪 Running Automated Tests

The repository features comprehensive automated unit and integration tests covering normal API operations and 5 critical edge/failure cases.

```bash
# Run complete test suite (11 tests)
pytest -v tests/
```

### Edge & Failure Cases Covered
1. **No Usage History** (`tests/adversarial/test_edge_cases.py::test_edge_case_1_no_usage_history`): Verifies new researcher access is labeled `INSUFFICIENT_DATA` rather than false unused alert.
2. **Offboarded Active Access** (`tests/adversarial/test_edge_cases.py::test_edge_case_2_offboarded_active_access`): Verifies offboarded identity access triggers critical alert (+50 risk), overriding usage recency.
3. **Adversarial Rubber-Stamping** (`tests/adversarial/test_edge_cases.py::test_edge_case_3_adversarial_rubber_stamping_rejection`): Asserts approving flagged anomaly without reason raises HTTP 400; direct API bypass is tagged as rubber stamp.
4. **Peer Baseline Collapse** (`tests/adversarial/test_edge_cases.py::test_edge_case_4_peer_baseline_collapse`): Suppresses raw deviation alerts when department sample size $N \le 2$.
5. **Conflicting Entitlements** (`tests/adversarial/test_edge_cases.py::test_edge_case_5_conflicting_duplicate_entitlements`): Flags multi-source duplicate access across `primary_iam` and `legacy_hr`.
6. **Policy Configurability** (`tests/adversarial/test_rules_configurability.py::test_rules_engine_runtime_configurability`): Proves changing `config/rules.yaml` thresholds dynamically alters risk flags.

*Complete test descriptions and execution logs are documented in [`docs/test-evidence.md`](docs/test-evidence.md).*

---

## 📁 Required Deliverables Directory

All required deliverables are checked into the repository:

1. **Stakeholder Assumptions** — [`docs/assumptions.md`](docs/assumptions.md)
2. **Architecture Diagram** — [`docs/architecture.md`](docs/architecture.md)
3. **Data Schema Specification** — [`docs/data-schema.md`](docs/data-schema.md) & [`backend/app/db/schema.sql`](backend/app/db/schema.sql)
4. **Functioning MVP** — Running FastAPI backend + Web UI at `http://localhost:8000`
5. **Baseline Comparison Flow** — Accessible via UI mode switcher ("📊 Baseline") & `/api/reviews/items?mode=baseline`
6. **Before & After Results** — [`docs/results.md`](docs/results.md)
7. **Edge / Failure Cases** — Implementations in [`scripts/seed_data.py`](scripts/seed_data.py) & [`tests/adversarial/`](tests/adversarial/)
8. **Measurable Experiment Script** — [`scripts/run_experiment.py`](scripts/run_experiment.py)
9. **Test Evidence Document** — [`docs/test-evidence.md`](docs/test-evidence.md)
10. **Risk Register** — [`docs/risk-register.md`](docs/risk-register.md)
11. **User Guide & Walkthroughs** — [`docs/user-guide.md`](docs/user-guide.md)
12. **Reproducible Repository** — [`README.md`](README.md), [`Dockerfile`](Dockerfile), [`docker-compose.yml`](docker-compose.yml)

---

## ⚙️ Rules Engine Configuration

Risk scoring is dynamically driven by `config/rules.yaml`:

```yaml
unused_threshold_days: 90
peer_deviation_threshold_pct: 10.0
high_risk_resources:
  - finance_system
  - student_records
  - research_data_vault
  - payroll_system
require_reason_on_override: true
require_reason_on_revoke: true
minimum_peer_sample_size: 2
```
Compliance officers can update rules live in the Web UI under **🔒 Compliance Admin** or via `POST /api/rules`.
