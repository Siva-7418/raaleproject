const API_BASE = "";

async function fetchJson(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        },
        ...options
    });
    
    if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || "API Request Failed");
    }
    return response.json();
}

const Api = {
    getReviewItems: (mode = "prototype", department = "") => {
        let url = `/api/reviews/items?mode=${mode}`;
        if (department) url += `&department=${encodeURIComponent(department)}`;
        return fetchJson(url);
    },

    submitDecision: (data) => {
        return fetchJson("/api/reviews/decision", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    bulkSubmitBaseline: (entitlementIds) => {
        return fetchJson("/api/reviews/bulk-baseline", {
            method: "POST",
            body: JSON.stringify({
                entitlement_ids: entitlementIds,
                reviewer_id: "rev-dept-head",
                review_mode: "baseline",
                decision: "approve"
            })
        });
    },

    getRulesConfig: () => {
        return fetchJson("/api/rules");
    },

    saveRulesConfig: (configData) => {
        return fetchJson("/api/rules", {
            method: "POST",
            body: JSON.stringify(configData)
        });
    },

    getAuditDecisions: (mode = "") => {
        let url = "/api/audit/decisions?limit=100";
        if (mode) url += `&mode=${mode}`;
        return fetchJson(url);
    },

    getAuditMetrics: () => {
        return fetchJson("/api/audit/metrics");
    }
};
