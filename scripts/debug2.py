from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app, raise_server_exceptions=True)
try:
    response = client.post("/api/classrooms/cls-101/join", json={"password": "", "username": "testuser", "role": "student"})
    print(response.status_code, response.json())
except Exception as e:
    print("Exception:", e)
