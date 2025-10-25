"""
Real-time Data Router

Provides WebSocket endpoints for real-time simulation data streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List, Any
import asyncio
import json
import logging
from datetime import datetime

from ..models.base_models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        if simulation_id not in self.active_connections:
            self.active_connections[simulation_id] = []
        self.active_connections[simulation_id].append(websocket)
        logger.info(f"WebSocket connected for simulation {simulation_id}")
    
    def disconnect(self, websocket: WebSocket, simulation_id: str):
        if simulation_id in self.active_connections:
            self.active_connections[simulation_id].remove(websocket)
            if not self.active_connections[simulation_id]:
                del self.active_connections[simulation_id]
        logger.info(f"WebSocket disconnected for simulation {simulation_id}")
    
    async def send_to_simulation(self, simulation_id: str, data: dict):
        if simulation_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[simulation_id]:
                try:
                    await connection.send_text(json.dumps(data))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[simulation_id].remove(conn)
    
    async def broadcast_to_all(self, data: dict):
        for sim_connections in self.active_connections.values():
            for connection in sim_connections:
                try:
                    await connection.send_text(json.dumps(data))
                except:
                    pass  # Connection closed

manager = ConnectionManager()


@router.websocket("/simulation/{simulation_id}")
async def simulation_websocket(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for real-time simulation updates."""
    await manager.connect(websocket, simulation_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "simulation_id": simulation_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, control commands)
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Handle different message types
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif data.get("type") == "subscribe":
                    # Client wants to subscribe to specific data types
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "subscriptions": data.get("channels", []),
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, simulation_id)
    except Exception as e:
        logger.error(f"WebSocket error for simulation {simulation_id}: {e}")
        manager.disconnect(websocket, simulation_id)


@router.websocket("/metrics/{simulation_id}")
async def metrics_websocket(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for real-time metrics streaming."""
    await manager.connect(websocket, f"metrics_{simulation_id}")
    
    try:
        # Send initial metrics
        await websocket.send_text(json.dumps({
            "type": "metrics_update",
            "simulation_id": simulation_id,
            "metrics": {
                "delivery_ratio": 0.0,
                "average_delay": 0.0,
                "active_contacts": 0,
                "buffer_utilization": 0.0,
                "bundles_in_transit": 0
            },
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)  # Send updates every second
            
            # Mock real-time metrics (would come from actual simulation)
            await websocket.send_text(json.dumps({
                "type": "metrics_update",
                "simulation_id": simulation_id,
                "metrics": {
                    "delivery_ratio": 0.85,
                    "average_delay": 120.5,
                    "active_contacts": 5,
                    "buffer_utilization": 45.2,
                    "bundles_in_transit": 23
                },
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"metrics_{simulation_id}")


@router.websocket("/visualization/{simulation_id}")
async def visualization_websocket(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for 3D visualization data streaming."""
    await manager.connect(websocket, f"viz_{simulation_id}")
    
    try:
        # Send initial satellite positions
        await websocket.send_text(json.dumps({
            "type": "satellite_positions",
            "simulation_id": simulation_id,
            "satellites": [
                {
                    "id": f"sat_{i:03d}",
                    "position": {"x": 1000 + i*100, "y": 2000, "z": 3000},
                    "velocity": {"x": 7.5, "y": 0, "z": 0}
                }
                for i in range(10)  # Mock 10 satellites
            ],
            "ground_stations": [
                {
                    "id": "gs_la",
                    "name": "Los Angeles",
                    "position": {"lat": 34.0522, "lon": -118.2437, "alt": 0.1}
                },
                {
                    "id": "gs_tokyo", 
                    "name": "Tokyo",
                    "position": {"lat": 35.6762, "lon": 139.6503, "alt": 0.04}
                }
            ],
            "contacts": [],
            "timestamp": datetime.now().isoformat()
        }))
        
        # Stream position updates
        while True:
            await asyncio.sleep(0.1)  # 10 FPS updates
            
            # Mock satellite movement (would come from orbital mechanics)
            await websocket.send_text(json.dumps({
                "type": "position_update",
                "simulation_id": simulation_id,
                "satellites": [
                    {
                        "id": f"sat_{i:03d}",
                        "position": {
                            "x": 1000 + i*100 + (datetime.now().second * 10),
                            "y": 2000,
                            "z": 3000
                        }
                    }
                    for i in range(10)
                ],
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"viz_{simulation_id}")


@router.get("/connections", response_model=APIResponse)
async def get_active_connections():
    """Get information about active WebSocket connections."""
    connection_info = {}
    total_connections = 0
    
    for sim_id, connections in manager.active_connections.items():
        connection_info[sim_id] = len(connections)
        total_connections += len(connections)
    
    return APIResponse(
        success=True,
        message="Connection information retrieved",
        data={
            "total_connections": total_connections,
            "connections_by_simulation": connection_info,
            "active_simulations": list(manager.active_connections.keys())
        }
    )


@router.post("/broadcast", response_model=APIResponse)
async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients."""
    try:
        broadcast_data = {
            "type": "broadcast",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_all(broadcast_data)
        
        return APIResponse(
            success=True,
            message="Message broadcasted successfully",
            data={"recipients": sum(len(conns) for conns in manager.active_connections.values())}
        )
        
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/{simulation_id}/send", response_model=APIResponse)
async def send_to_simulation(simulation_id: str, message: dict):
    """Send a message to all clients connected to a specific simulation."""
    try:
        if simulation_id not in manager.active_connections:
            raise HTTPException(status_code=404, detail="No active connections for simulation")
        
        message_data = {
            "type": "targeted_message",
            "simulation_id": simulation_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.send_to_simulation(simulation_id, message_data)
        
        return APIResponse(
            success=True,
            message="Message sent to simulation clients",
            data={
                "simulation_id": simulation_id,
                "recipients": len(manager.active_connections[simulation_id])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message to simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))