# AI Rescue Drone — Member 2: Vision & Sensing Subsystem

## Overview
Member 2 is responsible for edge computer vision, object detection, multi-object tracking, thermal simulation confirmation, and GPS coordinate association for the AI Rescue Drone system.

### Data Flow Pipeline
```
RGB / Thermal Input 
       ↓ 
Preprocessing 
       ↓ 
YOLOv8 Detection & Tracking 
       ↓ 
Person / Hazard Classification 
       ↓ 
Persistent Track ID (e.g. "1", "2", "H01") 
       ↓ 
Thermal IR Confirmation (Inferno Colormap Analysis) 
       ↓ 
GPS Ground Coordinates Calculation 
       ↓ 
Structured JSON Output 
       ↓ 
Member 5 FastAPI (POST /detection/)
```

---

## Output JSON Specification
Member 2 outputs structured detection events formatted as:
```json
{
  "drone_id": "DRONE01",
  "track_id": "12",
  "object_type": "person",
  "hazard_type": "none",
  "confidence": 0.95,
  "thermal_detected": true,
  "latitude": 13.0835,
  "longitude": 80.2720
}
```

For environmental hazards:
```json
{
  "drone_id": "DRONE01",
  "track_id": "H01",
  "object_type": "hazard",
  "hazard_type": "fire",
  "confidence": 0.91,
  "thermal_detected": true,
  "latitude": 13.0841,
  "longitude": 80.2731
}
```

> **Note on Team Division:** Member 2 produces detection, tracking, thermal confirmation, and GPS coordinates. Risk score, severity rating (CRITICAL, HIGH, MEDIUM, LOW), and rescue prioritization belong to **Member 3**.

---

## Directory Structure
```
AI-RESCUE-DRONE/
└── member2-vision/
    ├── main.py                 # Main visual pipeline & dual-feed HUD
    ├── detector.py             # YOLOv8 detection & tracking engine
    ├── tracker.py              # Persistent track ID resolution
    ├── thermal.py              # Simulated IR thermal & heat confirmation
    ├── gps.py                  # Drone flight GPS & object localization
    ├── api_client.py           # HTTP client to transmit to Member 5 FastAPI
    ├── config.py               # Central configuration & parameters
    ├── mock_member5_server.py  # Mock FastAPI server for local integration testing
    ├── requirements.txt        # Python package dependencies
    ├── models/
    │   └── best.pt             # Trained YOLOv8 model weights
    └── test_video/
        └── disaster.mp4        # Sample disaster footage with survivors & fire
```

---

## Quick Start Guide

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Member 2 Vision Pipeline
```bash
# Run with default disaster video & interactive dual-feed GUI:
python main.py

# Run with USB / Laptop Webcam:
python main.py --source 0

# Run in headless mode (terminal JSON only):
python main.py --headless

# Connect to Member 5 laptop across LAN:
python main.py --host 192.168.1.105 --port 8000
```

### 3. Testing with Mock Member 5 Server
In Terminal 1 (Start Mock FastAPI Receiver):
```bash
python mock_member5_server.py
```

In Terminal 2 (Start Vision Pipeline):
```bash
python main.py
```
You will see live detections appearing in the FastAPI terminal in real time!
