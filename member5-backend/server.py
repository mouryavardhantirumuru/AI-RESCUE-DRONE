import os
import sys
import time
import io
import csv
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Include sibling directories in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, os.path.join(PROJECT_DIR, "member3-risk"))
sys.path.insert(0, os.path.join(PROJECT_DIR, "member4-telemetry"))
sys.path.insert(0, CURRENT_DIR)

from database import RescueDatabase
from risk_engine import RescueRiskEngine
from telemetry_engine import DroneTelemetryEngine

app = FastAPI(
    title="AI Rescue Drone - Central Operational Platform",
    description="Unified API & Mission Control for Vision, Risk Evaluation, Flight Telemetry, and Rescue Operations",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Services
db = RescueDatabase()
risk_engine = RescueRiskEngine()
telemetry_engine = DroneTelemetryEngine()

# Latest Frame Cache (For video stream sharing)
latest_frame_bytes: Optional[bytes] = None
latest_frame_time: float = 0.0

# Background task to advance drone telemetry simulation
async def telemetry_background_loop():
    while True:
        try:
            telemetry_engine.tick(dt=1.0)
        except Exception as e:
            print(f"[Telemetry Error] {e}")
        await asyncio.sleep(1.0)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telemetry_background_loop())
    print("[Server] Telemetry background engine started.")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Member 2 Vision -> Member 5 FastAPI Endpoint (Step 12 & 13)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/detection/")
