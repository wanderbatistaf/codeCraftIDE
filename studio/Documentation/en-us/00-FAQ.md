# 00 - Frequently Asked Questions

## Overview

Q: Can I use Studio without a database?
A: Yes. The IDE works without an active DB connection, but DB features are disabled.

Q: Do I need to install anything in the browser?
A: No. The IDE runs in the browser and uses the backend via HTTP.

## Interface

Q: Where do I see Run output?
A: In the Console tab on the Bottom Panel.

Q: Can I hide the Bottom Panel?
A: Not currently; you can only resize its height.

## Files and Projects

Q: Can I version .ccp in Git?
A: You can, but it's usually better to version the source files directly.

Q: Does .ccp store DB credentials?
A: No. It stores files and IDE state, not credentials.

## Search and Command Palette

Q: Does search scan binary files?
A: No. It is designed for text.

Q: Can I search only within a folder?
A: Not currently; it searches the whole workspace.

## Editor and Languages

Q: Can I run .py in the IDE?
A: No. Only .4gl is executable by the interpreter.

Q: Does the editor have semantic autocomplete?
A: Monaco provides basic editing features, but no dedicated semantic autocomplete.

## 4GL Interpretation

Q: Why is Run disabled?
A: Active tab is not a .4gl or there's no active tab.

Q: Does Run auto-save?
A: No. Save manually if needed.

## 4make Compilation

Q: Where is the output binary?
A: On the backend environment, as configured by 4make.

Q: Can I compile entire projects?
A: IDE compiles the active file; directory compile is via backend/CLI.

## 4GL-Python Conversion

Q: Is the original file modified?
A: No. A new file is created next to it.

Q: Can I choose output folder?
A: Not in the current IDE; output is same directory.

## Diagnostics and Quick Fixes

Q: Why no diagnostics on .py?
A: Diagnostics focus on .4gl and .per.

Q: Do quick fixes modify files automatically?
A: Yes, when applied.

## Database

Q: Can I save multiple connections?
A: Yes, the IDE manages multiple configs.

Q: Does SQL Query support transactions?
A: Depends on backend and driver.

## Remote Mode (SFTP)

Q: Can I use remote mode without DB config?
A: Remote mode is tied to a DB connection config.

Q: Can I open files outside the remote workspace?
A: Yes, via absolute path, marked as external.

## Forms (PER and Lycia)

Q: Does preview update in real time?
A: Yes, with a small debounce after edits.

Q: Can I export HTML from Lycia?
A: Yes, via the HTML dialog.

## Session and Persistence

Q: Do my tabs persist after restarting the browser?
A: No. sessionStorage is per session.

Q: Can I persist permanently?
A: Not currently.

## Shortcuts

Q: Is there a Run shortcut?
A: Run button exists, but no dedicated shortcut yet.

Q: Can I customize shortcuts?
A: Not currently.

## Troubleshooting

Q: IDE opens but no files are listed.
A: Check backend status and /api/files/tree response.

Q: Search returns nothing.
A: Ensure Search Content mode and backend response.
