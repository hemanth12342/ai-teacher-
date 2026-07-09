import json
from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections per classroom room.
    Tracks participants and provides broadcast/unicast helpers.
    """

    def __init__(self):
        # room_id → {peer_id: WebSocket}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
        # room_id → {peer_id: (WebSocket, meta)}
        self.waiting_rooms: Dict[str, Dict[str, tuple[WebSocket, dict]]] = {}
        # peer_id → metadata
        self.peer_meta: Dict[str, dict] = {}

    # ── Connection lifecycle ──────────────────────────────

    async def connect(self, room_id: str, peer_id: str, ws: WebSocket, meta: dict):
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][peer_id] = ws
        self.peer_meta[peer_id] = meta
        logger.info(f"[WS] {peer_id} joined room {room_id}")

    def disconnect(self, room_id: str, peer_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].pop(peer_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        if room_id in self.waiting_rooms:
            self.waiting_rooms[room_id].pop(peer_id, None)
            if not self.waiting_rooms[room_id]:
                del self.waiting_rooms[room_id]
        self.peer_meta.pop(peer_id, None)
        logger.info(f"[WS] {peer_id} left room {room_id}")

    # ── Waiting Room ──────────────────────────────────────

    def add_waiting(self, room_id: str, peer_id: str, ws: WebSocket, meta: dict):
        if room_id not in self.waiting_rooms:
            self.waiting_rooms[room_id] = {}
        self.waiting_rooms[room_id][peer_id] = (ws, meta)
        self.peer_meta[peer_id] = meta
        logger.info(f"[WS] {peer_id} added to waiting room {room_id}")

    def remove_waiting(self, room_id: str, peer_id: str) -> tuple[WebSocket, dict] | None:
        if room_id in self.waiting_rooms and peer_id in self.waiting_rooms[room_id]:
            return self.waiting_rooms[room_id].pop(peer_id)
        return None

    def is_waiting(self, room_id: str, peer_id: str) -> bool:
        return room_id in self.waiting_rooms and peer_id in self.waiting_rooms[room_id]

    async def broadcast_to_teachers(self, room_id: str, message: dict):
        if room_id not in self.rooms:
            return
        data = json.dumps(message)
        dead: list[str] = []
        for pid, ws in list(self.rooms[room_id].items()):
            meta = self.peer_meta.get(pid, {})
            if meta.get("role") == "teacher":
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(pid)
        for pid in dead:
            self.disconnect(room_id, pid)

    # ── Messaging ─────────────────────────────────────────

    async def broadcast(self, room_id: str, message: dict, exclude_peer: str = ""):
        """Send to all peers in a room (optionally excluding sender)."""
        if room_id not in self.rooms:
            return
        data = json.dumps(message)
        dead: list[str] = []
        for pid, ws in list(self.rooms[room_id].items()):
            if pid == exclude_peer:
                continue
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.disconnect(room_id, pid)

    async def unicast(self, room_id: str, target_peer: str, message: dict):
        """Send to a specific peer in a room."""
        if room_id not in self.rooms:
            return
        ws = self.rooms[room_id].get(target_peer)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.disconnect(room_id, target_peer)

    async def send_to_peer(self, peer_id: str, message: dict):
        """Send to a peer regardless of which room they're in."""
        for room_id, peers in self.rooms.items():
            ws = peers.get(peer_id)
            if ws:
                try:
                    await ws.send_text(json.dumps(message))
                except Exception:
                    pass
                return

    # ── Room info ─────────────────────────────────────────

    def get_participants(self, room_id: str) -> list[dict]:
        if room_id not in self.rooms:
            return []
        result = []
        for pid in self.rooms[room_id]:
            meta = self.peer_meta.get(pid, {})
            result.append({"peer_id": pid, **meta})
        return result

    def participant_count(self, room_id: str) -> int:
        return len(self.rooms.get(room_id, {}))

    def all_room_counts(self) -> Dict[str, int]:
        return {rid: len(peers) for rid, peers in self.rooms.items()}


# Singleton
manager = ConnectionManager()