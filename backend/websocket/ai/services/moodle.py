"""
Moodle REST API client.
All methods are no-ops when MOODLE_BASE_URL / MOODLE_TOKEN are not set.
"""
import logging
import httpx
from ....config import MOODLE_BASE_URL, MOODLE_TOKEN

logger = logging.getLogger(__name__)


class MoodleClient:
    def __init__(self):
        self._base = MOODLE_BASE_URL.rstrip("/")
        self._token = MOODLE_TOKEN

    def is_configured(self) -> bool:
        return bool(self._token and "example.com" not in self._base)

    def _endpoint(self, function: str) -> str:
        return f"{self._base}/webservice/rest/server.php?wstoken={self._token}&moodlewsrestformat=json&wsfunction={function}"

    async def get_user(self, username: str) -> dict:
        if not self.is_configured():
            return {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    self._endpoint("core_user_get_users"),
                    params={"criteria[0][key]": "username", "criteria[0][value]": username},
                )
                data = r.json()
                users = data.get("users", [])
                return users[0] if users else {}
        except Exception as e:
            logger.warning(f"Moodle get_user error: {e}")
            return {}

    async def mark_attendance(self, room_id: str, username: str, event: str, duration: int = 0):
        if not self.is_configured():
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    self._endpoint("mod_attendance_add_session"),
                    data={
                        "attendanceid": room_id.replace("cls-", ""),
                        "sessiontime":  0,
                        "duration":     duration,
                        "studentscanmark": 0,
                    },
                )
            logger.info(f"Moodle attendance synced: {username} {event} room {room_id}")
        except Exception as e:
            logger.warning(f"Moodle attendance error: {e}")


moodle_client = MoodleClient()