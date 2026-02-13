"""SFTP File Manager for remote file system operations."""

import asyncio
import stat
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

import paramiko


@dataclass
class SFTPConfig:
    """SFTP connection configuration."""

    host: str
    username: str
    password: str
    port: int = 22
    workspace_path: str = "~/fgl-projects"  # Remote workspace directory


class SFTPFileManager:
    """Manages SFTP operations for remote file system access."""

    def __init__(self, config: SFTPConfig):
        """
        Initialize SFTP File Manager.

        Args:
            config: SFTP configuration with host, credentials, and workspace path
        """
        self.config = config
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish SFTP connection.

        Raises:
            Exception: If connection fails
        """
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Backend runs inside Docker, so use service names directly
        await asyncio.to_thread(
            self.client.connect,
            hostname=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        self.sftp = self.client.open_sftp()
        self._connected = True

        # Expand ~ to actual home path
        if self.config.workspace_path.startswith("~"):
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, "echo $HOME")
            home = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()
            self.config.workspace_path = self.config.workspace_path.replace("~", home)

        # Ensure workspace directory exists
        await self._ensure_directory(self.config.workspace_path)

    async def disconnect(self) -> None:
        """Close SFTP connection."""
        if self.sftp:
            await asyncio.to_thread(self.sftp.close)
        if self.client:
            await asyncio.to_thread(self.client.close)
        self._connected = False

    async def list_directory(self, path: str = "") -> List[Dict[str, Any]]:
        """
        List files and folders in a directory.

        Args:
            path: Relative path from workspace (empty = workspace root)

        Returns:
            List of dicts with {name, type, path, size, modified}
        """
        full_path = str(PurePosixPath(self.config.workspace_path) / path)

        items = await asyncio.to_thread(self.sftp.listdir_attr, full_path)

        result = []
        for item in items:
            is_dir = stat.S_ISDIR(item.st_mode)
            item_path = str(PurePosixPath(path) / item.filename) if path else item.filename

            result.append(
                {
                    "name": item.filename,
                    "type": "folder" if is_dir else "file",
                    "path": item_path,
                    "size": item.st_size if not is_dir else 0,
                    "modified": item.st_mtime,
                }
            )

        # Sort: folders first, then files, alphabetically
        return sorted(result, key=lambda x: (x["type"] != "folder", x["name"].lower()))

    async def read_file_absolute(self, path: str) -> str:
        """
        Read file content from absolute path on server.

        Args:
            path: Absolute path to file (supports ~)

        Returns:
            File content as string
        """
        # Expand ~
        if path.startswith("~"):
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, "echo $HOME")
            home = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()
            path = path.replace("~", home, 1)

        try:
            with await asyncio.to_thread(self.sftp.open, path, "r") as remote_file:
                content = await asyncio.to_thread(remote_file.read)
                # Try UTF-8 first, then fallback to Latin-1 (ISO-8859-1)
                try:
                    return content.decode("utf-8")
                except UnicodeDecodeError:
                    return content.decode("latin-1")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")

    async def read_file(self, path: str) -> str:
        """
        Read file content from remote server.

        Args:
            path: Relative path from workspace

        Returns:
            File content as string
        """
        full_path = str(PurePosixPath(self.config.workspace_path) / path)

        with await asyncio.to_thread(self.sftp.file, full_path, "r") as f:
            content = await asyncio.to_thread(f.read)

        # Try UTF-8 first, then fallback to Latin-1 (ISO-8859-1)
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")

    async def write_file(self, path: str, content: str) -> None:
        """
        Write file content to remote server.

        Args:
            path: Relative path from workspace
            content: File content to write
        """
        full_path = str(PurePosixPath(self.config.workspace_path) / path)

        # Ensure parent directory exists
        parent = str(PurePosixPath(full_path).parent)
        await self._ensure_directory(parent)

        with await asyncio.to_thread(self.sftp.file, full_path, "w") as f:
            await asyncio.to_thread(f.write, content.encode("utf-8"))

    async def write_file_absolute(self, path: str, content: str) -> None:
        """
        Write file content to absolute path on server.

        Args:
            path: Absolute path to file (supports ~)
            content: File content to write
        """
        # Expand ~
        if path.startswith("~"):
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, "echo $HOME")
            home = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()
            path = path.replace("~", home, 1)

        # Ensure parent directory exists
        parent = str(PurePosixPath(path).parent)
        await self._ensure_directory(parent)

        with await asyncio.to_thread(self.sftp.file, path, "w") as f:
            await asyncio.to_thread(f.write, content.encode("utf-8"))

    async def create_directory(self, path: str) -> None:
        """
        Create a directory on remote server.

        Args:
            path: Relative path from workspace
        """
        full_path = str(PurePosixPath(self.config.workspace_path) / path)
        await asyncio.to_thread(self.sftp.mkdir, full_path)

    async def delete(self, path: str, is_folder: bool = False) -> None:
        """
        Delete file or folder on remote server.

        Args:
            path: Relative path from workspace
            is_folder: True if deleting a folder (recursive)
        """
        full_path = str(PurePosixPath(self.config.workspace_path) / path)

        if is_folder:
            # Recursively delete folder contents first
            items = await asyncio.to_thread(self.sftp.listdir, full_path)
            for item in items:
                item_path = str(PurePosixPath(full_path) / item)
                item_stat = await asyncio.to_thread(self.sftp.stat, item_path)
                is_dir = stat.S_ISDIR(item_stat.st_mode)

                # Construct relative path for recursive call
                relative_item_path = str(PurePosixPath(path) / item)
                await self.delete(relative_item_path, is_dir)

            await asyncio.to_thread(self.sftp.rmdir, full_path)
        else:
            await asyncio.to_thread(self.sftp.remove, full_path)

    async def rename(self, old_path: str, new_name: str) -> str:
        """
        Rename file or folder on remote server.

        Args:
            old_path: Current relative path from workspace
            new_name: New name (not full path, just the name)

        Returns:
            New relative path after rename
        """
        old_full_path = str(PurePosixPath(self.config.workspace_path) / old_path)
        parent = PurePosixPath(old_full_path).parent
        new_full_path = str(parent / new_name)

        await asyncio.to_thread(self.sftp.rename, old_full_path, new_full_path)

        # Return new relative path
        new_relative_path = str(PurePosixPath(old_path).parent / new_name)
        # Handle root level (no parent)
        if new_relative_path == new_name:
            return new_name
        return new_relative_path

    async def build_file_tree(self, path: str = "") -> Dict[str, Any]:
        """
        Recursively build file tree structure.

        Args:
            path: Relative path from workspace (empty = root)

        Returns:
            FileTreeNode-compatible dict
        """
        # Get directory listing
        items = await self.list_directory(path)

        children = []
        for item in items:
            if item["type"] == "folder":
                # Recursively get folder contents
                subtree = await self.build_file_tree(item["path"])
                children.append(subtree)
            else:
                # File node (no content loaded yet)
                children.append(
                    {
                        "id": item["path"].replace("/", "-") or item["name"].replace("/", "-"),
                        "name": item["name"],
                        "type": "file",
                        "path": "/" + item["path"] if item["path"] else "/" + item["name"],
                        "content": None,
                    }
                )

        # Root or folder node
        if path == "":
            workspace_name = PurePosixPath(self.config.workspace_path).name
            return {
                "id": "root",
                "name": workspace_name,
                "type": "folder",
                "path": "/",
                "children": children,
            }
        else:
            return {
                "id": path.replace("/", "-"),
                "name": PurePosixPath(path).name,
                "type": "folder",
                "path": "/" + path,
                "children": children,
            }

    async def list_directory_absolute(self, path: str = "~") -> List[Dict[str, Any]]:
        """
        List files and folders in absolute path on server (unrestricted).

        Args:
            path: Absolute path to list (supports ~, default is home)

        Returns:
            List of {name, path, type, size, modified} dicts
        """
        # Expand ~
        if path.startswith("~"):
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, "echo $HOME")
            home = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()
            path = path.replace("~", home, 1)

        # Handle empty path (use home)
        if not path or path == "":
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, "echo $HOME")
            path = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()

        items = await asyncio.to_thread(self.sftp.listdir_attr, path)

        result = []
        for item in items:
            item_type = "folder" if stat.S_ISDIR(item.st_mode) else "file"
            result.append(
                {
                    "name": item.filename,
                    "path": str(PurePosixPath(path) / item.filename),
                    "type": item_type,
                    "size": item.st_size if hasattr(item, "st_size") else 0,
                    "modified": int(item.st_mtime) if hasattr(item, "st_mtime") else 0,
                }
            )

        return sorted(result, key=lambda x: (x["type"] == "file", x["name"].lower()))

    async def browse_directories(self, start_path: str = "~") -> List[Dict[str, str]]:
        """
        Browse directories on server for directory picker UI.

        Args:
            start_path: Absolute path to start browsing from (supports ~)

        Returns:
            List of {name, path} dicts for folders only
        """
        # Expand ~
        if start_path.startswith("~"):
            stdin, stdout, stderr = await asyncio.to_thread(self.client.exec_command, "echo $HOME")
            home = (await asyncio.to_thread(stdout.read)).decode("utf-8").strip()
            start_path = start_path.replace("~", home)

        items = await asyncio.to_thread(self.sftp.listdir_attr, start_path)

        folders = []
        for item in items:
            if stat.S_ISDIR(item.st_mode):
                folders.append(
                    {
                        "name": item.filename,
                        "path": str(PurePosixPath(start_path) / item.filename),
                    }
                )

        return sorted(folders, key=lambda x: x["name"].lower())

    async def _ensure_directory(self, path: str) -> None:
        """
        Ensure directory exists, creating it if necessary.

        Args:
            path: Absolute path to directory
        """
        try:
            await asyncio.to_thread(self.sftp.stat, path)
        except FileNotFoundError:
            parent = str(PurePosixPath(path).parent)
            if parent != path:  # Not root
                await self._ensure_directory(parent)
            await asyncio.to_thread(self.sftp.mkdir, path)

    async def _ensure_connected(self) -> None:
        """Ensure SFTP connection is active, reconnect if needed."""
        if not self._connected or not self.sftp:
            await self.connect()
