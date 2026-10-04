import random
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import text
from app.database import get_session, get_engine, init_db
from app.models.models import Category, Region, Customer, Product, Order, OrderItem

logger = logging.getLogger("sales_dashboard.generator")

# Master lookup definitions
REGIONS_DATA = [
    {"region_name": "North America", "code": "NA", "country": "United States"},
    {"region_name": "Europe", "code": "EU", "country": "Germany"},
    {"region_name": "Asia-Pacific", "code": "APAC", "country": "Singapore"},
    {"region_name": "Latin America", "code": "LATAM", "country": "Brazil"},
    {"region_name": "Middle East & Africa", "code": "MEA", "country": "United Arab Emirates"},
]

CATEGORIES_DATA = [
    {"category_name": "Electronics", "description": "High-tech consumer gadgets, computing, and peripherals"},
    {"category_name": "Furniture", "description": "Ergonomic office and home furniture"},
    {"category_name": "Office Supplies", "description": "Everyday office essentials, paper, and organization"},
    {"category_name": "Apparel", "description": "Professional and casual corporate clothing"},
    {"category_name": "Footwear", "description": "Work and athletic performance footwear"},
    {"category_name": "Home & Kitchen", "description": "Modern home appliances and kitchenware"},
]

PRODUCTS_MASTER = [
    # Electronics
    {"product_code": "PROD-E101", "name": "ThinkPad X1 Carbon Gen 11", "category": "Electronics", "price": 1499.00, "cost": 950.00, "sku": "TP-X1-C11"},
    {"product_code": "PROD-E102", "name": "Dell UltraSharp 27 4K Monitor", "category": "Electronics", "price": 589.00, "cost": 360.00, "sku": "DEL-U27-4K"},
    {"product_code": "PROD-E103", "name": "Sony WH-1000XM5 Headphones", "category": "Electronics", "price": 399.00, "cost": 240.00, "sku": "SNY-WH-XM5"},
    {"product_code": "PROD-E104", "name": "Logitech MX Master 3S Mouse", "category": "Electronics", "price": 99.00, "cost": 55.00, "sku": "LOG-MX-3S"},
    {"product_code": "PROD-E105", "name": "Keychron Q3 Pro Mechanical Keyboard", "category": "Electronics", "price": 210.00, "cost": 120.00, "sku": "KC-Q3-PRO"},
    {"product_code": "PROD-E106", "name": "Anker 737 Power Bank 24000mAh", "category": "Electronics", "price": 139.00, "cost": 75.00, "sku": "ANK-737-PB"},
    {"product_code": "PROD-E107", "name": "Apple iPad Pro 12.9 M2", "category": "Electronics", "price": 1099.00, "cost": 750.00, "sku": "APP-IPAD-12"},
    
    # Furniture
    {"product_code": "PROD-F201", "name": "Herman Miller Aeron Chair", "category": "Furniture", "price": 1250.00, "cost": 700.00, "sku": "HM-AER-CH"},
    {"product_code": "PROD-F202", "name": "Steelcase Gesture Ergonomic Chair", "category": "Furniture", "price": 1100.00, "cost": 620.00, "sku": "SC-GST-CH"},
    {"product_code": "PROD-F203", "name": "Autonomous SmartDesk Connect Pro", "category": "Furniture", "price": 699.00, "cost": 410.00, "sku": "AUT-SD-PRO"},
    {"product_code": "PROD-F204", "name": "Vari Electric Standing Desk 60x30", "category": "Furniture", "price": 795.00, "cost": 460.00, "sku": "VAR-ESD-60"},
    {"product_code": "PROD-F205", "name": "Solid Walnut Monitor Stand Riser", "category": "Furniture", "price": 120.00, "cost": 50.00, "sku": "WLN-MON-RSR"},
    {"product_code": "PROD-F206", "name": "Ergonomic Executive Footrest", "category": "Furniture", "price": 65.00, "cost": 28.00, "sku": "ERG-EXE-FT"},

    # Office Supplies
    {"product_code": "PROD-O301", "name": "Moleskine Classic Hardcover Notebook", "category": "Office Supplies", "price": 24.50, "cost": 9.50, "sku": "MOL-CLS-NB"},
    {"product_code": "PROD-O302", "name": "Lamy 2000 Fountain Pen", "category": "Office Supplies", "price": 195.00, "cost": 95.00, "sku": "LAM-2000-FP"},
    {"product_code": "PROD-O303", "name": "Heavy-Duty Cross-Cut Paper Shredder", "category": "Office Supplies", "price": 180.00, "cost": 95.00, "sku": "HVD-SHR-CC"},
    {"product_code": "PROD-O304", "name": "Magnetic Glass Dry Erase Board 48x36", "category": "Office Supplies", "price": 145.00, "cost": 70.00, "sku": "MGB-4836-WB"},
    {"product_code": "PROD-O305", "name": "Premium Multi-Color Gel Pens (20-Pack)", "category": "Office Supplies", "price": 28.00, "cost": 11.00, "sku": "GEL-PEN-20P"},
    {"product_code": "PROD-O306", "name": "Recycled Copy Paper Case (10 Reams)", "category": "Office Supplies", "price": 62.00, "cost": 36.00, "sku": "RCP-10R-CS"},

    # Apparel
    {"product_code": "PROD-A401", "name": "Patagonia Nano Puff Jacket", "category": "Apparel", "price": 229.00, "cost": 115.00, "sku": "PAT-NP-JKT"},
    {"product_code": "PROD-A402", "name": "Lululemon Commission Slim Pant", "category": "Apparel", "price": 138.00, "cost": 55.00, "sku": "LLL-COM-PNT"},
    {"product_code": "PROD-A403", "name": "Merino Wool V-Neck Sweater", "category": "Apparel", "price": 115.00, "cost": 48.00, "sku": "MRN-WOL-SWT"},
    {"product_code": "PROD-A404", "name": "Arc'teryx Solano Waterproof Hooded Jacket", "category": "Apparel", "price": 299.00, "cost": 150.00, "sku": "ARC-SOL-HD"},
    {"product_code": "PROD-A405", "name": "Organic Egyptian Cotton Oxford Shirt", "category": "Apparel", "price": 85.00, "cost": 32.00, "sku": "EGY-COT-SHT"},

    # Footwear
    {"product_code": "PROD-W501", "name": "Allen Edmonds Park Avenue Oxford Shoes", "category": "Footwear", "price": 395.00, "cost": 190.00, "sku": "AE-PRK-OXF"},
    {"product_code": "PROD-W502", "name": "On Cloud 5 All-Day Sneakers", "category": "Footwear", "price": 149.00, "cost": 65.00, "sku": "ON-CLD-5"},
    {"product_code": "PROD-W503", "name": "Allbirds Wool Runners Breathable", "category": "Footwear", "price": 110.00, "cost": 45.00, "sku": "ALB-WOL-RUN"},
    {"product_code": "PROD-W504", "name": "Cole Haan Zerogrand Stitchlite Wingtip", "category": "Footwear", "price": 180.00, "cost": 78.00, "sku": "CH-ZG-WNG"},
    {"product_code": "PROD-W505", "name": "Blundstone Classic 550 Chelsea Boot", "category": "Footwear", "price": 225.00, "cost": 105.00, "sku": "BLN-550-BT"},

    # Home & Kitchen
    {"product_code": "PROD-H601", "name": "Breville Barista Touch Espresso Machine", "category": "Home & Kitchen", "price": 999.00, "cost": 600.00, "sku": "BRV-BAR-TCH"},
    {"product_code": "PROD-H602", "name": "Fellow Ode Gen 2 Conical Coffee Grinder", "category": "Home & Kitchen", "price": 345.00, "cost": 190.00, "sku": "FLW-ODE-G2"},
    {"product_code": "PROD-H603", "name": "Ember Temperature Control Smart Mug 2", "category": "Home & Kitchen", "price": 149.00, "cost": 72.00, "sku": "EMB-SMT-MG2"},
    {"product_code": "PROD-H604", "name": "Vitamix Explorian E310 Blender", "category": "Home & Kitchen", "price": 379.00, "cost": 210.00, "sku": "VTX-EXP-E31"},
    {"product_code": "PROD-H605", "name": "Dyson Purifier Hot+Cool Air Filter", "category": "Home & Kitchen", "price": 649.00, "cost": 380.00, "sku": "DYS-PUR-HC"}
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
    "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
    "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Margaret", "Anthony", "Betty", "Mark", "Sandra",
    "Donald", "Ashley", "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna",
    "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah",
    "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon", "Jeffrey", "Laura", "Ryan", "Cynthia",
    "Jacob", "Kathleen", "Gary", "Amy", "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen",
    "Stephen", "Anna", "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra", "Alexander", "Rachel",
    "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet", "Dennis", "Ruth", "Jerry", "Maria"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
    "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper",
    "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez"
]

