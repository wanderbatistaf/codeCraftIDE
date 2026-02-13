"""
Terminal WebSocket API endpoints.

Provides WebSocket endpoints for interactive SSH terminal sessions,
bridging frontend terminal emulators to remote SSH servers.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..terminal.ssh_manager import SSHTerminalSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/terminal", tags=["terminal"])


class TerminalConnectionRequest(BaseModel):
    """Request model for terminal connection configuration."""

    host: str
    port: int = 22
    username: str
    password: str
    database: str  # Database name, for informational purposes only


@router.websocket("/connect")
async def terminal_connect(websocket: WebSocket):
    """
    WebSocket endpoint for interactive SSH terminal session.

    Protocol:
        1. Client connects and sends configuration as JSON
        2. Server connects to SSH and sends {"type": "connected", "message": "..."}
        3. Bidirectional streaming:
           - Client -> Server: {"type": "input", "data": "..."}
           - Client -> Server: {"type": "resize", "cols": 80, "rows": 24}
           - Client -> Server: {"type": "disconnect"}
           - Server -> Client: {"type": "output", "data": "..."}
           - Server -> Client: {"type": "error", "message": "..."}
    """
    await websocket.accept()
    session: Optional[SSHTerminalSession] = None
    read_task: Optional[asyncio.Task] = None

    try:
        # Receive initial configuration
        logger.info("Waiting for terminal configuration")
        config_data = await websocket.receive_text()
        config = json.loads(config_data)

        logger.info(
            f"Terminal connection request: {config['username']}@{config['host']}:{config.get('port', 22)}"
        )

        # Create SSH session
        session = SSHTerminalSession(
            host=config["host"],
            port=config.get("port", 22),
            username=config["username"],
            password=config["password"],
        )

        # Connect to SSH server
        await session.connect()

        # Send connection success message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "message": f"Connected to {config['username']}@{config['host']}",
                }
            )
        )

        # Start background task to read SSH output and send to WebSocket
        async def read_and_forward():
            """Read from SSH and forward to WebSocket."""

            def send_output(data: str):
                """Callback to send output to WebSocket."""
                asyncio.create_task(
                    websocket.send_text(json.dumps({"type": "output", "data": data}))
                )

            await session.read_output(send_output)

        read_task = asyncio.create_task(read_and_forward())

        # Main loop: receive input from WebSocket and send to SSH
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data["type"] == "input":
                    # Send user input to SSH
                    await session.send_input(data["data"])

                elif data["type"] == "resize":
                    # Resize terminal
                    await session.resize(data["cols"], data["rows"])

                elif data["type"] == "disconnect":
                    # Client requested disconnect
                    logger.info("Client requested disconnect")
                    break

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during handshake")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received: {e}")
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "message": f"Invalid JSON: {str(e)}"})
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Terminal connection error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass

    finally:
        # Cleanup
        logger.info("Cleaning up terminal session")

        # Cancel read task
        if read_task and not read_task.done():
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass

        # Disconnect SSH session
        if session:
            await session.disconnect()

        logger.info("Terminal session cleanup complete")
