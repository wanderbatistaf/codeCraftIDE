# fglInterpreter Examples

This directory contains sample Informix 4GL scripts demonstrating various language features and use cases.

## Basic Examples

### hello_world.4gl
A simple "Hello, World!" program to test basic display functionality.

**Features demonstrated:**
- MAIN block
- DISPLAY statements

**Usage:**
```bash
fgl run examples/hello_world.4gl
```

### variables_and_conditionals.4gl
Demonstrates variable declarations, assignments, and conditional logic.

**Features demonstrated:**
- Variable declarations (INTEGER, CHAR, DECIMAL)
- LET statements (assignments)
- IF/THEN/ELSE conditionals
- Nested IF statements
- Arithmetic expressions

**Usage:**
```bash
fgl run examples/variables_and_conditionals.4gl
```

## Control Flow Examples

### loops.4gl
Examples of different loop structures in 4GL.

**Features demonstrated:**
- FOR loops (simple and with STEP)
- WHILE loops
- Nested loops
- Loop-based calculations (factorial, multiplication tables)

**Usage:**
```bash
fgl run examples/loops.4gl
```

## Function Examples

### functions.4gl
Demonstrates function definitions and function calls.

**Features demonstrated:**
- FUNCTION declarations
- Function parameters
- RETURN statements
- Functions returning different types (INTEGER, DECIMAL, CHAR)
- Procedures (functions without return values)

**Usage:**
```bash
fgl run examples/functions.4gl
```

## Database Examples

### database_query.4gl
Examples of database operations using embedded SQL.

**Features demonstrated:**
- SELECT INTO statements
- INSERT statements
- UPDATE statements
- DELETE statements
- CURSOR declarations
- FOREACH loops with cursors
- Aggregate functions (COUNT)

**Prerequisites:**
- Informix database connection configured
- Database tables: customers, orders
- Environment variables set in .env file

**Usage:**
```bash
fgl run --db-config .env examples/database_query.4gl
```

**Note:** This example requires Epic 2 (Database Integration) to be completed.

## Testing the Examples

### Without Database
Most examples can be run without a database connection:

```bash
# Run all basic examples
fgl run examples/hello_world.4gl
fgl run examples/variables_and_conditionals.4gl
fgl run examples/loops.4gl
fgl run examples/functions.4gl
```

### With Database
Database examples require proper configuration:

1. Copy `.env.example` to `.env`
2. Configure your Informix database connection
3. Run the database example:

```bash
fgl run --db-config .env examples/database_query.4gl
```

## Converting Examples to Python

You can convert any example to Python using the converter:

```bash
fgl convert examples/hello_world.4gl -o hello_world.py
python hello_world.py
```

**Note:** The converter will be available after Story 1.5 is completed.

## Creating Your Own Examples

Feel free to create your own 4GL scripts and test them with fglInterpreter. The basic structure is:

```4gl
# Comments start with #

MAIN
    DEFINE variable_name TYPE

    # Your code here
    DISPLAY "Hello!"

END MAIN
```

For functions:

```4gl
FUNCTION function_name(param1, param2)
    DEFINE param1, param2 TYPE
    DEFINE result TYPE

    # Function logic here

    RETURN result
END FUNCTION
```

## Reference

For complete 4GL syntax reference, see:
- [Informix 4GL Reference Manual](https://www.ibm.com/docs/en/informix-servers/14.10?topic=reference-informix-4gl)
- [fglInterpreter Documentation](../docs/)
