"""WebSocket endpoints for real-time data."""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict
from datetime import datetime

from app.core.logging import get_logger
from app.api.deps import get_engine

router = APIRouter(tags=["WebSocket"])
logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "realtime": [],
            "alarm": []
        }
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)
        logger.info(f"WebSocket connected to channel: {channel}, total connections: {len(self.active_connections[channel])}")
    
    async def disconnect(self, websocket: WebSocket, channel: str):
        async with self._lock:
            if channel in self.active_connections:
                if websocket in self.active_connections[channel]:
                    self.active_connections[channel].remove(websocket)
        logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def broadcast(self, message: dict, channel: str):
        """Broadcast message to all connected clients on a channel."""
        if channel not in self.active_connections:
            return
        
        # Get a copy of connections to avoid modification during iteration
        async with self._lock:
            connections = list(self.active_connections.get(channel, []))
        
        if not connections:
            return
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending message to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn, channel)
    
    def get_connection_count(self, channel: str) -> int:
        """Get number of active connections on a channel."""
        return len(self.active_connections.get(channel, []))


manager = ConnectionManager()


@router.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system data.
    
    This endpoint only handles connection management and receives client messages.
    The actual state broadcasting is done by the background simulation task in main.py.
    This decoupling ensures:
    1. Simulation runs independently of client connections
    2. Multiple clients don't cause duplicate simulation steps
    3. System continues operating even when no clients are connected
    """
    await manager.connect(websocket, "realtime")
    engine = get_engine()
    
    try:
        # Send initial state immediately upon connection
        current_state = engine.get_current_state()
        if current_state:
            await websocket.send_json({
                "type": "state_update",
                "data": current_state
            })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong, commands, etc.)
                # Using a timeout to periodically check connection health
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client commands if needed
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "get_state":
                        # Client requests current state
                        current_state = engine.get_current_state()
                        if current_state:
                            await websocket.send_json({
                                "type": "state_update",
                                "data": current_state
                            })
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "realtime")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket, "realtime")


@router.websocket("/ws/alarm")
async def websocket_alarm(websocket: WebSocket):
    """WebSocket endpoint for alarm notifications."""
    await manager.connect(websocket, "alarm")
    
    try:
        while True:
            # Keep connection alive and handle client messages
            try:
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat"})
                except Exception:
                    break
    except WebSocketDisconnect:
        await manager.disconnect(websocket, "alarm")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket, "alarm")


async def broadcast_alarm(alarm_data: dict):
    """Broadcast alarm to all connected clients."""
    await manager.broadcast({
        "type": "alarm",
        "data": alarm_data
    }, "alarm")


async def broadcast_state(state_data: dict):
    """Broadcast state update to all connected clients."""
    await manager.broadcast({
        "type": "state_update",
        "data": state_data
    }, "realtime")


def get_realtime_connection_count() -> int:
    """Get number of active realtime WebSocket connections."""
    return manager.get_connection_count("realtime")
