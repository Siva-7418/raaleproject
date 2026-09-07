# Non-Technical User Guide & Reviewer Walkthroughs

Welcome to the **Evidence-Based Access Review System**. This guide explains how department managers and compliance reviewers use the system to conduct quarterly access reviews with clear context instead of rubber-stamping spreadsheets.

---

## 1. Getting Started: How the Interface Works

1. Open your browser and navigate to `http://localhost:8000`.
2. Select your role in the top-right corner:
   - **👤 Access Reviewer**: For department heads, lab directors, and managers reviewing employee access.
   - **🔒 Compliance Admin**: For security administrators configuring rules and inspecting audit logs.
3. Choose your **Review Mode**:
   - **📊 Baseline Mode**: Traditional flat table view (spreadsheet style).
   - **🛡️ Evidence Prototype Mode**: Risk-prioritized view showing usage recency, peer comparisons, and anomaly badges.

---

## 2. Reviewing Entitlements Step-by-Step

When reviewing an entitlement in **Evidence Prototype Mode**:
1. **Check Risk Score Badge**: Cards are color-coded:
   - 🔴 **Critical (Score 70-100)**: Offboarded user or critical anomaly. Action required immediately.
   - 🟠 **High Risk (Score 40-69)**: Dormant > 90 days or high-risk financial/student data.
   - 🟡 **Medium Risk (Score 20-39)**: Missing justification or unusual for role peers.
   - 🟢 **Low Risk (Score 0-19)**: Normal access aligning with peers and recent usage.
2. **Inspect Evidence Drawer**: Click **🔍 Inspect** to view:
   - **Days since last usage**: Verifies if the user actually uses the privilege.
   - **Peer prevalence %**: Shows how many colleagues in the same role hold this access.
   - **Employment status**: Alerts if the user has offboarded.
3. **Execute Action**:
   - **Approve**: Confirms access is needed. If flagged, you must enter a reason.
   - **Revoke**: Strips access. Requires entering a brief revocation reason.
   - **Flag for Follow-up**: Escalates to security team for clarification.

---

## 3. Scripted Reviewer Walkthrough Scenarios & Synthetic Validation

Here are 4 realistic walkthrough scenarios demonstrating reviewer workflows:

### Scenario 1: Reviewing an Active Faculty Member's Grading Access
- **Subject**: Prof. Sarah Jenkins (Computer Science Faculty)
- **Entitlement**: `grading_portal` (Privilege: `write`)
- **Evidence Displayed**:
  - Usage: Active 2 days ago.
  - Peer Baseline: 94.2% of CS Faculty hold this access.
  - Risk Score: 0/100 (Clean).
- **Reviewer Action**: Clicks **Approve**. System records approval instantly without prompting for reason.
- **Synthetic Critique**: *What worked*: Reviewer verified role alignment in <3 seconds. *Critique*: High peer alignment makes this a trivial approval; auto-approving zero-risk items could save reviewer time.

---

### Scenario 2: Offboarded Researcher Holding Active Vault Access (EDGE-02)
- **Subject**: Bob Miller (Former Temp Researcher, Computer Science)
- **Entitlement**: `research_data_vault` (Privilege: `admin`)
- **Evidence Displayed**:
  - Identity Status: 🔴 **OFFBOARDED** (End Date: 30 days ago).
  - Risk Score: 85/100 (Critical).
  - Flagged Anomaly: `OFFBOARDED_ACTIVE_ACCESS`.
- **Reviewer Action**: Reviewer clicks **Revoke**. System opens reason modal. Reviewer types: *"User offboarded last month; access must be removed immediately."*
- **Synthetic Critique**: *What worked*: In a spreadsheet, the reviewer would have missed the offboarding status. The red badge prevented a critical security breach. *Critique*: System should ideally support auto-revoking offboarded users at the IAM layer before review cycles start.

---

### Scenario 3: Attempting to Rubber-Stamp a High-Risk Resource Override (EDGE-03)
- **Subject**: Dr. Morgan Vance (Faculty)
- **Entitlement**: `finance_system` (Privilege: `admin`)
- **Evidence Displayed**:
  - Peer Baseline: ⚠️ Held by only 4.2% of CS Faculty.
  - Risk Score: 55/100 (High Risk).
  - Flagged Anomaly: `UNUSUAL_FOR_ROLE`, `HIGH_RISK_RESOURCE`.
- **Reviewer Action**: Reviewer clicks **Approve** without typing a reason. The system blocks submission and displays an alert: *"Reason text is required when approving an entitlement with flagged anomalies."* Reviewer enters: *"Approved: Dr. Vance is Primary Investigator on NSF Grant #4092."*
- **Synthetic Critique**: *What worked*: Enforced accountability; prevented accidental rubber-stamping. *Critique*: Reviewers might find mandatory text entry frustrating if reviewing dozens of legitimate exceptions; dropdown reason templates would improve UX.

---

### Scenario 4: Reviewing Access in a Small Department with Collapsed Baseline (EDGE-04)
- **Subject**: Dr. Carl Sagan (Astronomy Faculty)
- **Entitlement**: `astronomy_telescope_ctrl` (Privilege: `admin`)
- **Evidence Displayed**:
  - Department Size: $N=1$ active faculty.
  - Peer Baseline: 🟡 **PEER_BASELINE_COLLAPSED** (Sample size $n=1 \le 2$).
  - Risk Score: 10/100.
- **Reviewer Action**: Reviewer clicks **Approve**. System suppresses false "unusual for role" warnings.
- **Synthetic Critique**: *What worked*: Avoided false positive noise in single-person departments. *Critique*: Reviewer must rely entirely on usage recency and grant justification since peer comparison is unavailable.