CITIES_BY_REGION = {
    "North America": [
        ("New York", "NY", "United States"),
        ("Los Angeles", "CA", "United States"),
        ("Chicago", "IL", "United States"),
        ("Houston", "TX", "United States"),
        ("Toronto", "ON", "Canada"),
        ("Seattle", "WA", "United States"),
        ("San Francisco", "CA", "United States"),
        ("Austin", "TX", "United States"),
        ("Boston", "MA", "United States"),
        ("Vancouver", "BC", "Canada"),
    ],
    "Europe": [
        ("London", "England", "United Kingdom"),
        ("Berlin", "Berlin", "Germany"),
        ("Paris", "Île-de-France", "France"),
        ("Amsterdam", "North Holland", "Netherlands"),
        ("Madrid", "Madrid", "Spain"),
        ("Munich", "Bavaria", "Germany"),
        ("Milan", "Lombardy", "Italy"),
        ("Dublin", "Leinster", "Ireland"),
        ("Zurich", "Zurich", "Switzerland"),
        ("Stockholm", "Stockholm", "Sweden"),
    ],
    "Asia-Pacific": [
        ("Singapore", "Central", "Singapore"),
        ("Tokyo", "Kanto", "Japan"),
        ("Sydney", "NSW", "Australia"),
        ("Seoul", "Gyeonggi", "South Korea"),
        ("Melbourne", "VIC", "Australia"),
        ("Hong Kong", "Hong Kong", "Hong Kong"),
        ("Mumbai", "Maharashtra", "India"),
        ("Bangalore", "Karnataka", "India"),
        ("Taipei", "Northern", "Taiwan"),
        ("Auckland", "Auckland", "New Zealand"),
    ],
    "Latin America": [
        ("São Paulo", "SP", "Brazil"),
        ("Mexico City", "CDMX", "Mexico"),
        ("Buenos Aires", "CABA", "Argentina"),
        ("Santiago", "Santiago", "Chile"),
        ("Bogotá", "Bogotá DC", "Colombia"),
        ("Lima", "Lima", "Peru"),
        ("Rio de Janeiro", "RJ", "Brazil"),
        ("Monterrey", "NL", "Mexico"),
    ],
    "Middle East & Africa": [
        ("Dubai", "Dubai", "United Arab Emirates"),
        ("Abu Dhabi", "Abu Dhabi", "United Arab Emirates"),
        ("Riyadh", "Riyadh", "Saudi Arabia"),
        ("Tel Aviv", "Tel Aviv", "Israel"),
        ("Johannesburg", "Gauteng", "South Africa"),
        ("Cape Town", "Western Cape", "South Africa"),
        ("Doha", "Ad-Dawhah", "Qatar"),
        ("Nairobi", "Nairobi", "Kenya"),
    ]
}

