# Informix Database Setup

This directory contains SQL scripts for initializing the Informix database container.

## Container Details

The `docker-compose.yml` includes an Informix Developer Edition container with the following configuration:

- **Image**: `ibmcom/informix-developer-database:14.10.FC7W1DE`
- **Container name**: `fgl-informix`
- **Port**: 9088 (DRDA), 9089 (SQLI)
- **Database**: `stores_demo` (pre-installed demo database)

## Connection Details

### Default Credentials

- **Host**: `informix` (within Docker network) or `localhost` (from host machine)
- **Port**: 9088
- **Database**: `stores_demo`
- **Username**: `informix`
- **Password**: `in4mix`
- **Server**: `informix`

### Sample Configuration (Studio IDE)

A sample connection named "Docker Informix (Sample)" is automatically provided in the Studio IDE with these credentials.

## Pre-installed Demo Database: stores_demo

The Informix Developer Edition comes with a pre-installed `stores_demo` database that includes:

### Tables

- **customer** - Customer information
- **orders** - Order records
- **items** - Order line items
- **stock** - Product inventory
- **manufact** - Manufacturer information
- **state** - US state codes
- **cust_calls** - Customer service calls

### Schema Overview

```sql
-- Customer table
customer (
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
)

-- Orders table
orders (
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
)

-- Items table
items (
    item_num SERIAL PRIMARY KEY,
    order_num INTEGER,
    stock_num SMALLINT,
    manu_code CHAR(3),
    quantity SMALLINT,
    total_price DECIMAL(8,2)
)

-- Stock table
stock (
    stock_num SMALLINT,
    manu_code CHAR(3),
    description CHAR(15),
    unit_price DECIMAL(6,2),
    unit CHAR(4),
    unit_descr CHAR(15),
    PRIMARY KEY (stock_num, manu_code)
)
```

## Using the Database

### Important: Database Initialization Required

The Informix container needs to be initialized with sample data for the stores_demo database.

#### Quick Setup (Recommended)

Run the initialization script from the project root:

```bash
# 1. Start containers
docker compose up -d

# 2. Initialize database (run once)
./init-db.sh
```

This script will:
- ✓ Wait for Informix to be ready
- ✓ Create the stores_demo database
- ✓ Create all tables
- ✓ Populate with sample data (7 customers, 6 orders, etc.)
- ✓ Verify the setup

#### Manual Setup

If you prefer to initialize manually:

```bash
# 1. Start containers
docker compose up -d

# 2. Wait for Informix (60-90 seconds)
docker compose ps informix

# 3. Run initialization SQL
docker compose exec informix dbaccess stores_demo /opt/ibm/informix/sql/init_stores_demo.sql

# 4. Verify
./verify-db.sh
```

### From Studio IDE

1. Start the containers:
   ```bash
   docker compose up
   ```

2. **Wait 60-90 seconds** for Informix to fully initialize

3. Open Studio IDE at http://localhost:9002

4. Click "Database" in the menu bar

5. Select "Configure Connections..."

6. In the "Select Connection" tab, choose "Docker Informix (Sample)"

7. Click "Test Connection" to verify it works

8. Open one of the example files:
   - `stores_demo_query.4gl` - Simple queries to test connectivity
   - `customer_report.4gl` - Complex report with cursor loops

9. Run the code - it will automatically use the configured database connection

### From Command Line

```bash
# Execute a 4GL script with database
docker compose exec backend python -m fglinterpreter examples/stores_demo_query.4gl
```

### Direct Database Access

```bash
# Connect to the Informix container
docker compose exec informix bash

# Run dbaccess
dbaccess stores_demo

# Example query
SELECT customer_num, fname, lname, city, state
FROM customer
WHERE state = 'CA'
ORDER BY lname
LIMIT 5;
```

## Example 4GL Scripts

### stores_demo_query.4gl
A simple example that demonstrates:
- COUNT queries
- Single row SELECT INTO
- Cursor loops with FOREACH
- Perfect for testing database connectivity

### customer_report.4gl
A comprehensive example showing:
- Nested cursor loops
- Customer order history
- Aggregate functions
- Date handling
- Report formatting

## Adding Custom SQL Scripts

You can add your own SQL initialization scripts to this directory. Scripts placed here are mounted as read-only in the container at `/opt/ibm/informix/sql/`.

To run custom initialization:

```bash
docker compose exec informix dbaccess stores_demo /opt/ibm/informix/sql/your_script.sql
```

## Troubleshooting

### Container won't start
- Ensure you have enough disk space (Informix requires ~2GB)
- Check Docker has sufficient memory allocated (at least 2GB)

### Connection refused
- Wait for the container to fully initialize (can take 60-90 seconds)
- Check container health: `docker compose ps`
- View logs: `docker compose logs informix`

### Query errors
- Verify you're using the correct database: `stores_demo`
- Check table names match the schema (case-sensitive)
- Ensure proper 4GL syntax for SQL statements

## Additional Resources

- [Informix Documentation](https://www.ibm.com/docs/en/informix-servers)
- [stores_demo Database Guide](https://www.ibm.com/docs/en/informix-servers/14.10?topic=database-stores-demonstration)
- [4GL Reference Manual](https://www.ibm.com/docs/en/informix-servers/14.10?topic=reference-informix-4gl)
