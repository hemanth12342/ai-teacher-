import json
import uuid
import logging
from fastapi import WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

from .manager import manager
from .signaling import handle_webrtc_signal
from .ai.services.attendance_service import attendance_service
from ..config import SECRET_KEY, JWT_ALGORITHM, STUN_SERVERS

logger = logging.getLogger(__name__)

WEBRTC_TYPES = {"webrtc_offer", "webrtc_answer", "webrtc_ice"}


async def classroom_ws_handler(websocket: WebSocket, room_id: str, token: str = Query(...)):
    """
    Main WebSocket handler for a classroom room.
    Authenticates via JWT, registers the peer, routes all message types.
    """
    # ── Auth ──────────────────────────────────────────────
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    username  = claims.get("sub", "Unknown")
    role      = claims.get("role", "student")
    peer_id   = str(uuid.uuid4())[:8]

    meta = {"username": username, "role": role}

    needs_approval = False
    if role == "teacher":
        participants = manager.get_participants(room_id)
        if any(p.get("role") == "teacher" for p in participants):
            needs_approval = True

    await websocket.accept()

    if needs_approval:
        manager.add_waiting(room_id, peer_id, websocket, meta)
        await websocket.send_text(json.dumps({"type": "waiting_for_approval"}))
        await manager.broadcast_to_teachers(room_id, {
            "type": "teacher_join_request",
            "payload": {"peer_id": peer_id, "username": username}
        })
    else:
        await manager.connect(room_id, peer_id, websocket, meta)

        # ── Welcome ───────────────────────────────────────────
        await websocket.send_text(json.dumps({
            "type":    "system",
            "payload": {
                "msg":         f"Welcome, {username}! You joined room {room_id}.",
                "peer_id":     peer_id,
                "stun_servers": STUN_SERVERS,
                "participants": manager.get_participants(room_id),
            }
        }))

        # Notify others
        await manager.broadcast(room_id, {
            "type":    "participant",
            "payload": {
                "event":      "joined",
                "peer_id":    peer_id,
                "username":   username,
                "role":       role,
                "count":      manager.participant_count(room_id),
                "participants": manager.get_participants(room_id),
            }
        }, exclude_peer=peer_id)

        # ── Attendance: join ──────────────────────────────────
        await attendance_service.record_join(room_id, username, role)

    # ── Message loop ──────────────────────────────────────
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")
            msg["sender"] = username
            msg["sender_role"] = role

            if manager.is_waiting(room_id, peer_id):
                continue

            # WebRTC signaling
            if msg_type in WEBRTC_TYPES:
                await handle_webrtc_signal(room_id, peer_id, msg)

            # Chat → broadcast
            elif msg_type == "chat":
                await manager.broadcast(room_id, msg)

            # Q&A → run AI agent, stream answer back
            elif msg_type == "qa_question":
                question = msg.get("payload", {}).get("question", "")
                if question.strip():
                    await manager.broadcast(room_id, {
                        "type":    "qa_answer",
                        "sender":  "System",
                        "payload": {
                            "question": question,
                            "ai_answer": "⚠️ AI features have been disabled for this project.",
                            "sources":   [],
                        },
                    })

            # Subtitle chunk → broadcast to room
            elif msg_type == "subtitle":
                await manager.broadcast(room_id, msg, exclude_peer=peer_id)

            # Teacher Approval
            elif msg_type == "approve_teacher" and role == "teacher":
                target_peer = msg.get("payload", {}).get("peer_id")
                waiting = manager.remove_waiting(room_id, target_peer)
                if waiting:
                    t_ws, t_meta = waiting
                    await manager.connect(room_id, target_peer, t_ws, t_meta)
                    await t_ws.send_text(json.dumps({
                        "type": "system",
                        "payload": {
                            "msg": f"Welcome, {t_meta['username']}! You joined room {room_id}.",
                            "peer_id": target_peer,
                            "stun_servers": STUN_SERVERS,
                            "participants": manager.get_participants(room_id),
                        }
                    }))
                    await manager.broadcast(room_id, {
                        "type": "participant",
                        "payload": {
                            "event": "joined",
                            "peer_id": target_peer,
                            "username": t_meta['username'],
                            "role": t_meta['role'],
                            "count": manager.participant_count(room_id),
                            "participants": manager.get_participants(room_id),
                        }
                    }, exclude_peer=target_peer)
                    await attendance_service.record_join(room_id, t_meta['username'], t_meta['role'])

            elif msg_type == "reject_teacher" and role == "teacher":
                target_peer = msg.get("payload", {}).get("peer_id")
                waiting = manager.remove_waiting(room_id, target_peer)
                if waiting:
                    t_ws, _ = waiting
                    await t_ws.send_text(json.dumps({"type": "join_rejected"}))
                    await t_ws.close(code=4003, reason="Join rejected by host")

            else:
                logger.debug(f"Unhandled WS type: {msg_type}")

    except WebSocketDisconnect:
        manager.disconnect(room_id, peer_id)
        await attendance_service.record_leave(room_id, username)
        await manager.broadcast(room_id, {
            "type":    "participant",
            "payload": {
                "event":      "left",
                "peer_id":    peer_id,
                "username":   username,
                "count":      manager.participant_count(room_id),
                "participants": manager.get_participants(room_id),
            }
        })