PAYMENT_METHODS = ["Credit Card", "PayPal", "Bank Transfer", "Debit Card"]
PAYMENT_WEIGHTS = [0.46, 0.26, 0.18, 0.10]

STATUSES = ["Completed", "Shipped", "Processing", "Cancelled", "Refunded"]
STATUS_WEIGHTS = [0.90, 0.05, 0.02, 0.015, 0.015]

DISCOUNT_OPTIONS = [0.0, 0.05, 0.10, 0.15, 0.20]
DISCOUNT_WEIGHTS = [0.60, 0.16, 0.14, 0.07, 0.03]


def get_month_seasonality_weight(month: int, day: int) -> float:
    """Calculates realistic retail seasonality weight."""
    # Base monthly curves
    base_curve = {
        1: 0.85,   # Jan post-holiday dip
        2: 0.90,
        3: 1.00,
        4: 1.02,
        5: 1.05,
        6: 1.08,
        7: 1.10,
        8: 1.15,   # Back to school
        9: 1.12,
        10: 1.18,  # Pre-holiday runup
        11: 1.45,  # Black Friday / Cyber Monday
        12: 1.60   # Christmas / Year-end gifting
    }
    weight = base_curve.get(month, 1.0)
    # Extra surge around Black Friday (Late Nov: days 20-30)
    if month == 11 and day >= 20:
        weight *= 1.35
    # Extra surge for last minute holiday orders (Dec 1-22)
    elif month == 12 and day <= 22:
        weight *= 1.25
    return weight


