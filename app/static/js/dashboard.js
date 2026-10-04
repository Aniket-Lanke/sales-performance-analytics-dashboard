/**
 * Sales Performance Analytics - Main Dashboard Controller
 * Synchronizes KPI metrics, interactive charts, and real-time filter refreshes.
 */

window.DashboardApp = (function () {

    const currencyFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
    const numberFmt = new Intl.NumberFormat("en-US");

    function init() {
        // Initial load based on current page
        refreshAll();

        // Listen for filter changes
        window.addEventListener("dashboard:filtersChanged", function (e) {
            refreshAll();
        });

        // Quick Export listeners
        const exportCsvBtn = document.getElementById("btn-export-csv");
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener("click", function (e) {
                e.preventDefault();
                downloadExport("csv");
            });
        }

        const exportExcelBtn = document.getElementById("btn-export-excel");
        if (exportExcelBtn) {
            exportExcelBtn.addEventListener("click", function (e) {
                e.preventDefault();
                downloadExport("excel");
            });
        }

        // Window resize debounce for responsive charts
        let resizeTimer;
        window.addEventListener("resize", function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                const charts = document.querySelectorAll(".js-plotly-plot");
                charts.forEach(c => Plotly.Plots.resize(c));
            }, 200);
        });
    }

    function refreshAll() {
        const queryStr = window.FilterEngine ? window.FilterEngine.getQueryString() : "";
        loadKpis(queryStr);
        loadPageSpecificVisuals(queryStr);
    }

    function loadKpis(queryStr) {
        const kpiContainers = document.querySelectorAll("[data-kpi]");
        if (kpiContainers.length === 0) return;

        fetch(`/api/dashboard/kpis?${queryStr}`)
            .then(res => res.json())
            .then(res => {
                if (res.status === "success") {
                    updateKpiCards(res.data);
                }
            })
            .catch(err => console.error("Error loading KPIs:", err));
    }

    function updateKpiCards(data) {
        // Revenue
        const elRev = document.getElementById("kpi-revenue");
        if (elRev) elRev.textContent = currencyFmt.format(data.total_revenue);

        // Orders
        const elOrders = document.getElementById("kpi-orders");
        if (elOrders) elOrders.textContent = numberFmt.format(data.total_orders);

        // Units
        const elUnits = document.getElementById("kpi-units");
        if (elUnits) elUnits.textContent = numberFmt.format(data.units_sold);

        // Customers
        const elCust = document.getElementById("kpi-customers");
        if (elCust) elCust.textContent = numberFmt.format(data.total_customers);

        // AOV
        const elAov = document.getElementById("kpi-aov");
        if (elAov) elAov.textContent = currencyFmt.format(data.aov);

        // YoY Growth
        const elGrowth = document.getElementById("kpi-growth");
        if (elGrowth) {
            const growth = data.growth_pct;
            const sign = growth > 0 ? "+" : "";
            elGrowth.textContent = `${sign}${growth.toFixed(1)}%`;
            elGrowth.className = growth >= 0 ? "badge-growth-pos" : "badge-growth-neg";
        }

        // Best Product
        const elBestProd = document.getElementById("kpi-best-product");
        if (elBestProd) elBestProd.textContent = data.best_product.name || "N/A";
        const elBestProdSub = document.getElementById("kpi-best-product-rev");
        if (elBestProdSub) elBestProdSub.textContent = currencyFmt.format(data.best_product.revenue);

        // Top Region
        const elTopReg = document.getElementById("kpi-top-region");
        if (elTopReg) elTopReg.textContent = data.top_region.name || "N/A";
        const elTopRegSub = document.getElementById("kpi-top-region-rev");
        if (elTopRegSub) elTopRegSub.textContent = currencyFmt.format(data.top_region.revenue);
    }

    function loadPageSpecificVisuals(queryStr) {
        // Overview Dashboard Visuals
        if (document.getElementById("chart-sales-trend")) {
            fetch(`/api/dashboard/sales-trend?${queryStr}`)
                .then(r => r.json())
                .then(r => window.ChartEngine.renderSalesTrend("chart-sales-trend", r.data));
        }

        if (document.getElementById("chart-category-donut")) {
            fetch(`/api/dashboard/category-performance?${queryStr}`)
                .then(r => r.json())
                .then(r => window.ChartEngine.renderCategoryDonut("chart-category-donut", r.data));
        }

        if (document.getElementById("chart-top-products")) {
            fetch(`/api/dashboard/top-products?limit=8&${queryStr}`)
                .then(r => r.json())
                .then(r => window.ChartEngine.renderTopProductsBar("chart-top-products", r.data));
        }

        if (document.getElementById("chart-region-bar")) {
            fetch(`/api/dashboard/region-performance?${queryStr}`)
                .then(r => r.json())
                .then(r => window.ChartEngine.renderRegionBar("chart-region-bar", r.data));
        }

        // Sales Analysis Page
        if (document.getElementById("chart-yoy-comparison")) {
            fetch(`/api/dashboard/yoy-comparison?${queryStr}`)
                .then(r => r.json())
                .then(r => window.ChartEngine.renderYoYComparison("chart-yoy-comparison", r.data));
        }

        if (document.getElementById("chart-payment-methods")) {
            fetch(`/api/dashboard/payment-methods?${queryStr}`)
                .then(r => r.json())
                .then(r => window.ChartEngine.renderPaymentMethods("chart-payment-methods", r.data));
        }

        // Customer Segments Page
        if (document.getElementById("chart-customer-segments")) {
            fetch(`/api/dashboard/customer-segments?${queryStr}`)
                .then(r => r.json())
                .then(r => {
                    window.ChartEngine.renderCustomerSegments("chart-customer-segments", r.data.segments);
                    renderTopCustomersTable(r.data.top_customers);
                });
        }

        // Orders Table if present
        loadOrdersTable(queryStr, 1);
    }

    function renderTopCustomersTable(customers) {
        const tbody = document.getElementById("table-top-customers-body");
        if (!tbody || !customers) return;

        tbody.innerHTML = customers.map((c, i) => `
            <tr>
                <td class="fw-bold text-center text-muted">${i + 1}</td>
                <td><span class="badge bg-light text-dark font-monospace">${c.customer_code}</span></td>
                <td class="fw-semibold">${c.customer_name}</td>
                <td class="small text-muted">${c.email}</td>
                <td>${c.city}, ${c.country}</td>
                <td class="text-center">${c.orders_count}</td>
                <td class="text-end fw-bold text-primary">${currencyFmt.format(c.total_spent)}</td>
                <td class="text-end text-muted small">${currencyFmt.format(c.avg_order_val)}</td>
            </tr>
        `).join("");
    }

    function loadOrdersTable(queryStr, page = 1) {
        const tableContainer = document.getElementById("orders-table-container");
        if (!tableContainer) return;

        fetch(`/api/dashboard/orders-table?page=${page}&page_size=15&${queryStr}`)
            .then(r => r.json())
            .then(res => {
                if (res.status === "success") {
                    renderOrdersTable(res.data);
                }
            });
    }

    function renderOrdersTable(data) {
        const tbody = document.getElementById("orders-table-body");
        const pagination = document.getElementById("orders-pagination");
        const countBadge = document.getElementById("orders-count-badge");
        if (!tbody) return;

        if (countBadge) countBadge.textContent = `${numberFmt.format(data.total_count)} Transactions`;

        if (data.orders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No orders match the selected filters.</td></tr>`;
            if (pagination) pagination.innerHTML = "";
            return;
        }

        tbody.innerHTML = data.orders.map(o => `
            <tr>
                <td class="font-monospace fw-bold text-primary">${o.order_number}</td>
                <td>${o.order_date}</td>
                <td>${o.customer_name}</td>
                <td><span class="badge bg-light text-secondary border">${o.region_name}</span></td>
                <td>${o.payment_method}</td>
                <td>
                    <span class="badge ${o.order_status === 'Completed' ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-secondary-subtle text-secondary'}">
                        ${o.order_status}
                    </span>
                </td>
                <td class="text-center">${o.items_count}</td>
                <td class="text-end fw-bold">${currencyFmt.format(o.order_total)}</td>
            </tr>
        `).join("");

        // Render pagination controls
        if (pagination && data.total_pages > 1) {
            let pagHtml = `<ul class="pagination pagination-sm justify-content-end mb-0">`;
            const prevDisabled = data.page <= 1 ? "disabled" : "";
            pagHtml += `<li class="page-item ${prevDisabled}"><a class="page-link" href="#" onclick="DashboardApp.goToOrdersPage(${data.page - 1}); return false;">Prev</a></li>`;
            
            const startP = Math.max(1, data.page - 2);
            const endP = Math.min(data.total_pages, data.page + 2);
            for (let p = startP; p <= endP; p++) {
                const active = p === data.page ? "active" : "";
                pagHtml += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="DashboardApp.goToOrdersPage(${p}); return false;">${p}</a></li>`;
            }

            const nextDisabled = data.page >= data.total_pages ? "disabled" : "";
            pagHtml += `<li class="page-item ${nextDisabled}"><a class="page-link" href="#" onclick="DashboardApp.goToOrdersPage(${data.page + 1}); return false;">Next</a></li>`;
            pagHtml += `</ul>`;
            pagination.innerHTML = pagHtml;
        }
    }

    function goToOrdersPage(page) {
        const queryStr = window.FilterEngine ? window.FilterEngine.getQueryString() : "";
        loadOrdersTable(queryStr, page);
    }

    function downloadExport(format) {
        const queryStr = window.FilterEngine ? window.FilterEngine.getQueryString() : "";
        window.location.href = `/api/reports/export?format=${format}&${queryStr}`;
    }

    return {
        init,
        refreshAll,
        goToOrdersPage,
        downloadExport
    };
})();

document.addEventListener("DOMContentLoaded", function () {
    window.DashboardApp.init();
});
