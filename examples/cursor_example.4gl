-- cursor_example.4gl
-- Demonstrates cursor operations and iteration

MAIN
    DEFINE product_id INTEGER
    DEFINE product_name VARCHAR(100)
    DEFINE product_price DECIMAL(10,2)
    DEFINE total_price DECIMAL(10,2)
    DEFINE product_count INTEGER

    DISPLAY "=== Cursor Operations Example ==="
    DISPLAY ""

    -- Initialize counters
    LET total_price = 0.00
    LET product_count = 0

    -- Example 1: Simple cursor iteration with FOREACH
    DISPLAY "Products in stock:"
    DISPLAY "----------------------------------------"

    DECLARE product_cursor CURSOR FOR
        SELECT id, name, price
        FROM products
        WHERE stock > 0
        ORDER BY name

    OPEN product_cursor

    FOREACH product_cursor INTO product_id, product_name, product_price
        DISPLAY product_id, " | ", product_name, " | $", product_price

        -- Calculate totals
        LET total_price = total_price + product_price
        LET product_count = product_count + 1
    END FOREACH

    CLOSE product_cursor

    DISPLAY "----------------------------------------"
    DISPLAY "Total products: ", product_count
    DISPLAY "Total value: $", total_price
    DISPLAY ""

    -- Example 2: Cursor with filtered results
    DISPLAY "Expensive products (price > $100):"
    DISPLAY "----------------------------------------"

    DECLARE expensive_cursor CURSOR FOR
        SELECT id, name, price
        FROM products
        WHERE price > 100.00
        ORDER BY price DESC

    OPEN expensive_cursor

    LET product_count = 0

    FOREACH expensive_cursor INTO product_id, product_name, product_price
        DISPLAY product_name, ": $", product_price
        LET product_count = product_count + 1
    END FOREACH

    CLOSE expensive_cursor

    DISPLAY "Found ", product_count, " expensive products"
    DISPLAY ""

    -- Example 3: Nested cursor (orders and order items)
    DISPLAY "Orders with items:"
    DISPLAY "========================================"

    DECLARE order_cursor CURSOR FOR
        SELECT id, customer_id, total
        FROM orders
        WHERE status = "pending"

    DECLARE item_cursor CURSOR FOR
        SELECT product_id, quantity, price
        FROM order_items
        WHERE order_id = product_id  -- Would be actual order_id in real code

    OPEN order_cursor

    FOREACH order_cursor INTO product_id, product_name, product_price
        DISPLAY "Order #", product_id, " - Customer: ", product_name, " - Total: $", product_price

        -- Note: In real 4GL, inner cursor would use order_id from outer loop
        -- This is simplified for demonstration
    END FOREACH

    CLOSE order_cursor

    DISPLAY ""
    DISPLAY "=== Cursor Example Complete ==="

END MAIN
