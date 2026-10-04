/**
 * Sales Performance Analytics - High-Precision Chart Engine (Plotly.js)
 * Clean enterprise styling with responsive auto-resizing.
 */

window.ChartEngine = (function () {
    const defaultFont = { family: "Inter, sans-serif", color: "#475569" };
    const palette = ["#2563eb", "#0d9488", "#10b981", "#f59e0b", "#8b5cf6", "#f43f5e", "#06b6d4"];

    function getBaseLayout(title = "") {
        return {
            font: defaultFont,
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            margin: { t: 30, r: 25, b: 40, l: 55 },
            autosize: true,
            hoverlabel: {
                bgcolor: "#0f172a",
                font: { family: "Inter, sans-serif", color: "#ffffff", size: 12 },
                bordercolor: "#38bdf8"
            }
        };
    }

    function renderSalesTrend(elementId, trendData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!trendData || trendData.length === 0) {
            renderEmptyState(elementId, "No sales trend data available for selected filters.");
            return;
        }

        const months = trendData.map(d => d.year_month);
        const revenues = trendData.map(d => d.revenue);
        const orders = trendData.map(d => d.orders_count);

        const traceRevenue = {
            x: months,
            y: revenues,
            name: "Revenue ($)",
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#2563eb", width: 3, shape: "spline" },
            marker: { size: 6, color: "#1d4ed8" },
            fill: "tozeroy",
            fillcolor: "rgba(37, 99, 235, 0.08)",
            hovertemplate: "<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>"
        };

        const traceOrders = {
            x: months,
            y: orders,
            name: "Total Orders",
            type: "bar",
            yaxis: "y2",
            marker: { color: "rgba(13, 148, 136, 0.4)", line: { color: "#0d9488", width: 1.5 } },
            hovertemplate: "<b>%{x}</b><br>Orders: %{y:,}<extra></extra>"
        };

        const layout = {
            ...getBaseLayout(),
            showlegend: true,
            legend: { orientation: "h", x: 0, y: 1.15, font: { size: 11 } },
            xaxis: { showgrid: false, tickangle: -30, tickfont: { size: 10 } },
            yaxis: {
                title: "Revenue ($)",
                showgrid: true,
                gridcolor: "#f1f5f9",
                tickprefix: "$",
                tickfont: { size: 10 }
            },
            yaxis2: {
                title: "Orders Count",
                overlaying: "y",
                side: "right",
                showgrid: false,
                tickfont: { size: 10 }
            }
        };

        Plotly.newPlot(elementId, [traceOrders, traceRevenue], layout, { responsive: true, displayModeBar: false });
    }

    function renderYoYComparison(elementId, yoyData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!yoyData || !yoyData.years || Object.keys(yoyData.years).length === 0) {
            renderEmptyState(elementId, "No YoY comparison data available.");
            return;
        }

        const months = yoyData.months;
        const traces = [];
        const yearColors = {
            "2023": "#94a3b8",
            "2024": "#0d9488",
            "2025": "#2563eb",
            "2026": "#f59e0b"
        };

        let colorIdx = 0;
        for (const [year, revValues] of Object.entries(yoyData.years)) {
            const yrColor = yearColors[year] || palette[colorIdx % palette.length];
            traces.push({
                x: months,
                y: revValues,
                name: `FY ${year}`,
                type: "scatter",
                mode: "lines+markers",
                line: { color: yrColor, width: year === "2025" || year === "2026" ? 3 : 2 },
                marker: { size: 6 },
                hovertemplate: `<b>${year} - %{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>`
            });
            colorIdx++;
        }

        const layout = {
            ...getBaseLayout(),
            showlegend: true,
            legend: { orientation: "h", x: 0, y: 1.15, font: { size: 11 } },
            xaxis: { showgrid: false, tickfont: { size: 11 } },
            yaxis: {
                title: "Monthly Revenue ($)",
                showgrid: true,
                gridcolor: "#f1f5f9",
                tickprefix: "$",
                tickfont: { size: 10 }
            }
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
    }

    function renderCategoryDonut(elementId, categoryData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!categoryData || categoryData.length === 0) {
            renderEmptyState(elementId, "No category sales recorded.");
            return;
        }

        const labels = categoryData.map(c => c.category_name);
        const values = categoryData.map(c => c.total_revenue);

        const trace = {
            labels: labels,
            values: values,
            type: "pie",
            hole: 0.58,
            marker: { colors: palette },
            textinfo: "percent",
            hoverinfo: "label+value+percent",
            hovertemplate: "<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>"
        };

        const layout = {
            ...getBaseLayout(),
            showlegend: true,
            legend: { orientation: "v", x: 1.02, y: 0.5, font: { size: 10 } },
            margin: { t: 15, r: 10, b: 15, l: 10 }
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    function renderRegionBar(elementId, regionData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!regionData || regionData.length === 0) {
            renderEmptyState(elementId, "No regional data available.");
            return;
        }

        // Sort ascending for horizontal bar chart
        const sorted = [...regionData].reverse();
        const names = sorted.map(r => r.region_name);
        const revenues = sorted.map(r => r.total_revenue);
        const orders = sorted.map(r => r.total_orders);

        const trace = {
            y: names,
            x: revenues,
            type: "bar",
            orientation: "h",
            marker: {
                color: revenues,
                colorscale: [
                    [0, "#38bdf8"],
                    [0.5, "#2563eb"],
                    [1, "#0d9488"]
                ]
            },
            hovertemplate: "<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>"
        };

        const layout = {
            ...getBaseLayout(),
            margin: { t: 10, r: 25, b: 40, l: 120 },
            xaxis: {
                title: "Total Revenue ($)",
                showgrid: true,
                gridcolor: "#f1f5f9",
                tickprefix: "$"
            },
            yaxis: { showgrid: false }
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    function renderTopProductsBar(elementId, productsData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!productsData || productsData.length === 0) {
            renderEmptyState(elementId, "No product sales recorded.");
            return;
        }

        const sorted = [...productsData].reverse();
        const names = sorted.map(p => p.product_name.length > 22 ? p.product_name.substring(0, 22) + "..." : p.product_name);
        const revenues = sorted.map(p => p.total_revenue);

        const trace = {
            y: names,
            x: revenues,
            type: "bar",
            orientation: "h",
            marker: { color: "#2563eb", cornerRadius: 4 },
            hovertemplate: "<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>"
        };

        const layout = {
            ...getBaseLayout(),
            margin: { t: 10, r: 25, b: 40, l: 140 },
            xaxis: {
                title: "Revenue ($)",
                showgrid: true,
                gridcolor: "#f1f5f9",
                tickprefix: "$"
            },
            yaxis: { showgrid: false }
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    function renderCustomerSegments(elementId, segmentsData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!segmentsData || segmentsData.length === 0) {
            renderEmptyState(elementId, "No customer segmentation data found.");
            return;
        }

        const labels = segmentsData.map(s => s.segment_name);
        const values = segmentsData.map(s => s.customer_count);
        const colors = ["#2563eb", "#0d9488", "#f59e0b"];

        const trace = {
            labels: labels,
            values: values,
            type: "pie",
            hole: 0.5,
            marker: { colors: colors },
            textinfo: "label+percent",
            hovertemplate: "<b>%{label}</b><br>Customers: %{value:,}<br>Share: %{percent}<extra></extra>"
        };

        const layout = {
            ...getBaseLayout(),
            showlegend: false,
            margin: { t: 15, r: 15, b: 15, l: 15 }
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    function renderPaymentMethods(elementId, paymentData) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (!paymentData || paymentData.length === 0) {
            renderEmptyState(elementId, "No payment records found.");
            return;
        }

        const labels = paymentData.map(p => p.payment_method);
        const values = paymentData.map(p => p.total_revenue);

        const trace = {
            labels: labels,
            values: values,
            type: "pie",
            hole: 0.55,
            marker: { colors: ["#2563eb", "#0d9488", "#10b981", "#8b5cf6"] },
            hovertemplate: "<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>"
        };

        const layout = {
            ...getBaseLayout(),
            showlegend: true,
            legend: { orientation: "v", x: 1.02, y: 0.5, font: { size: 10 } },
            margin: { t: 10, r: 10, b: 10, l: 10 }
        };

        Plotly.newPlot(elementId, [trace], layout, { responsive: true, displayModeBar: false });
    }

    function renderEmptyState(elementId, message) {
        const el = document.getElementById(elementId);
        if (!el) return;
        el.innerHTML = `
            <div class="d-flex flex-column align-items-center justify-content-center h-100 py-5 text-muted">
                <i class="bi bi-bar-chart fs-1 mb-2 opacity-50"></i>
                <p class="small mb-0">${message}</p>
            </div>
        `;
    }

    return {
        renderSalesTrend,
        renderYoYComparison,
        renderCategoryDonut,
        renderRegionBar,
        renderTopProductsBar,
        renderCustomerSegments,
        renderPaymentMethods
    };
})();
