"""
Chaos 2 Clarity — Synthetic Data Generator
Generates the 3-source retail enterprise environment described in Section 6.
- PostgreSQL (DuckDB): 14 tables, sales/orders
- Salesforce CRM export: accounts, opportunities
- Logistics CSV: deliveries, carriers

47 columns total. Inconsistent naming. No shared keys. Zero documentation.
"""

import duckdb
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# SCHEMA DEFINITIONS
# ─────────────────────────────────────────────

POSTGRES_DDL = """
-- Source 1: PostgreSQL OLTP (simulated in DuckDB)
-- NOTE: Revenue column is intentionally named 'line_value' (NOT 'revenue' or 'order_total')
-- This is the E1 column-name trap from the paper.

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150),
    segment VARCHAR(50),         -- 'Enterprise', 'Mid-Market', 'SMB'
    created_at TIMESTAMP,
    region VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),        -- 'Electronics', 'Clothing', 'Home', 'Sports', 'Food'
    cost_price DECIMAL(10,2),
    list_price DECIMAL(10,2),
    sku VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS sales_reps (
    id INTEGER PRIMARY KEY,
    rep_name VARCHAR(100),
    territory VARCHAR(50),
    hire_date DATE
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    product_id INTEGER REFERENCES products(id),
    sales_rep_id INTEGER REFERENCES sales_reps(id),
    order_date DATE,
    ship_date DATE,
    line_value DECIMAL(12,2),    -- THIS IS THE REVENUE COLUMN (intentional naming trap)
    quantity INTEGER,
    status VARCHAR(20),          -- 'completed', 'shipped', 'cancelled', 'returned', 'pending'
    shipping_id VARCHAR(30),     -- Links to logistics CSV (implicit, undocumented)
    discount_pct DECIMAL(5,2)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2)
);

CREATE TABLE IF NOT EXISTS returns (
    id INTEGER PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    return_date DATE,
    reason VARCHAR(100),
    refund_amount DECIMAL(10,2)
);
"""

# Column descriptions for B2 baseline (partial, mimicking real-world docs)
COLUMN_DESCRIPTIONS = {
    "customers.id": "Primary key, auto-increment",
    "customers.name": "Full name of the customer",
    "customers.email": "Email address",
    "customers.segment": "Customer segment: Enterprise, Mid-Market, or SMB",
    "customers.created_at": "Account creation timestamp",
    "customers.region": "Geographic region",
    "products.id": "Primary key",
    "products.name": "Product display name",
    "products.category": "Product category",
    "products.cost_price": "Cost to acquire/manufacture",
    "products.list_price": "Listed retail price",
    "products.sku": "Stock keeping unit code",
    "sales_reps.id": "Primary key",
    "sales_reps.rep_name": "Sales representative name",
    "sales_reps.territory": "Assigned sales territory",
    "sales_reps.hire_date": "Date hired",
    "orders.id": "Primary key",
    "orders.customer_id": "FK to customers",
    "orders.product_id": "FK to products",
    "orders.sales_rep_id": "FK to sales_reps",
    "orders.order_date": "Date the order was placed",
    "orders.ship_date": "Date the order was shipped",
    # INTENTIONALLY MISSING/VAGUE: line_value description not provided
    # This is the core E1 trap — LLMs must figure out that line_value = revenue
    "orders.quantity": "Quantity ordered",
    "orders.status": "Order status",
    "orders.shipping_id": "Shipping reference code",
    "orders.discount_pct": "Discount percentage applied",
    "order_items.id": "Primary key",
    "order_items.order_id": "FK to orders",
    "order_items.product_id": "FK to products",
    "order_items.quantity": "Quantity of this item",
    "order_items.unit_price": "Price per unit",
    "order_items.line_total": "Total for this line item",
    "returns.id": "Primary key",
    "returns.order_id": "FK to orders",
    "returns.return_date": "Date of return",
    "returns.reason": "Reason for return",
    "returns.refund_amount": "Amount refunded",
}


