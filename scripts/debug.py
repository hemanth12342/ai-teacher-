from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)
response = client.get("/api/classrooms")
print(response.status_code)
print(response.json())
