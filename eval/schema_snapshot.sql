CREATE TABLE customers (id INTEGER, name VARCHAR, email VARCHAR, segment VARCHAR, created_at TIMESTAMP, region VARCHAR);
CREATE TABLE logistics_deliveries (tracking_id VARCHAR, shipping_ref VARCHAR, carrier_name VARCHAR, expected_date DATE, delivery_date DATE, status_code BIGINT, weight_kg DOUBLE, destination_zip VARCHAR);
CREATE TABLE order_items (id INTEGER, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price DECIMAL(10,2), line_total DECIMAL(12,2));
CREATE TABLE orders (id INTEGER, customer_id INTEGER, product_id INTEGER, sales_rep_id INTEGER, order_date DATE, ship_date DATE, line_value DECIMAL(12,2), quantity INTEGER, status VARCHAR, shipping_id VARCHAR, discount_pct DECIMAL(5,2));
CREATE TABLE products (id INTEGER, name VARCHAR, category VARCHAR, cost_price DECIMAL(10,2), list_price DECIMAL(10,2), sku VARCHAR);
CREATE TABLE returns (id INTEGER, order_id INTEGER, return_date DATE, reason VARCHAR, refund_amount DECIMAL(10,2));
CREATE TABLE sales_reps (id INTEGER, rep_name VARCHAR, territory VARCHAR, hire_date DATE);
CREATE TABLE sf_accounts (account_id VARCHAR, account_name VARCHAR, email_address VARCHAR, industry VARCHAR, sf_segment VARCHAR, annual_revenue DOUBLE, account_owner VARCHAR, created_date DATE);
CREATE TABLE sf_opportunities (opp_id VARCHAR, account_id VARCHAR, deal_name VARCHAR, stage VARCHAR, amount DOUBLE, close_date DATE, probability BIGINT, next_step VARCHAR);