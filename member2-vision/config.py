import os

# Drone Identification
DRONE_ID = "DRONE01"

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "best.pt")
TEST_VIDEO_PATH = os.path.join(BASE_DIR, "test_video", "disaster.mp4")

# Model & Detection Settings
CONFIDENCE_THRESHOLD = 0.35
IOU_THRESHOLD = 0.45

# GPS Coordinates (Disaster Operations Center / Field Base in Chennai)
BASE_LATITUDE = 13.0827
BASE_LONGITUDE = 80.2707

# Member 5 FastAPI Endpoint
# For distributed laptops on LAN, set MEMBER5_HOST to Member 5's IP (e.g. 192.168.1.X)
MEMBER5_HOST = os.environ.get("MEMBER5_HOST", "127.0.0.1")
MEMBER5_PORT = int(os.environ.get("MEMBER5_PORT", 8000))
MEMBER5_API_URL = f"http://{MEMBER5_HOST}:{MEMBER5_PORT}/detection/"

# Disaster Hazard Classes
HAZARD_CLASSES = {
    "fire", "smoke", "flood", "damaged_structure",
    "electrical_line", "debris", "landslide", "chemical_leak"
}
