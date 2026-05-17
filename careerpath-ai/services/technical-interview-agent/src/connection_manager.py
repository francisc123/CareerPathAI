from __future__ import annotations

from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str) -> None:
        self.active_connections.pop(session_id, None)

    async def send_text(self, session_id: str, message: str) -> None:
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_text(message)

    async def send_json(self, session_id: str, payload: dict[str, Any]) -> None:
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_json(payload)


manager = ConnectionManager()
