let currentMode = "prototype"; // "baseline" or "prototype"
let currentRole = "reviewer"; // "reviewer" or "admin"
let currentItems = [];
let activePendingDecision = null; // Stored when waiting for reason input

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    setReviewMode("prototype");
}

function setReviewMode(mode) {
    currentMode = mode;
    document.getElementById("btn-mode-baseline").classList.toggle("active", mode === "baseline");
    document.getElementById("btn-mode-prototype").classList.toggle("active", mode === "prototype");
    
    document.getElementById("baseline-actions").classList.toggle("hidden", mode !== "baseline");
    loadReviewItems();
}

function switchRole(role) {
    currentRole = role;
    document.getElementById("view-reviewer").classList.toggle("hidden", role !== "reviewer");
    document.getElementById("view-admin").classList.toggle("hidden", role !== "admin");

    if (role === "admin") {
        loadAdminView();
    } else {
        loadReviewItems();
    }
}

async function loadReviewItems() {
    const dept = document.getElementById("dept-filter").value;
    try {
        currentItems = await Api.getReviewItems(currentMode, dept);
        renderStats();
        renderTable();
    } catch (err) {
        showToast("Error loading review items: " + err.message);
    }
}

function renderStats() {
    const statsContainer = document.getElementById("stats-container");
    if (!currentItems) return;

    const total = currentItems.length;

    if (currentMode === "baseline") {
        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${total}</div>
                <div class="stat-label">Total Entitlements</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--text-muted);">Unverified</div>
                <div class="stat-label">Evidence Context</div>
            </div>
        `;
    } else {
        const highRisk = currentItems.filter(i => i.evidence && i.evidence.risk_score >= 40).length;
        const offboarded = currentItems.filter(i => i.evidence && i.evidence.user_status === "offboarded").length;
        const dormant = currentItems.filter(i => i.evidence && i.evidence.usage_status === "UNUSED").length;

        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${total}</div>
                <div class="stat-label">Total Entitlements</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--accent-red);">${offboarded}</div>
                <div class="stat-label">Offboarded Active</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--accent-orange);">${highRisk}</div>
                <div class="stat-label">High Risk Flagged</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--accent-yellow);">${dormant}</div>
                <div class="stat-label">Dormant > 90d</div>
            </div>
        `;
    }
}

