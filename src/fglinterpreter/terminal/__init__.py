"""
Terminal module for SSH-based terminal integration.

Provides SSH client functionality for connecting to remote database servers
and exposing interactive shell sessions via WebSocket.
"""

from .ssh_manager import SSHTerminalSession

__all__ = ["SSHTerminalSession"]
