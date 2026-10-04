import logging
import re
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger("sales_dashboard.cleaning")

STANDARD_COLUMNS = [
    "order_number", "order_date", "customer_code", "region_name",
    "category_name", "product_code", "product_name", "unit_price",
    "quantity", "discount_rate", "total_price", "payment_method", "order_status"
]

COLUMN_SYNONYMS = {
    "order_number": ["order_id", "order_number", "order id", "invoice_no", "transaction_id", "ordernumber", "order"],
    "order_date": ["order_date", "date", "order date", "order_timestamp", "transaction_date", "orderdate"],
    "customer_code": ["customer_id", "customer_code", "customer id", "cust_id", "client_id", "customercode"],
    "region_name": ["region", "region_name", "sales_region", "territory", "zone", "location", "regionname"],
    "category_name": ["category", "category_name", "product_category", "department", "cat_name", "categoryname"],
    "product_code": ["product_code", "product_id", "sku", "item_code", "prod_id", "productcode"],
    "product_name": ["product_name", "product", "item_name", "item_description", "description", "productname"],
    "unit_price": ["unit_price", "price", "item_price", "rate", "cost", "unitprice"],
    "quantity": ["quantity", "qty", "units", "units_sold", "volume", "count"],
    "discount_rate": ["discount", "discount_rate", "discount_pct", "discount_percent", "disc"],
    "total_price": ["total_price", "total", "line_total", "amount", "sales_amount", "sales", "revenue", "totalprice"],
    "payment_method": ["payment_method", "payment_type", "payment", "pay_mode", "paymentmethod"],
    "order_status": ["order_status", "status", "fulfillment_status", "state", "orderstatus"]
}


