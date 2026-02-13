# Example demonstrating variables and conditional logic
# Tests: variable declaration, assignment, and IF statements

MAIN
    DEFINE x, y, sum INTEGER
    DEFINE name CHAR(50)
    DEFINE price DECIMAL(10,2)

    # Variable assignments
    LET x = 10
    LET y = 20
    LET sum = x + y
    LET name = "John Doe"
    LET price = 99.99

    # Display variables
    DISPLAY "Name: ", name
    DISPLAY "X = ", x
    DISPLAY "Y = ", y
    DISPLAY "Sum = ", sum
    DISPLAY "Price = $", price

    # Conditional logic
    IF x < y THEN
        DISPLAY "x is less than y"
    ELSE
        DISPLAY "x is greater than or equal to y"
    END IF

    # Nested conditionals
    IF sum > 25 THEN
        IF sum > 30 THEN
            DISPLAY "Sum is greater than 30"
        ELSE
            DISPLAY "Sum is between 25 and 30"
        END IF
    ELSE
        DISPLAY "Sum is 25 or less"
    END IF

END MAIN
