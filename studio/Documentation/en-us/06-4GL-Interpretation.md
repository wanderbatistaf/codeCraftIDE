# 05 - 4GL Interpretation

## What happens when you click Run
Studio sends the active .4gl file to the backend via `POST /api/execute`.
Backend flow:
1) Parse code (lexer + parser)
2) Build AST
3) Interpreter executes AST
4) Backend returns output, timing, and errors

Output shows in the Console tab.

## Database during execution
- If a DB connection is active, it's included
- Interpreter uses it for embedded SQL

## Error types
- LexerError / ParserError: syntax errors
- RuntimeError: execution errors
- DB errors: connection or SQL failures

## Full example
File `hello.4gl`:
```4gl
MAIN
    DEFINE name CHAR(20)
    LET name = "World"
    DISPLAY "Hello", name
END MAIN
```

Steps:
1) Open `hello.4gl`
2) Click Run
3) Check Console output

Expected console:
```
Hello World
```

Known limitations:
- Only .4gl files can be executed
- Execution depends on backend availability

