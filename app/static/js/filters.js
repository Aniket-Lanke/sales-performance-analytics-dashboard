/**
 * Sales Performance Analytics - Global Filter Engine
 * Manages query parameters, date presets, and broadcasts filter changes to charts.
 */

window.FilterEngine = (function () {
    const defaultState = {
        start_date: "",
        end_date: "",
        region_id: "all",
        category_id: "all",
        payment_method: "all",
        order_status: "all"
    };

    let state = { ...defaultState };

    function init() {
        // Load initial values from DOM if present
        const startInput = document.getElementById("filter-start-date");
        const endInput = document.getElementById("filter-end-date");
        const regionSelect = document.getElementById("filter-region");
        const categorySelect = document.getElementById("filter-category");
        const paymentSelect = document.getElementById("filter-payment");
        const statusSelect = document.getElementById("filter-status");

        if (startInput) state.start_date = startInput.value;
        if (endInput) state.end_date = endInput.value;
        if (regionSelect) state.region_id = regionSelect.value;
        if (categorySelect) state.category_id = categorySelect.value;
        if (paymentSelect) state.payment_method = paymentSelect.value;
        if (statusSelect) state.order_status = statusSelect.value;

        // Bind preset buttons
        const presetBtns = document.querySelectorAll(".date-preset-btn");
        presetBtns.forEach(btn => {
            btn.addEventListener("click", function () {
                presetBtns.forEach(b => b.classList.remove("active"));
                this.classList.add("active");
                applyDatePreset(this.dataset.preset);
            });
        });

        // Bind Apply button
        const applyBtn = document.getElementById("btn-apply-filters");
        if (applyBtn) {
            applyBtn.addEventListener("click", function (e) {
                e.preventDefault();
                readDomInputs();
                triggerFilterChange();
            });
        }

        // Bind Reset button
        const resetBtn = document.getElementById("btn-reset-filters");
        if (resetBtn) {
            resetBtn.addEventListener("click", function (e) {
                e.preventDefault();
                resetFilters();
            });
        }
    }

    function readDomInputs() {
        const startInput = document.getElementById("filter-start-date");
        const endInput = document.getElementById("filter-end-date");
        const regionSelect = document.getElementById("filter-region");
        const categorySelect = document.getElementById("filter-category");
        const paymentSelect = document.getElementById("filter-payment");
        const statusSelect = document.getElementById("filter-status");

        state.start_date = startInput ? startInput.value.trim() : "";
        state.end_date = endInput ? endInput.value.trim() : "";
        state.region_id = regionSelect ? regionSelect.value : "all";
        state.category_id = categorySelect ? categorySelect.value : "all";
        state.payment_method = paymentSelect ? paymentSelect.value : "all";
        state.order_status = statusSelect ? statusSelect.value : "all";
    }

    function applyDatePreset(preset) {
        const today = new Date();
        const formatDate = (d) => d.toISOString().split("T")[0];
        let start = "";
        let end = formatDate(today);

        switch (preset) {
            case "30d":
                const d30 = new Date(today);
                d30.setDate(d30.getDate() - 30);
                start = formatDate(d30);
                break;
            case "90d":
                const d90 = new Date(today);
                d90.setDate(d90.getDate() - 90);
                start = formatDate(d90);
                break;
            case "ytd":
                start = `${today.getFullYear()}-01-01`;
                break;
            case "12m":
                const d12m = new Date(today);
                d12m.setFullYear(d12m.getFullYear() - 1);
                start = formatDate(d12m);
                break;
            case "all":
            default:
                start = "";
                end = "";
                break;
        }

        const startInput = document.getElementById("filter-start-date");
        const endInput = document.getElementById("filter-end-date");
        if (startInput) startInput.value = start;
        if (endInput) endInput.value = end;

        state.start_date = start;
        state.end_date = end;
        triggerFilterChange();
    }

    function resetFilters() {
        state = { ...defaultState };
        const startInput = document.getElementById("filter-start-date");
        const endInput = document.getElementById("filter-end-date");
        const regionSelect = document.getElementById("filter-region");
        const categorySelect = document.getElementById("filter-category");
        const paymentSelect = document.getElementById("filter-payment");
        const statusSelect = document.getElementById("filter-status");

        if (startInput) startInput.value = "";
        if (endInput) endInput.value = "";
        if (regionSelect) regionSelect.value = "all";
        if (categorySelect) categorySelect.value = "all";
        if (paymentSelect) paymentSelect.value = "all";
        if (statusSelect) statusSelect.value = "all";

        document.querySelectorAll(".date-preset-btn").forEach(b => {
            if (b.dataset.preset === "all") b.classList.add("active");
            else b.classList.remove("active");
        });

        triggerFilterChange();
    }

    function triggerFilterChange() {
        const event = new CustomEvent("dashboard:filtersChanged", { detail: getFilters() });
        window.dispatchEvent(event);
    }

    function getFilters() {
        return { ...state };
    }

    function getQueryString() {
        const params = new URLSearchParams();
        for (const [key, value] of Object.entries(state)) {
            if (value && value !== "all") {
                params.append(key, value);
            }
        }
        return params.toString();
    }

    return {
        init,
        getFilters,
        getQueryString,
        applyDatePreset,
        resetFilters,
        triggerFilterChange
    };
})();

document.addEventListener("DOMContentLoaded", function () {
    window.FilterEngine.init();
});
