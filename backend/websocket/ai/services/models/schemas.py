from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ── Auth ──────────────────────────────────────────────────
class JoinRequest(BaseModel):
    password: str
    username: str = Field(default="Student", min_length=2, max_length=40)
    role: str = Field(default="student")   # "teacher" | "student"


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=40)
    email: str = Field(..., min_length=5, description="Email is required for password recovery")
    password: str = Field(..., min_length=4)
    role: str = Field(default="student") # "student" | "teacher" | "admin"


class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str = Field(..., min_length=4)


class AuthTokenResponse(BaseModel):
    token: str
    username: str
    role: str
    expires_in: int


class TokenResponse(BaseModel):
    token: str
    username: str
    role: str
    classroom_id: str
    expires_in: int


# ── Classroom ─────────────────────────────────────────────
class CreateClassroomRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    subject: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=3, max_length=30)
    username: str = Field(..., min_length=2, max_length=40)
    max_participants: int = Field(default=1000)
    description: str = Field(default="")

class ClassroomInfo(BaseModel):
    id: str
    name: str
    slug: str
    subject: str
    description: str
    color: str
    participant_count: int
    max_participants: int
    is_active: bool
    owner: str = ""


class ClassroomDetail(ClassroomInfo):
    share_url: str
    files: List[str] = []


# ── Chat / WebSocket Messages ─────────────────────────────
class WSMessageType(str, Enum):
    CHAT          = "chat"
    SYSTEM        = "system"
    WEBRTC_OFFER  = "webrtc_offer"
    WEBRTC_ANSWER = "webrtc_answer"
    WEBRTC_ICE    = "webrtc_ice"
    QA_QUESTION   = "qa_question"
    QA_ANSWER     = "qa_answer"
    QA_STREAM     = "qa_stream"
    SUBTITLE      = "subtitle"
    ATTENDANCE    = "attendance"
    PARTICIPANT   = "participant"
    ERROR         = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    sender: str = ""
    sender_role: str = "student"
    target: Optional[str] = None   # peer_id for WebRTC unicast
    payload: Any = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Q&A ───────────────────────────────────────────────────
class QuestionPayload(BaseModel):
    question: str
    classroom_id: str


class AnswerPayload(BaseModel):
    question: str
    ai_answer: str
    sources: List[str] = []
    teacher_note: Optional[str] = None


# ── File ──────────────────────────────────────────────────
class FileInfo(BaseModel):
    name: str
    url: str
    size: int
    uploaded_at: str
    uploaded_by: str


# ── Attendance ────────────────────────────────────────────
class AttendanceRecord(BaseModel):
    classroom_id: str
    username: str
    role: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class AttendanceSummary(BaseModel):
    classroom_id: str
    total_sessions: int
    records: List[AttendanceRecord]