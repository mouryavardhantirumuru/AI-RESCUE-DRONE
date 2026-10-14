import cv2
import numpy as np

def simulate_thermal(frame):
    """
    Converts RGB frame to simulated thermal/infrared feed using INFERNO colormap.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Enhance local contrast to mimic FLIR infrared signatures
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    thermal = cv2.applyColorMap(enhanced, cv2.COLORMAP_INFERNO)
    return thermal

def check_thermal_confirmation(frame, bbox, threshold=95):
    """
    Analyzes region within bounding box for human body or fire heat profile.
    Returns: bool (thermal_detected = True / False)
    """
    x1, y1, x2, y2 = bbox
    h, w = frame.shape[:2]
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))
    
    if x2 <= x1 or y2 <= y1:
        return False
        
    roi = frame[y1:y2, x1:x2]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Calculate heat statistics
    p90 = float(np.percentile(gray_roi, 90))
    mean_val = float(np.mean(gray_roi))
    
    # Thermal response triggered by high intensity / distinct infrared contrast
    return bool(p90 >= threshold or mean_val >= 75)
