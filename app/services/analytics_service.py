import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy import text
from app.database import get_engine

logger = logging.getLogger("sales_dashboard.analytics")


class AnalyticsService:
    """
    Core Business Analytics service delivering dynamic KPI calculations,
    aggregate metrics, and visualization feeds with strict zero-division protection.
    """

    def __init__(self, engine=None):
        self.engine = engine or get_engine()

    def _build_filter_clause(self, filters: Dict[str, Any], date_col: str = "o.order_date") -> (str, dict):
        """Builds parameterized WHERE clauses based on user filter selections."""
        clauses = ["1=1"]
        params = {}

        if filters.get("start_date"):
            clauses.append(f"{date_col} >= :start_date")
            params["start_date"] = filters["start_date"]

        if filters.get("end_date"):
            clauses.append(f"{date_col} <= :end_date")
            params["end_date"] = filters["end_date"]

        if filters.get("region_id") and filters["region_id"] != "all":
            clauses.append("o.region_id = :region_id")
            params["region_id"] = int(filters["region_id"])

        if filters.get("category_id") and filters["category_id"] != "all":
            clauses.append("p.category_id = :category_id")
            params["category_id"] = int(filters["category_id"])

        if filters.get("payment_method") and filters["payment_method"] != "all":
            clauses.append("o.payment_method = :payment_method")
            params["payment_method"] = str(filters["payment_method"])

        if filters.get("order_status") and filters["order_status"] != "all":
            clauses.append("o.order_status = :order_status")
            params["order_status"] = str(filters["order_status"])
        else:
            # Default to successful revenue orders if not explicitly filtering all
            clauses.append("o.order_status IN ('Completed', 'Shipped')")

        return " AND ".join(clauses), params

    def get_kpis(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates all high-level executive KPIs:
        - Total Revenue
        - Total Orders
        - Units Sold
        - Total Customers
        - Average Order Value (AOV)
        - YoY Revenue Growth %
        - Best Selling Product
        - Top Performing Region
        """
        where_clause, params = self._build_filter_clause(filters)

        # Primary aggregation query
        sql_primary = f"""
        SELECT
            COALESCE(SUM(oi.total_price), 0.0) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            COUNT(DISTINCT o.customer_id) AS total_customers
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        """

        # Best-selling product query
        sql_best_product = f"""
        SELECT p.product_name, SUM(oi.total_price) as rev, SUM(oi.quantity) as qty
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        GROUP BY p.product_id, p.product_name
        ORDER BY rev DESC
        LIMIT 1
        """

        # Top-performing region query
        sql_top_region = f"""
        SELECT r.region_name, SUM(oi.total_price) as rev
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN regions r ON o.region_id = r.region_id
        WHERE {where_clause}
        GROUP BY r.region_id, r.region_name
        ORDER BY rev DESC
        LIMIT 1
        """

        with self.engine.connect() as conn:
            prim_row = conn.execute(text(sql_primary), params).mappings().fetchone()
            best_prod_row = conn.execute(text(sql_best_product), params).mappings().fetchone()
            top_region_row = conn.execute(text(sql_top_region), params).mappings().fetchone()

        total_revenue = float(prim_row["total_revenue"]) if prim_row else 0.0
        total_orders = int(prim_row["total_orders"]) if prim_row else 0
        units_sold = int(prim_row["units_sold"]) if prim_row else 0
        total_customers = int(prim_row["total_customers"]) if prim_row else 0

        # Safe AOV Calculation
        aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

        best_product_name = best_prod_row["product_name"] if best_prod_row else "N/A"
        best_product_rev = float(best_prod_row["rev"]) if best_prod_row else 0.0

        top_region_name = top_region_row["region_name"] if top_region_row else "N/A"
        top_region_rev = float(top_region_row["rev"]) if top_region_row else 0.0

        # Calculate Prior Period Revenue for Growth %
        prior_revenue = self._calculate_prior_period_revenue(filters)
        
        # Safe YoY Growth Calculation: ((Current - Prior) / Prior) * 100
        if prior_revenue > 0:
            growth_pct = round(((total_revenue - prior_revenue) / prior_revenue) * 100.0, 2)
        elif prior_revenue == 0 and total_revenue > 0:
            growth_pct = 100.0
        else:
            growth_pct = 0.0

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "units_sold": units_sold,
            "total_customers": total_customers,
            "aov": aov,
            "growth_pct": growth_pct,
            "prior_revenue": prior_revenue,
            "best_product": {
                "name": best_product_name,
                "revenue": best_product_rev
            },
            "top_region": {
                "name": top_region_name,
                "revenue": top_region_rev
            }
        }

    def _calculate_prior_period_revenue(self, filters: Dict[str, Any]) -> float:
        """Calculates revenue for the exact comparable prior period (e.g. previous year or prior date delta)."""
        start_date_str = filters.get("start_date")
        end_date_str = filters.get("end_date")

        if not start_date_str or not end_date_str:
            # If all-time is selected, compare last 365 days with previous 365 days
            today = datetime.now().date()
            cur_start = today - timedelta(days=365)
            cur_end = today
            prior_start = cur_start - timedelta(days=365)
            prior_end = cur_start - timedelta(days=1)
        else:
            try:
                dt_start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                dt_end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                duration_days = (dt_end - dt_start).days
                
                # Check if it looks like a calendar year
                if duration_days in (364, 365, 366):
                    prior_start = dt_start.replace(year=dt_start.year - 1)
                    prior_end = dt_end.replace(year=dt_end.year - 1)
                else:
                    prior_end = dt_start - timedelta(days=1)
                    prior_start = prior_end - timedelta(days=duration_days)
            except Exception:
                return 0.0

        prior_filters = filters.copy()
        prior_filters["start_date"] = prior_start.strftime("%Y-%m-%d")
        prior_filters["end_date"] = prior_end.strftime("%Y-%m-%d")

        where_clause, params = self._build_filter_clause(prior_filters)
        sql = f"""
        SELECT COALESCE(SUM(oi.total_price), 0.0) AS prior_rev
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        """
        try:
            with self.engine.connect() as conn:
                row = conn.execute(text(sql), params).mappings().fetchone()
                return float(row["prior_rev"]) if row else 0.0
        except Exception as e:
            logger.warning(f"Error computing prior period revenue: {e}")
            return 0.0

    def get_monthly_sales_trend(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns monthly revenue, order count, and units sold over time."""
        where_clause, params = self._build_filter_clause(filters)

        # Uses substr for date formatting to ensure 100% compatibility across both SQLite and MySQL
        sql = f"""
        SELECT
            SUBSTR(o.order_date, 1, 7) AS year_month,
            COALESCE(SUM(oi.total_price), 0.0) AS revenue,
            COUNT(DISTINCT o.order_id) AS orders_count,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            ROUND(COALESCE(SUM(oi.total_price), 0.0) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        GROUP BY SUBSTR(o.order_date, 1, 7)
        ORDER BY year_month ASC
        """
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().fetchall()
            return [dict(r) for r in rows]

    def get_yoy_comparison(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Compares monthly sales across available years to show YoY trajectory."""
        where_clause, params = self._build_filter_clause(filters)
        
        sql = f"""
        SELECT
            CAST(SUBSTR(o.order_date, 1, 4) AS INT) AS order_year,
            CAST(SUBSTR(o.order_date, 6, 2) AS INT) AS order_month,
            COALESCE(SUM(oi.total_price), 0.0) AS revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        GROUP BY SUBSTR(o.order_date, 1, 4), SUBSTR(o.order_date, 6, 2)
        ORDER BY order_year, order_month
        """
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().fetchall()

        # Reshape into {year: [12 months of revenue]}
        months_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        years_data = {}
        for r in rows:
            yr = int(r["order_year"])
            m_idx = int(r["order_month"]) - 1
            if yr not in years_data:
                years_data[yr] = [0.0] * 12
            if 0 <= m_idx < 12:
                years_data[yr][m_idx] = round(float(r["revenue"]), 2)

        return {
            "months": months_names,
            "years": years_data
        }

    def get_top_products(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Returns top products ranked by revenue."""
        where_clause, params = self._build_filter_clause(filters)
        params["limit"] = limit

        sql = f"""
        SELECT
            p.product_id,
            p.product_code,
            p.product_name,
            c.category_name,
            p.unit_price,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            COALESCE(SUM(oi.total_price), 0.0) AS total_revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE {where_clause}
        GROUP BY p.product_id, p.product_code, p.product_name, c.category_name, p.unit_price
        ORDER BY total_revenue DESC
        LIMIT :limit
        """
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().fetchall()
            return [dict(r) for r in rows]

    def get_category_performance(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns revenue, units, and order count aggregated by product category."""
        where_clause, params = self._build_filter_clause(filters)

        sql = f"""
        SELECT
            c.category_id,
            c.category_name,
            COALESCE(SUM(oi.total_price), 0.0) AS total_revenue,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            COUNT(DISTINCT o.order_id) AS orders_count,
            ROUND(AVG(oi.unit_price), 2) AS avg_item_price
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE {where_clause}
        GROUP BY c.category_id, c.category_name
        ORDER BY total_revenue DESC
        """
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().fetchall()
            results = [dict(r) for r in rows]

        # Calculate percentage share
        total_rev_all = sum(r["total_revenue"] for r in results)
        for r in results:
            r["share_pct"] = round((r["total_revenue"] / total_rev_all * 100.0), 2) if total_rev_all > 0 else 0.0
            r["total_revenue"] = round(r["total_revenue"], 2)

        return results

    def get_region_performance(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns regional performance and rankings."""
        where_clause, params = self._build_filter_clause(filters)

        sql = f"""
        SELECT
            r.region_id,
            r.region_name,
            r.code AS region_code,
            r.country,
            COALESCE(SUM(oi.total_price), 0.0) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS units_sold,
            ROUND(COALESCE(SUM(oi.total_price), 0.0) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN regions r ON o.region_id = r.region_id
        WHERE {where_clause}
        GROUP BY r.region_id, r.region_name, r.code, r.country
        ORDER BY total_revenue DESC
        """
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().fetchall()
            results = [dict(r) for r in rows]

        total_rev_all = sum(r["total_revenue"] for r in results)
        for idx, r in enumerate(results, start=1):
            r["rank"] = idx
            r["share_pct"] = round((r["total_revenue"] / total_rev_all * 100.0), 2) if total_rev_all > 0 else 0.0
            r["total_revenue"] = round(r["total_revenue"], 2)

        return results

    def get_customer_segments(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates customer segmentation distribution and customer metrics:
        - High Spending (VIP): > $5,000
        - Medium Spending: $1,500 - $5,000
        - Low Spending: < $1,500
        """
        where_clause, params = self._build_filter_clause(filters)

        # Segment distribution based on active filter period spend
        sql_segments = f"""
        WITH customer_spend AS (
            SELECT
                o.customer_id,
                SUM(oi.total_price) AS period_spend,
                COUNT(DISTINCT o.order_id) AS order_count
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE {where_clause}
            GROUP BY o.customer_id
        )
        SELECT
            CASE
                WHEN period_spend >= 5000 THEN 'High Spending (VIP)'
                WHEN period_spend >= 1500 THEN 'Medium Spending'
                ELSE 'Low Spending'
            END AS segment_name,
            COUNT(*) AS customer_count,
            SUM(period_spend) AS total_segment_spend,
            ROUND(AVG(period_spend), 2) AS avg_spend_per_customer,
            SUM(order_count) AS total_orders
        FROM customer_spend
        GROUP BY segment_name
        ORDER BY total_segment_spend DESC
        """

        # Top 10 high-value customers
        sql_top_customers = f"""
        SELECT
            c.customer_id,
            c.customer_code,
            c.first_name || ' ' || c.last_name AS customer_name,
            c.email,
            c.city,
            c.country,
            COUNT(DISTINCT o.order_id) AS orders_count,
            COALESCE(SUM(oi.total_price), 0.0) AS total_spent,
            ROUND(COALESCE(SUM(oi.total_price), 0.0) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_order_val
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE {where_clause}
        GROUP BY c.customer_id, c.customer_code, c.first_name, c.last_name, c.email, c.city, c.country
        ORDER BY total_spent DESC
        LIMIT 10
        """

        with self.engine.connect() as conn:
            seg_rows = conn.execute(text(sql_segments), params).mappings().fetchall()
            top_cust_rows = conn.execute(text(sql_top_customers), params).mappings().fetchall()

        segments = [dict(r) for r in seg_rows]
        total_customers = sum(s["customer_count"] for s in segments)
        for s in segments:
            s["share_pct"] = round((s["customer_count"] / total_customers * 100.0), 2) if total_customers > 0 else 0.0
            s["total_segment_spend"] = round(s["total_segment_spend"], 2)

        return {
            "segments": segments,
            "top_customers": [dict(r) for r in top_cust_rows]
        }

    def get_payment_methods(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns revenue and order breakdown by payment method."""
        where_clause, params = self._build_filter_clause(filters)

        sql = f"""
        SELECT
            o.payment_method,
            COALESCE(SUM(oi.total_price), 0.0) AS total_revenue,
            COUNT(DISTINCT o.order_id) AS orders_count
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        GROUP BY o.payment_method
        ORDER BY total_revenue DESC
        """
        with self.engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().fetchall()
            results = [dict(r) for r in rows]

        total_rev = sum(r["total_revenue"] for r in results)
        for r in results:
            r["share_pct"] = round((r["total_revenue"] / total_rev * 100.0), 2) if total_rev > 0 else 0.0
            r["total_revenue"] = round(r["total_revenue"], 2)

        return results

    def get_orders_table(self, filters: Dict[str, Any], page: int = 1, page_size: int = 25) -> Dict[str, Any]:
        """Returns paginated order records matching current filters."""
        where_clause, params = self._build_filter_clause(filters)
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset

        # Count total matching
        sql_count = f"""
        SELECT COUNT(DISTINCT o.order_id)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_clause}
        """

        sql_data = f"""
        SELECT
            o.order_id,
            o.order_number,
            o.order_date,
            c.customer_code,
            c.first_name || ' ' || c.last_name AS customer_name,
            r.region_name,
            o.payment_method,
            o.order_status,
            COUNT(oi.order_item_id) AS items_count,
            COALESCE(SUM(oi.total_price), 0.0) AS order_total
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN regions r ON o.region_id = r.region_id
        WHERE {where_clause}
        GROUP BY o.order_id, o.order_number, o.order_date, c.customer_code, c.first_name, c.last_name, r.region_name, o.payment_method, o.order_status
        ORDER BY o.order_date DESC, o.order_id DESC
        LIMIT :limit OFFSET :offset
        """

        with self.engine.connect() as conn:
            total_count = conn.execute(text(sql_count), params).scalar() or 0
            rows = conn.execute(text(sql_data), params).mappings().fetchall()

        total_pages = max(1, (total_count + page_size - 1) // page_size)

        return {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "orders": [dict(r) for r in rows]
        }

    def get_filter_options(self) -> Dict[str, Any]:
        """Fetches distinct regions, categories, and payment methods for filter dropdowns."""
        sql_regions = "SELECT region_id, region_name FROM regions ORDER BY region_name"
        sql_categories = "SELECT category_id, category_name FROM categories ORDER BY category_name"
        sql_payments = "SELECT DISTINCT payment_method FROM orders ORDER BY payment_method"
        sql_date_bounds = "SELECT MIN(order_date) AS min_date, MAX(order_date) AS max_date FROM orders"

        with self.engine.connect() as conn:
            regions = [dict(r) for r in conn.execute(text(sql_regions)).mappings().fetchall()]
            categories = [dict(r) for r in conn.execute(text(sql_categories)).mappings().fetchall()]
            payments = [r["payment_method"] for r in conn.execute(text(sql_payments)).mappings().fetchall()]
            date_row = conn.execute(text(sql_date_bounds)).mappings().fetchone()

        return {
            "regions": regions,
            "categories": categories,
            "payment_methods": payments,
            "min_date": str(date_row["min_date"]) if date_row and date_row["min_date"] else "2023-01-01",
            "max_date": str(date_row["max_date"]) if date_row and date_row["max_date"] else datetime.now().strftime("%Y-%m-%d")
        }
