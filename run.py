import os
import sys
import argparse
from app import create_app
from app.config import Config

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sales Performance Analytics Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", default=True, help="Enable Flask debug mode")
    parser.add_argument("--seed", action="store_true", help="Generate 50,000 synthetic records on startup")
    
    args = parser.parse_args()

    if args.seed:
        print("[INFO] Seeding database with 50,000 synthetic sales transactions...")
        from app.services.generator_service import generate_synthetic_dataset
        generate_synthetic_dataset(total_records=50000, save_csv_path=str(Config.DATA_DIR / "sample_sales_data.csv"))
        print("[SUCCESS] Database seeding complete.")

    port = int(os.getenv("PORT", args.port))
    host = os.getenv("HOST", args.host)
    print(f"\n[STARTING] Sales Performance Analytics Dashboard at http://{host}:{port}")
    print(f"[DATABASE] Engine: {Config.DB_ENGINE.upper()} (Fallback to SQLite: {Config.ALLOW_SQLITE_FALLBACK})")
    print(f"[PATH] Base Directory: {Config.BASE_DIR}\n")

    app.run(host=host, port=port, debug=args.debug)