function renderTable() {
    const headersTr = document.getElementById("table-headers");
    const tbody = document.getElementById("review-table-body");
    tbody.innerHTML = "";

    if (currentMode === "baseline") {
        headersTr.innerHTML = `
            <th>User Name</th>
            <th>Role & Dept</th>
            <th>Resource</th>
            <th>Privilege</th>
            <th>Granted Date</th>
            <th>Actions</th>
        `;

        currentItems.forEach(item => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${item.identity.name}</strong> <span class="subtitle">(${item.identity.id})</span></td>
                <td><span class="badge badge-role">${item.identity.role_type}</span> <br><small>${item.identity.department}</small></td>
                <td><code>${item.entitlement.resource}</code></td>
                <td><code>${item.entitlement.privilege_level}</code></td>
                <td><small>${item.entitlement.granted_date.split("T")[0]}</small></td>
                <td>
                    <button class="btn btn-success btn-sm" onclick="executeDecision('${item.entitlement_id}', 'approve')">Approve</button>
                    <button class="btn btn-danger btn-sm" onclick="executeDecision('${item.entitlement_id}', 'revoke')">Revoke</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } else {
        // PROTOTYPE EVIDENCE MODE
        headersTr.innerHTML = `
            <th>Risk & Score</th>
            <th>Identity Context</th>
            <th>Resource & Privilege</th>
            <th>Usage Recency</th>
            <th>Peer Baseline</th>
            <th>Evidence Breakdown</th>
            <th>Review Actions</th>
        `;

        currentItems.forEach(item => {
            const ev = item.evidence;
            const score = ev ? ev.risk_score : 0;
            let riskBadgeClass = "badge-risk-low";
            if (score >= 70) riskBadgeClass = "badge-risk-critical";
            else if (score >= 40) riskBadgeClass = "badge-risk-high";
            else if (score >= 20) riskBadgeClass = "badge-risk-medium";

            const tr = document.createElement("tr");
            
            // Usage text
            let usageText = `<span style="color:var(--accent-green)">Active Recent</span>`;
            if (ev.usage_status === "UNUSED") {
                usageText = `<span style="color:var(--accent-yellow)">Dormant (${ev.days_since_last_use}d)</span>`;
            } else if (ev.usage_status === "INSUFFICIENT_DATA") {
                usageText = `<span style="color:var(--text-muted)">Insufficient Data</span>`;
            }

            // Peer text
            let peerText = `${ev.peer_holding_pct}% of peers`;
            if (ev.peer_baseline_collapsed) {
                peerText = `<small style="color:var(--accent-yellow)">Collapsed (n=${ev.peer_sample_size})</small>`;
            }

            tr.innerHTML = `
                <td>
                    <span class="badge ${riskBadgeClass}">Score: ${score}/100</span>
                </td>
                <td>
                    <strong>${item.identity.name}</strong> 
                    ${item.identity.status === 'offboarded' ? '<span class="badge badge-offboarded">OFFBOARDED</span>' : ''}
                    <br><span class="badge badge-role">${item.identity.role_type}</span> <small>${item.identity.department}</small>
                </td>
                <td>
                    <code>${item.entitlement.resource}</code>
                    ${ev.is_high_risk_resource ? '<span style="color:var(--accent-orange)"> 🔥</span>' : ''}
                    <br><small>Level: <b>${item.entitlement.privilege_level}</b></small>
                </td>
                <td>${usageText}</td>
                <td>
                    ${peerText}
                    <div class="peer-bar-container">
                        <div class="peer-bar-fill ${ev.peer_holding_pct < 10 ? 'low' : ''}" style="width: ${Math.min(100, ev.peer_holding_pct)}%"></div>
                    </div>
                </td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="openEvidenceDrawer('${item.entitlement_id}')">
                        🔍 Inspect (${ev.flagged_anomalies.length} Flags)
                    </button>
                </td>
                <td>
                    <button class="btn btn-success btn-sm" onclick="executeDecision('${item.entitlement_id}', 'approve')">Approve</button>
                    <button class="btn btn-danger btn-sm" onclick="executeDecision('${item.entitlement_id}', 'revoke')">Revoke</button>
                    <button class="btn btn-warning btn-sm" onclick="executeDecision('${item.entitlement_id}', 'flag_for_follow_up')">Flag</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
}

function openEvidenceDrawer(entitlementId) {
    const item = currentItems.find(i => i.entitlement_id === entitlementId);
    if (!item || !item.evidence) return;

    const ev = item.evidence;
    const modalBody = document.getElementById("modal-evidence-body");

    let flagsHtml = "";
    if (ev.flagged_anomalies.length > 0) {
        flagsHtml = `
            <div class="evidence-card" style="border-left: 4px solid var(--accent-red)">
                <h3 style="color: var(--accent-red)">⚠️ Flagged Risk Anomalies (${ev.flagged_anomalies.length})</h3>
                <ul class="evidence-flag-list">
                    ${ev.flagged_anomalies.map(f => `<li>${f}</li>`).join("")}
                </ul>
            </div>
        `;
    } else {
        flagsHtml = `
            <div class="evidence-card" style="border-left: 4px solid var(--accent-green)">
                <h3 style="color: var(--accent-green)">✅ No Anomaly Flags Triggered</h3>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.3rem;">Entitlement aligns with standard peer role baseline and recency guidelines.</p>
            </div>
        `;
    }

    modalBody.innerHTML = `
        <div class="evidence-card">
            <h3>👤 Identity Lifecycle Context</h3>
            <p><strong>Name:</strong> ${item.identity.name} (${item.identity.id})</p>
            <p><strong>Role Type:</strong> ${item.identity.role_type} | <strong>Dept:</strong> ${item.identity.department}</p>
            <p><strong>Employment Status:</strong> ${item.identity.status.toUpperCase()} ${item.identity.end_date ? `(Offboarded on ${item.identity.end_date.split("T")[0]})` : ''}</p>
        </div>

        ${flagsHtml}

        <div class="evidence-card">
            <h3>📊 Peer Baseline & Usage Analysis</h3>
            <p><strong>Peer Prevalence:</strong> ${ev.peer_holding_pct}% of peers in ${item.identity.role_type} hold this entitlement.</p>
            <p><strong>Peer Sample Size:</strong> n=${ev.peer_sample_size} ${ev.peer_baseline_collapsed ? '(COLLAPSED BASELINE)' : ''}</p>
            <p><strong>Usage Recency:</strong> ${ev.days_since_last_use !== null ? `Last active ${ev.days_since_last_use} days ago (${ev.last_used_timestamp.split("T")[0]})` : 'No usage events logged since provisioning'}</p>
        </div>

        <div class="evidence-card">
            <h3>🔑 Privilege & Governance Metadata</h3>
            <p><strong>Target Resource:</strong> <code>${item.entitlement.resource}</code> ${ev.is_high_risk_resource ? '(CLASSIFIED HIGH RISK)' : ''}</p>
            <p><strong>Privilege Level:</strong> ${item.entitlement.privilege_level.toUpperCase()}</p>
            <p><strong>Granted Date:</strong> ${item.entitlement.granted_date.split("T")[0]} by ${item.entitlement.granted_by}</p>
            <p><strong>Business Justification:</strong> ${item.entitlement.justification || '<span style="color:var(--accent-red)">None provided</span>'}</p>
            <p><strong>Source System:</strong> ${item.entitlement.source_system}</p>
            ${ev.source_system_conflict ? `<p style="color:var(--accent-red)">⚠️ <strong>Conflict:</strong> ${ev.conflict_details}</p>` : ''}
        </div>
    `;

    document.getElementById("evidence-modal").classList.remove("hidden");
}

async function executeDecision(entitlementId, decision) {
    const item = currentItems.find(i => i.entitlement_id === entitlementId);
    
    // Check if reason is required
    let needsReason = false;
    let title = "Justification Required";
    let desc = "";

    if (currentMode === "prototype" && item && item.evidence) {
        const ev = item.evidence;
        const hasAnomalies = ev.flagged_anomalies.length > 0 || ev.risk_score > 0;

        if (decision === "revoke") {
            needsReason = true;
            title = "Revocation Justification Required";
            desc = `Please provide a reason for revoking ${item.identity.name}'s access to ${item.entitlement.resource}.`;
        } else if (decision === "approve" && hasAnomalies) {
            needsReason = true;
            title = "Override Justification Required";
            desc = `This entitlement has flagged anomalies (${ev.flagged_anomalies.length}). A mandatory justification is required to override flags and approve.`;
        }
    }

    if (needsReason) {
        activePendingDecision = { entitlement_id: entitlementId, decision: decision };
        document.getElementById("reason-modal-title").innerText = title;
        document.getElementById("reason-modal-desc").innerText = desc;
        document.getElementById("reason-text-input").value = "";
        document.getElementById("reason-modal").classList.remove("hidden");
    } else {
        // Direct Submit
        await performSubmit({
            entitlement_id: entitlementId,
            reviewer_id: "rev-dept-head",
            review_mode: currentMode,
            decision: decision,
            reason_text: null
        });
    }
}

async function submitReasonDecision() {
    const reasonText = document.getElementById("reason-text-input").value.trim();
    if (!reasonText) {
        showToast("Please enter a reason before submitting.");
        return;
    }

    if (!activePendingDecision) return;

    closeModal("reason-modal");
    await performSubmit({
        entitlement_id: activePendingDecision.entitlement_id,
        reviewer_id: "rev-dept-head",
        review_mode: currentMode,
        decision: activePendingDecision.decision,
        reason_text: reasonText
    });
    activePendingDecision = null;
}

async function performSubmit(payload) {
    try {
        const record = await Api.submitDecision(payload);
        showToast(`Decision saved! (${record.decision.toUpperCase()})`);
        
        // Remove item from UI table
        currentItems = currentItems.filter(i => i.entitlement_id !== payload.entitlement_id);
        renderStats();
        renderTable();
    } catch (err) {
        showToast("Failed to save decision: " + err.message);
    }
}

async function bulkApproveBaseline() {
    if (!confirm("Execute 'Approve All' blanket rubber-stamp for all visible entitlements?")) return;

    const ids = currentItems.map(i => i.entitlement_id);
    try {
        const records = await Api.bulkSubmitBaseline(ids);
        showToast(`Bulk approved ${records.length} items without evidence!`);
        currentItems = [];
        renderStats();
        renderTable();
    } catch (err) {
        showToast("Bulk approve failed: " + err.message);
    }
}

/* ADMIN VIEW FUNCTIONS */
async function loadAdminView() {
    try {
        const cfg = await Api.getRulesConfig();
        document.getElementById("cfg-unused").value = cfg.unused_threshold_days;
        document.getElementById("cfg-peer-dev").value = cfg.peer_deviation_threshold_pct;
        document.getElementById("cfg-high-risk").value = cfg.high_risk_resources.join(", ");
        document.getElementById("cfg-req-override").checked = cfg.require_reason_on_override;
        document.getElementById("cfg-req-revoke").checked = cfg.require_reason_on_revoke;

        await loadAuditMetrics();
        await loadAuditTable();
    } catch (err) {
        showToast("Error loading admin view: " + err.message);
    }
}

async function saveRules(e) {
    e.preventDefault();
    const configData = {
        unused_threshold_days: parseInt(document.getElementById("cfg-unused").value),
        peer_deviation_threshold_pct: parseFloat(document.getElementById("cfg-peer-dev").value),
        high_risk_resources: document.getElementById("cfg-high-risk").value.split(",").map(s => s.trim()).filter(Boolean),
        require_reason_on_override: document.getElementById("cfg-req-override").checked,
        require_reason_on_revoke: document.getElementById("cfg-req-revoke").checked
    };

    try {
        await Api.saveRulesConfig(configData);
        showToast("Rules configuration updated successfully!");
    } catch (err) {
        showToast("Failed to update rules: " + err.message);
    }
}

async function loadAuditMetrics() {
    try {
        const metrics = await Api.getAuditMetrics();
        const container = document.getElementById("audit-metrics-container");

        const bMode = metrics.baseline || { total_decisions: 0, blanket_approval_rate_pct: 0 };
        const pMode = metrics.prototype || { total_decisions: 0, blanket_approval_rate_pct: 0 };

        container.innerHTML = `
            <div class="metric-card" style="border-color: var(--accent-yellow)">
                <div class="metric-number" style="color: var(--accent-yellow)">${bMode.blanket_approval_rate_pct}%</div>
                <div class="stat-label">Baseline Blanket Approval Rate (${bMode.total_decisions} decisions)</div>
            </div>
            <div class="metric-card" style="border-color: var(--accent-green)">
                <div class="metric-number" style="color: var(--accent-green)">${pMode.blanket_approval_rate_pct}%</div>
                <div class="stat-label">Prototype Blanket Approval Rate (${pMode.total_decisions} decisions)</div>
            </div>
        `;
    } catch (err) {
        console.error("Audit metrics error:", err);
    }
}

async function loadAuditTable() {
    try {
        const logs = await Api.getAuditDecisions();
        const tbody = document.getElementById("audit-table-body");
        tbody.innerHTML = "";

        logs.forEach(log => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><small>${log.timestamp.replace("T", " ").substring(0, 16)}</small></td>
                <td><span class="badge ${log.review_mode === 'baseline' ? 'badge-risk-medium' : 'badge-role'}">${log.review_mode}</span></td>
                <td><code>${log.resource}</code></td>
                <td><b>${log.decision.toUpperCase()}</b></td>
                <td>${log.is_rubber_stamp ? '<span style="color:var(--accent-red)">⚠️ YES</span>' : '<span style="color:var(--accent-green)">NO</span>'}</td>
                <td><small>${log.reason_text || '<i>None</i>'}</small></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick='viewSnapshot(${JSON.stringify(log.evidence_shown)})'>
                        Snapshot
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Audit table error:", err);
    }
}

function viewSnapshot(snapshotObj) {
    document.getElementById("snapshot-json-display").innerText = JSON.stringify(snapshotObj, null, 2);
    document.getElementById("snapshot-modal").classList.remove("hidden");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 3000);
}
