-- database_example.4gl
-- Demonstrates database integration features in fglInterpreter
--
-- This example shows:
-- - DATABASE statement
-- - SELECT with INTO clause
-- - INSERT/UPDATE/DELETE statements
-- - Transaction management (BEGIN WORK, COMMIT, ROLLBACK)
-- - Cursor management (DECLARE, OPEN, FETCH, CLOSE)
-- - FOREACH iteration
-- - SQLCA usage

MAIN
    DEFINE customer_id INTEGER
    DEFINE customer_name VARCHAR(50)
    DEFINE customer_email VARCHAR(100)
    DEFINE row_count INTEGER
    DEFINE cursor_id INTEGER
    DEFINE cursor_name VARCHAR(50)

    -- Connect to database
    DATABASE testdb@localhost:9088

    DISPLAY "=== Database Integration Example ==="
    DISPLAY ""

    -- Example 1: Simple SELECT with INTO
    DISPLAY "1. SELECT with INTO clause:"
    SELECT name, email INTO customer_name, customer_email
    FROM customers
    WHERE id = 1

    IF SQLCODE = 0 THEN
        DISPLAY "Customer found: ", customer_name, " <", customer_email, ">"
    ELSE
        DISPLAY "Customer not found (SQLCODE: ", SQLCODE, ")"
    END IF
    DISPLAY ""

    -- Example 2: Transaction with INSERT
    DISPLAY "2. Transaction with INSERT:"
    BEGIN WORK

    INSERT INTO customers (name, email, status)
    VALUES ("John Doe", "john@example.com", "active")

    IF SQLCODE = 0 THEN
        LET customer_id = SQLCA.SQLERRD[1]  -- Last insert ID
        DISPLAY "Customer inserted with ID: ", customer_id
        COMMIT WORK
        DISPLAY "Transaction committed"
    ELSE
        ROLLBACK WORK
        DISPLAY "Transaction rolled back (SQLCODE: ", SQLCODE, ")"
    END IF
    DISPLAY ""

    -- Example 3: UPDATE statement
    DISPLAY "3. UPDATE statement:"
    UPDATE customers
    SET status = "inactive"
    WHERE id = customer_id

    LET row_count = SQLCA.SQLERRD[1]  -- Rows affected
    DISPLAY "Rows updated: ", row_count
    DISPLAY ""

    -- Example 4: Cursor with DECLARE/OPEN/CLOSE
    DISPLAY "4. Cursor management:"
    DECLARE customer_cursor CURSOR FOR
        SELECT id, name FROM customers WHERE status = "active"

    OPEN customer_cursor

    -- Note: In real 4GL, you would FETCH in a loop
    -- For this example, we'll show the cursor is working
    DISPLAY "Cursor opened successfully"

    CLOSE customer_cursor
    DISPLAY "Cursor closed"
    DISPLAY ""

    -- Example 5: FOREACH iteration
    DISPLAY "5. FOREACH iteration:"
    DECLARE active_customers CURSOR FOR
        SELECT id, name FROM customers WHERE status = "active"

    OPEN active_customers

    FOREACH active_customers INTO cursor_id, cursor_name
        DISPLAY "Customer ", cursor_id, ": ", cursor_name
    END FOREACH

    CLOSE active_customers
    DISPLAY ""

    -- Example 6: DELETE with transaction
    DISPLAY "6. DELETE with transaction:"
    BEGIN WORK

    DELETE FROM customers WHERE status = "inactive"

    IF SQLCODE = 0 THEN
        LET row_count = SQLCA.SQLERRD[1]
        DISPLAY "Deleted ", row_count, " inactive customer(s)"
        COMMIT WORK
    ELSE
        ROLLBACK WORK
        DISPLAY "Delete failed (SQLCODE: ", SQLCODE, ")"
    END IF
    DISPLAY ""

    -- Example 7: Error handling
    DISPLAY "7. Error handling:"
    SELECT name INTO customer_name
    FROM non_existent_table

    IF SQLCODE != 0 THEN
        DISPLAY "Error occurred: ", SQLCA.SQLERRM
        DISPLAY "SQLCODE: ", SQLCODE
    END IF

    DISPLAY ""
    DISPLAY "=== Example Complete ==="

END MAIN
