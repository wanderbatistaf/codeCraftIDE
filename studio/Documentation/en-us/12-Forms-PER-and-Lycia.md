# 11 - Forms (PER and Lycia)

## PER Preview
When you open a .per:
- Editor on the left
- Preview on the right
- Backend validates the form

Example:
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

Errors show in the preview if any.

## Lycia (FM2)
For .fm2, Lycia Editor provides:
- Visual preview
- Grid and zoom
- Fullscreen
- Properties panel
- External CSS
- HTML snapshot

Example flow:
1) Open a .fm2
2) Enable grid
3) Adjust zoom
4) Load CSS

Known limitations:
- Preview depends on parser and may fail on incomplete files

