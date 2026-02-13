# 12 - Session and Persistence

Studio saves state per browser tab in sessionStorage:
- Open tabs
- Expanded folders
- Bottom panel height
- Active connection

Each browser tab has an isolated session.

Example:
1) Open two browser tabs
2) Each tab keeps its own state

Known limitations:
- State is not synced across browsers
- Clearing sessionStorage loses state

