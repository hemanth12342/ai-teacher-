from fastapi import APIRouter, HTTPException
from ..data_store import store
from ..websocket.ai.services.attendance_service import attendance_service

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("/{room_id}")
async def get_attendance(room_id: str):
    if store.get_by_id(room_id) is None:
        raise HTTPException(404, "Classroom not found")
    return attendance_service.get_summary(room_id)


@router.get("/{room_id}/records")
async def get_records(room_id: str):
    if store.get_by_id(room_id) is None:
        raise HTTPException(404, "Classroom not found")
    return {"records": [r.model_dump() for r in attendance_service.get_records(room_id)]}

@router.post("/{room_id}/export-sheets")
async def export_to_google_sheets(room_id: str):
    if store.get_by_id(room_id) is None:
        raise HTTPException(404, "Classroom not found")
        
    records = attendance_service.get_records(room_id)
    if not records:
        raise HTTPException(400, "No attendance records to export")
        
    from ..websocket.ai.services.google_sheets import google_sheets_service
    try:
        result = google_sheets_service.export_attendance(room_id, records)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))