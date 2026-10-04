import pandas as pd
import pytest
from app.services.cleaning_service import DataCleaner


def test_cleaner_detects_duplicates_and_normalizes_dates():
    dirty_data = {
        "Order ID": ["ORD-001", "ORD-001", "ORD-002", "ORD-003"],
        "Date": ["2024-05-12", "2024-05-12", "05/15/2024", "invalid_date"],
        "Quantity": [2, 2, 3, 1],
        "Unit Price": [100.0, 100.0, 50.0, 40.0],
        "Category": ["Electronics", "Electronics", "FURNITURE", "Apparel"]
    }
    df = pd.DataFrame(dirty_data)
    cleaner = DataCleaner(df, filename="test_upload.csv")
    report = cleaner.run_cleaning_pipeline()

    # Should detect 1 duplicate
    assert cleaner.stats["duplicate_rows"] == 1
    # Should reject the invalid date row
    assert cleaner.stats["rejected_rows"] >= 1
    # Verify rejected records list contains reason
    assert any("unparseable" in r["reason"].lower() or "invalid" in r["reason"].lower() for r in cleaner.rejected_records)
    # Valid records must be deduplicated
    assert len(cleaner.cleaned_df) == 2


def test_cleaner_rejects_negative_and_zero_values():
    dirty_data = {
        "order_number": ["ORD-101", "ORD-102", "ORD-103"],
        "order_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "quantity": [-5, 0, 2],
        "unit_price": [10.0, 20.0, -15.0]
    }
    df = pd.DataFrame(dirty_data)
    cleaner = DataCleaner(df)
    report = cleaner.run_cleaning_pipeline()

    # All three rows have invalid quantity or price
    assert cleaner.stats["rejected_rows"] == 3
    assert len(cleaner.cleaned_df) == 0


def test_cleaner_imputes_missing_columns_and_calculates_total():
    sparse_data = {
        "order_number": ["ORD-201", "ORD-202"],
        "order_date": ["2024-02-01", "2024-02-02"],
        "quantity": [2, 4],
        "unit_price": [50.00, 25.00]
        # total_price, category, region missing
    }
    df = pd.DataFrame(sparse_data)
    cleaner = DataCleaner(df)
    report = cleaner.run_cleaning_pipeline()

    assert cleaner.stats["valid_records"] == 2
    # Verify total_price calculated correctly: 2 * 50 = 100, 4 * 25 = 100
    totals = list(cleaner.cleaned_df["total_price"])
    assert totals == [100.00, 100.00]
    # Check default category imputed
    assert "category_name" in cleaner.cleaned_df.columns
