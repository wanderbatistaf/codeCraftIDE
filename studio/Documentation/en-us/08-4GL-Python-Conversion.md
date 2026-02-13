# 07 - 4GL <-> Python Conversion

## 4GL -> Python
Run > Convert to Python

Flow:
1) Studio sends .4gl to `POST /api/conversion/convert`
2) Backend generates Python
3) IDE creates `.py` in the same directory
4) New file opens automatically

Example 4GL:
```4gl
MAIN
    DEFINE x INTEGER
    LET x = 10
    DISPLAY x
END MAIN
```

Example Python output:
```python
def main() -> None:
    x: int = 0
    x = 10
    print(x)
```

## Python -> 4GL
Run > Convert to 4GL

Flow:
1) Studio sends .py to `POST /api/conversion/reverse`
2) Backend generates 4GL
3) IDE creates `.4gl` in the same directory
4) New file opens

## Warnings
- Conversion may emit warnings for unmapped constructs
- IDE displays warnings when provided

Tips:
- Convert small files first
- Compare 4GL vs Python output when possible

Known limitations:
- Not all 4GL features map 1:1 to Python
- Reverse conversion is limited to supported subset