def ensure_master_records_in_db(session):
    """Inserts Master Regions, Categories, and Products if not already existing."""
    # 1. Regions
    existing_regions = {r.region_name: r.region_id for r in session.query(Region).all()}
    for reg_data in REGIONS_DATA:
        if reg_data["region_name"] not in existing_regions:
            new_reg = Region(**reg_data)
            session.add(new_reg)
            session.flush()
            existing_regions[reg_data["region_name"]] = new_reg.region_id

    # 2. Categories
    existing_cats = {c.category_name: c.category_id for c in session.query(Category).all()}
    for cat_data in CATEGORIES_DATA:
        if cat_data["category_name"] not in existing_cats:
            new_cat = Category(**cat_data)
            session.add(new_cat)
            session.flush()
            existing_cats[cat_data["category_name"]] = new_cat.category_id

    # 3. Products
    existing_prods = {p.product_code: p.product_id for p in session.query(Product).all()}
    for prod_info in PRODUCTS_MASTER:
        if prod_info["product_code"] not in existing_prods:
            cat_id = existing_cats[prod_info["category"]]
            new_prod = Product(
                product_code=prod_info["product_code"],
                product_name=prod_info["name"],
                category_id=cat_id,
                unit_price=prod_info["price"],
                cost_price=prod_info["cost"],
                sku=prod_info["sku"],
                is_active=True
            )
            session.add(new_prod)
            session.flush()
            existing_prods[prod_info["product_code"]] = new_prod.product_id

    session.commit()
    return existing_regions, existing_cats, existing_prods


