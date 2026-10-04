import pytest
from app import create_app
from app.database import get_session, init_db
from app.services.generator_service import ensure_master_records_in_db, generate_synthetic_dataset


@pytest.fixture(scope="module")
def test_client():
    app = create_app("testing")
    with app.app_context():
        init_db()
        session = get_session()
        ensure_master_records_in_db(session)
        # Generate 100 sample records for test coverage
        generate_synthetic_dataset(total_records=100, seed_to_db=True)
        session.close()

    with app.test_client() as client:
        yield client


def test_api_kpis(test_client):
    res = test_client.get("/api/dashboard/kpis")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "total_revenue" in data["data"]
    assert "total_orders" in data["data"]
    assert "aov" in data["data"]
    assert "growth_pct" in data["data"]


def test_api_sales_trend(test_client):
    res = test_client.get("/api/dashboard/sales-trend")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert isinstance(data["data"], list)


def test_api_top_products(test_client):
    res = test_client.get("/api/dashboard/top-products?limit=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) <= 5


def test_api_region_performance(test_client):
    res = test_client.get("/api/dashboard/region-performance")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) > 0


def test_api_customer_segments(test_client):
    res = test_client.get("/api/dashboard/customer-segments")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "segments" in data["data"]


def test_api_sql_presets(test_client):
    res = test_client.get("/api/sql/presets")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 5


def test_api_sql_execute_select(test_client):
    payload = {"query": "SELECT COUNT(*) as total_orders FROM orders;"}
    res = test_client.post("/api/sql/execute", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "total_orders" in data["columns"]


def test_api_sql_execute_blocks_drop_table(test_client):
    payload = {"query": "DROP TABLE customers;"}
    res = test_client.post("/api/sql/execute", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "Security Restriction" in data["error"]


def test_api_export_csv(test_client):
    res = test_client.get("/api/reports/export?format=csv")
    assert res.status_code == 200
    assert res.headers["Content-Type"].startswith("text/csv")
    csv_text = res.data.decode("utf-8")
    assert "Order ID" in csv_text
