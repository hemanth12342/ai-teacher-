import logging
import aiofiles
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from jose import jwt, JWTError

from ..config import SECRET_KEY, JWT_ALGORITHM, UPLOAD_DIR
from ..data_store import store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/classrooms", tags=["files"])

ALLOWED_EXT = {".pdf", ".docx", ".txt", ".xlsx"}
MAX_FILE_MB = 20

# In-memory file registry: room_id → list[dict]
_file_registry: dict[str, list] = {}


def _auth(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing auth token")
    try:
        return jwt.decode(authorization[7:], SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(401, "Invalid token")


@router.post("/{room_id}/upload")
async def upload_file(
    room_id: str,
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    claims = _auth(authorization)
    if store.get_by_id(room_id) is None:
        raise HTTPException(404, "Classroom not found")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"File type '{ext}' not allowed. Use: {', '.join(ALLOWED_EXT)}")

    contents = await file.read()
    if len(contents) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_FILE_MB}MB limit")

    # Save to disk
    room_dir = Path(UPLOAD_DIR) / room_id
    room_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}"
    save_path = room_dir / safe_name

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(contents)

    # File is saved to disk, no AI ingestion needed

    record = {
        "name":        file.filename,
        "url":         f"/api/classrooms/{room_id}/files/{safe_name}",
        "size":        len(contents),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": claims.get("sub", "unknown"),
        "saved_as":    safe_name,
    }
    _file_registry.setdefault(room_id, []).append(record)

    return {"status": "ok", "file": record}


@router.get("/{room_id}/files")
async def list_files(room_id: str):
    if store.get_by_id(room_id) is None:
        raise HTTPException(404, "Classroom not found")
    return {"files": _file_registry.get(room_id, [])}


@router.get("/{room_id}/files/{filename}")
async def download_file(room_id: str, filename: str):
    from fastapi.responses import FileResponse
    path = Path(UPLOAD_DIR) / room_id / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(path), filename=filename)