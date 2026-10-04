/**
 * Sales Performance Analytics - SQL Analytics Controller
 */

window.SQLAnalyticsApp = (function () {

    let presetsCache = [];

    function init() {
        loadPresets();

        const runBtn = document.getElementById("btn-run-sql");
        if (runBtn) {
            runBtn.addEventListener("click", executeCurrentQuery);
        }
    }

    function loadPresets() {
        fetch("/api/sql/presets")
            .then(r => r.json())
            .then(res => {
                if (res.status === "success") {
                    presetsCache = res.data;
                    renderPresetsList(presetsCache);
                    // Select first preset by default
                    if (presetsCache.length > 0) {
                        selectPreset(presetsCache[0].id);
                    }
                }
            })
            .catch(err => console.error("Error loading presets:", err));
    }

    function renderPresetsList(presets) {
        const container = document.getElementById("sql-presets-list");
        if (!container) return;

        container.innerHTML = presets.map((p, idx) => `
            <button class="list-group-item list-group-item-action py-3 px-3 border-start-0 border-end-0 border-top-0 preset-item ${idx === 0 ? 'active' : ''}" 
                    data-preset-id="${p.id}" onclick="SQLAnalyticsApp.selectPreset('${p.id}')">
                <div class="d-flex w-100 justify-content-between align-items-center mb-1">
                    <span class="badge bg-secondary-subtle text-secondary small font-monospace">${p.category}</span>
                </div>
                <h6 class="mb-1 fw-bold fs-6">${p.title}</h6>
                <p class="mb-1 text-muted small text-truncate-2">${p.description}</p>
            </button>
        `).join("");
    }

    function selectPreset(presetId) {
        const preset = presetsCache.find(p => p.id === presetId);
        if (!preset) return;

        // Update active class on preset list
        document.querySelectorAll(".preset-item").forEach(item => {
            item.classList.toggle("active", item.dataset.presetId === presetId);
        });

        // Set SQL in textarea
        const sqlInput = document.getElementById("sql-editor-input");
        if (sqlInput) sqlInput.value = preset.sql;

        // Set metadata
        const titleEl = document.getElementById("active-query-title");
        const descEl = document.getElementById("active-query-desc");
        if (titleEl) titleEl.textContent = preset.title;
        if (descEl) descEl.textContent = preset.description;

        // Automatically run preset query
        executeCurrentQuery();
    }

    function executeCurrentQuery() {
        const sqlInput = document.getElementById("sql-editor-input");
        const query = sqlInput ? sqlInput.value.trim() : "";
        if (!query) return;

        const runBtn = document.getElementById("btn-run-sql");
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Executing Query...`;
        }

        const resultsContainer = document.getElementById("sql-results-container");
        const errorAlert = document.getElementById("sql-error-alert");
        const metaBadge = document.getElementById("sql-execution-meta");

        if (errorAlert) errorAlert.classList.add("d-none");

        fetch("/api/sql/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        })
        .then(r => r.json())
        .then(res => {
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.innerHTML = `<i class="bi bi-play-fill me-1"></i>Execute SQL`;
            }

            if (res.success) {
                if (metaBadge) {
                    metaBadge.innerHTML = `<span class="badge bg-success-subtle text-success border me-2"><i class="bi bi-clock me-1"></i>${res.execution_time_ms} ms</span><span class="badge bg-light text-dark border">${res.row_count} rows returned</span>`;
                }
                renderTableResults(res.columns, res.rows);
            } else {
                if (errorAlert) {
                    errorAlert.textContent = res.error || "Query execution failed.";
                    errorAlert.classList.remove("d-none");
                }
                if (resultsContainer) {
                    resultsContainer.innerHTML = `<div class="p-4 text-center text-muted">No results to display due to query error.</div>`;
                }
            }
        })
        .catch(err => {
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.innerHTML = `<i class="bi bi-play-fill me-1"></i>Execute SQL`;
            }
            if (errorAlert) {
                errorAlert.textContent = "Failed to communicate with database server.";
                errorAlert.classList.remove("d-none");
            }
        });
    }

    function renderTableResults(columns, rows) {
        const container = document.getElementById("sql-results-container");
        if (!container) return;

        if (!rows || rows.length === 0) {
            container.innerHTML = `<div class="p-4 text-center text-muted">Query executed successfully. 0 rows returned.</div>`;
            return;
        }

        const headHtml = `<tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr>`;
        const bodyHtml = rows.map(r => `
            <tr>
                ${columns.map(c => {
                    const val = r[c];
                    let formatted = val !== null && val !== undefined ? val : '<span class="text-muted italic">NULL</span>';
                    // Format numeric values
                    if (typeof val === "number") {
                        formatted = Number.isInteger(val) ? val.toLocaleString() : val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                    }
                    return `<td>${formatted}</td>`;
                }).join('')}
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="table-responsive" style="max-height: 480px; overflow-y: auto;">
                <table class="table table-custom table-hover align-middle mb-0">
                    <thead class="sticky-top bg-light">${headHtml}</thead>
                    <tbody>${bodyHtml}</tbody>
                </table>
            </div>
        `;
    }

    return {
        init,
        selectPreset,
        executeCurrentQuery
    };
})();

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("sql-presets-list")) {
        window.SQLAnalyticsApp.init();
    }
});
