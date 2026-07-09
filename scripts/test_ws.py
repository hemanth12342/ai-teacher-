import asyncio
import websockets
import json
import requests

def get_token():
    # Login
    res = requests.post("http://localhost:8000/api/auth/login", json={"username": "testuser", "password": "password123"})
    if res.status_code == 200:
        return res.json()["token"]
    print("Login failed:", res.text)
    return None

async def test_ws(token):
    uri = f"ws://localhost:8000/ws/cls-101?token={token}"
    async with websockets.connect(uri) as websocket:
        print("connection open")
        try:
            msg = await websocket.recv()
            print(f"Received: {msg}")
            
            # send a dummy message to see if it closes
            await websocket.send(json.dumps({"type": "chat", "payload": {"text": "hello"}}))
            msg2 = await websocket.recv()
            print(f"Received2: {msg2}")
            
        except Exception as e:
            print(f"Error: {e}")

token = get_token()
if token:
    asyncio.run(test_ws(token))
else:
    print("Could not login")
