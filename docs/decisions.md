# Technical Decisions & Rationale

This document logs key architectural choices made during the engineering of the Evidence-Based Privilege/Access Review Prototype.

---

## 1. Backend Architecture: Python 3.11 + FastAPI

### Decision
Use **FastAPI** with **Pydantic v2** for backend REST API endpoints.

### Rationale
1. **Self-Documenting API**: FastAPI automatically generates interactive OpenAPI/Swagger documentation at `/docs`, simplifying review and testing.
2. **Speed & Type Safety**: Native async handling and Pydantic validation ensure strict schema enforcement for incoming decision requests, rule updates, and seed data formats.
3. **Ecosystem Compatibility**: Python seamlessly interfaces with data analysis libraries (e.g. PyYAML, Pytest) needed for the rules engine and experiment simulation runner.

---

## 2. Persistence Layer: SQLite

### Decision
Use **SQLite3** stored in local database file `data/app.db` (with in-memory SQLite support for fast unit testing).

### Rationale
1. **Zero External Dependencies**: Enables true one-command execution via `docker-compose up` or simple `python` launch scripts without needing a separate PostgreSQL/MySQL container.
2. **Transactional Integrity & JSON Support**: SQLite provides native JSON support (`JSON_EXTRACT`, JSON storage) perfectly suited for storing immutable `evidence_shown` JSON snapshots.
3. **Reproducibility**: Database file can be deleted and recreated deterministically via `python scripts/seed_data.py`.

---

## 3. Frontend Architecture: Modern Single-Page Application (HTML5 / Vanilla CSS3 / Modular JS)

### Decision
Build an interactive Web UI using HTML5, modern CSS3 (Glassmorphism dark theme with micro-animations), and modular vanilla JavaScript, served directly by FastAPI via `StaticFiles`.

### Rationale
1. **No Node/npm Build Pipeline Required**: Eliminates potential Node version conflicts or compilation build steps. Anyone running `docker-compose up` or `python backend/main.py` immediately gets a working UI at `http://localhost:8000`.
2. **Rich Aesthetics & Interactivity**: Vanilla JS paired with modern CSS custom variables provides complete flexibility for responsive evidence drawers, side-by-side Baseline vs. Prototype comparisons, and animated risk badges.
3. **Zero UI Framework Overhead**: Ensures lightweight loading times and absolute control over DOM updates during review actions.

---

## 4. Configurable Rules Engine: Runtime YAML Parser

### Decision
Store flagging thresholds, risk weights, and high-risk resource definitions in `config/rules.yaml` and load them dynamically at runtime.

### Rationale
1. **No Code Deployment Required for Policy Changes**: Compliance officers can modify inactivity thresholds (e.g. 90 days to 60 days) or add sensitive database resources directly in YAML, and the API reflects the updated risk flags instantly.
2. **Testability**: Pytest can modify rules dynamically in memory or pass alternative config objects to prove that changing thresholds immediately alters flagged entitlement counts (covering adversarial test cases).

---

## 5. Audit Persistence Rationale: Immutable `evidence_shown` Snapshot

### Decision
Every review decision record MUST serialize and store a complete snapshot of all evidence, risk flags, usage numbers, and peer stats displayed to the reviewer at the exact moment of decision.

### Rationale
In traditional systems, audit logs only record "Reviewer X approved Entitlement Y on Date Z". If audited 6 months later, there is no way to verify whether the reviewer ignored an anomaly flag or if the anomaly flag didn't exist at the time. By embedding `evidence_shown` as a JSON blob on `ReviewDecision`, compliance teams can inspect historical decisions with 100% audit accuracy.
