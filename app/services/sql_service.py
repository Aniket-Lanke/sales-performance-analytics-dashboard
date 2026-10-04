import time
import logging
import re
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from app.database import get_engine

logger = logging.getLogger("sales_dashboard.sql_analytics")

# Catalog of Advanced SQL Analytics Queries demonstrating CTEs, Window Functions, and Joins
PRESET_QUERIES = [
    {
        "id": "monthly_yoy_lag",
        "title": "Monthly Revenue & YoY Growth (CTEs + LAG Window Function)",
        "category": "Window Functions & CTEs",
        "description": "Calculates monthly sales revenue, compares it against the same month from the prior year using LAG(..., 12), and calculates the exact YoY growth percentage.",
        "sql": """WITH monthly_sales AS (
    SELECT
        SUBSTR(o.order_date, 1, 7) AS year_month,
        CAST(SUBSTR(o.order_date, 1, 4) AS INT) AS order_year,
        CAST(SUBSTR(o.order_date, 6, 2) AS INT) AS order_month,
        ROUND(SUM(oi.total_price), 2) AS current_revenue,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status IN ('Completed', 'Shipped')
    GROUP BY SUBSTR(o.order_date, 1, 7), SUBSTR(o.order_date, 1, 4), SUBSTR(o.order_date, 6, 2)
),
prior_comparison AS (
    SELECT
        year_month,
        order_year,
        order_month,
        current_revenue,
        total_orders,
        LAG(current_revenue, 12) OVER (ORDER BY year_month ASC) AS prior_year_revenue
    FROM monthly_sales
)
SELECT
    year_month,
    current_revenue,
    COALESCE(prior_year_revenue, 0.00) AS prior_year_revenue,
    total_orders,
    CASE
        WHEN prior_year_revenue IS NULL OR prior_year_revenue = 0 THEN 'N/A (Baseline)'
        ELSE ROUND(((current_revenue - prior_year_revenue) / prior_year_revenue) * 100.0, 2) || '%'
    END AS yoy_growth_pct
FROM prior_comparison
ORDER BY year_month DESC
LIMIT 24;"""
    },
    {
        "id": "regional_dense_rank",
        "title": "Regional Revenue Ranking (DENSE_RANK & Market Share)",
        "category": "Window Functions",
        "description": "Ranks commercial sales regions by total revenue using DENSE_RANK() and computes each territory's percentage contribution to overall company revenue.",
        "sql": """WITH regional_totals AS (
    SELECT
        r.region_name,
        r.country,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.quantity) AS total_units,
        ROUND(SUM(oi.total_price), 2) AS territory_revenue
    FROM regions r
    JOIN orders o ON r.region_id = o.region_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status IN ('Completed', 'Shipped')
    GROUP BY r.region_name, r.country
)
SELECT
    DENSE_RANK() OVER (ORDER BY territory_revenue DESC) AS sales_rank,
    region_name,
    country,
    total_orders,
    total_units,
    territory_revenue,
    ROUND((territory_revenue * 100.0) / SUM(territory_revenue) OVER (), 2) || '%' AS global_share_pct
FROM regional_totals
ORDER BY sales_rank ASC;"""
    },
    {
        "id": "top_products_partition",
        "title": "Top 3 Products Per Category (RANK() OVER PARTITION BY)",
        "category": "Window Functions & Joins",
        "description": "Partitions product catalog by category and ranks products within each department to isolate top revenue drivers.",
        "sql": """WITH product_revenue AS (
    SELECT
        c.category_name,
        p.product_code,
        p.product_name,
        SUM(oi.quantity) AS units_sold,
        ROUND(SUM(oi.total_price), 2) AS total_revenue
    FROM categories c
    JOIN products p ON c.category_id = p.category_id
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status IN ('Completed', 'Shipped')
    GROUP BY c.category_name, p.product_code, p.product_name
),
ranked_products AS (
    SELECT
        category_name,
        product_code,
        product_name,
        units_sold,
        total_revenue,
        RANK() OVER (PARTITION BY category_name ORDER BY total_revenue DESC) as category_rank
    FROM product_revenue
)
SELECT
    category_name,
    category_rank,
    product_code,
    product_name,
    units_sold,
    total_revenue
FROM ranked_products
WHERE category_rank <= 3
ORDER BY category_name ASC, category_rank ASC;"""
    },
    {
        "id": "customer_rfm_segments",
        "title": "Customer Value & Segmentation (Aggregates & CASE Logic)",
        "category": "Customer Analytics",
        "description": "Analyzes customer purchasing frequency, lifetime spend, and categorizes customers into High Value (VIP), Mid-Tier, and Casual segments.",
        "sql": """WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.customer_code,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.city,
        c.country,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.quantity) AS total_items_bought,
        ROUND(SUM(oi.total_price), 2) AS lifetime_spend,
        ROUND(AVG(oi.total_price), 2) AS avg_item_spend,
        MAX(o.order_date) AS most_recent_purchase
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Completed'
    GROUP BY c.customer_id, c.customer_code, c.first_name, c.last_name, c.city, c.country
)
SELECT
    customer_code,
    customer_name,
    city,
    country,
    total_orders,
    lifetime_spend,
    most_recent_purchase,
    CASE
        WHEN lifetime_spend >= 5000 THEN 'VIP / High Value'
        WHEN lifetime_spend >= 1500 THEN 'Mid-Tier Spender'
        ELSE 'Casual Spender'
    END AS spending_segment
FROM customer_metrics
ORDER BY lifetime_spend DESC
LIMIT 20;"""
    },
    {
        "id": "cumulative_running_total",
        "title": "Cumulative Running Total of Revenue (Window SUM)",
        "category": "Time-Series & Window Functions",
        "description": "Calculates running cumulative enterprise revenue day-by-day across all recorded transactions.",
        "sql": """WITH daily_sales AS (
    SELECT
        o.order_date,
        COUNT(DISTINCT o.order_id) AS daily_orders,
        ROUND(SUM(oi.total_price), 2) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status IN ('Completed', 'Shipped')
    GROUP BY o.order_date
)
SELECT
    order_date,
    daily_orders,
    daily_revenue,
    ROUND(SUM(daily_revenue) OVER (ORDER BY order_date ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue
FROM daily_sales
ORDER BY order_date DESC
LIMIT 30;"""
    },
    {
        "id": "category_profit_having",
        "title": "High Volume Categories (INNER JOIN + GROUP BY + HAVING)",
        "category": "Relational Aggregation",
        "description": "Filters product categories with significant sales volume, computing revenue, unit margins, and order frequency.",
        "sql": """SELECT
    c.category_name,
    COUNT(DISTINCT o.order_id) AS order_occurrences,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.total_price), 2) AS gross_revenue,
    ROUND(SUM(oi.quantity * p.cost_price), 2) AS estimated_cost,
    ROUND(SUM(oi.total_price) - SUM(oi.quantity * p.cost_price), 2) AS estimated_gross_profit,
    ROUND(((SUM(oi.total_price) - SUM(oi.quantity * p.cost_price)) / SUM(oi.total_price)) * 100.0, 2) || '%' AS gross_margin_pct
FROM categories c
INNER JOIN products p ON c.category_id = p.category_id
INNER JOIN order_items oi ON p.product_id = oi.product_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY c.category_id, c.category_name
HAVING order_occurrences >= 100
ORDER BY gross_revenue DESC;"""
    }
]


