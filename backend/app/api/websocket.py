"""WebSocket connection manager for real-time evaluation updates."""

import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for evaluation status updates."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # task_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """Connect a WebSocket client to a specific task.

        Args:
            websocket: The WebSocket connection
            task_id: The task ID to connect to
        """
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)

    def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """Disconnect a WebSocket client from a task.

        Args:
            websocket: The WebSocket connection
            task_id: The task ID to disconnect from
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            # Clean up empty sets
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def send_update(self, task_id: str, message: dict) -> None:
        """Send an update to all connected clients for a specific task.

        Args:
            task_id: The task ID
            message: The message to send (will be JSON serialized)
        """
        if task_id in self.active_connections:
            # Send to all connected clients for this task
            disconnected = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Mark for removal if sending fails
                    disconnected.add(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, task_id)

    async def broadcast_event(
        self,
        task_id: str,
        event_type: str,
        data: dict,
    ) -> None:
        """Broadcast an evaluation event to all connected clients.

        Args:
            task_id: The task ID
            event_type: The event type (e.g., 'run_created', 'result', 'complete', 'error')
            data: The event data
        """
        message = {
            "type": event_type,
            "data": data,
        }
        await self.send_update(task_id, message)

    def get_connection_count(self, task_id: str) -> int:
        """Get the number of active connections for a task.

        Args:
            task_id: The task ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(task_id, set()))


# Global connection manager instance
manager = ConnectionManager()
