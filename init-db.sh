#!/bin/bash
# Quick database initialization script
# Run this after starting the containers to set up stores_demo database

set -e

echo "=== Initializing stores_demo database ==="
echo ""

# Check if containers are running
if ! docker compose ps | grep -q "fgl-informix.*running"; then
    echo "❌ Error: Informix container is not running"
    echo "   Please start containers first: docker compose up -d"
    exit 1
fi

echo "✓ Informix container is running"

# Wait for Informix to be fully ready
echo "⏳ Waiting for Informix to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose exec -T informix bash -c "echo 'SELECT 1 FROM systables WHERE tabid = 1;' | dbaccess sysmaster - > /dev/null 2>&1"; then
        echo "✓ Informix is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "  Waiting... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 3
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Error: Informix failed to become ready"
    echo "   Check logs: docker compose logs informix"
    exit 1
fi

# Create the database if it doesn't exist
echo ""
echo "Creating stores_demo database..."
docker compose exec -T informix bash -c "echo 'CREATE DATABASE stores_demo WITH LOG;' | dbaccess sysmaster - 2>/dev/null" || echo "  (Database may already exist)"

# Run initialization SQL
echo ""
echo "Initializing tables and sample data..."
docker compose exec -T informix dbaccess stores_demo /opt/ibm/informix/sql/init_stores_demo.sql

# Verify data
echo ""
echo "=== Verification ==="
docker compose exec -T informix dbaccess stores_demo - <<'EOF'
SELECT 'Customers: ' || COUNT(*)::CHAR(10) FROM customer;
SELECT 'Orders: ' || COUNT(*)::CHAR(10) FROM orders;
SELECT 'Items: ' || COUNT(*)::CHAR(10) FROM items;
SELECT 'Stock: ' || COUNT(*)::CHAR(10) FROM stock;
SELECT 'Manufacturers: ' || COUNT(*)::CHAR(10) FROM manufact;
SELECT 'States: ' || COUNT(*)::CHAR(10) FROM state;
EOF

echo ""
echo "=== ✓ Database initialization complete! ==="
echo ""
echo "You can now:"
echo "  • Run example 4GL programs: docker compose exec backend python -m fglinterpreter examples/stores_demo_query.4gl"
echo "  • Use the Studio IDE: http://localhost:9002"
echo "  • Access Informix directly: docker compose exec informix dbaccess stores_demo"
echo ""
