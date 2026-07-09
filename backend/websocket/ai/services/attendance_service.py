"""
Auto-attendance service.
Records join / leave events and computes duration.
Optionally syncs with Moodle if credentials are configured.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List
from collections import defaultdict

from .models.schemas import AttendanceRecord

logger = logging.getLogger(__name__)


class AttendanceService:
    def __init__(self):
        # room_id → list[AttendanceRecord]
        self._records: Dict[str, List[AttendanceRecord]] = defaultdict(list)
        # (room_id, username) → open record index
        self._open: Dict[tuple, int] = {}

    # ── Recording ─────────────────────────────────────────

    async def record_join(self, room_id: str, username: str, role: str = "student"):
        key = (room_id, username)
        rec = AttendanceRecord(
            classroom_id = room_id,
            username     = username,
            role         = role,
            joined_at    = datetime.now(timezone.utc),
        )
        idx = len(self._records[room_id])
        self._records[room_id].append(rec)
        self._open[key] = idx
        logger.info(f"[ATT] JOIN  {username} → {room_id}")
        await self._sync_moodle_join(room_id, username)

    async def record_leave(self, room_id: str, username: str):
        key = (room_id, username)
        idx = self._open.pop(key, None)
        if idx is None:
            return
        rec = self._records[room_id][idx]
        left_at = datetime.now(timezone.utc)
        duration = int((left_at - rec.joined_at).total_seconds())
        self._records[room_id][idx] = AttendanceRecord(
            **{**rec.model_dump(), "left_at": left_at, "duration_seconds": duration}
        )
        logger.info(f"[ATT] LEAVE {username} ← {room_id}  ({duration}s)")
        await self._sync_moodle_leave(room_id, username, duration)

    # ── Queries ───────────────────────────────────────────

    def get_records(self, room_id: str) -> List[AttendanceRecord]:
        return self._records.get(room_id, [])

    def get_summary(self, room_id: str) -> dict:
        records = self.get_records(room_id)
        return {
            "classroom_id":   room_id,
            "total_sessions": len(records),
            "records": [r.model_dump() for r in records],
        }

    # ── Moodle hooks (no-op when not configured) ──────────

    async def _sync_moodle_join(self, room_id: str, username: str):
        try:
            from .moodle import moodle_client
            if moodle_client.is_configured():
                await moodle_client.mark_attendance(room_id, username, "join")
        except Exception as e:
            logger.debug(f"Moodle join sync skipped: {e}")

    async def _sync_moodle_leave(self, room_id: str, username: str, duration: int):
        try:
            from .moodle import moodle_client
            if moodle_client.is_configured():
                await moodle_client.mark_attendance(room_id, username, "leave", duration)
        except Exception as e:
            logger.debug(f"Moodle leave sync skipped: {e}")


attendance_service = AttendanceService()