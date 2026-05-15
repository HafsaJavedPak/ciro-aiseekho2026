# backend/services/websocket_manager.py
import json
import asyncio
from datetime import datetime
from fastapi import WebSocket
from typing import Literal


class ConnectionManager:
    """
    Manages all active WebSocket connections.
    
    Supports broadcasting to all clients or targeting by room (incident-specific feeds).
    The Flutter app connects once and receives all updates — no polling needed.
    """
    
    def __init__(self):
        # All connected clients
        self._connections: list[WebSocket] = []
        # Room-based connections: incident_id → list of WebSocket
        self._rooms: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str | None = None):
        await websocket.accept()
        self._connections.append(websocket)
        
        if room:
            if room not in self._rooms:
                self._rooms[room] = []
            self._rooms[room].append(websocket)
        
        # Send immediate state snapshot on connect
        await self._send_json(websocket, {
            "event": "connected",
            "message": "CIRO WebSocket connected",
            "timestamp": datetime.utcnow().isoformat(),
        })
        print(f"[WS] Client connected. Total: {len(self._connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self._connections:
            self._connections.remove(websocket)
        for room_clients in self._rooms.values():
            if websocket in room_clients:
                room_clients.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(self._connections)}")
    
    async def broadcast(
        self,
        event: str,
        data: dict,
        event_type: Literal["signal", "incident", "trace", "alert", "resource", "system"] = "system"
    ):
        """
        Send an event to ALL connected clients.
        Used for: new incidents, global alerts, system status changes.
        """
        message = {
            "event": event,
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        dead_connections = []
        for ws in self._connections:
            try:
                await self._send_json(ws, message)
            except Exception:
                dead_connections.append(ws)
        
        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws)
    
    async def broadcast_to_room(self, room: str, event: str, data: dict):
        """
        Send to clients watching a specific incident.
        Used for: agent traces, incident-specific updates.
        """
        if room not in self._rooms:
            return
        
        message = {
            "event": event,
            "room": room,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        dead = []
        for ws in self._rooms[room]:
            try:
                await self._send_json(ws, message)
            except Exception:
                dead.append(ws)
        
        for ws in dead:
            self.disconnect(ws)
    
    async def _send_json(self, websocket: WebSocket, data: dict):
        """Serialize and send. Handles datetime serialization."""
        await websocket.send_text(json.dumps(data, default=str))
    
    async def heartbeat(self):
        """
        Sends periodic pings to keep connections alive.
        Run as a background task on app startup.
        """
        while True:
            await asyncio.sleep(30)
            if self._connections:
                await self.broadcast("heartbeat", {"active_connections": len(self._connections)})


# Singleton — imported by API routes and services
ws_manager = ConnectionManager()
