# 10 - Remote Mode (SFTP)

## What remote mode is
Edit files directly from a remote server via SFTP. The IDE switches to Remote mode.

## Activation
- In the DB connection, enable `use_remote_files`
- Set `remote_workspace_path` if needed
- Top indicator switches to Remote

## Open remote files
- File > Open File(s) from Server
- File > Browse Server Folder

## Important rules
- Unsaved changes block mode switching
- Files opened by absolute path are marked as external
- Save uses SFTP endpoints

Example:
1) Enable remote mode
2) Browse Server Folder
3) Open a remote file
4) Edit and Save

Known limitations:
- Performance depends on network/server
- Some paths require server permissions

