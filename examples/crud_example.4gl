-- crud_example.4gl
-- Simple CRUD (Create, Read, Update, Delete) operations example

MAIN
    DEFINE user_id INTEGER
    DEFINE user_name VARCHAR(50)
    DEFINE user_email VARCHAR(100)

    DISPLAY "=== CRUD Operations Example ==="
    DISPLAY ""

    -- CREATE: Insert a new user
    DISPLAY "CREATE: Inserting new user..."
    BEGIN WORK

    INSERT INTO users (name, email, status)
    VALUES ("Alice Smith", "alice@example.com", "active")

    IF SQLCODE = 0 THEN
        LET user_id = SQLCA.SQLERRD[1]
        DISPLAY "User created with ID: ", user_id
        COMMIT WORK
    ELSE
        ROLLBACK WORK
        DISPLAY "Failed to create user"
    END IF
    DISPLAY ""

    -- READ: Select the user
    DISPLAY "READ: Fetching user..."
    SELECT name, email INTO user_name, user_email
    FROM users
    WHERE id = user_id

    IF SQLCODE = 0 THEN
        DISPLAY "User found:"
        DISPLAY "  Name: ", user_name
        DISPLAY "  Email: ", user_email
    ELSE
        DISPLAY "User not found"
    END IF
    DISPLAY ""

    -- UPDATE: Modify the user
    DISPLAY "UPDATE: Updating user email..."
    UPDATE users
    SET email = "alice.smith@example.com"
    WHERE id = user_id

    IF SQLCODE = 0 THEN
        DISPLAY "User updated successfully"
        DISPLAY "Rows affected: ", SQLCA.SQLERRD[1]
    ELSE
        DISPLAY "Failed to update user"
    END IF
    DISPLAY ""

    -- DELETE: Remove the user
    DISPLAY "DELETE: Removing user..."
    BEGIN WORK

    DELETE FROM users WHERE id = user_id

    IF SQLCODE = 0 THEN
        DISPLAY "User deleted successfully"
        DISPLAY "Rows affected: ", SQLCA.SQLERRD[1]
        COMMIT WORK
    ELSE
        ROLLBACK WORK
        DISPLAY "Failed to delete user"
    END IF

    DISPLAY ""
    DISPLAY "=== CRUD Example Complete ==="

END MAIN
