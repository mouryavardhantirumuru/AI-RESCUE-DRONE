# AI RESCUE DRONE: AUTONOMOUS SEARCH & RESCUE PLATFORM

### Department of Computer Science & Engineering • Smart India Hackathon (SIH)
*Accredited by NAAC with 'A' GRADE & CGPA of 3.27*

---

## 🚁 Project Overview
The **AI Rescue Drone** platform is an end-to-end edge AI, telemetry simulation, and incident management system designed for disaster relief missions (earthquakes, floods, industrial fires, collapsed buildings).

The architecture is divided into modular subsystems matching the multi-member engineering team:

```
[ DISASTER ZONE INPUT: RGB Video / Thermal IR ]
                       │
                       ▼
          ┌──────────────────────────┐
          │  MEMBER 2: VISION        │
          │  • YOLOv8 Person/Hazard  │
          │  • ByteTrack Track ID    │
          │  • Simulated Thermal IR  │
          │  • GPS Coordinate Calc   │
          └────────────┬─────────────┘
                       │ JSON Payload (POST /detection/)
                       ▼
          ┌──────────────────────────┐
          │  MEMBER 5: BACKEND       │ ◄─────── [ MEMBER 4: TELEMETRY ]
          │  • FastAPI REST Server   │          • Lawnmower Flight Path
          │  • SQLite Database       │          • GPS, Altitude, Speed
          │  • Telemetry Logger      │          • Battery & RTL Logic
          └────────────┬─────────────┘
                       │
                       ▼
          ┌──────────────────────────┐
          │  MEMBER 3: RISK ENGINE   │
          │  • Hazard Distance Calc  │
          │  • Risk Score (0-100)    │
          │  • Severity & Priority   │
          │  • Rescue Recommendation │
          └────────────┬─────────────┘
                       │
                       ▼
       ┌─────────────────────────────────┐
       │   WEB MISSION CONTROL DASHBOARD │
       │   • Tactical Satellite GPS Map  │
       │   • Live RGB & Thermal Canvas   │
       │   • Real-Time Victim Table      │
       │   • One-Click Action Controls   │
       │   • CSV & JSON Export Reports   │
       └─────────────────────────────────┘
```

---

## 📂 Subsystems Breakdown

### 1. `member2-vision/` (Vision & Sensing)
- **`detector.py`**: YOLOv8 engine detecting persons and disaster hazards (`fire`, `flood`, `debris`, `damaged_structure`).
- **`tracker.py`**: Persistent Track ID management preventing duplicate victim alerts.
- **`thermal.py`**: Simulated FLIR Infrared feed via Inferno colormap & heat confirmation.
- **`gps.py`**: Converts pixel offsets into geographical coordinates relative to drone flight center.
- **`api_client.py`**: Sends JSON payloads to Member 5 backend.
- **`models/best.pt`**: Trained YOLOv8 model weights.
- **`test_video/disaster.mp4`**: High-resolution disaster test video with people & fire hazards.

### 2. `member3-risk/` (Severity, Risk & Priority Engine)
- **`risk_engine.py`**: Computes proximity to environmental hazards using Haversine formula, analyzes thermal exposure, calculates a normalized **Risk Score (0 to 100)**, and assigns:
  - **Severity**: `CRITICAL` (>=75), `HIGH` (50-74), `MEDIUM` (30-49), `LOW` (<30)
  - **Priority**: `HIGH`, `MEDIUM`, `LOW`
  - **Rescue Decision**: e.g., `IMMEDIATE_AIRLIFT_EXTRACTION`, `DISPATCH_FIRST_RESPONDER_TEAM`

### 3. `member4-telemetry/` (Flight Simulation & Geofencing)
- **`telemetry_engine.py`**: Simulates physics and navigation dynamics:
  - Latitude, Longitude, Altitude (30m), Speed (7.5 m/s), Heading (0°-360°)
  - Dynamic battery depletion & 6S LiPo voltage curves
  - Autonomous search sweep pattern (lawnmower grid)
  - Return-To-Launch (RTL) autonomous return routing
  - Breadcrumbs trajectory recording for satellite map polyline

### 4. `member5-backend/` (FastAPI Central Server & Database)
- **`server.py`**: Async FastAPI platform serving REST APIs, MJPEG camera streams, and Web Dashboard.
- **`database.py`**: SQLite database (`rescue_drone.db`) persisting:
  - `victims`: Persistent records with victim ID (`V001`, `V002`...), coordinates, severity, status
  - `hazards`: Active disaster locations (`H01`, `H02`...)
  - `telemetry_logs`: Drone flight records

### 5. `web-dashboard/` (Interactive Mission Control Website)
- **`index.html`**:
  - Live Tactical Satellite Map (Leaflet.js + Esri World Imagery)
  - Live Animated Drone Radar Ping & Flight Path Polyline
  - Color-coded Victim & Hazard Pins with interactive popups
  - Live RGB YOLOv8 Camera Canvas with bounding boxes & track IDs
  - Simulated Thermal IR Canvas (Inferno colormap & temperature gradient)
  - Camera Switcher (Simulation / Live USB Webcam / Phone Camera via WebRTC)
  - Real-time Victim Incident Table with instant "Mark Rescued" actions
  - Drone Control Buttons: Toggle Search, Calibrate Thermal, Save Geolocation, RTL, Export CSV/JSON

---

## 🚀 Quick Start Guide

### 1. Installation
Install all requirements:
```powershell
pip install -r requirements.txt
```

### 2. One-Click Launch (All Subsystems)
To launch the complete system (Backend, Database, Telemetry, Vision Pipeline, and Web Dashboard):
```powershell
python run_all.py
```
*Your browser will automatically open to `http://localhost:8000` with live mission control!*

### 3. Running Subsystems Separately (Distributed Laptops / Testing)
- **To run Backend & Web Dashboard:**
  ```powershell
  cd member5-backend
  python server.py
  ```
- **To run Member 2 Vision Subsystem (with live camera/video):**
  ```powershell
  cd member2-vision
  python main.py
  ```
  *(To use your laptop's USB webcam instead of test video, run: `python main.py --source 0`)*

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the Mission Control Web Dashboard |
| `POST` | `/detection/` | Ingests Member 2 JSON and runs Member 3 Risk Engine |
| `GET` | `/api/victims` | Returns all victims sorted by risk severity |
| `PUT` | `/api/victims/{id}/status` | Updates victim status (`Rescued`, `In Progress`, `Pending`) |
| `GET` | `/api/telemetry` | Returns real-time drone coordinates, speed, battery, altitude |
| `POST` | `/api/action` | Triggers drone commands (`toggle_status`, `rtl`, `calibrate_thermal`) |
| `GET` | `/api/export/csv` | Downloads CSV incident report |
| `GET` | `/api/export/json` | Downloads JSON incident report |
| `GET` | `/docs` | Interactive Swagger API documentation |