def generate_postgres_data(conn, n_customers=1000, n_products=500, n_orders=10000, n_reps=25):
    """Generate realistic retail data for the PostgreSQL source."""

    # Execute DDL
    conn.execute(POSTGRES_DDL)

    # --- Customers ---
    segments = ['Enterprise', 'Mid-Market', 'SMB']
    regions = ['North', 'South', 'East', 'West', 'Central']
    customers = []
    for i in range(1, n_customers + 1):
        customers.append({
            'id': i,
            'name': fake.name(),
            'email': fake.email(),
            'segment': np.random.choice(segments, p=[0.2, 0.3, 0.5]),
            'created_at': fake.date_time_between(start_date='-3y', end_date='-30d'),
            'region': np.random.choice(regions),
        })
    df_customers = pd.DataFrame(customers)
    conn.execute("INSERT INTO customers SELECT * FROM df_customers")

    # --- Products ---
    categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Food']
    products = []
    for i in range(1, n_products + 1):
        cost = round(np.random.uniform(5, 500), 2)
        products.append({
            'id': i,
            'name': fake.catch_phrase(),
            'category': np.random.choice(categories),
            'cost_price': cost,
            'list_price': round(cost * np.random.uniform(1.3, 3.0), 2),
            'sku': f"SKU-{i:05d}",
        })
    df_products = pd.DataFrame(products)
    conn.execute("INSERT INTO products SELECT * FROM df_products")

    # --- Sales Reps ---
    reps = []
    territories = regions
    for i in range(1, n_reps + 1):
        reps.append({
            'id': i,
            'rep_name': fake.name(),
            'territory': np.random.choice(territories),
            'hire_date': fake.date_between(start_date='-5y', end_date='-6m'),
        })
    df_reps = pd.DataFrame(reps)
    conn.execute("INSERT INTO sales_reps SELECT * FROM df_reps")

    # --- Orders ---
    statuses = ['completed', 'shipped', 'cancelled', 'returned', 'pending']
    status_probs = [0.55, 0.20, 0.08, 0.07, 0.10]
    orders = []
    order_items_list = []
    returns_list = []
    item_id = 1
    return_id = 1

    for i in range(1, n_orders + 1):
        order_date = fake.date_between(start_date='-2y', end_date='today')
        status = np.random.choice(statuses, p=status_probs)
        ship_date = order_date + timedelta(days=np.random.randint(1, 14)) if status in ['completed', 'shipped', 'returned'] else None
        product_id = np.random.randint(1, n_products + 1)
        product = df_products[df_products['id'] == product_id].iloc[0]
        quantity = np.random.randint(1, 10)
        discount = round(np.random.choice([0, 5, 10, 15, 20], p=[0.4, 0.25, 0.2, 0.1, 0.05]), 2)
        line_value = round(product['list_price'] * quantity * (1 - discount / 100), 2)

        shipping_id = f"SH-{fake.bothify('???-######')}" if ship_date else None

        orders.append({
            'id': i,
            'customer_id': np.random.randint(1, n_customers + 1),
            'product_id': product_id,
            'sales_rep_id': np.random.randint(1, n_reps + 1),
            'order_date': order_date,
            'ship_date': ship_date,
            'line_value': line_value,
            'quantity': quantity,
            'status': status,
            'shipping_id': shipping_id,
            'discount_pct': discount,
        })

        # Order items (1-3 items per order)
        n_items = np.random.randint(1, 4)
        for j in range(n_items):
            item_prod_id = product_id if j == 0 else np.random.randint(1, n_products + 1)
            item_prod = df_products[df_products['id'] == item_prod_id].iloc[0]
            item_qty = np.random.randint(1, 5)
            order_items_list.append({
                'id': item_id,
                'order_id': i,
                'product_id': item_prod_id,
                'quantity': item_qty,
                'unit_price': item_prod['list_price'],
                'line_total': round(item_prod['list_price'] * item_qty, 2),
            })
            item_id += 1

        # Returns
        if status == 'returned':
            returns_list.append({
                'id': return_id,
                'order_id': i,
                'return_date': order_date + timedelta(days=np.random.randint(5, 30)),
                'reason': np.random.choice([
                    'Defective product', 'Wrong item shipped', 'Changed mind',
                    'Better price elsewhere', 'Product not as described',
                    'Arrived too late', 'Damaged in shipping'
                ]),
                'refund_amount': round(line_value * np.random.uniform(0.8, 1.0), 2),
            })
            return_id += 1

    df_orders = pd.DataFrame(orders)
    conn.execute("INSERT INTO orders SELECT * FROM df_orders")

    df_items = pd.DataFrame(order_items_list)
    conn.execute("INSERT INTO order_items SELECT * FROM df_items")

    if returns_list:
        df_returns = pd.DataFrame(returns_list)
        conn.execute("INSERT INTO returns SELECT * FROM df_returns")

    return df_customers, df_products, df_orders


