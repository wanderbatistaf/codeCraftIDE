# Example demonstrating database operations
# Tests: SELECT, INSERT, UPDATE, DELETE statements
# Requires: Informix database connection (Epic 2)

MAIN
    DEFINE cust_id INTEGER
    DEFINE cust_name CHAR(100)
    DEFINE cust_email CHAR(100)
    DEFINE order_count INTEGER

    # Simple SELECT query
    SELECT customer_name, customer_email
        INTO cust_name, cust_email
        FROM customers
        WHERE customer_id = 1

    DISPLAY "Customer Name: ", cust_name
    DISPLAY "Customer Email: ", cust_email

    # SELECT with aggregate function
    SELECT COUNT(*)
        INTO order_count
        FROM orders
        WHERE customer_id = 1

    DISPLAY "Number of orders: ", order_count

    # INSERT statement
    INSERT INTO customers (customer_id, customer_name, customer_email)
        VALUES (100, "Jane Smith", "jane.smith@example.com")

    DISPLAY "New customer inserted"

    # UPDATE statement
    UPDATE customers
        SET customer_email = "jane.updated@example.com"
        WHERE customer_id = 100

    DISPLAY "Customer email updated"

    # SELECT with cursor (multiple rows)
    DECLARE customer_cursor CURSOR FOR
        SELECT customer_id, customer_name
        FROM customers
        WHERE customer_id > 10
        ORDER BY customer_name

    OPEN customer_cursor

    FOREACH customer_cursor INTO cust_id, cust_name
        DISPLAY "ID: ", cust_id, " - Name: ", cust_name
    END FOREACH

    CLOSE customer_cursor
    FREE customer_cursor

    # DELETE statement
    DELETE FROM customers
        WHERE customer_id = 100

    DISPLAY "Customer deleted"

END MAIN