def generate_synthetic_dataset(total_records=50000, save_csv_path=None, seed_to_db=True, progress_callback=None):
    """
    Generates total_records (default 50,000+) realistic synthetic transactions.
    Optionally saves to CSV and bulk-loads into the active database.
    """
    random.seed(42)
    np.random.seed(42)

    logger.info(f"Beginning generation of {total_records:,} synthetic sales transactions...")
    
    init_db()
    session = get_session()
    
    # 1. Ensure master metadata
    region_id_map, cat_id_map, prod_id_map = ensure_master_records_in_db(session)
    
    # 2. Generate 2,500 realistic Customers if not present
    existing_customers = session.query(Customer).all()
    if len(existing_customers) < 1500:
        logger.info("Generating customer base...")
        new_customers = []
        customer_codes = set()
        
        region_names = list(CITIES_BY_REGION.keys())
        for i in range(1, 2501):
            c_code = f"CUST-{i:05d}"
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            domain = random.choice(["gmail.com", "enterprise.org", "techcorp.io", "outlook.com", "workmail.net"])
            email = f"{fn.lower()}.{ln.lower()}{i % 99}@{domain}"
            reg_name = random.choice(region_names)
            city_tuple = random.choice(CITIES_BY_REGION[reg_name])
            
            c = Customer(
                customer_code=c_code,
                first_name=fn,
                last_name=ln,
                email=email,
                segment="Standard",
                city=city_tuple[0],
                state=city_tuple[1],
                country=city_tuple[2],
                created_at=datetime(2023, 1, 1) + timedelta(days=random.randint(0, 700))
            )
            new_customers.append(c)
        session.bulk_save_objects(new_customers)
        session.commit()
        customer_ids = [c.customer_id for c in session.query(Customer.customer_id).all()]
    else:
        customer_ids = [c.customer_id for c in existing_customers]

    # Pre-fetch lookup mappings
    region_list = list(region_id_map.items()) # [('North America', 1), ...]
    products_list = PRODUCTS_MASTER
    
    # Dates: span from 2023-01-01 to 2026-03-31
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2026, 3, 31)
    total_days = (end_date - start_date).days

    orders_to_insert = []
    items_to_insert = []
    flattened_rows = [] # For CSV export

    order_counter = 1
    
    # Find existing max order number to avoid collision
    max_order = session.execute(text("SELECT MAX(order_id) FROM orders")).scalar()
    if max_order:
        order_counter = int(max_order) + 1

    logger.info("Synthesizing order transactions with seasonality and realistic variance...")
    
    # We will generate orders until we reach target order item records (each order has 1 to 4 items)
    generated_records = 0
    batch_size = 5000
    
    while generated_records < total_records:
        # Pick random day with seasonal bias
        day_offset = random.randint(0, total_days)
        curr_dt = start_date + timedelta(days=day_offset)
        
        # Seasonality acceptance test
        s_weight = get_month_seasonality_weight(curr_dt.month, curr_dt.day)
        # Random rejection if weight < 1.0 (to shape seasonality curve)
        if random.random() > (s_weight / 1.7):
            continue

        # Add random time of day (8 AM to 11 PM)
        order_time = curr_dt.replace(
            hour=random.randint(8, 22),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )

        customer_id = random.choice(customer_ids)
        reg_name, reg_id = random.choices(
            region_list,
            weights=[0.38, 0.28, 0.20, 0.08, 0.06] # Real business regional distribution
        )[0]
        
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        
        order_num = f"ORD-202{curr_dt.year % 10}-{order_counter:07d}"
        
        # Number of line items in this order: 1 (65%), 2 (22%), 3 (10%), 4 (3%)
        num_items = random.choices([1, 2, 3, 4], weights=[0.65, 0.22, 0.10, 0.03])[0]
        
        # Don't exceed total_records drastically
        if generated_records + num_items > total_records + 50:
            num_items = 1

        selected_prods = random.sample(products_list, min(num_items, len(products_list)))
        
        order_subtotal = 0.0
        order_items_temp = []
        
        for p in selected_prods:
            qty = random.choices([1, 2, 3, 4, 5], weights=[0.72, 0.16, 0.07, 0.03, 0.02])[0]
            unit_price = float(p["price"])
            disc_rate = random.choices(DISCOUNT_OPTIONS, weights=DISCOUNT_WEIGHTS)[0]
            item_total = round(qty * unit_price * (1.0 - disc_rate), 2)
            order_subtotal += item_total
            
            order_items_temp.append({
                "product_id": prod_id_map[p["product_code"]],
                "product_code": p["product_code"],
                "product_name": p["name"],
                "category_name": p["category"],
                "quantity": qty,
                "unit_price": unit_price,
                "cost_price": float(p["cost"]),
                "discount_rate": disc_rate,
                "total_price": item_total
            })

        # Shipping cost ($0 for orders > $150, else $9.99-$19.99)
        shipping_cost = 0.0 if order_subtotal > 150.0 else random.choice([9.99, 14.99, 19.99])
        total_order_amount = round(order_subtotal + shipping_cost, 2)
        
        # Store order
        order_record = {
            "order_number": order_num,
            "customer_id": customer_id,
            "region_id": reg_id,
            "order_date": order_time.date(),
            "order_timestamp": order_time,
            "payment_method": payment_method,
            "order_status": status,
            "shipping_cost": shipping_cost,
            "discount_amount": 0.0,
            "total_amount": total_order_amount,
            "is_synthetic": True,
            "items": order_items_temp
        }
        
        orders_to_insert.append(order_record)
        order_counter += 1
        generated_records += num_items

        # Build flattened row for CSV
        for itm in order_items_temp:
            flattened_rows.append({
                "Order_ID": order_num,
                "Order_Date": order_time.strftime("%Y-%m-%d"),
                "Order_Timestamp": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Customer_ID": f"CUST-{customer_id:05d}",
                "Region": reg_name,
                "Category": itm["category_name"],
                "Product_Code": itm["product_code"],
                "Product_Name": itm["product_name"],
                "Unit_Price": itm["unit_price"],
                "Cost_Price": itm["cost_price"],
                "Quantity": itm["quantity"],
                "Discount": itm["discount_rate"],
                "Total_Price": itm["total_price"],
                "Payment_Method": payment_method,
                "Order_Status": status,
                "Is_Synthetic": "Yes"
            })

    # Save to CSV if requested or default path
    df = pd.DataFrame(flattened_rows)
    if save_csv_path:
        logger.info(f"Saving synthetic dataset to CSV: {save_csv_path}")
        df.to_csv(save_csv_path, index=False)

    # 3. Seed directly into DB in batches if requested
    if seed_to_db:
        logger.info(f"Bulk loading {len(orders_to_insert):,} orders into database...")
        db_engine = get_engine()
        
        # Use bulk insert for orders and order_items
        # To maintain relational integrity across both engines (MySQL and SQLite),
        # we insert orders in chunks and retrieve their IDs.
        for chunk_idx in range(0, len(orders_to_insert), batch_size):
            chunk_orders = orders_to_insert[chunk_idx:chunk_idx + batch_size]
            
            for o_data in chunk_orders:
                items_data = o_data.pop("items")
                new_order = Order(
                    order_number=o_data["order_number"],
                    customer_id=o_data["customer_id"],
                    region_id=o_data["region_id"],
                    order_date=o_data["order_date"],
                    order_timestamp=o_data["order_timestamp"],
                    payment_method=o_data["payment_method"],
                    order_status=o_data["order_status"],
                    shipping_cost=o_data["shipping_cost"],
                    discount_amount=o_data["discount_amount"],
                    total_amount=o_data["total_amount"],
                    is_synthetic=True
                )
                session.add(new_order)
                session.flush() # populated new_order.order_id
                
                for itm in items_data:
                    new_item = OrderItem(
                        order_id=new_order.order_id,
                        product_id=itm["product_id"],
                        quantity=itm["quantity"],
                        unit_price=itm["unit_price"],
                        discount_rate=itm["discount_rate"],
                        total_price=itm["total_price"]
                    )
                    session.add(new_item)
                    
            session.commit()
            if progress_callback:
                progress_callback(min(generated_records, chunk_idx + batch_size), total_records)
            logger.info(f"Committed batch up to order {min(len(orders_to_insert), chunk_idx + batch_size):,}...")

        # Update customer segmentation in database based on aggregated spend
        update_customer_spending_segments(session)

    session.close()
    logger.info(f"Synthetic generation complete: {len(flattened_rows):,} item records generated.")
    return df


def update_customer_spending_segments(session):
    """
    Computes cumulative customer spending and updates segment in customers table:
    - High Spending (VIP): Total Spend > $5,000
    - Medium Spending: Total Spend $1,500 - $5,000
    - Low Spending: Total Spend < $1,500
    """
    logger.info("Updating customer spending segments...")
    sql = """
    UPDATE customers
    SET segment = (
        CASE
            WHEN COALESCE((SELECT SUM(total_amount) FROM orders WHERE orders.customer_id = customers.customer_id AND orders.order_status = 'Completed'), 0) >= 5000 THEN 'High Spending (VIP)'
            WHEN COALESCE((SELECT SUM(total_amount) FROM orders WHERE orders.customer_id = customers.customer_id AND orders.order_status = 'Completed'), 0) >= 1500 THEN 'Medium Spending'
            ELSE 'Low Spending'
        END
    )
    """
    try:
        session.execute(text(sql))
        session.commit()
    except Exception as e:
        logger.warning(f"Error updating customer segments with subquery: {e}")
        session.rollback()
