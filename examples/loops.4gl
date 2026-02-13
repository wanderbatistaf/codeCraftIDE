# Example demonstrating loop structures
# Tests: FOR loops, WHILE loops, and FOREACH

MAIN
    DEFINE i, j, factorial INTEGER
    DEFINE count INTEGER

    # Simple FOR loop
    DISPLAY "Counting from 1 to 10:"
    FOR i = 1 TO 10
        DISPLAY "Count: ", i
    END FOR

    # FOR loop with STEP
    DISPLAY ""
    DISPLAY "Counting by 2s from 0 to 20:"
    FOR i = 0 TO 20 STEP 2
        DISPLAY i
    END FOR

    # Nested FOR loops (multiplication table)
    DISPLAY ""
    DISPLAY "3x3 Multiplication Table:"
    FOR i = 1 TO 3
        FOR j = 1 TO 3
            DISPLAY i, " x ", j, " = ", i * j
        END FOR
    END FOR

    # WHILE loop
    DISPLAY ""
    DISPLAY "WHILE loop countdown:"
    LET count = 5
    WHILE count > 0
        DISPLAY "Count: ", count
        LET count = count - 1
    END WHILE
    DISPLAY "Blast off!"

    # Calculate factorial using loop
    DISPLAY ""
    LET factorial = 1
    FOR i = 1 TO 5
        LET factorial = factorial * i
    END FOR
    DISPLAY "5! (factorial) = ", factorial

END MAIN
