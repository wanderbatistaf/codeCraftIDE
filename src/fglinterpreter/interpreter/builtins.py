"""
Built-in functions for Informix 4GL.

This module implements all standard 4GL built-in functions including:
- String functions (LENGTH, UPSHIFT, DOWNSHIFT, TRIM, SUBSTR, etc.)
- Date/Time functions (TODAY, CURRENT, DATE, DATETIME, etc.)
- Math functions (ABS, SQRT, MOD, ROUND, etc.)
- Type conversion functions
"""

import datetime
import math
from decimal import Decimal
from typing import Any, Optional, Union

# ============================================================================
# String Functions
# ============================================================================


def LENGTH(s: Optional[str]) -> int:
    """Return the length of a string."""
    if s is None:
        return 0
    return len(str(s))


def LEN(s: Optional[str]) -> int:
    """Alias for LENGTH."""
    return LENGTH(s)


def UPSHIFT(s: Optional[str]) -> str:
    """Convert string to uppercase."""
    if s is None:
        return ""
    return str(s).upper()


def DOWNSHIFT(s: Optional[str]) -> str:
    """Convert string to lowercase."""
    if s is None:
        return ""
    return str(s).lower()


def UPPER(s: Optional[str]) -> str:
    """Alias for UPSHIFT."""
    return UPSHIFT(s)


def LOWER(s: Optional[str]) -> str:
    """Alias for DOWNSHIFT."""
    return DOWNSHIFT(s)


def TRIM(s: Optional[str]) -> str:
    """Remove leading and trailing whitespace."""
    if s is None:
        return ""
    return str(s).strip()


def LTRIM(s: Optional[str]) -> str:
    """Remove leading whitespace."""
    if s is None:
        return ""
    return str(s).lstrip()


def RTRIM(s: Optional[str]) -> str:
    """Remove trailing whitespace."""
    if s is None:
        return ""
    return str(s).rstrip()


def SUBSTR(s: Optional[str], start: int, length: Optional[int] = None) -> str:
    """
    Extract substring. 4GL uses 1-based indexing.

    Args:
        s: Source string
        start: Starting position (1-based)
        length: Number of characters (optional)
    """
    if s is None:
        return ""

    s_str = str(s)

    # Convert to 0-based indexing
    start_idx = start - 1

    if start_idx < 0:
        start_idx = 0

    if length is None:
        return s_str[start_idx:]
    else:
        end_idx = start_idx + length
        return s_str[start_idx:end_idx]


def CLIPPED(s: Optional[str]) -> str:
    """Remove trailing spaces (CHAR to VARCHAR conversion)."""
    if s is None:
        return ""
    return str(s).rstrip()


def SPACES(n: int) -> str:
    """Return a string of n spaces."""
    return " " * max(0, int(n))


def ASCII(char: str) -> int:
    """Return ASCII code of first character."""
    if not char:
        return 0
    return ord(char[0])


def ORD(char: str) -> int:
    """Alias for ASCII."""
    return ASCII(char)


def CHR(code: int) -> str:
    """Return character for ASCII code."""
    try:
        return chr(int(code))
    except (ValueError, OverflowError):
        return ""


# ============================================================================
# Date/Time Functions
# ============================================================================


def TODAY() -> datetime.date:
    """Return current date."""
    return datetime.date.today()


def CURRENT() -> datetime.datetime:
    """Return current date and time."""
    return datetime.datetime.now()


def DATE(value: Union[str, datetime.date, datetime.datetime]) -> datetime.date:
    """
    Convert value to date.

    Args:
        value: String, date, or datetime

    Returns:
        Date object
    """
    if isinstance(value, datetime.date):
        return value
    elif isinstance(value, datetime.datetime):
        return value.date()
    elif isinstance(value, str):
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                return datetime.datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {value}")
    else:
        raise TypeError(f"Cannot convert {type(value)} to date")


def DATETIME(value: Union[str, datetime.datetime]) -> datetime.datetime:
    """
    Convert value to datetime.

    Args:
        value: String or datetime

    Returns:
        Datetime object
    """
    if isinstance(value, datetime.datetime):
        return value
    elif isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time())
    elif isinstance(value, str):
        # Try common datetime formats
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"]:
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse datetime: {value}")
    else:
        raise TypeError(f"Cannot convert {type(value)} to datetime")


def DAY(d: datetime.date) -> int:
    """Return day of month from date."""
    return d.day


def MONTH(d: datetime.date) -> int:
    """Return month from date."""
    return d.month


def YEAR(d: datetime.date) -> int:
    """Return year from date."""
    return d.year


def WEEKDAY(d: datetime.date) -> int:
    """Return day of week (0=Sunday, 1=Monday, ..., 6=Saturday)."""
    # Python's weekday(): 0=Monday, 6=Sunday
    # 4GL's weekday(): 0=Sunday, 6=Saturday
    py_weekday = d.weekday()
    return (py_weekday + 1) % 7


def MDY(month: int, day: int, year: int) -> datetime.date:
    """Create date from month, day, year."""
    return datetime.date(year, month, day)


def DMY(day: int, month: int, year: int) -> datetime.date:
    """Create date from day, month, year."""
    return datetime.date(year, month, day)


