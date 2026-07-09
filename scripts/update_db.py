import sys
sys.path.append(".")
from backend.data_store import store
from backend.config import CLASSROOMS

# Find the teacher meeting room from config
teacher_room = next((c for c in CLASSROOMS if c["id"] == "cls-teacher-meeting"), None)

if teacher_room:
    if not store.get_by_id("cls-teacher-meeting"):
        store.add_classroom(teacher_room)
        print("Added cls-teacher-meeting to database.")
    else:
        print("Already exists.")
