"""
SSH Terminal Session Manager.

Manages interactive SSH sessions for remote terminal access,
including PTY allocation, input/output streaming, and session lifecycle.
"""

import asyncio
import logging
from typing import Callable, Optional

import paramiko

logger = logging.getLogger(__name__)


class SSHTerminalSession:
    """Manages an interactive SSH session with PTY support."""

    def __init__(self, host: str, port: int, username: str, password: str):
        """
        Initialize SSH terminal session.

        Args:
            host: SSH server hostname or IP
            port: SSH server port (default 22)
            username: SSH username
            password: SSH password
        """
        self.host = host
        self.port = port if port else 22
        self.username = username
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Establish SSH connection and create interactive shell channel.

        Raises:
            paramiko.AuthenticationException: If authentication fails
            paramiko.SSHException: If SSH connection fails
            Exception: For other connection errors
        """
        try:
            self.client = paramiko.SSHClient()
            # Auto-add host keys (WARNING: accepts any host key)
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to SSH server (run in thread pool to avoid blocking)
            # Note: Backend runs inside Docker, so use service names directly
            logger.info(f"Connecting to SSH server: {self.username}@{self.host}:{self.port}")
            await asyncio.to_thread(
                self.client.connect,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                look_for_keys=False,  # Don't look for SSH keys, use password only
                allow_agent=False,  # Don't use SSH agent
            )

            # Create interactive shell with PTY
            logger.info("Creating interactive shell with PTY")
            self.channel = self.client.invoke_shell(
                term="xterm-256color",
                width=80,
                height=24,
            )

            # Set non-blocking mode for the channel
            self.channel.setblocking(False)
            self._connected = True
            logger.info("SSH connection established successfully")

        except paramiko.AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            raise Exception("Authentication failed: Invalid username or password")
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error: {e}")
            raise Exception(f"SSH connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Connection error: {str(e)}")

    async def send_input(self, data: str) -> None:
        """
        Send user input to the remote shell.

        Args:
            data: Input string to send to shell
        """
        if self.channel and self._connected:
            try:
                await asyncio.to_thread(self.channel.send, data)
            except Exception as e:
                logger.error(f"Error sending input: {e}")
                raise

    async def read_output(self, callback: Callable[[str], None]) -> None:
        """
        Continuously read output from remote shell and send to callback.

        This is a long-running coroutine that should be run as a background task.
        It will read output from the channel and call the callback function
        with the data.

        Args:
            callback: Function to call with output data
        """
        while self.channel and self._connected and not self.channel.closed:
            try:
                if self.channel.recv_ready():
                    # Read available data
                    data = await asyncio.to_thread(self.channel.recv, 4096)
                    if data:
                        # Decode and send to callback
                        decoded = data.decode("utf-8", errors="ignore")
                        callback(decoded)

                # Small sleep to avoid busy-waiting
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break

        logger.info("Output reading loop ended")

    async def resize(self, width: int, height: int) -> None:
        """
        Resize the remote PTY.

        Args:
            width: New terminal width in columns
            height: New terminal height in rows
        """
        if self.channel and self._connected:
            try:
                await asyncio.to_thread(self.channel.resize_pty, width=width, height=height)
                logger.debug(f"Terminal resized to {width}x{height}")
            except Exception as e:
                logger.error(f"Error resizing terminal: {e}")

    async def disconnect(self) -> None:
        """Close SSH connection and cleanup resources."""
        try:
            self._connected = False

            if self.channel:
                try:
                    self.channel.close()
                except Exception as e:
                    logger.warning(f"Error closing channel: {e}")
                self.channel = None

            if self.client:
                try:
                    self.client.close()
                except Exception as e:
                    logger.warning(f"Error closing client: {e}")
                self.client = None

            logger.info("SSH connection closed")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if session is currently connected."""
        return self._connected and self.channel is not None and not self.channel.closed