# ============================================================================
# Math Functions
# ============================================================================


def ABS(n: Union[int, float, Decimal]) -> Union[int, float, Decimal]:
    """Return absolute value."""
    return abs(n)


def SQRT(n: Union[int, float]) -> float:
    """Return square root."""
    return math.sqrt(float(n))


def MOD(n: Union[int, float], m: Union[int, float]) -> Union[int, float]:
    """Return modulo (remainder of n/m)."""
    return n % m


def ROUND(n: Union[int, float, Decimal], digits: int = 0) -> Union[float, Decimal]:
    """Round to specified number of digits."""
    if isinstance(n, Decimal):
        return round(n, digits)
    return round(float(n), digits)


def TRUNC(n: Union[int, float, Decimal], digits: int = 0) -> Union[float, Decimal]:
    """Truncate to specified number of digits."""
    if digits == 0:
        return math.trunc(float(n))
    else:
        multiplier = 10**digits
        return math.trunc(float(n) * multiplier) / multiplier


def CEIL(n: Union[int, float]) -> int:
    """Return ceiling (smallest integer >= n)."""
    return math.ceil(float(n))


def FLOOR(n: Union[int, float]) -> int:
    """Return floor (largest integer <= n)."""
    return math.floor(float(n))


def POW(base: Union[int, float], exp: Union[int, float]) -> float:
    """Return base raised to power exp."""
    return math.pow(float(base), float(exp))


def POWER(base: Union[int, float], exp: Union[int, float]) -> float:
    """Alias for POW."""
    return POW(base, exp)


def LOG(n: Union[int, float]) -> float:
    """Return natural logarithm."""
    return math.log(float(n))


def LOG10(n: Union[int, float]) -> float:
    """Return base-10 logarithm."""
    return math.log10(float(n))


def EXP(n: Union[int, float]) -> float:
    """Return e raised to power n."""
    return math.exp(float(n))


def SIN(n: Union[int, float]) -> float:
    """Return sine (radians)."""
    return math.sin(float(n))


def COS(n: Union[int, float]) -> float:
    """Return cosine (radians)."""
    return math.cos(float(n))


def TAN(n: Union[int, float]) -> float:
    """Return tangent (radians)."""
    return math.tan(float(n))


def ASIN(n: Union[int, float]) -> float:
    """Return arcsine (radians)."""
    return math.asin(float(n))


def ACOS(n: Union[int, float]) -> float:
    """Return arccosine (radians)."""
    return math.acos(float(n))


def ATAN(n: Union[int, float]) -> float:
    """Return arctangent (radians)."""
    return math.atan(float(n))


# ============================================================================
# Type Conversion Functions
# ============================================================================


def NVL(value: Any, default: Any) -> Any:
    """Return default if value is None, otherwise return value."""
    return default if value is None else value


def COALESCE(*args: Any) -> Any:
    """Return first non-None value."""
    for arg in args:
        if arg is not None:
            return arg
    return None


# ============================================================================
# Built-in Functions Registry
# ============================================================================

BUILTIN_FUNCTIONS = {
    # String functions
    "LENGTH": LENGTH,
    "LEN": LEN,
    "UPSHIFT": UPSHIFT,
    "DOWNSHIFT": DOWNSHIFT,
    "UPPER": UPPER,
    "LOWER": LOWER,
    "TRIM": TRIM,
    "LTRIM": LTRIM,
    "RTRIM": RTRIM,
    "SUBSTR": SUBSTR,
    "CLIPPED": CLIPPED,
    "SPACES": SPACES,
    "ASCII": ASCII,
    "ORD": ORD,
    "CHR": CHR,
    # Date/Time functions
    "TODAY": TODAY,
    "CURRENT": CURRENT,
    "DATE": DATE,
    "DATETIME": DATETIME,
    "DAY": DAY,
    "MONTH": MONTH,
    "YEAR": YEAR,
    "WEEKDAY": WEEKDAY,
    "MDY": MDY,
    "DMY": DMY,
    # Math functions
    "ABS": ABS,
    "SQRT": SQRT,
    "MOD": MOD,
    "ROUND": ROUND,
    "TRUNC": TRUNC,
    "CEIL": CEIL,
    "FLOOR": FLOOR,
    "POW": POW,
    "POWER": POWER,
    "LOG": LOG,
    "LOG10": LOG10,
    "EXP": EXP,
    "SIN": SIN,
    "COS": COS,
    "TAN": TAN,
    "ASIN": ASIN,
    "ACOS": ACOS,
    "ATAN": ATAN,
    # Utility functions
    "NVL": NVL,
    "COALESCE": COALESCE,
}


def get_builtin_function(name: str) -> Optional[callable]:
    """
    Get a built-in function by name (case-insensitive).

    Args:
        name: Function name

    Returns:
        Function object or None if not found
    """
    return BUILTIN_FUNCTIONS.get(name.upper())


def is_builtin_function(name: str) -> bool:
    """
    Check if a name is a built-in function.

    Args:
        name: Function name

    Returns:
        True if it's a built-in function
    """
    return name.upper() in BUILTIN_FUNCTIONS
