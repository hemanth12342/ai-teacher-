import logging
from .config import CLASSROOMS as DEFAULT_CLASSROOMS
from .database import SessionLocal, engine, Base
from .models import Classroom, User

logger = logging.getLogger(__name__)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

def to_dict(obj):
    """Converts a SQLAlchemy model instance to a dictionary."""
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

class ClassroomStore:
    def __init__(self):
        self._seed_if_empty()

    def _seed_if_empty(self):
        with SessionLocal() as db:
            if db.query(Classroom).count() == 0:
                for cls_data in DEFAULT_CLASSROOMS:
                    db.add(Classroom(**cls_data))
                db.commit()

    def get_all(self):
        with SessionLocal() as db:
            classrooms = db.query(Classroom).all()
            return [to_dict(c) for c in classrooms]

    def get_by_id(self, room_id: str):
        with SessionLocal() as db:
            classroom = db.query(Classroom).filter(Classroom.id == room_id).first()
            return to_dict(classroom)

    def get_by_slug(self, slug: str):
        with SessionLocal() as db:
            classroom = db.query(Classroom).filter(Classroom.slug == slug).first()
            return to_dict(classroom)

    def add_classroom(self, classroom_data: dict):
        with SessionLocal() as db:
            classroom = Classroom(**classroom_data)
            db.add(classroom)
            db.commit()

    def delete_classroom(self, room_id: str):
        with SessionLocal() as db:
            db.query(Classroom).filter(Classroom.id == room_id).delete()
            db.commit()

    def update_password(self, room_id: str, new_password: str, owner: str = None):
        with SessionLocal() as db:
            update_data = {"password": new_password}
            if owner is not None:
                update_data["owner"] = owner
            db.query(Classroom).filter(Classroom.id == room_id).update(update_data)
            db.commit()

    def release_ownership(self, room_id: str):
        """Remove owner and password from a classroom, making it unclaimed again."""
        with SessionLocal() as db:
            db.query(Classroom).filter(Classroom.id == room_id).update({"owner": None, "password": None})
            db.commit()

    def update_info(self, room_id: str, name: str = None, description: str = None):
        """Update classroom name and/or description."""
        with SessionLocal() as db:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if update_data:
                db.query(Classroom).filter(Classroom.id == room_id).update(update_data)
                db.commit()

# Global singleton instance
store = ClassroomStore()

class UserStore:
    def __init__(self):
        self._seed_if_empty()

    def _seed_if_empty(self):
        with SessionLocal() as db:
            if db.query(User).count() == 0:
                admin_user = User(
                    id="u-admin",
                    username="admin",
                    password="password",
                    role="admin"
                )
                db.add(admin_user)
                db.commit()

    def get_all(self):
        with SessionLocal() as db:
            users = db.query(User).all()
            return [to_dict(u) for u in users]

    def get_by_username(self, username: str):
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            return to_dict(user)

    def get_by_email(self, email: str):
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
            return to_dict(user)

    def add_user(self, user_data: dict):
        with SessionLocal() as db:
            user = User(**user_data)
            db.add(user)
            db.commit()

    def update_password(self, username: str, new_password: str):
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.password = new_password
                db.commit()
                return True
            return False

    def delete_user(self, username: str):
        with SessionLocal() as db:
            db.query(User).filter(User.username == username).delete()
            db.commit()

user_store = UserStore()
