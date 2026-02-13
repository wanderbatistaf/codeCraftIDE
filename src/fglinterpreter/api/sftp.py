"""SFTP API endpoints for remote file system operations."""

import asyncio
from typing import Any, Dict

import paramiko
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..sftp.sftp_manager import SFTPConfig, SFTPFileManager

router = APIRouter(prefix="/api/sftp", tags=["sftp"])

# In-memory cache of active SFTP connections (keyed by config name)
_sftp_managers: Dict[str, SFTPFileManager] = {}


def _create_sftp_client(config_data: Dict[str, Any]) -> paramiko.SSHClient:
    """
    Create a Paramiko SSH client from config data.

    Helper function for direct SFTP operations (e.g., project creation).

    Args:
        config_data: Database configuration dict with SSH fields

    Returns:
        Connected SSH client

    Raises:
        Exception: If connection fails
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    host = config_data.get("ssh_host") or config_data.get("host")
    port = config_data.get("ssh_port") or 22
    username = config_data.get("ssh_username") or config_data.get("username")
    password = config_data.get("ssh_password") or config_data.get("password")

    ssh_client.connect(hostname=host, port=port, username=username, password=password, timeout=10)

    return ssh_client


async def get_sftp_manager(config_name: str, config_data: Dict[str, Any]) -> SFTPFileManager:
    """
    Get or create SFTP manager for a database config.

    Reuses existing connection if available and connected.

    Args:
        config_name: Name of the database configuration
        config_data: Database configuration dict with SSH fields

    Returns:
        Active SFTP manager

    Raises:
        HTTPException: If connection fails
    """
    # Get requested workspace path
    requested_workspace = config_data.get("remote_workspace_path", "~/fgl-projects")

    # Check if we have an existing connection
    if config_name in _sftp_managers:
        manager = _sftp_managers[config_name]
        # Verify connection is still alive
        if manager._connected and manager.sftp:
            try:
                # Test if connection is still alive
                manager.sftp.stat(".")

                # Check if workspace path changed - if so, update it
                if manager.config.workspace_path != requested_workspace:
                    print(
                        f"[SFTP] Workspace path changed from {manager.config.workspace_path} to {requested_workspace}"
                    )
                    # Expand ~ if needed
                    if requested_workspace.startswith("~"):
                        stdin, stdout, stderr = await asyncio.to_thread(
                            manager.client.exec_command, "echo $HOME"
                        )
                        home = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()
                        manager.config.workspace_path = requested_workspace.replace("~", home)
                    else:
                        manager.config.workspace_path = requested_workspace

                return manager
            except Exception:
                # Connection lost, remove from cache
                print(f"SFTP connection lost for {config_name}, reconnecting...")
                del _sftp_managers[config_name]

    # Create SFTP config from database config
    # Fallback to regular host/username/password if ssh_* fields are not set
    ssh_host = config_data.get("ssh_host") or config_data.get("host")
    ssh_port = config_data.get("ssh_port") or 22
    ssh_username = config_data.get("ssh_username") or config_data.get("username")
    ssh_password = config_data.get("ssh_password") or config_data.get("password")

    if not ssh_host:
        raise HTTPException(
            status_code=400,
            detail="Missing SSH configuration. Set ssh_host (or host) in the configuration.",
        )

    if not ssh_username:
        raise HTTPException(
            status_code=400,
            detail="Missing SSH configuration. Set ssh_username (or username) in the configuration.",
        )

    sftp_config = SFTPConfig(
        host=ssh_host,
        port=ssh_port,
        username=ssh_username,
        password=ssh_password,
        workspace_path=config_data.get("remote_workspace_path", "~/fgl-projects"),
    )

    manager = SFTPFileManager(sftp_config)

    try:
        await manager.connect()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect via SFTP: {str(e)}")

    _sftp_managers[config_name] = manager
    return manager


class SFTPTreeRequest(BaseModel):
    """Request to get file tree from SFTP server."""

    config_name: str
    config_data: Dict[str, Any]


class SFTPContentRequest(BaseModel):
    """Request to read file content from SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    path: str