class SQLAnalyticsService:
    """Service to execute preset queries and safely evaluate read-only analytical queries."""

    def __init__(self, engine=None):
        self.engine = engine or get_engine()

    def get_presets(self) -> List[Dict[str, Any]]:
        return PRESET_QUERIES

    def get_preset_by_id(self, preset_id: str) -> Optional[Dict[str, Any]]:
        for p in PRESET_QUERIES:
            if p["id"] == preset_id:
                return p
        return None

    def execute_query(self, raw_sql: str) -> Dict[str, Any]:
        """
        Executes a SQL query safely (Read-Only validation).
        Returns columns, row dictionaries, row count, execution time in ms, and status.
        """
        clean_sql = raw_sql.strip()

        # Security check: Only allow SELECT and WITH statements
        first_word = clean_sql.split()[0].upper() if clean_sql.split() else ""
        if first_word not in ("SELECT", "WITH", "EXPLAIN"):
            return {
                "success": False,
                "error": "Security Restriction: Only analytical queries starting with 'SELECT', 'WITH', or 'EXPLAIN' are permitted.",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0
            }

        # Check for harmful keywords
        forbidden = [r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b", r"\bALTER\b", r"\bTRUNCATE\b", r"\bGRANT\b", r"\bEXEC\b"]
        for pattern in forbidden:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                return {
                    "success": False,
                    "error": f"Security Restriction: Write/DDL operation detected in query: {pattern}",
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": 0.0
                }

        t_start = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                cursor_result = conn.execute(text(clean_sql))
                columns = list(cursor_result.keys())
                raw_rows = cursor_result.mappings().fetchmany(500) # Fetch up to 500 rows for display
                rows = [dict(r) for r in raw_rows]
                
            execution_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time_ms,
                "error": None
            }
        except Exception as e:
            execution_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            logger.error(f"SQL execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": execution_time_ms
            }
