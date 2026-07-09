import requests

login_res = requests.post("http://127.0.0.1:8000/api/auth/login", json={"username": "admin", "password": "password", "role": "teacher"})
token = login_res.json()["token"]

headers = {"Authorization": f"Bearer {token}"}
cls_res = requests.post("http://127.0.0.1:8000/api/classrooms/create", json={"name": "Test Class", "subject": "Testing", "password": "old_password", "username": "admin", "description": "", "max_participants": 30}, headers=headers)
room_id = cls_res.json()["classroom_id"]
print("Created class:", room_id)

pwd_res = requests.put(f"http://127.0.0.1:8000/api/classrooms/{room_id}/password", json={"new_password": "new_password"}, headers=headers)
print("Change password response:", pwd_res.json())

join_old = requests.post(f"http://127.0.0.1:8000/api/classrooms/{room_id}/join", json={"username": "student1", "role": "student", "password": "old_password"})
print("Join with old password:", join_old.status_code, join_old.text)

join_new = requests.post(f"http://127.0.0.1:8000/api/classrooms/{room_id}/join", json={"username": "student1", "role": "student", "password": "new_password"})
print("Join with new password:", join_new.status_code)
