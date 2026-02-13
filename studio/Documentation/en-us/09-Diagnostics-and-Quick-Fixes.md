# 08 - Diagnostics and Quick Fixes

## What diagnostics are
Diagnostics are static analyses that detect errors, warnings, and improvements.
Backend endpoint: `POST /api/diagnostics`.

## Quick Fixes
When diagnostics provide suggestions, the editor shows quick fixes.
Actions are fetched via `POST /api/code-actions`.

Example:
1) Create an undefined variable
2) Editor marks the line
3) Apply a quick fix

Example issue:
```4gl
MAIN
    DISPLAY x
END MAIN
```

Result:
- Diagnostic: undefined variable x
- Quick fix: suggest DEFINE x

Known limitations:
- Diagnostics do not replace the compiler (static analysis only)

