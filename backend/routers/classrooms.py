from fastapi import APIRouter, HTTPException, Request, Header
from datetime import datetime, timezone, timedelta
from jose import jwt

from ..config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from ..data_store import store
from ..websocket.ai.services.models.schemas import JoinRequest, TokenResponse, ClassroomInfo, CreateClassroomRequest
from ..websocket.manager import manager

router = APIRouter(prefix="/api/classrooms", tags=["classrooms"])


def _room_info(cls: dict) -> ClassroomInfo:
    return ClassroomInfo(
        id               = cls["id"],
        name             = cls["name"],
        slug             = cls["slug"],
        subject          = cls["subject"],
        description      = cls["description"],
        color            = cls["color"],
        participant_count= manager.participant_count(cls["id"]),
        max_participants = cls["max_participants"],
        is_active        = manager.participant_count(cls["id"]) > 0,
        has_password     = bool(cls.get("password")),
        owner            = cls.get("owner") or "",
    )


@router.get("", response_model=list[ClassroomInfo])
async def list_classrooms():
    """Return all classrooms with live participant counts."""
    return [_room_info(c) for c in store.get_all()]


@router.get("/{room_id}", response_model=ClassroomInfo)
async def get_classroom(room_id: str):
    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")
    return _room_info(cls)


@router.post("/{room_id}/join", response_model=TokenResponse)
async def join_classroom(room_id: str, body: JoinRequest):
    """Validate password and issue a JWT session token.
    - If class has no password: anyone can enter freely.
    - If class has a password: must match.
    """
    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")

    # Special logic for Teacher Meeting Room
    if room_id == "cls-teacher-meeting":
        if body.role != "teacher":
            raise HTTPException(403, "Access Denied: This room is for teachers only.")
        # If it's a teacher, allow them to join the meeting room freely (skip password checks)
    else:
        # If class has no password, it's unclaimed. No one can join until a teacher sets one.
        if not cls.get("password"):
            raise HTTPException(403, "This class is currently closed. A teacher must set a password to open it.")

        # Validate password
        if body.password != cls["password"]:
            raise HTTPException(401, "Incorrect password")
                
        # Host-must-be-present logic:
        owner = cls.get("owner")
        if owner and body.username != owner:
            # Check if owner is currently in the room
            participants = manager.get_participants(room_id)
            owner_present = any(p.get("username") == owner for p in participants)
            if not owner_present:
                raise HTTPException(403, f"The teacher ({owner}) has not started the class yet. Please wait for them to join.")

    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token  = jwt.encode(
        {"sub": body.username, "role": body.role, "room": room_id, "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    return TokenResponse(
        token        = token,
        username     = body.username,
        role         = body.role,
        classroom_id = room_id,
        expires_in   = JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/{room_id}/join_as_owner", response_model=TokenResponse)
async def join_classroom_as_owner(room_id: str, body: JoinRequest, authorization: str = Header(None)):
    """Join a classroom without a password if the user is the owner."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if role != "teacher":
            raise HTTPException(403, "Only teachers can take ownership")
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")

    existing_owner = cls.get("owner")
    # Allow if: no owner yet (open class) OR user is the owner
    if existing_owner and existing_owner != username:
        raise HTTPException(403, "You are not the owner of this class")

    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    session_token = jwt.encode(
        {"sub": username, "role": "teacher", "room": room_id, "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return TokenResponse(
        token        = session_token,
        username     = username,
        role         = "teacher",
        classroom_id = room_id,
        expires_in   = JWT_EXPIRE_MINUTES * 60,
    )


from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    new_password: str

@router.put("/{room_id}/password")
async def change_classroom_password(room_id: str, body: ChangePasswordRequest, authorization: str = Header(None)):
    """Set or change the password of a classroom.
    Rules:
    - If class has NO owner yet → any teacher can claim it by setting the first password (they become the owner).
    - If class ALREADY has an owner → only that owner can change the password.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")

    existing_owner = cls.get("owner")

    if existing_owner and existing_owner != username:
        raise HTTPException(403, f"This class already belongs to '{existing_owner}'. Only that teacher can change the password.")

    # First time: claim ownership; subsequent times: keep same owner
    new_owner = existing_owner if existing_owner else username
    store.update_password(room_id, body.new_password, owner=new_owner)

    action = "claimed" if not existing_owner else "updated"
    return {"message": f"Password {action} successfully. You are now the owner of this class."}


@router.delete("/{room_id}/ownership")
async def release_classroom_ownership(room_id: str, authorization: str = Header(None)):
    """Remove the teacher's ownership from a classroom.
    Only the current owner can release their own ownership.
    The class password is also cleared, making it open again.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")

    existing_owner = cls.get("owner")
    if not existing_owner:
        raise HTTPException(400, "This class has no owner to release.")
    if existing_owner != username:
        raise HTTPException(403, "You are not the owner of this class.")

    store.release_ownership(room_id)
    return {"message": f"Ownership released. '{room_id}' is now unclaimed and open to all."}


class UpdateInfoRequest(BaseModel):
    name: str = None
    description: str = None

@router.put("/{room_id}/info")
async def update_classroom_info(room_id: str, body: UpdateInfoRequest, authorization: str = Header(None)):
    """Update the name and/or description of a classroom.
    Only the owner of the class can do this.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")

    existing_owner = cls.get("owner")
    if not existing_owner:
        raise HTTPException(403, "This class has no owner. Set a password first to claim ownership.")
    if existing_owner != username:
        raise HTTPException(403, "Only the class owner can edit the name or description.")

    store.update_info(room_id, name=body.name, description=body.description)
    return {"message": "Class info updated successfully."}


import uuid
import re

@router.post("/create", response_model=TokenResponse)
async def create_classroom(body: CreateClassroomRequest, authorization: str = Header(None)):
    """Create a new classroom and return a JWT session token for the teacher."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Token decode error: {e}, Token: {token}")
        raise HTTPException(401, f"Invalid token: {e}")
        
    role = claims.get("role")
    if role != "teacher":
        raise HTTPException(403, "Only teachers can create a classroom")
        
    room_id = f"cls-{uuid.uuid4().hex[:8]}"
    slug = re.sub(r'[^a-z0-9]+', '-', body.name.lower()).strip('-')
    
    # Generate random bright color
    import random
    colors = ["#6366f1", "#22d3ee", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"]
    color = random.choice(colors)

    new_cls = {
        "id": room_id,
        "name": body.name,
        "slug": slug,
        "subject": body.subject,
        "password": body.password,
        "description": body.description,
        "color": color,
        "max_participants": body.max_participants,
        "owner": body.username,
    }
    
    store.add_classroom(new_cls)
    
    # Automatically generate join token for the teacher
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    token  = jwt.encode(
        {"sub": body.username, "role": "teacher", "room": room_id, "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    return TokenResponse(
        token        = token,
        username     = body.username,
        role         = "teacher",
        classroom_id = room_id,
        expires_in   = JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/{room_id}/link")
async def get_share_link(room_id: str, request: Request):
    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")
    base = str(request.base_url).rstrip("/")
    return {"url": f"{base}/?join={room_id}", "slug": cls["slug"]}


@router.get("/{room_id}/participants")
async def get_participants(room_id: str):
    return {"participants": manager.get_participants(room_id),
            "count": manager.participant_count(room_id)}

@router.delete("/{room_id}")
async def delete_classroom(room_id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception as e:
        print(f"Delete token decode error: {e}, Token: {token}")
        raise HTTPException(401, f"Invalid token: {e}")
        
    role = claims.get("role")
    token_room = claims.get("room")
    
    if role != "teacher":
        raise HTTPException(403, "Only teachers can delete the classroom")
        
    if token_room and token_room != room_id:
        # For the global login token, token_room might be None, which is fine
        # If it's a join token, it will have a token_room
        if token_room is not None:
            raise HTTPException(403, "Not authorized to delete this classroom")
        
    cls = store.get_by_id(room_id)
    if not cls:
        raise HTTPException(404, "Classroom not found")
        
    username = claims.get("sub")
    if cls.get("owner") and cls.get("owner") != username:
        raise HTTPException(403, "You can only delete classrooms you created")
        
    store.delete_classroom(room_id)
    return {"message": "Classroom deleted successfully"}