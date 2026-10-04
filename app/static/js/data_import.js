/**
 * Sales Performance Analytics - Data Import & Quality Engine Controller
 */

window.DataImportApp = (function () {

    let activeStageId = null;

    function init() {
        loadDataStatus();

        // Bind file upload form
        const uploadForm = document.getElementById("upload-form");
        const fileInput = document.getElementById("file-input");
        const dropArea = document.getElementById("upload-drop-area");

        if (fileInput && uploadForm) {
            fileInput.addEventListener("change", function () {
                if (this.files.length > 0) {
                    handleFileUpload(this.files[0]);
                }
            });

            if (dropArea) {
                ["dragenter", "dragover"].forEach(name => {
                    dropArea.addEventListener(name, (e) => {
                        e.preventDefault();
                        dropArea.classList.add("border-primary", "bg-light");
                    });
                });

                ["dragleave", "drop"].forEach(name => {
                    dropArea.addEventListener(name, (e) => {
                        e.preventDefault();
                        dropArea.classList.remove("border-primary", "bg-light");
                    });
                });

                dropArea.addEventListener("drop", (e) => {
                    const dt = e.dataTransfer;
                    if (dt.files.length > 0) {
                        handleFileUpload(dt.files[0]);
                    }
                });
            }
        }

        // Bind commit button
        const commitBtn = document.getElementById("btn-commit-data");
        if (commitBtn) {
            commitBtn.addEventListener("click", handleCommitData);
        }

        // Bind synthetic generator button
        const genBtn = document.getElementById("btn-generate-synthetic");
        if (genBtn) {
            genBtn.addEventListener("click", handleGenerateSynthetic);
        }
    }

    function loadDataStatus() {
        fetch("/api/data/status")
            .then(r => r.json())
            .then(res => {
                if (res.status === "success") {
                    renderDatabaseStatus(res.db_status, res.recent_imports);
                }
            })
            .catch(err => console.error("Error loading status:", err));
    }

    function renderDatabaseStatus(dbStatus, imports) {
        const counts = dbStatus.table_counts || {};
        const elOrders = document.getElementById("status-orders-count");
        const elItems = document.getElementById("status-items-count");
        const elCustomers = document.getElementById("status-customers-count");
        const elProducts = document.getElementById("status-products-count");
        const elEngine = document.getElementById("status-engine-name");

        const fmt = new Intl.NumberFormat("en-US");

        if (elOrders) elOrders.textContent = fmt.format(counts.orders || 0);
        if (elItems) elItems.textContent = fmt.format(counts.order_items || 0);
        if (elCustomers) elCustomers.textContent = fmt.format(counts.customers || 0);
        if (elProducts) elProducts.textContent = fmt.format(counts.products || 0);
        if (elEngine) elEngine.textContent = dbStatus.engine_type;

        // Render import history table
        const tbody = document.getElementById("table-import-history-body");
        if (tbody) {
            if (!imports || imports.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-muted">No previous data imports recorded.</td></tr>`;
                return;
            }
            tbody.innerHTML = imports.map(log => `
                <tr>
                    <td class="small text-muted">${log.created_at}</td>
                    <td class="fw-semibold">${log.filename}</td>
                    <td><span class="badge bg-light text-dark border">${log.file_type}</span></td>
                    <td class="text-center font-monospace">${fmt.format(log.valid_records)} / ${fmt.format(log.total_rows)}</td>
                    <td class="text-center">
                        <span class="badge ${log.quality_score >= 95 ? 'bg-success' : 'bg-warning text-dark'}">
                            ${log.quality_score}%
                        </span>
                    </td>
                    <td><span class="badge bg-success-subtle text-success border">${log.status}</span></td>
                </tr>
            `).join("");
        }
    }

    function handleFileUpload(file) {
        const formData = new FormData();
        formData.append("file", file);

        showUploadSpinner(true, "Inspecting columns, standardizing formats, and running quality validation...");
        hideReportSections();

        fetch("/api/data/upload", {
            method: "POST",
            body: formData
        })
        .then(r => r.json())
        .then(res => {
            showUploadSpinner(false);
            if (res.status === "success") {
                activeStageId = res.stage_id;
                renderAuditReport(res.audit_report);
            } else {
                showAlertModal("Upload Error", res.message, "danger");
            }
        })
        .catch(err => {
            showUploadSpinner(false);
            showAlertModal("Network Error", "Failed to communicate with upload server.", "danger");
        });
    }

    function renderAuditReport(report) {
        const stats = report.stats;
        const fmt = new Intl.NumberFormat("en-US");

        // Populate summary metrics
        document.getElementById("stat-total-rows").textContent = fmt.format(stats.total_rows);
        document.getElementById("stat-valid-rows").textContent = fmt.format(stats.valid_records);
        document.getElementById("stat-duplicate-rows").textContent = fmt.format(stats.duplicate_rows);
        document.getElementById("stat-missing-handled").textContent = fmt.format(stats.missing_values_handled);
        document.getElementById("stat-rejected-rows").textContent = fmt.format(stats.rejected_rows);
        
        const qScoreEl = document.getElementById("stat-quality-score");
        qScoreEl.textContent = `${stats.quality_score}%`;
        qScoreEl.className = stats.quality_score >= 90 ? "fs-2 fw-bold text-success" : "fs-2 fw-bold text-warning";

        // Audit actions log
        const actionsList = document.getElementById("audit-actions-list");
        actionsList.innerHTML = report.actions.map(act => `
            <li class="list-group-item d-flex align-items-center gap-2 py-2 small">
                <i class="bi bi-check-circle-fill text-success"></i>
                <span>${act}</span>
            </li>
        `).join("");

        // Cleaned preview table
        const previewHead = document.getElementById("table-preview-head");
        const previewBody = document.getElementById("table-preview-body");
        
        if (report.preview_cleaned && report.preview_cleaned.length > 0) {
            const cols = Object.keys(report.preview_cleaned[0]).slice(0, 8);
            previewHead.innerHTML = `<tr>${cols.map(c => `<th>${c.replace(/_/g, ' ')}</th>`).join('')}</tr>`;
            previewBody.innerHTML = report.preview_cleaned.map(row => `
                <tr>${cols.map(c => `<td>${row[c] !== null ? row[c] : ''}</td>`).join('')}</tr>
            `).join('');
        }

        // Rejected records table
        const rejectedContainer = document.getElementById("rejected-records-container");
        const rejectedBody = document.getElementById("table-rejected-body");
        if (stats.rejected_rows > 0 && report.rejected_records) {
            rejectedContainer.classList.remove("d-none");
            rejectedBody.innerHTML = report.rejected_records.map(r => `
                <tr>
                    <td class="text-center font-monospace">${r.row_index}</td>
                    <td class="font-monospace">${r.order_number}</td>
                    <td class="text-danger small"><i class="bi bi-exclamation-triangle-fill me-1"></i>${r.reason}</td>
                </tr>
            `).join("");
        } else {
            rejectedContainer.classList.add("d-none");
        }

        // Show report card and action button
        document.getElementById("data-quality-report-card").classList.remove("d-none");
        const commitBtn = document.getElementById("btn-commit-data");
        commitBtn.disabled = stats.valid_records === 0;
    }

    function handleCommitData() {
        if (!activeStageId) return;

        const commitBtn = document.getElementById("btn-commit-data");
        commitBtn.disabled = true;
        commitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Committing to Database...`;

        fetch("/api/data/commit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stage_id: activeStageId })
        })
        .then(r => r.json())
        .then(res => {
            commitBtn.innerHTML = `<i class="bi bi-database-check me-2"></i>Approved & Committed`;
            if (res.status === "success") {
                showAlertModal("Import Complete", res.message, "success");
                loadDataStatus();
                activeStageId = null;
            } else {
                commitBtn.disabled = false;
                showAlertModal("Commit Error", res.message, "danger");
            }
        })
        .catch(err => {
            commitBtn.disabled = false;
            commitBtn.innerHTML = `<i class="bi bi-database-check me-2"></i>Commit Cleaned Data to Database`;
            showAlertModal("Network Error", "Failed to commit records to database.", "danger");
        });
    }

    function handleGenerateSynthetic() {
        const genBtn = document.getElementById("btn-generate-synthetic");
        const countInput = document.getElementById("synthetic-count-select");
        const count = countInput ? parseInt(countInput.value, 10) : 50000;

        genBtn.disabled = true;
        genBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Synthesizing ${count.toLocaleString()} Records...`;

        fetch("/api/data/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count: count })
        })
        .then(r => r.json())
        .then(res => {
            genBtn.disabled = false;
            genBtn.innerHTML = `<i class="bi bi-magic me-2"></i>Generate Synthetic Records`;
            if (res.status === "success") {
                showAlertModal("Generation Complete", res.message, "success");
                loadDataStatus();
            } else {
                showAlertModal("Generation Error", res.message, "danger");
            }
        })
        .catch(err => {
            genBtn.disabled = false;
            genBtn.innerHTML = `<i class="bi bi-magic me-2"></i>Generate Synthetic Records`;
            showAlertModal("Error", "Synthetic generation encountered a timeout or network issue.", "danger");
        });
    }

    function showUploadSpinner(show, text = "Processing...") {
        const overlay = document.getElementById("upload-spinner-overlay");
        const spinnerText = document.getElementById("upload-spinner-text");
        if (overlay) {
            overlay.classList.toggle("d-none", !show);
            if (spinnerText) spinnerText.textContent = text;
        }
    }

    function hideReportSections() {
        const card = document.getElementById("data-quality-report-card");
        if (card) card.classList.add("d-none");
    }

    function showAlertModal(title, message, type = "info") {
        const modalEl = document.getElementById("alertModal");
        if (!modalEl) {
            alert(`${title}: ${message}`);
            return;
        }
        document.getElementById("alertModalTitle").textContent = title;
        document.getElementById("alertModalBody").innerHTML = `<div class="alert alert-${type} mb-0">${message}</div>`;
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    return {
        init,
        loadDataStatus
    };
})();

document.addEventListener("DOMContentLoaded", function () {
    if (document.getElementById("upload-drop-area")) {
        window.DataImportApp.init();
    }
});
