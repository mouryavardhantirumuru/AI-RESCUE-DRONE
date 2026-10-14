import os
from ultralytics import YOLO
import config

class RescueDetector:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = config.MODEL_PATH
            
        self.model_path = model_path
        
        # Check if custom best.pt exists; if not, initialize with yolov8n.pt and save as best.pt
        if not os.path.exists(model_path):
            print(f"[RescueDetector] '{model_path}' not found.")
            print(f"[RescueDetector] Bootstrapping YOLOv8 Nano base model and saving to '{model_path}'...")
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            base_model = YOLO("yolov8n.pt")
            # Save weights to models/best.pt
            import shutil
            shutil.copy("yolov8n.pt", model_path)
            self.model = YOLO(model_path)
        else:
            print(f"[RescueDetector] Loading model from '{model_path}'...")
            self.model = YOLO(model_path)

        print(f"[RescueDetector] Model ready. Detected class count: {len(self.model.names)}")

    def detect(self, frame, conf=config.CONFIDENCE_THRESHOLD):
        """Standard YOLO detection (Step 4 & 5)."""
        results = self.model(frame, conf=conf, verbose=False)
        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names.get(class_id, f"class_{class_id}")
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox": [x1, y1, x2, y2]
                })
        return detections

    def track(self, frame, conf=config.CONFIDENCE_THRESHOLD):
        """YOLO Persistent Tracking with Track IDs (Step 6 onwards)."""
        results = self.model.track(frame, persist=True, conf=conf, verbose=False)
        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names.get(class_id, f"class_{class_id}")
                
                track_id = None
                if box.id is not None:
                    track_id = int(box.id[0])
                    
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox": [x1, y1, x2, y2],
                    "track_id": track_id
                })
        return detections
