"""
WebSocket Connection Manager for Real-Time Deal Rooms.
Maintains active socket connections per deal and orchestrates encrypted broadcasting,
buyer-private AI risk alerts, typing indicators, and shared PayPal payment cards.
"""
from typing import Dict, Any, Optional
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger("dealcheck.websocket")

class DealRoomSocketManager:
    def __init__(self):
        # Maps deal_id -> {user_id: WebSocket}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, deal_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if deal_id not in self.rooms:
            self.rooms[deal_id] = {}
        self.rooms[deal_id][user_id] = websocket
        logger.info(f"[WS] User {user_id} connected to Deal {deal_id}. Total active in room: {len(self.rooms[deal_id])}")

    def disconnect(self, deal_id: str, user_id: str):
        if deal_id in self.rooms:
            if user_id in self.rooms[deal_id]:
                del self.rooms[deal_id][user_id]
                logger.info(f"[WS] User {user_id} disconnected from Deal {deal_id}.")
            if not self.rooms[deal_id]:
                del self.rooms[deal_id]

    async def broadcast_to_deal(self, deal_id: str, event_type: str, data: Dict[str, Any]):
        """Broadcasts a shared event to both participants in the deal room."""
        if deal_id not in self.rooms:
            return

        payload = {
            "type": event_type,
            "deal_id": deal_id,
            "data": data
        }
        dead_connections = []

        for uid, socket in self.rooms[deal_id].items():
            try:
                await socket.send_json(payload)
            except Exception as e:
                logger.warning(f"[WS] Failed sending to user {uid}: {e}")
                dead_connections.append(uid)

        for uid in dead_connections:
            self.disconnect(deal_id, uid)

    async def send_to_user(self, deal_id: str, user_id: str, event_type: str, data: Dict[str, Any]):
        """Sends an event privately to a single user in the deal room (e.g., Buyer-only AI alerts)."""
        if deal_id not in self.rooms or user_id not in self.rooms[deal_id]:
            return

        payload = {
            "type": event_type,
            "deal_id": deal_id,
            "data": data
        }
        try:
            socket = self.rooms[deal_id][user_id]
            await socket.send_json(payload)
        except Exception as e:
            logger.warning(f"[WS] Failed sending private event to user {user_id}: {e}")
            self.disconnect(deal_id, user_id)

    def is_user_online(self, deal_id: str, user_id: str) -> bool:
        return bool(deal_id in self.rooms and user_id in self.rooms[deal_id])

socket_manager = DealRoomSocketManager()
