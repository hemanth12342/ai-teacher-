"""
AI Teacher Assistant — FastAPI backend
Run with:  uvicorn backend.main:app --reload --port 8000
"""
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ── Routers ───────────────────────────────────────────────
from .routers.classrooms import router as classrooms_router
from .routers.files       import router as files_router
from .routers.attendance  import router as attendance_router
from .routers import auth
from .websocket.classroom_ws import classroom_ws_handler

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title       = "AI Teacher Assistant",
    description = "Virtual classroom platform with AI Q&A, WebRTC, live subtitles, and attendance.",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# ── REST routers ──────────────────────────────────────────
app.include_router(classrooms_router)
app.include_router(files_router)
app.include_router(attendance_router)
app.include_router(auth.router)

# ── DB Status ─────────────────────────────────────────────
@app.get("/api/db-status")
async def db_status():
    """Check if MySQL connection is alive."""
    try:
        from .database import SessionLocal
        with SessionLocal() as db:
            db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"connected": True, "database": "PostgreSQL (Neon)"}
    except Exception as e:
        return {"connected": False, "error": str(e)}

# ── WebSocket ─────────────────────────────────────────────
@app.websocket("/ws/{room_id}")
async def ws_endpoint(websocket: WebSocket, room_id: str, token: str = Query(...)):
    await classroom_ws_handler(websocket, room_id, token)


# ── WebSocket: subtitle audio ingestion ───────────────────
@app.websocket("/ws/subtitles/{room_id}")
async def ws_subtitles(websocket: WebSocket, room_id: str, token: str = Query(...)):
    """Receives binary PCM audio, returns transcribed text."""
    from jose import jwt, JWTError
    from .config import SECRET_KEY, JWT_ALGORITHM
    from .websocket.ai.transcription import transcribe_chunk
    import json

    try:
        jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            text = await transcribe_chunk(audio_bytes)
            if text:
                await websocket.send_text(json.dumps({"type": "subtitle", "text": text}))
    except Exception:
        pass


# ── Static frontend ───────────────────────────────────────
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(frontend_path / "index.html"))

    @app.get("/classroom.html")
    async def serve_classroom():
        return FileResponse(str(frontend_path / "classroom.html"))

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_path / "index.html"))


# ── Health check ──────────────────────────────────────────
@app.get("/api/health")
async def health():
    from .websocket.manager import manager
    return {
        "status": "ok",
        "rooms":  manager.all_room_counts(),
    }