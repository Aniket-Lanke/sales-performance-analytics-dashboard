import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
import pandas as pd
from app.config import Config
from app.database import get_session, get_engine, init_db, get_db_status
from app.models.models import (
    Category, Region, Customer, Product, Order, OrderItem, DataImportLog
)
from app.services.cleaning_service import DataCleaner
from app.services.generator_service import (
    generate_synthetic_dataset, ensure_master_records_in_db, update_customer_spending_segments
)

logger = logging.getLogger("sales_dashboard.data_routes")

data_bp = Blueprint("data", __name__, url_prefix="/api/data")

# In-memory staging for reviewed upload before committing to DB
STAGED_CLEANED_DATA = {}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@data_bp.route("/status", methods=["GET"])
def get_status():
    """Returns database status, table counts, and recent import logs."""
    try:
        db_stat = get_db_status()
        session = get_session()
        recent_logs = session.query(DataImportLog).order_by(DataImportLog.created_at.desc()).limit(10).all()
        logs_data = [l.to_dict() for l in recent_logs]
        session.close()

        return jsonify({
            "status": "success",
            "db_status": db_stat,
            "recent_imports": logs_data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching data status: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@data_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Accepts CSV or Excel upload, runs data inspection & cleaning,
    generates audit statistics, and stages the cleaned dataset for user review.
    Does NOT commit to database yet, giving user complete control.
    """
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": f"Unsupported file extension. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
        }), 400

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_filename = f"{timestamp}_{filename}"
    upload_path = Config.UPLOAD_FOLDER / saved_filename

    try:
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        file.save(upload_path)

        # Parse with Pandas
        ext = filename.rsplit(".", 1)[1].lower()
        if ext == "csv":
            df = pd.read_csv(upload_path, low_memory=False)
        else:
            df = pd.read_excel(upload_path)

        # Run Cleaning Pipeline
        cleaner = DataCleaner(df, filename=filename)
        audit_report = cleaner.run_cleaning_pipeline()

        # Cache cleaned dataframe in staging keyed by saved_filename
        STAGED_CLEANED_DATA[saved_filename] = {
            "cleaner": cleaner,
            "filename": filename,
            "upload_path": str(upload_path),
            "created_at": datetime.now()
        }

        return jsonify({
            "status": "success",
            "stage_id": saved_filename,
            "audit_report": audit_report
        }), 200

    except Exception as e:
        logger.error(f"Error processing file upload: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Data processing failed: {str(e)}"
        }), 500


@data_bp.route("/commit", methods=["POST"])
def commit_cleaned_data():
    """
    Commits approved staged cleaned records into the database.
    Logs data quality metrics and audit actions in data_import_logs.
    """
    body = request.get_json(force=True, silent=True) or {}
    stage_id = body.get("stage_id")

    if not stage_id or stage_id not in STAGED_CLEANED_DATA:
        return jsonify({
            "status": "error",
            "message": "Staged dataset not found or expired. Please upload and inspect the file again."
        }), 404

    staged_entry = STAGED_CLEANED_DATA[stage_id]
    cleaner = staged_entry["cleaner"]
    df = cleaner.cleaned_df
    stats = cleaner.stats
    filename = staged_entry["filename"]

    try:
        init_db()
        session = get_session()

        # Ensure Master lookup records
        region_id_map, cat_id_map, prod_id_map = ensure_master_records_in_db(session)

        # Pre-fetch existing customer codes
        cust_map = {c.customer_code: c.customer_id for c in session.query(Customer).all()}
        # Pre-fetch existing products
        prod_map = {p.product_code: p.product_id for p in session.query(Product).all()}

        # 1. Insert any new customers found in upload
        new_cust_objs = []
        if "customer_code" in df.columns:
            unique_custs = df["customer_code"].unique()
            for c_code in unique_custs:
                if c_code not in cust_map:
                    new_c = Customer(
                        customer_code=str(c_code),
                        first_name="Imported",
                        last_name=f"User_{str(c_code)[-4:]}",
                        email=f"{str(c_code).lower()}@imported-customer.com",
                        segment="Standard",
                        country="United States"
                    )
                    new_cust_objs.append(new_c)

            if new_cust_objs:
                session.bulk_save_objects(new_cust_objs)
                session.commit()
                # Refresh map
                cust_map = {c.customer_code: c.customer_id for c in session.query(Customer).all()}

        # 2. Insert any new categories
        if "category_name" in df.columns:
            for cat_name in df["category_name"].unique():
                if cat_name not in cat_id_map:
                    new_cat = Category(category_name=cat_name, description="Imported category")
                    session.add(new_cat)
                    session.flush()
                    cat_id_map[cat_name] = new_cat.category_id
            session.commit()

        # 3. Insert any new products
        new_prods = []
        for _, row in df.iterrows():
            p_code = str(row.get("product_code", "PROD-GENERIC"))
            if p_code not in prod_map:
                cat_name = row.get("category_name", "General Supplies")
                cat_id = cat_id_map.get(cat_name, list(cat_id_map.values())[0])
                p_name = row.get("product_name", f"Product {p_code}")
                price = float(row.get("unit_price", 10.0))
                new_p = Product(
                    product_code=p_code,
                    product_name=p_name,
                    category_id=cat_id,
                    unit_price=price,
                    cost_price=round(price * 0.65, 2),
                    sku=p_code,
                    is_active=True
                )
                session.add(new_p)
                session.flush()
                prod_map[p_code] = new_p.product_id
        session.commit()

        # 4. Group by order_number and insert orders + items
        orders_inserted = 0
        items_inserted = 0

        # Group rows by order
        grouped = df.groupby("order_number")

        for order_num, group_rows in grouped:
            first_row = group_rows.iloc[0]
            c_code = first_row.get("customer_code", "CUST-UNASSIGNED")
            customer_id = cust_map.get(c_code, list(cust_map.values())[0])

            r_name = first_row.get("region_name", "North America")
            region_id = region_id_map.get(r_name, list(region_id_map.values())[0])

            order_date_str = str(first_row.get("order_date"))
            order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
            order_timestamp = datetime.strptime(f"{order_date_str} 12:00:00", "%Y-%m-%d %H:%M:%S")

            pay_method = str(first_row.get("payment_method", "Credit Card"))
            status = str(first_row.get("order_status", "Completed"))
            order_total = float(group_rows["total_price"].sum())

            # Check if order already exists in DB
            existing_order = session.query(Order).filter_by(order_number=str(order_num)).first()
            if existing_order:
                # Update total
                existing_order.total_amount = order_total
                curr_order_id = existing_order.order_id
            else:
                new_order = Order(
                    order_number=str(order_num),
                    customer_id=customer_id,
                    region_id=region_id,
                    order_date=order_date,
                    order_timestamp=order_timestamp,
                    payment_method=pay_method,
                    order_status=status,
                    shipping_cost=0.00,
                    discount_amount=0.00,
                    total_amount=order_total,
                    is_synthetic=False
                )
                session.add(new_order)
                session.flush()
                curr_order_id = new_order.order_id
                orders_inserted += 1

            for _, itm_row in group_rows.iterrows():
                p_code = str(itm_row.get("product_code", "PROD-GENERIC"))
                prod_id = prod_map.get(p_code, list(prod_map.values())[0])
                qty = int(itm_row.get("quantity", 1))
                u_price = float(itm_row.get("unit_price", 0.0))
                d_rate = float(itm_row.get("discount_rate", 0.0))
                tot_price = float(itm_row.get("total_price", qty * u_price * (1 - d_rate)))

                new_item = OrderItem(
                    order_id=curr_order_id,
                    product_id=prod_id,
                    quantity=qty,
                    unit_price=u_price,
                    discount_rate=d_rate,
                    total_price=tot_price
                )
                session.add(new_item)
                items_inserted += 1

        # 5. Record Import Audit Log
        import_log = DataImportLog(
            filename=filename,
            file_type="Uploaded File",
            total_rows=stats["total_rows"],
            valid_records=stats["valid_records"],
            duplicate_rows=stats["duplicate_rows"],
            missing_values_handled=stats["missing_values_handled"],
            rejected_rows=stats["rejected_rows"],
            quality_score=stats["quality_score"],
            status="Committed",
            audit_details=json.dumps(cleaner.audit_actions)
        )
        session.add(import_log)
        session.commit()

        # Update customer spending segmentation
        update_customer_spending_segments(session)
        session.close()

        # Clear staged data
        del STAGED_CLEANED_DATA[stage_id]

        return jsonify({
            "status": "success",
            "message": f"Successfully committed {orders_inserted:,} orders ({items_inserted:,} line items) to the database.",
            "stats": {
                "orders_inserted": orders_inserted,
                "items_inserted": items_inserted,
                "quality_score": stats["quality_score"]
            }
        }), 200

    except Exception as e:
        logger.error(f"Error committing staged data to DB: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Database commit failed: {str(e)}"}), 500


@data_bp.route("/generate", methods=["POST"])
def generate_sample_data():
    """
    Generates 50,000+ realistic synthetic sales records,
    populates the database, and saves to data/sample_sales_data.csv.
    """
    body = request.get_json(force=True, silent=True) or {}
    record_count = int(body.get("count", 50000))
    # Cap between 1,000 and 100,000 for web triggers
    record_count = max(1000, min(100000, record_count))

    csv_path = Config.DATA_DIR / "sample_sales_data.csv"

    try:
        logger.info(f"Generating synthetic dataset of {record_count:,} records via API...")
        df = generate_synthetic_dataset(
            total_records=record_count,
            save_csv_path=str(csv_path),
            seed_to_db=True
        )

        session = get_session()
        log = DataImportLog(
            filename="synthetic_sales_generator",
            file_type="Synthetic Generator",
            total_rows=len(df),
            valid_records=len(df),
            duplicate_rows=0,
            missing_values_handled=0,
            rejected_rows=0,
            quality_score=100.0,
            status="Generated",
            audit_details=f"Generated {len(df):,} realistic synthetic sales records spanning 2023-2026."
        )
        session.add(log)
        session.commit()
        session.close()

        return jsonify({
            "status": "success",
            "message": f"Successfully generated {len(df):,} synthetic sales records and seeded the database.",
            "count": len(df),
            "csv_path": "data/sample_sales_data.csv"
        }), 200

    except Exception as e:
        logger.error(f"Error generating synthetic dataset: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Dataset generation failed: {str(e)}"}), 500
