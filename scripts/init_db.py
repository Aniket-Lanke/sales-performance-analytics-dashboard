import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import get_engine, init_db, get_session
from app.services.generator_service import ensure_master_records_in_db

def main():
    print("=" * 60)
    print("Initializing Sales Performance Analytics Database")
    print("=" * 60)
    
    engine = get_engine()
    print(f"Connecting to database: {engine.url}")
    
    init_db(engine)
    print("[SUCCESS] All tables created successfully.")
    
    session = get_session(engine)
    regions, cats, prods = ensure_master_records_in_db(session)
    print(f"[SUCCESS] Master Metadata Seeded:")
    print(f"   - {len(regions)} Commercial Regions")
    print(f"   - {len(cats)} Product Categories")
    print(f"   - {len(prods)} Enterprise Products")
    
    session.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    main()
