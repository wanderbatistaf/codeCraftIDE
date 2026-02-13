# 09 - Database

## Configure connections
Database > Configure Connections

Main fields:
- host, port, database, username, password
- driver: wbjdbc or wborm
- server and db_type optional

After saving, the connection appears in the list and can be activated.

## Database Explorer
Shows tables and columns for the active DB.
- Expand table to see columns
- Search by table or column name
- Context menu:
  - Copy Table Name
  - Generate SELECT *
- View Sample Data opens data dialog

## SQL Query Panel
- Multiple query tabs
- Ctrl+Enter executes
- Results in table
- Export CSV (Copy/Download)

## SSH Terminal
- Opens remote terminal using SSH
- Uses SSH credentials from the connection
- If not set, uses DB host/user

Example flow:
1) Configure a connection
2) Activate it
3) Explore tables
4) Run a SELECT in SQL Query

Known limitations:
- Terminal requires SSH access on the server
- Data viewer may limit rows (default 100)