class SFTPWriteRequest(BaseModel):
    """Request to write file content to SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    path: str
    content: str


class SFTPCreateRequest(BaseModel):
    """Request to create file or folder on SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    parent_path: str
    name: str
    type: str  # "file" or "folder"


class SFTPRenameRequest(BaseModel):
    """Request to rename file or folder on SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    old_path: str
    new_name: str


class SFTPDeleteRequest(BaseModel):
    """Request to delete file or folder on SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    path: str
    is_folder: bool


class SFTPBrowseRequest(BaseModel):
    """Request to browse directories on SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    start_path: str = "~"


class SFTPSearchRequest(BaseModel):
    """Request to search files on SFTP server."""

    config_name: str
    config_data: Dict[str, Any]
    query: str
    case_sensitive: bool = False
    regex: bool = False


@router.post("/tree")
async def get_sftp_tree(request: SFTPTreeRequest):
    """
    Get file tree from remote SFTP server.

    Args:
        request: Tree request with config name and data

    Returns:
        Dict with 'tree' key containing FileTreeNode structure
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        tree = await manager.build_file_tree()
        return {"tree": tree}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load file tree: {str(e)}")


@router.post("/content/read")
async def read_sftp_file(request: SFTPContentRequest):
    """
    Read file content from SFTP server.

    Args:
        request: Content request with config and file path

    Returns:
        Dict with 'path' and 'content' keys
    """
    try:
        print(f"[SFTP] Reading file: {request.path}")
        print(
            f"[SFTP] Config: {request.config_name}, workspace: {request.config_data.get('remote_workspace_path')}"
        )
        manager = await get_sftp_manager(request.config_name, request.config_data)
        # Remove leading / for SFTP operations
        path = request.path.lstrip("/")
        print(f"[SFTP] Full path will be: {manager.config.workspace_path}/{path}")
        content = await manager.read_file(path)
        return {"path": request.path, "content": content}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SFTP] Error reading file: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/content/read-absolute")
