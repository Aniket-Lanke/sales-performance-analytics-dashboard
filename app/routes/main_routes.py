from flask import Blueprint, render_template, request
from app.database import get_db_status
from app.services.analytics_service import AnalyticsService

main_bp = Blueprint("main", __name__)
analytics_service = AnalyticsService()


@main_bp.context_processor
def inject_global_context():
    """Injects database status and filter options into all templates."""
    db_status = get_db_status()
    try:
        filter_options = analytics_service.get_filter_options()
    except Exception:
        filter_options = {"regions": [], "categories": [], "payment_methods": [], "min_date": "2023-01-01", "max_date": "2026-03-31"}
    
    return {
        "db_status": db_status,
        "filter_options": filter_options
    }


@main_bp.route("/")
@main_bp.route("/overview")
def overview():
    return render_template("overview.html", active_page="overview", page_title="Executive Overview")


@main_bp.route("/sales")
def sales():
    return render_template("sales.html", active_page="sales", page_title="Sales Performance & Trends")


@main_bp.route("/products")
def products():
    return render_template("products.html", active_page="products", page_title="Product & Category Performance")


@main_bp.route("/regional")
def regional():
    return render_template("regional.html", active_page="regional", page_title="Regional Sales Analysis")


@main_bp.route("/customers")
def customers():
    return render_template("customers.html", active_page="customers", page_title="Customer Segmentation")


@main_bp.route("/data-import")
def data_import():
    return render_template("data_import.html", active_page="data_import", page_title="Data Import & Quality Engine")


@main_bp.route("/sql-analytics")
def sql_analytics():
    return render_template("sql_analytics.html", active_page="sql_analytics", page_title="Advanced SQL Analytics")


@main_bp.route("/reports")
def reports():
    return render_template("reports.html", active_page="reports", page_title="Reports & Analytics Export")


@main_bp.route("/documentation")
def documentation():
    return render_template("documentation.html", active_page="documentation", page_title="System Architecture & Documentation")
