import logging
from flask import Blueprint, request, jsonify, Response, send_file
from app.services.analytics_service import AnalyticsService
from app.services.sql_service import SQLAnalyticsService
from app.services.export_service import ExportService

logger = logging.getLogger("sales_dashboard.api")

api_bp = Blueprint("api", __name__, url_prefix="/api")

analytics_service = AnalyticsService()
sql_service = SQLAnalyticsService()
export_service = ExportService(analytics_service)


def _extract_filters_from_request():
    """Extracts analytical filters from request query parameters."""
    return {
        "start_date": request.args.get("start_date", "").strip() or None,
        "end_date": request.args.get("end_date", "").strip() or None,
        "region_id": request.args.get("region_id", "all").strip(),
        "category_id": request.args.get("category_id", "all").strip(),
        "payment_method": request.args.get("payment_method", "all").strip(),
        "order_status": request.args.get("order_status", "all").strip(),
    }


# ==============================================================================
# Dashboard Analytics Endpoints
# ==============================================================================

@api_bp.route("/dashboard/kpis", methods=["GET"])
def get_kpis():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_kpis(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"KPI calculation error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute KPIs"}), 500


@api_bp.route("/dashboard/sales-trend", methods=["GET"])
def get_sales_trend():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_monthly_sales_trend(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Sales trend error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute sales trend"}), 500


@api_bp.route("/dashboard/yoy-comparison", methods=["GET"])
def get_yoy_comparison():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_yoy_comparison(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"YoY comparison error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute YoY comparison"}), 500


@api_bp.route("/dashboard/top-products", methods=["GET"])
def get_top_products():
    try:
        filters = _extract_filters_from_request()
        limit = int(request.args.get("limit", 10))
        data = analytics_service.get_top_products(filters, limit=limit)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Top products error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute top products"}), 500


@api_bp.route("/dashboard/category-performance", methods=["GET"])
def get_category_performance():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_category_performance(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Category performance error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute category performance"}), 500


@api_bp.route("/dashboard/region-performance", methods=["GET"])
def get_region_performance():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_region_performance(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Regional performance error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute regional performance"}), 500


@api_bp.route("/dashboard/customer-segments", methods=["GET"])
def get_customer_segments():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_customer_segments(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Customer segments error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute customer segments"}), 500


@api_bp.route("/dashboard/payment-methods", methods=["GET"])
def get_payment_methods():
    try:
        filters = _extract_filters_from_request()
        data = analytics_service.get_payment_methods(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Payment methods error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to compute payment methods"}), 500


@api_bp.route("/dashboard/orders-table", methods=["GET"])
def get_orders_table():
    try:
        filters = _extract_filters_from_request()
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 25))
        data = analytics_service.get_orders_table(filters, page=page, page_size=page_size)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Orders table error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to retrieve orders"}), 500


@api_bp.route("/filter-options", methods=["GET"])
def get_filter_options():
    try:
        options = analytics_service.get_filter_options()
        return jsonify({"status": "success", "data": options}), 200
    except Exception as e:
        logger.error(f"Filter options error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to retrieve filter options"}), 500


# ==============================================================================
# SQL Analytics Endpoints
# ==============================================================================

@api_bp.route("/sql/presets", methods=["GET"])
def get_sql_presets():
    try:
        presets = sql_service.get_presets()
        return jsonify({"status": "success", "data": presets}), 200
    except Exception as e:
        logger.error(f"SQL presets error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to load presets"}), 500


@api_bp.route("/sql/execute", methods=["POST"])
def execute_sql():
    try:
        body = request.get_json(force=True, silent=True) or {}
        query = body.get("query", "").strip()
        if not query:
            return jsonify({"status": "error", "message": "Query string is required"}), 400

        result = sql_service.execute_query(query)
        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Execute SQL error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ==============================================================================
# Export Endpoints
# ==============================================================================

@api_bp.route("/reports/export", methods=["GET"])
def export_report():
    try:
        export_format = request.args.get("format", "csv").lower()
        filters = _extract_filters_from_request()

        if export_format == "csv":
            csv_content = export_service.export_filtered_csv(filters)
            return Response(
                csv_content,
                mimetype="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=sales_analytics_export.csv"
                }
            )
        elif export_format in ("excel", "xlsx"):
            excel_stream = export_service.export_excel_report(filters)
            return send_file(
                excel_stream,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="sales_performance_report.xlsx"
            )
        else:
            return jsonify({"status": "error", "message": f"Unsupported export format: {export_format}"}), 400
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to generate report export"}), 500


@api_bp.route("/reports/kpis-summary", methods=["GET"])
def export_kpi_summary():
    try:
        filters = _extract_filters_from_request()
        kpis = analytics_service.get_kpis(filters)
        return jsonify({"status": "success", "data": kpis}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