class DataCleaner:
    """
    Production-grade Data Cleaning and Transformation pipeline for sales records.
    Provides detailed before-and-after audit statistics, quality metrics,
    and structured rejection logs without silent data deletion.
    """

    def __init__(self, df: pd.DataFrame, filename: str = "uploaded_file"):
        self.raw_df = df.copy()
        self.filename = filename
        self.total_raw_rows = len(df)
        self.audit_actions = []
        self.rejected_records = []
        self.cleaned_df = pd.DataFrame()
        self.stats = {
            "total_rows": self.total_raw_rows,
            "valid_records": 0,
            "duplicate_rows": 0,
            "missing_values_handled": 0,
            "rejected_rows": 0,
            "quality_score": 0.0,
            "actions": []
        }

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Maps arbitrary input headers to standardized column names."""
        clean_cols = {}
        for col in df.columns:
            normalized_header = re.sub(r'[^a-z0-9_]', '_', str(col).strip().lower())
            mapped = False
            for std_col, synonyms in COLUMN_SYNONYMS.items():
                if normalized_header in synonyms or str(col).strip().lower() in synonyms:
                    clean_cols[col] = std_col
                    mapped = True
                    break
            if not mapped:
                clean_cols[col] = normalized_header

        df = df.rename(columns=clean_cols)
        self.audit_actions.append(f"Mapped {len(clean_cols)} column headers to standardized schema.")
        return df

    def run_cleaning_pipeline(self):
        """
        Executes the complete data cleaning, imputation, validation, and audit process.
        """
        df = self._normalize_column_names(self.raw_df)

        # Track before stats
        before_missing_cells = int(df.isnull().sum().sum())

        # 1. Deduplication Detection
        initial_count = len(df)
        dup_subset = [c for c in ["order_number", "product_code"] if c in df.columns]
        if not dup_subset and "order_number" in df.columns:
            dup_subset = ["order_number"]
        
        duplicates_count = 0
        if dup_subset:
            is_dup = df.duplicated(subset=dup_subset, keep="first")
            duplicates_count = int(is_dup.sum())
            if duplicates_count > 0:
                self.audit_actions.append(f"Identified {duplicates_count} duplicate row(s) based on {dup_subset}; deduplicating dataset.")
                df = df[~is_dup].copy()
            else:
                self.audit_actions.append("Zero duplicate transaction rows detected.")
        self.stats["duplicate_rows"] = duplicates_count

        # 2. Date Standardization
        if "order_date" in df.columns:
            parsed_dates = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
            invalid_dates = parsed_dates.isnull()
            if invalid_dates.sum() > 0:
                rejected_date_rows = df[invalid_dates]
                for idx, row in rejected_date_rows.iterrows():
                    self.rejected_records.append({
                        "row_index": idx + 1,
                        "order_number": row.get("order_number", "N/A"),
                        "reason": f"Invalid or unparseable order_date value: '{row.get('order_date')}'"
                    })
                df = df[~invalid_dates].copy()
                parsed_dates = parsed_dates[~invalid_dates]
                self.audit_actions.append(f"Rejected {invalid_dates.sum()} row(s) with unparseable date formats.")
            
            df["order_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
            self.audit_actions.append("Standardized order dates to ISO 8601 (YYYY-MM-DD).")
        else:
            # Generate default current date if completely omitted
            df["order_date"] = datetime.now().strftime("%Y-%m-%d")
            self.audit_actions.append("Order date column was missing; populated with default current date.")

        # 3. Numeric Fields Validation & Cleaning
        imputed_cells = 0

        # Quantity
        if "quantity" in df.columns:
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
            invalid_qty = df["quantity"].isnull() | (df["quantity"] <= 0)
            if invalid_qty.sum() > 0:
                for idx, row in df[invalid_qty].iterrows():
                    self.rejected_records.append({
                        "row_index": idx + 1,
                        "order_number": row.get("order_number", "N/A"),
                        "reason": f"Invalid quantity value: {row.get('quantity')} (must be positive integer)"
                    })
                df = df[~invalid_qty].copy()
                self.audit_actions.append(f"Rejected {invalid_qty.sum()} row(s) with non-positive or non-numeric quantity.")
            df["quantity"] = df["quantity"].astype(int)
        else:
            df["quantity"] = 1
            imputed_cells += len(df)
            self.audit_actions.append("Quantity column missing; defaulted to 1 unit per line.")

        # Unit Price
        if "unit_price" in df.columns:
            df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
            invalid_price = df["unit_price"].isnull() | (df["unit_price"] <= 0)
            if invalid_price.sum() > 0:
                for idx, row in df[invalid_price].iterrows():
                    self.rejected_records.append({
                        "row_index": idx + 1,
                        "order_number": row.get("order_number", "N/A"),
                        "reason": f"Invalid unit price value: {row.get('unit_price')} (must be positive number)"
                    })
                df = df[~invalid_price].copy()
                self.audit_actions.append(f"Rejected {invalid_price.sum()} row(s) with non-positive or non-numeric unit price.")
            df["unit_price"] = df["unit_price"].round(2)
        else:
            # If total_price exists, estimate unit_price
            if "total_price" in df.columns:
                df["total_price"] = pd.to_numeric(df["total_price"], errors="coerce").fillna(0.0)
                df["unit_price"] = (df["total_price"] / df["quantity"]).round(2)
                imputed_cells += len(df)
                self.audit_actions.append("Computed unit_price from total_price / quantity.")
            else:
                df["unit_price"] = 50.00
                imputed_cells += len(df)

        # Discount Rate
        if "discount_rate" in df.columns:
            df["discount_rate"] = pd.to_numeric(df["discount_rate"], errors="coerce").fillna(0.0)
            # If formatted like 15 for 15%, scale down
            scaled_mask = df["discount_rate"] > 1.0
            if scaled_mask.sum() > 0:
                df.loc[scaled_mask, "discount_rate"] = df.loc[scaled_mask, "discount_rate"] / 100.0
                self.audit_actions.append(f"Normalized {scaled_mask.sum()} percentage discount values (e.g. 15% -> 0.15).")
            # Clamp between 0.0 and 0.90
            df["discount_rate"] = df["discount_rate"].clip(lower=0.0, upper=0.90).round(4)
        else:
            df["discount_rate"] = 0.0

        # Total Price
        if "total_price" in df.columns:
            df["total_price"] = pd.to_numeric(df["total_price"], errors="coerce")
            recalc_mask = df["total_price"].isnull() | (df["total_price"] <= 0)
            if recalc_mask.sum() > 0:
                df.loc[recalc_mask, "total_price"] = (
                    df.loc[recalc_mask, "quantity"] * df.loc[recalc_mask, "unit_price"] * (1.0 - df.loc[recalc_mask, "discount_rate"])
                ).round(2)
                imputed_cells += int(recalc_mask.sum())
                self.audit_actions.append(f"Recalculated {recalc_mask.sum()} missing or zero total_price values.")
        else:
            df["total_price"] = (df["quantity"] * df["unit_price"] * (1.0 - df["discount_rate"])).round(2)
            imputed_cells += len(df)
            self.audit_actions.append("Calculated line total_price = quantity * unit_price * (1 - discount).")

        # 4. Text Fields Sanitization and Categorical Imputation
        text_cols = {
            "customer_code": "CUST-UNASSIGNED",
            "region_name": "North America",
            "category_name": "General Supplies",
            "product_code": "PROD-GENERIC",
            "product_name": "Generic Sales Item",
            "payment_method": "Credit Card",
            "order_status": "Completed"
        }

        for col, default_val in text_cols.items():
            if col not in df.columns:
                df[col] = default_val
                imputed_cells += len(df)
                self.audit_actions.append(f"Column '{col}' was missing; initialized with '{default_val}'.")
            else:
                # Handle nulls
                null_mask = df[col].isnull() | (df[col].astype(str).str.strip() == "")
                if null_mask.sum() > 0:
                    df.loc[null_mask, col] = default_val
                    imputed_cells += int(null_mask.sum())
                    self.audit_actions.append(f"Imputed {null_mask.sum()} blank values in '{col}' with '{default_val}'.")
                
                # Strip and normalize title case
                df[col] = df[col].astype(str).str.strip()
                if col in ["region_name", "category_name", "order_status", "payment_method"]:
                    df[col] = df[col].str.title()

        # Generate order_number if missing
        if "order_number" not in df.columns:
            df["order_number"] = [f"IMP-ORD-{i:06d}" for i in range(1, len(df) + 1)]
            self.audit_actions.append("Generated sequential order_number identifiers.")
        else:
            df["order_number"] = df["order_number"].astype(str).str.strip()

        # 5. Outlier Detection
        # Flag transactions with total_price exceeding mean + 4 std devs as high-value alerts
        mean_val = df["total_price"].mean()
        std_val = df["total_price"].std()
        if pd.notnull(std_val) and std_val > 0:
            threshold = mean_val + (4 * std_val)
            high_val_count = int((df["total_price"] > threshold).sum())
            if high_val_count > 0:
                self.audit_actions.append(f"Flagged {high_val_count} high-value transaction(s) exceeding ${threshold:,.2f} for analyst review.")

        # Ensure order_timestamp exists
        if "order_timestamp" not in df.columns:
            df["order_timestamp"] = df["order_date"] + " 12:00:00"

        # Calculate Quality Score
        valid_rows = len(df)
        rejected_count = len(self.rejected_records)
        total_eval = self.total_raw_rows if self.total_raw_rows > 0 else 1
        
        quality_score = max(0.0, min(100.0, round((valid_rows / total_eval) * 100.0, 2)))

        self.stats["valid_records"] = valid_rows
        self.stats["missing_values_handled"] = imputed_cells
        self.stats["rejected_rows"] = rejected_count
        self.stats["quality_score"] = quality_score
        self.stats["actions"] = self.audit_actions

        self.cleaned_df = df
        return self.get_audit_report()

    def get_audit_report(self) -> dict:
        """Returns structured audit metrics, sample rows, and rejection logs."""
        preview_cleaned = []
        if not self.cleaned_df.empty:
            preview_cleaned = self.cleaned_df.head(15).to_dict(orient="records")

        return {
            "filename": self.filename,
            "stats": self.stats,
            "actions": self.audit_actions,
            "rejected_records": self.rejected_records[:50],  # Return up to 50 sample rejections
            "rejected_count": len(self.rejected_records),
            "preview_cleaned": preview_cleaned,
            "total_cleaned_count": len(self.cleaned_df)
        }