@app.post("/detection")
@app.post("/api/detection")
async def receive_detection(request: Request):
    """
    Receives detection from Member 2 Vision Subsystem:
    {
      "drone_id": "DRONE01",
      "track_id": "12",
      "object_type": "person",
      "hazard_type": "fire",
      "confidence": 0.95,
      "thermal_detected": true,
      "latitude": 13.0835,
      "longitude": 80.272
    }
    Evaluates risk with Member 3 Risk Engine and persists in SQLite.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Step: Member 3 Risk Evaluation
    enriched = risk_engine.evaluate(payload)

    # Step: Store / Update in Member 5 Database
    entity_id = db.record_detection(enriched)

    print(f"[MEMBER 5 API] Received {enriched.get('object_type')} Track:{enriched.get('track_id')} -> ID:{entity_id} | Risk:{enriched.get('risk_score')} ({enriched.get('severity')})")

    return {
        "status": "success",
        "entity_id": entity_id,
        "track_id": enriched.get("track_id"),
        "severity": enriched.get("severity"),
        "priority": enriched.get("priority"),
        "risk_score": enriched.get("risk_score"),
        "rescue_decision": enriched.get("rescue_decision"),
        "timestamp": enriched.get("timestamp")
    }

# ─────────────────────────────────────────────────────────────────────────────
# 2. Victims & Hazards REST APIs
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/victims")
def get_victims():
    """Returns all victim records ordered by risk priority."""
    return db.get_all_victims()

@app.put("/api/victims/{victim_id}/status")
async def update_victim_status(victim_id: str, request: Request):
    """Updates victim status: 'Pending', 'In Progress', 'Rescued'."""
    data = await request.json()
    new_status = data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing status field")

    ok = db.update_victim_status(victim_id, new_status)
    if not ok:
        raise HTTPException(status_code=404, detail="Victim not found")

    return {"status": "success", "victim_id": victim_id, "new_status": new_status}

@app.get("/api/hazards")
def get_hazards():
    """Returns all active environmental disaster hazards."""
    return db.get_all_hazards()

# ─────────────────────────────────────────────────────────────────────────────
# 3. Telemetry & Drone Actions
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/telemetry")
def get_telemetry():
    """Returns current real-time flight telemetry from Member 4."""
    telem = telemetry_engine.get_telemetry()
    stats = db.get_summary_stats()
    telem["victims_detected"] = stats["total_victims"]
    telem["critical_victims"] = stats["critical_count"]
    telem["records"] = db.get_all_victims()
    return telem

@app.post("/api/action")
async def trigger_action(request: Request):
    """Handles drone operational commands."""
    body = await request.json()
    action = body.get("action")

    if action == "toggle_status":
        is_searching = telemetry_engine.toggle_search()
        return {"status": "success", "message": f"Drone search mode set to: {'Searching' if is_searching else 'Hovering'}"}
    elif action == "rtl":
        msg = telemetry_engine.return_to_launch()
        return {"status": "success", "message": msg}
    elif action == "calibrate_thermal":
        return {"status": "success", "message": "Thermal infrared sensor recalibrated to current ambient baseline."}
    elif action == "save_victim":
        telem = telemetry_engine.get_telemetry()
        enriched = risk_engine.evaluate({
            "drone_id": telem["drone_id"],
            "track_id": f"MAN_{int(time.time()) % 1000}",
            "object_type": "person",
            "hazard_type": "none",
            "confidence": 0.99,
            "thermal_detected": True,
            "latitude": telem["latitude"],
            "longitude": telem["longitude"]
        })
        vid = db.record_detection(enriched)
        return {"status": "success", "message": f"Pinned victim coordinates saved as {vid}."}
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

@app.get("/api/stats")
def get_stats():
    """Comprehensive system metrics."""
    stats = db.get_summary_stats()
    stats.update({
        "battery": telemetry_engine.battery_pct,
        "flight_mode": telemetry_engine.flight_mode,
        "drone_lat": telemetry_engine.current_lat,
        "drone_lon": telemetry_engine.current_lon
    })
    return stats

# ─────────────────────────────────────────────────────────────────────────────
# 4. Reports Export (CSV & JSON)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/export/csv")
def export_csv():
    victims = db.get_all_victims()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Victim ID", "Track ID", "Object Type", "Hazard Type", "Confidence",
        "Thermal Confirmed", "Latitude", "Longitude", "Risk Score (0-100)",
        "Severity", "Priority", "Rescue Recommendation", "Status", "First Seen", "Last Updated"
    ])
    for v in victims:
        writer.writerow([
            v["victim_id"], v["track_id"], v["object_type"], v["hazard_type"], v["confidence"],
            "YES" if v["thermal_detected"] else "NO", v["latitude"], v["longitude"],
            v["risk_score"], v["severity"], v["priority"], v["rescue_decision"],
            v["status"], v["first_seen"], v["last_updated"]
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=AI_Rescue_Drone_Report_{int(time.time())}.csv"}
    )

@app.get("/api/export/json")
def export_json():
    victims = db.get_all_victims()
    hazards = db.get_all_hazards()
    telem = telemetry_engine.get_telemetry()
    report = {
        "report_generated": datetime.datetime.now().isoformat(),
        "drone_telemetry": telem,
        "summary": db.get_summary_stats(),
        "victims": victims,
        "hazards": hazards
    }
    return JSONResponse(
        content=report,
        headers={"Content-Disposition": f"attachment; filename=AI_Rescue_Drone_Report_{int(time.time())}.json"}
    )

# ─────────────────────────────────────────────────────────────────────────────
# 5. Video Frame Ingestion & Live MJPEG Streaming
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/frame")
async def upload_frame(request: Request):
    global latest_frame_bytes, latest_frame_time
    data = await request.body()
    if data:
        latest_frame_bytes = data
        latest_frame_time = time.time()
        return {"status": "ok", "bytes": len(data)}
    raise HTTPException(status_code=400, detail="Empty frame body")

@app.get("/api/frame")
def get_frame():
    global latest_frame_bytes
    if latest_frame_bytes:
        return Response(content=latest_frame_bytes, media_type="image/jpeg")
    return Response(content=b"", status_code=204)

@app.get("/api/stream")
def stream_mjpeg():
    def mjpeg_generator():
        global latest_frame_bytes
        while True:
            if latest_frame_bytes:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + latest_frame_bytes + b"\r\n")
            time.sleep(0.04) # ~25 FPS
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Web Dashboard Frontend Mount
# ─────────────────────────────────────────────────────────────────────────────
WEB_DIR = os.path.join(PROJECT_DIR, "web-dashboard")
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>AI Rescue Drone Platform Ready</h1><p>Dashboard file loading...</p>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n============================================================")
    print(f"  AI RESCUE DRONE - CENTRAL PLATFORM & FASTAPI BACKEND")
    print(f"  Web Dashboard:    http://localhost:{port}/")
    print(f"  API Docs (Swagger): http://localhost:{port}/docs")
    print(f"  Detection Ingest: POST http://localhost:{port}/detection/")
    print(f"============================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
