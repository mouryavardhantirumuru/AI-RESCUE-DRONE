from fastapi import FastAPI, Request
import uvicorn
import json
import socket
import os

app = FastAPI(title="Member 5 Mock Receiver - AI Rescue Drone")

@app.post("/detection/")
@app.post("/detection")
async def receive_detection(request: Request):
    payload = await request.json()
    print(f"\n[MEMBER 5 RECEIVED DETECTION] Drone: {payload.get('drone_id')} - Track: {payload.get('track_id')} - Type: {payload.get('object_type')}")
    print(json.dumps(payload, indent=2))
    return {
        "status": "success",
        "message": "Detection recorded by Member 5",
        "track_id": payload.get("track_id")
    }

@app.get("/")
def root():
    return {"message": "Member 5 Backend Active", "endpoint": "/detection/"}

def get_free_port(preferred=8000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', preferred))
        s.close()
        return preferred
    except OSError:
        s.close()
        return 8001

if __name__ == "__main__":
    port = int(os.environ.get('PORT', get_free_port(8000)))
    print(f"Starting Member 5 Mock Server on http://0.0.0.0:{port} ...")
    uvicorn.run(app, host="0.0.0.0", port=port)
