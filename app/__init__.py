import logging
from flask import Flask, jsonify, render_template, request
from app.config import Config, config_by_name
from app.database import init_db, get_session

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("sales_dashboard")


def create_app(config_name="default"):
    """Application factory for Sales Performance Analytics Dashboard."""
    app = Flask(__name__)
    
    # Load configuration
    cfg = config_by_name.get(config_name, Config)
    app.config.from_object(cfg)
    cfg.init_folders()

    logger.info("Initializing Sales Analytics Dashboard application...")

    # Initialize Database Schema if not already present
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database initialization deferred or encountered warning: {e}")

    # Register Blueprints
    from app.routes.main_routes import main_bp
    from app.routes.api_routes import api_bp
    from app.routes.data_routes import data_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(data_bp)

    # Teardown database session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass

    # Error Handlers
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Resource not found"}), 404
        return render_template("base.html", page_title="Page Not Found", active_page="404", error_message="The requested dashboard page could not be located."), 404

    @app.errorhandler(413)
    def handle_413(e):
        return jsonify({
            "status": "error",
            "message": "File exceeds the allowed size limit (maximum 32MB)."
        }), 413

    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "An unexpected server error occurred while processing your request."
            }), 500
        return render_template("base.html", page_title="Server Error", active_page="500", error_message="An internal system error occurred. Please verify database connectivity."), 500

    return app
