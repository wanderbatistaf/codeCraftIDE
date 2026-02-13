# 06 - 4make Compilation

## What compilation does
Compilation uses 4make (Informix/4GL compiler) on the backend to generate binaries.

## How to compile
Run > Compile with 4make

Rules:
- Only .4gl files can be compiled
- Backend must have 4make installed

Example:
1) Open a .4gl
2) Run > Compile with 4make
3) See success/error toast

Notes:
- Compilation is different from interpretation
- Compile does not replace Run

Known limitations:
- Without 4make installed, compilation fails

