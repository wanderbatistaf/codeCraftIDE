# 03 - Search and Command Palette

## File Search Modal
Studio search can find text inside files or find files by name.
Open it via the magnifier icon in Explorer.

Modes:
- Search Content: search within file contents
- Search File Names: search by file name only

Options:
- Case Sensitive
- Use Regex (Search Content only)

How it works:
- Local mode: `POST /api/files/search`
- Remote mode: `POST /api/sftp/search`
- Backend returns matching files and line hits
- IDE groups results by file and line
- Click a result to open the file and jump to the line

Example (Search Content):
1) Open search
2) Type `DISPLAY`
3) Click a result

Example (Search File Names):
1) Select Search File Names
2) Type `global`
3) Open the found file

Tips:
- Use regex like `LET\s+\w+\s*=`
- Case Sensitive helps find exact variable names

## Command Palette
Shortcut: Ctrl+P / Cmd+P

Use it to:
- Open files quickly
- Run common commands (e.g., Save All)
- Access recent files

Example:
1) Press Ctrl+P
2) Type part of a filename
3) Press Enter

Known limitations:
- Command Palette only exposes listed commands

