# Example demonstrating function definitions and calls
# Tests: FUNCTION declarations, parameters, RETURN values

# Main program
MAIN
    DEFINE result INTEGER
    DEFINE area DECIMAL(10,2)
    DEFINE greeting CHAR(100)

    # Call function that returns an integer
    LET result = add_numbers(10, 20)
    DISPLAY "10 + 20 = ", result

    # Call function that calculates area
    LET area = calculate_circle_area(5.0)
    DISPLAY "Area of circle with radius 5.0 = ", area

    # Call function that returns a string
    LET greeting = get_greeting("Alice")
    DISPLAY greeting

    # Call function with no return value
    CALL print_multiplication_table(5)

END MAIN

# Function to add two numbers
FUNCTION add_numbers(a, b)
    DEFINE a, b INTEGER
    DEFINE sum INTEGER

    LET sum = a + b
    RETURN sum

END FUNCTION

# Function to calculate circle area
FUNCTION calculate_circle_area(radius)
    DEFINE radius DECIMAL(10,2)
    DEFINE area DECIMAL(10,2)
    DEFINE pi DECIMAL(10,5)

    LET pi = 3.14159
    LET area = pi * radius * radius
    RETURN area

END FUNCTION

# Function to generate a greeting
FUNCTION get_greeting(name)
    DEFINE name CHAR(50)
    DEFINE message CHAR(100)

    LET message = "Hello, ", name, "! Welcome to fglInterpreter."
    RETURN message

END FUNCTION

# Function with no return value (procedure)
FUNCTION print_multiplication_table(num)
    DEFINE num, i, result INTEGER

    DISPLAY "Multiplication table for ", num, ":"
    FOR i = 1 TO 10
        LET result = num * i
        DISPLAY num, " x ", i, " = ", result
    END FOR

END FUNCTION