async def read_sftp_file_absolute(request: SFTPContentRequest):
    """
    Read file content from absolute path on SFTP server.

    Args:
        request: Content request with config and absolute file path

    Returns:
        Dict with 'path' and 'content' keys
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        content = await manager.read_file_absolute(request.path)
        return {"path": request.path, "content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/content/write")
async def write_sftp_file(request: SFTPWriteRequest):
    """
    Write file content to SFTP server.

    Args:
        request: Write request with config, path, and content

    Returns:
        Success status dict
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        path = request.path.lstrip("/")
        await manager.write_file(path, request.content)
        return {"status": "success", "message": f"File saved: {request.path}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@router.post("/content/write-absolute")
async def write_sftp_file_absolute(request: SFTPWriteRequest):
    """
    Write file content to absolute path on SFTP server.

    Args:
        request: Write request with config, absolute path, and content

    Returns:
        Success status dict
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        await manager.write_file_absolute(request.path, request.content)
        return {"status": "success", "message": f"File saved: {request.path}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@router.post("/create")
async def create_sftp_node(request: SFTPCreateRequest):
    """
    Create file or folder on SFTP server.

    Args:
        request: Create request with config, parent path, name, and type

    Returns:
        Success status and created node info
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        parent = request.parent_path.lstrip("/")
        new_path = str(parent + "/" + request.name if parent else request.name)

        if request.type == "folder":
            await manager.create_directory(new_path)
        else:
            await manager.write_file(new_path, "")  # Empty file

        return {
            "status": "success",
            "node": {
                "id": new_path.replace("/", "-"),
                "name": request.name,
                "type": request.type,
                "path": "/" + new_path,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")


@router.post("/rename")
async def rename_sftp_node(request: SFTPRenameRequest):
    """
    Rename file or folder on SFTP server.

    Args:
        request: Rename request with config, old path, and new name

    Returns:
        Success status and renamed node info
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        old_path = request.old_path.lstrip("/")
        new_path = await manager.rename(old_path, request.new_name)

        return {
            "status": "success",
            "node": {
                "id": new_path.replace("/", "-"),
                "name": request.new_name,
                "path": "/" + new_path,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename node: {str(e)}")


@router.post("/delete")
async def delete_sftp_node(request: SFTPDeleteRequest):
    """
    Delete file or folder on SFTP server.

    Args:
        request: Delete request with config, path, and is_folder flag

    Returns:
        Success status dict
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        path = request.path.lstrip("/")
        await manager.delete(path, request.is_folder)
        return {"status": "success", "message": f"Deleted: {request.path}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")


@router.post("/browse")
async def browse_sftp_directories(request: SFTPBrowseRequest):
    """
    Browse directories on SFTP server for directory picker.

    Args:
        request: Browse request with config and start path

    Returns:
        Dict with 'folders' key containing list of folder dicts
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        folders = await manager.browse_directories(request.start_path)
        return {"folders": folders}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to browse directories: {str(e)}")


class SFTPListRequest(BaseModel):
    """Request to list files and folders in a directory."""

    config_name: str
    config_data: Dict[str, Any]
    path: str = ""


@router.post("/list")
async def list_sftp_directory(request: SFTPListRequest):
    """
    List files and folders in a specific directory on SFTP server.

    Args:
        request: List request with config and directory path

    Returns:
        Dict with 'items' key containing list of files and folders
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        items = await manager.list_directory(request.path)
        return {"items": items, "current_path": request.path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list directory: {str(e)}")


@router.post("/list-absolute")
async def list_sftp_directory_absolute(request: SFTPListRequest):
    """
    List files and folders in any directory on SFTP server (unrestricted navigation).

    Args:
        request: List request with config and absolute directory path

    Returns:
        Dict with 'items' key containing list of files and folders
    """
    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)
        items = await manager.list_directory_absolute(request.path or "~")
        return {"items": items, "current_path": request.path or "~"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list directory: {str(e)}")


@router.post("/disconnect")
async def disconnect_sftp(request: SFTPTreeRequest):
    """
    Disconnect SFTP session.

    Args:
        request: Request with config name

    Returns:
        Success status dict
    """
    if request.config_name in _sftp_managers:
        manager = _sftp_managers[request.config_name]
        await manager.disconnect()
        del _sftp_managers[request.config_name]
    return {"status": "success"}


@router.post("/search")
async def search_sftp_files(request: SFTPSearchRequest):
    """
    Search for text across all files on SFTP server.

    Args:
        request: Search request with query and options

    Returns:
        Dict with 'status' and 'results' keys
    """
    import re

    try:
        manager = await get_sftp_manager(request.config_name, request.config_data)

        # Build file tree to get all files
        tree = await manager.build_file_tree()

        # Collect all file paths recursively
        def collect_files(node, files_list):
            if node.get("type") == "file":
                files_list.append(node.get("path"))
            if node.get("children"):
                for child in node["children"]:
                    collect_files(child, files_list)

        file_paths = []
        collect_files(tree, file_paths)

        # Search in each file
        results = []

        for file_path in file_paths:
            try:
                # Remove leading slash for read_file (expects relative path)
                relative_path = file_path.lstrip("/")

                # Read file content
                content = await manager.read_file(relative_path)
                if not content:
                    continue

                # Search for matches
                matches = []
                lines = content.split("\n")

                for line_num, line_text in enumerate(lines, start=1):
                    # Prepare search pattern
                    if request.regex:
                        try:
                            flags = 0 if request.case_sensitive else re.IGNORECASE
                            pattern = re.compile(request.query, flags)
                        except re.error:
                            # Invalid regex, skip this file
                            continue
                    else:
                        # Escape special regex characters for literal search
                        escaped_query = re.escape(request.query)
                        flags = 0 if request.case_sensitive else re.IGNORECASE
                        pattern = re.compile(escaped_query, flags)

                    # Search for matches in the line
                    for match in pattern.finditer(line_text):
                        matches.append(
                            {
                                "line": line_num,
                                "column": match.start() + 1,
                                "text": line_text.strip(),
                            }
                        )

                if matches:
                    results.append({"file": file_path, "matches": matches})

            except Exception as e:
                # Skip files that can't be read
                print(f"Error reading {file_path}: {e}")
                continue

        return {"status": "success", "results": results}

    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "results": [], "error": str(e)}
