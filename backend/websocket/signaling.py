import logging
from .manager import manager

logger = logging.getLogger(__name__)


async def handle_webrtc_signal(room_id: str, sender_id: str, msg: dict):
    """
    Relay WebRTC signaling messages (offer / answer / ICE candidate)
    between peers in the same room.

    The frontend sets msg["payload"]["target"] to the remote peer_id.
    If no target is set, the signal is broadcast to all peers in the room.
    """
    payload = msg.get("payload", {})
    target  = msg.get("target") or payload.get("target")

    relay = {
        "type":    msg["type"],
        "sender":  sender_id,
        "payload": payload,
    }

    if target:
        logger.debug(f"[SIG] {sender_id} → {target}  type={msg['type']}")
        await manager.unicast(room_id, target, relay)
    else:
        logger.debug(f"[SIG] {sender_id} → room:{room_id}  type={msg['type']}")
        await manager.broadcast(room_id, relay, exclude_peer=sender_id)