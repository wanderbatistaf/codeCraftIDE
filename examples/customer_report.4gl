-- customer_report.4gl
-- Demonstrates cursor loops with real Informix stores_demo database
-- This example connects to the Docker Informix container and queries
-- the pre-installed stores_demo database

MAIN
    DEFINE cust_num INTEGER
    DEFINE fname CHAR(15)
    DEFINE lname CHAR(15)
    DEFINE company CHAR(20)
    DEFINE city CHAR(15)
    DEFINE state CHAR(2)
    DEFINE order_num INTEGER
    DEFINE order_date DATE
    DEFINE ship_date DATE
    DEFINE customer_count INTEGER
    DEFINE total_orders INTEGER

    DISPLAY "=== Customer Orders Report ==="
    DISPLAY "Using stores_demo database on Docker Informix"
    DISPLAY ""

    -- Initialize counters
    LET customer_count = 0
    LET total_orders = 0

    -- Main cursor: Get customers from California
    DISPLAY "California Customers and Their Orders:"
    DISPLAY "========================================"
    DISPLAY ""

    DECLARE customer_cursor CURSOR FOR
        SELECT customer_num, fname, lname, company, city, state
        FROM customer
        WHERE state = "CA"
        ORDER BY lname, fname

    FOREACH customer_cursor INTO cust_num, fname, lname, company, city, state
        LET customer_count = customer_count + 1

        DISPLAY "Customer #", cust_num, ": ", fname, " ", lname
        DISPLAY "  Company: ", company
        DISPLAY "  Location: ", city, ", ", state
        DISPLAY "  Orders:"

        -- Nested cursor: Get orders for this customer
        DECLARE order_cursor CURSOR FOR
            SELECT order_num, order_date, ship_date
            FROM orders
            WHERE customer_num = cust_num
            ORDER BY order_date DESC

        FOREACH order_cursor INTO order_num, order_date, ship_date
            DISPLAY "    Order #", order_num
            DISPLAY "      Date: ", order_date
            IF ship_date IS NOT NULL THEN
                DISPLAY "      Shipped: ", ship_date
            ELSE
                DISPLAY "      Status: Not yet shipped"
            END IF

            LET total_orders = total_orders + 1
        END FOREACH

        CLOSE order_cursor

        DISPLAY ""
    END FOREACH

    CLOSE customer_cursor

    -- Display summary
    DISPLAY "========================================"
    DISPLAY "Summary:"
    DISPLAY "  Total CA Customers: ", customer_count
    DISPLAY "  Total Orders: ", total_orders
    DISPLAY ""
    DISPLAY "=== Report Complete ==="

END MAIN
