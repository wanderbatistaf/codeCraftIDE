#!/bin/bash
# Initialization script for stores_demo database
# This script checks if stores_demo exists and creates/populates it if needed

set -e

echo "Checking stores_demo database..."

# Wait for Informix to be ready
sleep 10

# Check if stores_demo database exists with data
if echo "SELECT COUNT(*) FROM customer;" | dbaccess stores_demo - 2>/dev/null | grep -q "[0-9]"; then
    echo "stores_demo database already exists with data"
    exit 0
fi

echo "Creating and populating stores_demo database..."

# Create the database if it doesn't exist
echo "DATABASE stores_demo;" | dbaccess sysmaster - 2>/dev/null || {
    echo "CREATE DATABASE stores_demo WITH LOG;" | dbaccess sysmaster -
}

# Create tables and populate with sample data
dbaccess stores_demo - <<'EOF'

-- Create customer table
CREATE TABLE IF NOT EXISTS customer (
    customer_num SERIAL PRIMARY KEY,
    fname CHAR(15),
    lname CHAR(15),
    company CHAR(20),
    address1 CHAR(20),
    address2 CHAR(20),
    city CHAR(15),
    state CHAR(2),
    zipcode CHAR(5),
    phone CHAR(18)
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_num SERIAL PRIMARY KEY,
    order_date DATE,
    customer_num INTEGER,
    ship_instruct CHAR(40),
    backlog CHAR(1),
    po_num CHAR(10),
    ship_date DATE,
    ship_weight DECIMAL(8,2),
    ship_charge DECIMAL(6,2),
    paid_date DATE
);

-- Create items table
CREATE TABLE IF NOT EXISTS items (
    item_num SERIAL PRIMARY KEY,
    order_num INTEGER,
    stock_num SMALLINT,
    manu_code CHAR(3),
    quantity SMALLINT,
    total_price DECIMAL(8,2)
);

-- Create stock table
CREATE TABLE IF NOT EXISTS stock (
    stock_num SMALLINT,
    manu_code CHAR(3),
    description CHAR(15),
    unit_price DECIMAL(6,2),
    unit CHAR(4),
    unit_descr CHAR(15),
    PRIMARY KEY (stock_num, manu_code)
);

-- Create manufact table
CREATE TABLE IF NOT EXISTS manufact (
    manu_code CHAR(3) PRIMARY KEY,
    manu_name CHAR(15),
    lead_time INTERVAL DAY(3) TO DAY
);

-- Create state table
CREATE TABLE IF NOT EXISTS state (
    code CHAR(2) PRIMARY KEY,
    sname CHAR(15)
);

-- Insert sample customers (California customers for the examples)
INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (101, 'Ludwig', 'Pauli', 'All Sports Supplies', 'Los Altos', 'CA', '94022', '415-555-1234');

INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (102, 'Carole', 'Sadler', 'Sports Spot', 'San Francisco', 'CA', '94117', '415-555-2314');

INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (103, 'Philip', 'Currie', 'Phil''s Sports', 'San Jose', 'CA', '95129', '408-555-3434');

INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (104, 'Anthony', 'Higgins', 'Olympic City', 'Los Angeles', 'CA', '90034', '213-555-4545');

INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (105, 'Raymond', 'Vector', 'Blue Ribbon Sports', 'San Diego', 'CA', '92121', '619-555-5656');

-- Insert sample customers from other states
INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (106, 'James', 'Watson', 'Dallas Sports', 'Dallas', 'TX', '75201', '214-555-6767');

INSERT INTO customer (customer_num, fname, lname, company, city, state, zipcode, phone)
VALUES (107, 'Nancy', 'Green', 'Phoenix Athletics', 'Phoenix', 'AZ', '85001', '602-555-7878');

-- Insert sample manufacturers
INSERT INTO manufact (manu_code, manu_name, lead_time)
VALUES ('HRO', 'Hero', 5 UNITS DAY);

INSERT INTO manufact (manu_code, manu_name, lead_time)
VALUES ('SMT', 'SmithKline', 3 UNITS DAY);

INSERT INTO manufact (manu_code, manu_name, lead_time)
VALUES ('ANZ', 'Anza', 7 UNITS DAY);

-- Insert sample stock items
INSERT INTO stock (stock_num, manu_code, description, unit_price, unit, unit_descr)
VALUES (1, 'HRO', 'baseball', 4.50, 'each', 'each');

INSERT INTO stock (stock_num, manu_code, description, unit_price, unit, unit_descr)
VALUES (5, 'SMT', 'baseball bat', 24.00, 'each', 'each');

INSERT INTO stock (stock_num, manu_code, description, unit_price, unit, unit_descr)
VALUES (9, 'ANZ', 'tennis racquet', 75.00, 'each', 'each');

INSERT INTO stock (stock_num, manu_code, description, unit_price, unit, unit_descr)
VALUES (10, 'HRO', 'tennis ball', 1.80, 'can', 'can');

-- Insert sample orders
INSERT INTO orders (order_num, order_date, customer_num, ship_date, ship_charge)
VALUES (1001, '2024-01-15', 101, '2024-01-17', 10.00);

INSERT INTO orders (order_num, order_date, customer_num, ship_date, ship_charge)
VALUES (1002, '2024-01-20', 101, '2024-01-22', 15.00);

INSERT INTO orders (order_num, order_date, customer_num, ship_date, ship_charge)
VALUES (1003, '2024-02-01', 102, '2024-02-03', 8.50);

INSERT INTO orders (order_num, order_date, customer_num, ship_date, ship_charge)
VALUES (1004, '2024-02-10', 103, NULL, 12.00);

INSERT INTO orders (order_num, order_date, customer_num, ship_date, ship_charge)
VALUES (1005, '2024-02-15', 104, '2024-02-18', 20.00);

INSERT INTO orders (order_num, order_date, customer_num, ship_date, ship_charge)
VALUES (1006, '2024-03-01', 105, '2024-03-05', 18.00);

-- Insert sample order items
INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (1, 1001, 1, 'HRO', 10, 45.00);

INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (2, 1001, 5, 'SMT', 2, 48.00);

INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (3, 1002, 9, 'ANZ', 1, 75.00);

INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (4, 1003, 10, 'HRO', 12, 21.60);

INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (5, 1004, 1, 'HRO', 5, 22.50);

INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (6, 1005, 5, 'SMT', 3, 72.00);

INSERT INTO items (item_num, order_num, stock_num, manu_code, quantity, total_price)
VALUES (7, 1006, 9, 'ANZ', 2, 150.00);

-- Insert state data
INSERT INTO state (code, sname) VALUES ('CA', 'California');
INSERT INTO state (code, sname) VALUES ('TX', 'Texas');
INSERT INTO state (code, sname) VALUES ('AZ', 'Arizona');
INSERT INTO state (code, sname) VALUES ('NY', 'New York');
INSERT INTO state (code, sname) VALUES ('FL', 'Florida');

EOF

echo "stores_demo database initialized successfully!"
echo "Sample data includes:"
echo "  - 7 customers (5 in California)"
echo "  - 6 orders"
echo "  - 7 order items"
echo "  - 4 stock items"
echo "  - 3 manufacturers"
echo "  - 5 states"
