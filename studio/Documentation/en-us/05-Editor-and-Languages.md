# 04 - Editor and Languages

## 4GL (.4gl)
- Diagnostics and quick fixes
- Run execution
- Convert to Python

Example:
```4gl
MAIN
    DEFINE name CHAR(20)
    LET name = "World"
    DISPLAY "Hello", name
END MAIN
```

## PER (.per)
- Diagnostics
- Form preview next to editor
- Field validation

Minimal example:
```per
DATABASE mydb

SCREEN
{
    [name      ]
}
END

ATTRIBUTES
    name = formonly.name;
END
```

## FM2 (.fm2)
- Opens Lycia editor
- Visual preview with grid and zoom
- Can load external CSS

## Python (.py)
- Standard editing
- Convert to 4GL

## SQL (.sql), DEF (.def), CSS (.css)
- Standard editing
- CSS can be used in Lycia preview

Important behavior:
- Dirty marker for modified files
- Ctrl+S saves active file
- Save All saves all dirty tabs

Known limitations:
- Full diagnostics are only active for .4gl and .per

