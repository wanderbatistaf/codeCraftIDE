#!/bin/bash
# Script to verify Informix stores_demo database is ready

echo "Waiting for Informix to be ready..."
sleep 10

# Check if database is accessible
echo "Checking if stores_demo database exists..."
docker compose exec -T informix bash -c "echo 'SELECT COUNT(*) FROM customer;' | dbaccess stores_demo -" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ stores_demo database is ready!"
    echo "✓ Sample data is available"
else
    echo "✗ Database not ready yet. Please wait 60-90 seconds for Informix to fully initialize."
    echo "  Run this script again or check: docker compose logs informix"
fi
