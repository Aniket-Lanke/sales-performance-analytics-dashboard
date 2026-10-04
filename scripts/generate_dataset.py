import sys
import argparse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import Config
from app.services.generator_service import generate_synthetic_dataset

def main():
    parser = argparse.ArgumentParser(description="Synthetic Sales Dataset Generator (50,000+ records)")
    parser.add_argument("--count", type=int, default=50000, help="Number of transaction item records (default: 50,000)")
    parser.add_argument("--csv", default=str(Config.DATA_DIR / "sample_sales_data.csv"), help="Output CSV path")
    parser.add_argument("--no-db", action="store_true", help="Skip loading directly into database")
    
    args = parser.parse_args()
    
    print("=" * 65)
    print(f"Generating {args.count:,} Synthetic Sales Transaction Records")
    print(f"Output CSV : {args.csv}")
    print(f"Seed to DB : {not args.no_db}")
    print("=" * 65)
    
    def progress_callback(cur, total):
        pct = (cur / total) * 100
        print(f"Progress: {cur:,} / {total:,} ({pct:.1f}%)", end="\r")
        
    df = generate_synthetic_dataset(
        total_records=args.count,
        save_csv_path=args.csv,
        seed_to_db=not args.no_db,
        progress_callback=progress_callback
    )
    
    print(f"\n[SUCCESS] Completed successfully! Generated {len(df):,} total line item records.")
    print(f"[FILE] CSV saved at: {args.csv}")

if __name__ == "__main__":
    main()