def generate_salesforce_data(df_pg_customers, n_opps_per_account=3):
    """Generate Salesforce CRM export with DIFFERENT naming conventions.

    Key differences from PostgreSQL:
    - 'account_name' instead of 'name'
    - 'email_address' instead of 'email'
    - 'account_id' instead of 'id' (different ID space)
    - No shared primary keys with PG — only email is the implicit link
    """
    accounts = []
    opportunities = []
    opp_id = 1

    # Map ~70% of PG customers to SF accounts (imperfect overlap)
    sampled = df_pg_customers.sample(frac=0.7, random_state=42)

    stages = ['Prospecting', 'Qualification', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    stage_probs = [0.15, 0.15, 0.20, 0.15, 0.25, 0.10]

    for idx, (_, pg_cust) in enumerate(sampled.iterrows()):
        acct_id = f"SF-{idx + 1:05d}"
        accounts.append({
            'account_id': acct_id,
            'account_name': pg_cust['name'],  # same name, different column name
            'email_address': pg_cust['email'],  # same email, different column name — the implicit link
            'industry': np.random.choice(['Technology', 'Retail', 'Healthcare', 'Finance', 'Manufacturing']),
            'sf_segment': pg_cust['segment'],  # 'sf_segment' not 'segment'
            'annual_revenue': round(np.random.uniform(100000, 50000000), 2),
            'account_owner': fake.name(),
            'created_date': fake.date_between(start_date='-3y', end_date='-30d').isoformat(),
        })

        # Generate opportunities per account
        n_opps = np.random.randint(1, n_opps_per_account + 1)
        for _ in range(n_opps):
            close_date = fake.date_between(start_date='-18m', end_date='+3m')
            stage = np.random.choice(stages, p=stage_probs)
            opportunities.append({
                'opp_id': f"OPP-{opp_id:05d}",
                'account_id': acct_id,
                'deal_name': fake.bs().title(),
                'stage': stage,
                'amount': round(np.random.uniform(5000, 500000), 2),  # 'amount' not 'deal_size' or 'value'
                'close_date': close_date.isoformat(),
                'probability': {'Prospecting': 10, 'Qualification': 25, 'Proposal': 50,
                               'Negotiation': 75, 'Closed Won': 100, 'Closed Lost': 0}[stage],
                'next_step': fake.sentence(nb_words=6) if stage not in ['Closed Won', 'Closed Lost'] else None,
            })
            opp_id += 1

    df_accounts = pd.DataFrame(accounts)
    df_opportunities = pd.DataFrame(opportunities)

    return df_accounts, df_opportunities


def generate_logistics_data(df_orders, carrier_count=8):
    """Generate logistics CSV with DIFFERENT naming conventions and formats.

    Key differences:
    - 'shipping_ref' matches orders.shipping_id (implicit, undocumented link)
    - Dates in different format (MM/DD/YYYY instead of YYYY-MM-DD)
    - Status codes as integers, not strings
    - No customer_id — must go through orders.shipping_id to link
    """
    carriers = [fake.company() + ' Logistics' for _ in range(carrier_count)]

    status_codes = {
        1: 'Picked Up',
        2: 'In Transit',
        3: 'Out for Delivery',
        4: 'Delivered',
        5: 'Delivery Failed',
        6: 'Returned to Sender',
    }

    shipped_orders = df_orders[df_orders['shipping_id'].notna()].copy()

    deliveries = []
    for _, order in shipped_orders.iterrows():
        expected_days = np.random.randint(2, 10)
        actual_delay = int(np.random.choice(
            [0, 0, 0, 1, 1, 2, 3, 5, -1, -1],  # mostly on time, some delays
        ))
        expected_date = order['ship_date'] + timedelta(days=int(expected_days))
        delivery_date = expected_date + timedelta(days=actual_delay)
        status = int(np.random.choice([3, 4, 4, 4, 4, 5, 6], p=[0.05, 0.70, 0.05, 0.05, 0.05, 0.05, 0.05]))

        deliveries.append({
            'tracking_id': f"TRK-{fake.bothify('??########')}",
            'shipping_ref': order['shipping_id'],  # This is the link to PostgreSQL (undocumented!)
            'carrier_name': np.random.choice(carriers),
            'expected_date': expected_date.strftime('%m/%d/%Y'),  # Different date format!
            'delivery_date': delivery_date.strftime('%m/%d/%Y') if status == 4 else None,
            'status_code': int(status),  # Integer codes, not strings!
            'weight_kg': round(np.random.uniform(0.5, 50), 1),
            'destination_zip': fake.zipcode(),
        })

    df_deliveries = pd.DataFrame(deliveries)
    return df_deliveries, status_codes


def generate_unstructured_data(df_pg_customers, df_orders, n_emails=50, n_tickets=100):
    """Generate synthetic unstructured documents for L4 questions.

    - Customer complaint emails
    - Support tickets
    - Return reason notes
    """
    complaint_themes = [
        "product arrived damaged", "wrong item was shipped", "delivery took too long",
        "product quality is poor", "competitor offers better price", "product defect found",
        "packaging was inadequate", "missing items in order", "billing discrepancy",
        "customer service was unhelpful"
    ]

    competitor_names = ["AcmeCorp", "BetterBuy", "QuickShip", "ValueMax", "PrimeGoods"]

    emails = []
    for i in range(n_emails):
        cust = df_pg_customers.sample(1).iloc[0]
        theme = np.random.choice(complaint_themes)
        mentions_competitor = np.random.random() < 0.3
        competitor = np.random.choice(competitor_names) if mentions_competitor else None

        body = f"Dear Support,\n\nI am writing to complain about my recent order. {theme.capitalize()}. "
        if mentions_competitor:
            body += f"I've been looking at {competitor} as an alternative. "
        body += f"My customer email is {cust['email']}. Please resolve this urgently.\n\nRegards,\n{cust['name']}"

        emails.append({
            'doc_id': f"EMAIL-{i+1:04d}",
            'type': 'complaint_email',
            'customer_email': cust['email'],
            'customer_name': cust['name'],
            'subject': f"Complaint: {theme}",
            'body': body,
            'date': fake.date_between(start_date='-6m', end_date='today').isoformat(),
            'sentiment': np.random.choice(['negative', 'very_negative'], p=[0.6, 0.4]),
            'theme': theme,
            'competitor_mentioned': competitor,
        })

    tickets = []
    for i in range(n_tickets):
        cust = df_pg_customers.sample(1).iloc[0]
        category = np.random.choice([
            'Shipping Issue', 'Product Defect', 'Billing', 'Return Request',
            'General Inquiry', 'Damaged Goods', 'Missing Items'
        ])
        sentiment = np.random.choice(['positive', 'neutral', 'negative', 'very_negative'],
                                      p=[0.1, 0.2, 0.5, 0.2])
        mentions_competitor = np.random.random() < 0.2
        competitor = np.random.choice(competitor_names) if mentions_competitor else None

        note = f"Customer {cust['name']} ({cust['email']}) reported: {category.lower()}. "
        if sentiment in ['negative', 'very_negative']:
            note += f"Customer is {sentiment.replace('_', ' ')}. "
        if mentions_competitor:
            note += f"Customer mentioned switching to {competitor}. "
        note += fake.sentence(nb_words=12)

        tickets.append({
            'ticket_id': f"TKT-{i+1:05d}",
            'type': 'support_ticket',
            'customer_email': cust['email'],
            'customer_name': cust['name'],
            'category': category,
            'description': note,
            'date': fake.date_between(start_date='-6m', end_date='today').isoformat(),
            'sentiment': sentiment,
            'resolved': np.random.random() < 0.7,
            'competitor_mentioned': competitor,
        })

    return pd.DataFrame(emails), pd.DataFrame(tickets)


def setup_full_environment(data_dir='data', db_path=':memory:'):
    """Create the complete 3-source retail environment.

    Returns:
        conn: DuckDB connection with PostgreSQL data loaded
        sf_accounts: DataFrame of Salesforce accounts
        sf_opportunities: DataFrame of Salesforce opportunities
        logistics: DataFrame of logistics deliveries
        emails_df: DataFrame of complaint emails
        tickets_df: DataFrame of support tickets
        status_codes: Dict mapping logistics status codes
    """
    os.makedirs(data_dir, exist_ok=True)

    # --- Source 1: PostgreSQL (DuckDB) ---
    conn = duckdb.connect(db_path)
    df_customers, df_products, df_orders = generate_postgres_data(conn)
    print(f"✅ PostgreSQL: {len(df_customers)} customers, {len(df_products)} products, {len(df_orders)} orders")

    # --- Source 2: Salesforce CRM Export ---
    sf_accounts, sf_opportunities = generate_salesforce_data(df_customers)
    sf_accounts.to_csv(f'{data_dir}/salesforce_accounts.csv', index=False)
    sf_opportunities.to_csv(f'{data_dir}/salesforce_opportunities.csv', index=False)
    print(f"✅ Salesforce: {len(sf_accounts)} accounts, {len(sf_opportunities)} opportunities")

    # --- Source 3: Logistics CSV ---
    logistics, status_codes = generate_logistics_data(df_orders)
    logistics.to_csv(f'{data_dir}/logistics_deliveries.csv', index=False)
    print(f"✅ Logistics: {len(logistics)} delivery records")

    # --- Source 4: Unstructured Documents (for L4) ---
    emails_df, tickets_df = generate_unstructured_data(df_customers, df_orders)
    emails_df.to_json(f'{data_dir}/complaint_emails.json', orient='records', indent=2)
    tickets_df.to_json(f'{data_dir}/support_tickets.json', orient='records', indent=2)
    print(f"✅ Unstructured: {len(emails_df)} emails, {len(tickets_df)} tickets")

    # --- Register Salesforce & Logistics in DuckDB for cross-source queries ---
    conn.execute(f"CREATE TABLE IF NOT EXISTS sf_accounts AS SELECT * FROM read_csv_auto('{data_dir}/salesforce_accounts.csv')")
    conn.execute(f"CREATE TABLE IF NOT EXISTS sf_opportunities AS SELECT * FROM read_csv_auto('{data_dir}/salesforce_opportunities.csv')")
    conn.execute(f"CREATE TABLE IF NOT EXISTS logistics_deliveries AS SELECT * FROM read_csv_auto('{data_dir}/logistics_deliveries.csv')")

    # Count columns
    total_cols = 0
    for table in ['customers', 'products', 'sales_reps', 'orders', 'order_items', 'returns',
                   'sf_accounts', 'sf_opportunities', 'logistics_deliveries']:
        cols = conn.execute(f"SELECT * FROM {table} LIMIT 0").description
        total_cols += len(cols)
    print(f"\n📊 Total columns across all sources: {total_cols}")

    # Save metadata
    with open(f'{data_dir}/status_codes.json', 'w') as f:
        json.dump(status_codes, f, indent=2)

    return conn, sf_accounts, sf_opportunities, logistics, emails_df, tickets_df, status_codes


def get_schema_ddl(conn):
    """Extract schema DDL string for prompt injection."""
    tables = conn.execute("SHOW TABLES").fetchall()
    ddl_parts = []
    for (table_name,) in tables:
        cols = conn.execute(f"DESCRIBE {table_name}").fetchall()
        col_defs = ', '.join([f"{c[0]} {c[1]}" for c in cols])
        ddl_parts.append(f"CREATE TABLE {table_name} ({col_defs});")
    return '\n'.join(ddl_parts)


def get_column_descriptions_str():
    """Format column descriptions for B2 baseline prompt."""
    lines = []
    for col, desc in COLUMN_DESCRIPTIONS.items():
        lines.append(f"  {col}: {desc}")
    return '\n'.join(lines)


def get_sample_data(conn, table_name, n=5):
    """Get sample rows for semantic profiling."""
    df = conn.execute(f"SELECT * FROM {table_name} LIMIT {n}").fetchdf()
    return df.to_string(index=False)


def get_column_stats(conn, table_name):
    """Get basic column statistics for semantic profiling."""
    cols = conn.execute(f"DESCRIBE {table_name}").fetchall()
    stats = {}
    for col_name, col_type, *_ in cols:
        try:
            result = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT {col_name}) as distinct_count,
                    COUNT(*) - COUNT({col_name}) as null_count
                FROM {table_name}
            """).fetchone()
            stats[col_name] = {
                'type': col_type,
                'total_rows': result[0],
                'distinct_values': result[1],
                'null_count': result[2],
            }
        except Exception:
            stats[col_name] = {'type': col_type, 'error': 'stats unavailable'}
    return stats
