from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio

class WebSocketManager:
    """WebSocket 连接管理 - 实时推送智能体动态"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._broadcast_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # 发送历史事件
        from .event_bus import event_bus
        for event in event_bus.get_history(10):
            await self._send_event(websocket, event)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    async def _send_event(self, websocket: WebSocket, event):
        """发送单个事件"""
        try:
            await websocket.send_json({
                "type": "agent_event",
                "event": {
                    "type": event.type,
                    "data": event.data,
                    "source": event.source,
                    "timestamp": event.timestamp
                }
            })
        except:
            pass

websocket_manager = WebSocketManager()