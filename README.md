# Sales Performance Analytics Dashboard (Enterprise Pro)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.3-150458.svg)](https://pandas.pydata.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%2F%20SQLite%203.25+-00758F.svg)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-brightgreen.svg)](tests/)

An end-to-end, enterprise-grade sales analytics web application built with **Python, Flask, Pandas, NumPy, MySQL / SQLAlchemy, and Plotly.js**. Designed as a centerpiece **Data Analyst / Analytics Engineer portfolio project**, it models commercial sales operations across **50,000+ transaction records**, delivering interactive dashboards, data cleaning pipelines, window-function SQL analytics, customer LTV segmentation, and multi-tab executive reports.

---

## 📑 Table of Contents

1. [Executive Overview & Portfolio Value](#1-executive-overview--portfolio-value)
2. [Technology Stack](#2-technology-stack)
3. [Dashboard Architecture & Design](#3-dashboard-architecture--design)
4. [Relational Database Schema (3NF)](#4-relational-database-schema-3nf)
5. [Data Cleaning & Quality Assurance Pipeline](#5-data-cleaning--quality-assurance-pipeline)
6. [Executive KPI Mathematical Formulations](#6-executive-kpi-mathematical-formulations)
7. [Advanced SQL Analytics Showcase](#7-advanced-sql-analytics-showcase)
8. [REST API Reference](#8-rest-api-reference)
9. [Quickstart & Setup Instructions](#9-quickstart--setup-instructions)
10. [Automated Testing Suite](#10-automated-testing-suite)
11. [Project Structure](#11-project-structure)

---

## 1. Executive Overview & Portfolio Value

Senior data analysts must demonstrate mastery across four pillars:
1. **Data Engineering & Ingestion**: Ingesting messy CSV/Excel files, detecting anomalies, handling duplicates, normalizing dates, and maintaining a non-destructive audit trail before committing to storage.
2. **Relational Database Architecture**: Designing normalized 3NF schemas with primary keys, foreign key constraints, indexes, and writing optimized SQL utilizing CTEs, `DENSE_RANK()`, `LAG()`, and partition windows.
3. **Statistical Business Analysis**: Computing mathematically sound KPIs (AOV, YoY growth trajectories, customer LTV distribution) with strict division-by-zero handling.
4. **Interactive Enterprise Visualization & UI/UX**: Crafting executive dashboards with cohesive corporate styling (dark navy `#0f172a`, blue `#2563eb`, teal `#0d9488`), responsive sidebars, multi-parameter filters, and styled Excel exports.

---

## 2. Technology Stack

- **Backend**: Python 3.12, Flask 3.0 (Modular Blueprints: `main`, `api`, `data`)
- **Data Transformation & Cleaning**: Pandas 2.3, NumPy 2.2
- **Database & Connectivity**: MySQL 8.0, SQLAlchemy 2.1, PyMySQL
- **Zero-Setup Demo Engine**: SQLite 3.25+ (with complete native CTE & Window function support)
- **Frontend / UI**: HTML5, CSS3 (Enterprise Theme), Bootstrap 5.3, Bootstrap Icons 1.11
- **Visualizations**: Plotly.js 2.30 (Dual-axis trend lines, category donuts, ranked horizontal bars, market share charts)
- **Reporting & Export**: OpenPyXL 3.1 (Styled multi-tab Excel workbooks), Pandas CSV streaming
- **Testing**: Pytest 9.0

---

## 3. Dashboard Architecture & Design

The platform consists of **9 specialized views**:

1. **Overview Dashboard** (`/` or `/overview`): Executive summary with 8 dynamic KPI cards, dual-axis revenue trend, category share donut, regional bar charts, and filtered transaction ledger.
2. **Sales Analysis** (`/sales`): Year-over-Year (YoY) multi-year trajectory comparisons (FY 2023–2026), payment channel performance, and monthly volume curves.
3. **Product Performance** (`/products`): Top 10 revenue-driving merchandise, product price vs. unit volume metrics, and category performance tables.
4. **Regional Analysis** (`/regional`): Commercial territory rankings (`DENSE_RANK()`), percentage global market share, and regional Average Order Value.
5. **Customer Segmentation** (`/customers`): Spending tier distribution (VIP / High, Medium, Low), LTV curves, and Top 10 high-value customer leaderboard.
6. **Data Import and Cleaning** (`/data-import`): Drag-and-drop CSV/Excel file uploader, automated Pandas cleaning audit, before/after statistics, rejected row inspector, and one-click 50,000+ synthetic record generator.
7. **SQL Analytics** (`/sql-analytics`): Interactive SQL query runner with a curated library of production analytical queries (CTEs, `LAG()`, `DENSE_RANK()`, `RANK() OVER PARTITION BY`), execution timing in milliseconds, and column-formatted result tables.
8. **Reports and Export** (`/reports`): Download filtered transaction CSVs, styled multi-tab Excel workbooks, or generate clean, printer-friendly PDF dashboard reports.
9. **Project Documentation** (`/documentation`): In-app interactive documentation, ERD diagrams, formula explanations, and setup instructions.

---

## 4. Relational Database Schema (3NF)

```
+---------------+       +------------------+       +-------------------+
|  categories   |       |     products     |       |    order_items    |
+---------------+       +------------------+       +-------------------+
| category_id PK|<------| category_id   FK |       | order_item_id  PK |
| category_name |       | product_id    PK |<------| product_id     FK |
| description   |       | product_code     |       | order_id       FK |----+
+---------------+       | unit_price       |       | quantity          |    |
                        | cost_price       |       | discount_rate     |    |
                        +------------------+       | total_price       |    |
                                                   +-------------------+    |
+---------------+       +------------------+                                |
|    regions    |       |      orders      |                                |
+---------------+       +------------------+                                |
| region_id   PK|<------| region_id     FK |                                |
| region_name   |       | order_id      PK |<-------------------------------+
| country       |       | customer_id   FK |<------+
+---------------+       | order_number     |       |
                        | order_date       |       |
                        | total_amount     |       |
                        +------------------+       |
                                                   |
                        +------------------+       |
                        |    customers     |       |
                        +------------------+       |
                        | customer_id   PK |-------+
                        | customer_code    |
                        | segment          |
                        +------------------+
```

### Key Schema Optimizations:
- **Indexes**: Applied on `orders(order_date)`, `orders(customer_id)`, `orders(region_id)`, `orders(order_status)`, and `order_items(product_id)`.
- **Foreign Key Cascades**: Configured on `order_items` cascading from `orders`.
- **Integrity Constraints**: `CHECK (quantity > 0)` and `CHECK (discount_rate BETWEEN 0.0 AND 1.0)`.

---

## 5. Data Cleaning & Quality Assurance Pipeline

The `DataCleaner` service enforces production data hygiene:

| Cleaning Stage | Transformation & Validation Logic | Audit Trail Metric |
| :--- | :--- | :--- |
| **Column Normalization** | Fuzzy matches synonyms (e.g. `order id`, `invoice_no` &rarr; `order_number`) | Headers Mapped Count |
| **Deduplication** | Identifies identical `(order_number, product_code)` records; retains first occurrence | Duplicates Flagged |
| **Date Standardization** | Coerces heterogeneous formats (`YYYY-MM-DD`, `MM/DD/YYYY`, ISO) with `format='mixed'`. Invalid dates sent to rejection log | Dates Standardized |
| **Numeric Validation** | Rejects non-numeric, zero, or negative quantities/prices. Automatically recalculates `total_price` if inconsistent | Rejections with Reason |
| **Quality Score** | `(Valid Records / Total Inspected Rows) * 100.0` | Quality Score % |
| **Human in the Loop** | Cleaned records staged in memory; **never committed to database without explicit user confirmation**. | Staged Review |

---

## 6. Executive KPI Mathematical Formulations

- **Total Revenue**:
  $$\text{Revenue} = \sum (\text{order\_items.total\_price}) \quad \forall \; \text{orders.order\_status} \in \{\text{'Completed'}, \text{'Shipped'}\}$$
- **Average Order Value (AOV)**:
  $$\text{AOV} = \begin{cases} \frac{\text{Total Revenue}}{\text{Total Orders}}, & \text{if } \text{Total Orders} > 0 \\ 0.00, & \text{otherwise} \end{cases}$$
- **Year-over-Year (YoY) Revenue Growth %**:
  $$\text{Growth \%} = \begin{cases} \frac{\text{Rev}_{\text{Current}} - \text{Rev}_{\text{Prior}}}{\text{Rev}_{\text{Prior}}} \times 100, & \text{if } \text{Rev}_{\text{Prior}} > 0 \\ 100.0\%, & \text{if } \text{Rev}_{\text{Prior}} = 0 \text{ and } \text{Rev}_{\text{Current}} > 0 \\ 0.0\%, & \text{otherwise} \end{cases}$$

---

## 7. Advanced SQL Analytics Showcase

The SQL Analytics module includes pre-built queries demonstrating advanced SQL techniques:

### Monthly Revenue & YoY Growth (CTEs + LAG)
```sql
WITH monthly_sales AS (
    SELECT
        SUBSTR(o.order_date, 1, 7) AS year_month,
        ROUND(SUM(oi.total_price), 2) AS current_revenue,
        COUNT(DISTINCT o.order_id) AS total_orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status IN ('Completed', 'Shipped')
    GROUP BY SUBSTR(o.order_date, 1, 7)
),
prior_comparison AS (
    SELECT
        year_month,
        current_revenue,
        total_orders,
        LAG(current_revenue, 12) OVER (ORDER BY year_month ASC) AS prior_year_revenue
    FROM monthly_sales
)
SELECT
    year_month,
    current_revenue,
    COALESCE(prior_year_revenue, 0.00) AS prior_year_revenue,
    total_orders,
    CASE
        WHEN prior_year_revenue IS NULL OR prior_year_revenue = 0 THEN 'N/A (Baseline)'
        ELSE ROUND(((current_revenue - prior_year_revenue) / prior_year_revenue) * 100.0, 2) || '%'
    END AS yoy_growth_pct
FROM prior_comparison
ORDER BY year_month DESC
LIMIT 24;
```

### Regional Market Share & Density Ranking (DENSE_RANK)
```sql
WITH regional_totals AS (
    SELECT
        r.region_name,
        r.country,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.quantity) AS total_units,
        ROUND(SUM(oi.total_price), 2) AS territory_revenue
    FROM regions r
    JOIN orders o ON r.region_id = o.region_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status IN ('Completed', 'Shipped')
    GROUP BY r.region_name, r.country
)
SELECT
    DENSE_RANK() OVER (ORDER BY territory_revenue DESC) AS sales_rank,
    region_name,
    country,
    total_orders,
    total_units,
    territory_revenue,
    ROUND((territory_revenue * 100.0) / SUM(territory_revenue) OVER (), 2) || '%' AS global_share_pct
FROM regional_totals
ORDER BY sales_rank ASC;
```

---

## 8. REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/dashboard/kpis` | `GET` | Returns 8 dynamic KPI metrics with safe growth comparisons |
| `/api/dashboard/sales-trend` | `GET` | Monthly revenue, order count, and AOV trend array |
| `/api/dashboard/yoy-comparison` | `GET` | 12-month multi-year comparison matrix (2023–2026) |
| `/api/dashboard/top-products` | `GET` | Products ranked by revenue with units and unit price |
| `/api/dashboard/region-performance`| `GET` | Regional sales metrics with `DENSE_RANK` and share % |
| `/api/dashboard/customer-segments` | `GET` | Customer tier breakdown (VIP, Medium, Low) and leaderboard |
| `/api/dashboard/payment-methods` | `GET` | Payment method breakdown and share % |
| `/api/dashboard/orders-table` | `GET` | Paginated transaction ledger matching filters |
| `/api/sql/presets` | `GET` | Curated SQL analytics catalog |
| `/api/sql/execute` | `POST` | Executes analytical query in read-only sandbox with timing |
| `/api/data/upload` | `POST` | Accepts CSV/Excel, runs cleaning pipeline, stages records |
| `/api/data/commit` | `POST` | Persists approved staged dataset into database |
| `/api/data/generate` | `POST` | Triggers synthetic 50,000+ record generation |
| `/api/reports/export` | `GET` | Streams filtered CSV or multi-sheet Excel report |

---

## 9. Quickstart & Setup Instructions

### Option A: Local Demo Mode (Zero Configuration)
The application defaults to SQLite 3.25+ mode so it can run immediately without configuring an external database:

```bash
# 1. Clone or navigate to the project directory
cd sales-performance-dashboard

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Initialize database and generate 50,000+ benchmark transactions
python scripts/generate_dataset.py --count 50000

# 4. Start the application
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

### Option B: Production MySQL 8.0 Mode
1. Ensure your MySQL server is running.
2. Create the target database:
   ```sql
   CREATE DATABASE IF NOT EXISTS sales_analytics_db;
   ```
3. Update `.env`:
   ```ini
   DB_ENGINE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=sales_analytics_db
   ```
4. Initialize schema and seed metadata:
   ```bash
   python scripts/init_db.py
   python scripts/generate_dataset.py --count 50000
   python run.py
   ```

---

## 10. Automated Testing Suite

The project includes unit and integration tests covering calculations, data cleaning, and REST endpoints:

```bash
python -m pytest tests/ -v
```

Test coverage includes:
- `test_aov_calculation_standard` & `test_aov_calculation_zero_orders`
- `test_yoy_growth_standard`, `test_yoy_growth_negative`, and `test_yoy_growth_zero_prior_period`
- `test_customer_segmentation_tiers`
- `test_cleaner_detects_duplicates_and_normalizes_dates`
- `test_cleaner_rejects_negative_and_zero_values`
- `test_cleaner_imputes_missing_columns_and_calculates_total`
- `test_api_kpis`, `test_api_sales_trend`, `test_api_top_products`, `test_api_region_performance`
- `test_api_sql_execute_blocks_drop_table` (Security validation blocking DDL/DML attacks)
- `test_api_export_csv`

---

## 11. Project Structure

```
sales-performance-dashboard/
├── app/
│   ├── __init__.py                # Flask application factory & error handlers
│   ├── config.py                  # Environment config & DB connection URI builder
│   ├── database.py                # SQLAlchemy engine, session, & SQLite/MySQL fallback
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py              # Normalized 3NF SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main_routes.py         # 9 Web page views with global context
│   │   ├── api_routes.py          # Analytical REST APIs, SQL runner, & exports
│   │   └── data_routes.py         # Upload, inspection, commit, & synthetic generator
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analytics_service.py   # Business KPI calculations & aggregations
│   │   ├── cleaning_service.py    # Pandas & NumPy data quality & cleaning engine
│   │   ├── sql_service.py         # CTE & Window function SQL query catalog
│   │   ├── generator_service.py   # 50,000+ synthetic transaction generator
│   │   └── export_service.py      # CSV & multi-tab Excel report generator
│   ├── templates/
│   │   ├── base.html              # Master layout with navbar, sidebar, modal
│   │   ├── components/
│   │   │   ├── sidebar.html       # Dark navy sidebar navigation
│   │   │   ├── navbar.html        # Header with export dropdown & database pill
│   │   │   └── filter_bar.html    # Interactive date presets & filter dropdowns
│   │   ├── overview.html          # Executive Overview with 8 KPIs & charts
│   │   ├── sales.html             # Sales Analysis & YoY trajectory
│   │   ├── products.html          # Product Performance & category metrics
│   │   ├── regional.html          # Regional rankings & market share
│   │   ├── customers.html         # Customer Segmentation & leaderboard
│   │   ├── data_import.html       # Data upload, cleaning audit, & generator
│   │   ├── sql_analytics.html     # Interactive SQL console & presets
│   │   ├── reports.html           # Excel, CSV, & printable report downloads
│   │   └── documentation.html     # In-app architecture & setup documentation
│   └── static/
│       ├── css/
│       │   └── dashboard.css      # Custom enterprise CSS theme
│       └── js/
│           ├── filters.js         # Client-side filter state & event engine
│           ├── charts.js          # Plotly.js chart configurations
│           ├── dashboard.js       # Main dashboard controller & pagination
│           ├── data_import.js     # Upload & cleaning audit controller
│           └── sql_analytics.js   # SQL query execution & timing runner
├── data/
│   ├── sample_sales_data.csv      # Generated 50,000+ transaction dataset
│   ├── sales_analytics.db         # SQLite demo database
│   ├── uploads/                   # Staged upload directory
│   └── exports/                   # Generated reports directory
├── scripts/
│   ├── init_db.py                 # Schema creation & master metadata seed
│   └── generate_dataset.py        # Standalone 50,000+ record CLI generator
├── tests/
│   ├── test_calculations.py       # KPI & business math tests
│   ├── test_cleaning.py           # Pandas cleaning pipeline tests
│   └── test_api.py                # REST API & security sandbox tests
├── schema.sql                     # ANSI & MySQL 8.0 DDL schema script
├── requirements.txt               # Python package dependencies
├── .env.example                   # Documented configuration template
├── .env                           # Local environment configuration
├── .gitignore                     # Git exclusions
├── run.py                         # Application entrypoint
└── README.md                      # Comprehensive project documentation
```
