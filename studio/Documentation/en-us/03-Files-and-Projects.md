# 02 - Files and Projects

Open files and folders:
- File > Open File(s) / Open Folder
- Double-click a file in the Explorer
- Command Palette (Ctrl+P / Cmd+P)

Create files and folders:
- File > New File / New Folder
- Buttons in Explorer
- Context menu (right-click) on a folder

Rename and delete:
- Context menu in Explorer
- Deleting closes related open tabs

Download file:
- Context menu on file > Download

Tabs and state:
- Open tabs are saved per browser tab (sessionStorage)
- Dirty indicator (dot)
- Closing a dirty tab asks for confirmation

## Projects (.ccp)

### What is a .ccp
A `.ccp` (CodeCraft Project) is the IDE project package. It contains:
- All project files (4GL, PER, SQL, etc.)
- IDE state at save time:
  - Open tabs
  - Active tab
  - Expanded folders

In practice, it's a snapshot of the project plus your working state.

### New Project
- Creates a new project in the workspace
- Initial structure:
  - `name.4gl` (main file)
  - `global.4gl` (global definitions)
  - `name.per` (sample form)
- Explorer switches root to the project folder

### Open Project
- Imports a `.ccp`
- Recreates files in the workspace
- Restores open tabs

### Save Project
- Generates a `.ccp` for download
- Includes current files + IDE state

Example: create and save
1) File > New Project
2) Enter name and description
3) Edit files
4) File > Save Project (downloads a .ccp)

Example: open project
1) File > Open Project
2) Select a .ccp
3) IDE recreates files and reopens tabs

Known limitations:
- Opening a .ccp overwrites current workspace contents
- Save Project always downloads (does not save on server)

