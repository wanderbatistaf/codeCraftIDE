-- stores_demo_query.4gl
-- Simple query example using Informix stores_demo database
-- Perfect for testing database connectivity

MAIN
    DEFINE cust_num INTEGER
    DEFINE fname CHAR(15)
    DEFINE lname CHAR(15)
    DEFINE city CHAR(15)
    DEFINE state CHAR(2)
    DEFINE count_result INTEGER

    DISPLAY "=== Stores Demo Database Query ==="
    DISPLAY ""

    -- Example 1: Simple count query
    SELECT COUNT(*) INTO count_result
    FROM customer

    DISPLAY "Total customers in database: ", count_result
    DISPLAY ""

    -- Example 2: Select specific customer
    DISPLAY "Sample Customer (Customer #101):"
    DISPLAY "--------------------------------"

    SELECT customer_num, fname, lname, city, state
    INTO cust_num, fname, lname, city, state
    FROM customer
    WHERE customer_num = 101

    DISPLAY "Customer Number: ", cust_num
    DISPLAY "Name: ", fname, " ", lname
    DISPLAY "Location: ", city, ", ", state
    DISPLAY ""

    -- Example 3: List first 5 customers
    DISPLAY "First 5 Customers:"
    DISPLAY "--------------------------------"

    DECLARE cust_cursor CURSOR FOR
        SELECT FIRST 5 customer_num, fname, lname, city, state
        FROM customer
        ORDER BY customer_num

    FOREACH cust_cursor INTO cust_num, fname, lname, city, state
        DISPLAY cust_num, " | ", fname, " ", lname, " | ", city, ", ", state
    END FOREACH

    CLOSE cust_cursor

    DISPLAY ""
    DISPLAY "=== Query Complete ==="

END MAIN
