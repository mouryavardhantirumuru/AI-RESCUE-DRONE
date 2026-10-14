import math
import datetime

class RescueRiskEngine:
    """
    Member 3 - AI Rescue Drone
    Evaluates raw detections from Member 2 (Vision & Sensing) and computes:
    1. Distance to nearest environmental hazards (fire, flood, debris, electrical lines)
    2. Composite Risk Score (0 - 100)
    3. Severity Category (CRITICAL, HIGH, MEDIUM, LOW)
    4. Rescue Priority Ranking (1 = Immediate Airlift down to 4 = Routine)
    5. Actionable Rescue Recommendation
    """

    HAZARD_BASE_WEIGHTS = {
        "fire": 50,
        "smoke": 35,
        "chemical_leak": 55,
        "electrical_line": 45,
        "flood": 40,
        "landslide": 45,
        "damaged_structure": 30,
        "debris": 20,
        "none": 0
    }

    def __init__(self):
        # In-memory registry of active persistent victims and hazards
        self.victim_history = {} # track_id -> history dict
        self.active_hazards = []  # list of hazard dicts

    def register_hazard(self, hazard_type, latitude, longitude, confidence=0.9):
        """Registers an active hazard discovered in the disaster zone."""
        hazard_entry = {
            "type": hazard_type.lower(),
            "lat": latitude,
            "lon": longitude,
            "confidence": confidence,
            "radius_m": 35.0, # hazard influence radius
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.active_hazards.append(hazard_entry)
        return hazard_entry

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculates distance between two GPS coordinates in meters."""
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def find_nearest_hazard(self, lat, lon):
        """Finds closest environmental hazard and distance in meters."""
        if not self.active_hazards:
            return None, 999.0

        min_dist = 999999.0
        nearest = None

        for hz in self.active_hazards:
            d = self.haversine_distance(lat, lon, hz["lat"], hz["lon"])
            if d < min_dist:
                min_dist = d
                nearest = hz

        return nearest, round(min_dist, 1)

    def evaluate(self, detection):
        """
        Takes Member 2 JSON payload:
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
        Returns enriched payload with Member 3 calculations.
        """
        track_id = str(detection.get("track_id", "0"))
        obj_type = detection.get("object_type", "person").lower()
        hazard_type = detection.get("hazard_type", "none").lower()
        thermal_detected = bool(detection.get("thermal_detected", False))
        confidence = float(detection.get("confidence", 0.8))
        lat = float(detection.get("latitude", 13.0827))
        lon = float(detection.get("longitude", 80.2707))

        # If it's a standalone hazard, register it
        if obj_type == "hazard" or hazard_type not in ("none", ""):
            hz_type = hazard_type if hazard_type != "none" else obj_type
            self.register_hazard(hz_type, lat, lon, confidence)

        # Base Risk Computation
        base_risk = 20.0

        # 1. Proximity to hazards
        nearest_hazard, hazard_dist = self.find_nearest_hazard(lat, lon)
        hazard_risk_boost = 0.0

        if hazard_type in self.HAZARD_BASE_WEIGHTS:
            hazard_risk_boost += self.HAZARD_BASE_WEIGHTS[hazard_type] * 0.8

        if nearest_hazard and hazard_dist < 50.0:
            # Proximity penalty: closer to hazard = dramatically higher risk
            proximity_factor = max(0.0, (50.0 - hazard_dist) / 50.0)
            hazard_weight = self.HAZARD_BASE_WEIGHTS.get(nearest_hazard["type"], 30)
            hazard_risk_boost += hazard_weight * proximity_factor

        # 2. Thermal Signature Evaluation
        # If human has thermal signature in normal range, body heat is present.
        # If human thermal signature is abnormally low or absent -> hypothermia / unconsciousness risk (+25)
        # If in extreme fire zone and thermal is confirmed -> high burn risk (+20)
        thermal_risk = 0.0
        if obj_type == "person":
            if not thermal_detected:
                thermal_risk += 25.0 # Potential hypothermia or buried under rubble
            elif hazard_type == "fire" or (nearest_hazard and nearest_hazard["type"] == "fire" and hazard_dist < 20):
                thermal_risk += 20.0 # Heat exposure / flame proximity

        # 3. Detection Confidence Factor
        confidence_factor = confidence * 10.0

        # Total Composite Risk Score (0 - 100)
        total_risk = min(100.0, max(10.0, base_risk + hazard_risk_boost + thermal_risk + confidence_factor))
        risk_score = int(round(total_risk))

        # Categorize Severity & Priority
        if risk_score >= 75:
            severity = "CRITICAL"
            priority = "HIGH"
            priority_rank = 1
            decision = "IMMEDIATE_AIRLIFT_EXTRACTION"
        elif risk_score >= 50:
            severity = "HIGH"
            priority = "HIGH"
            priority_rank = 2
            decision = "DISPATCH_FIRST_RESPONDER_TEAM"
        elif risk_score >= 30:
            severity = "MEDIUM"
            priority = "MEDIUM"
            priority_rank = 3
            decision = "DEPLOY_DRONE_PAYLOAD_FIRST_AID"
        else:
            severity = "LOW"
            priority = "LOW"
            priority_rank = 4
            decision = "CONTINUOUS_MONITORING"

        # Track persistent history
        if track_id not in self.victim_history:
            self.victim_history[track_id] = {
                "first_seen": datetime.datetime.now().isoformat(),
                "seen_count": 0
            }
        self.victim_history[track_id]["seen_count"] += 1

        # Enriched JSON Result
        enriched = {
            "drone_id": detection.get("drone_id", "DRONE01"),
            "track_id": track_id,
            "object_type": obj_type,
            "hazard_type": hazard_type,
            "confidence": round(confidence, 2),
            "thermal_detected": thermal_detected,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "risk_score": risk_score,
            "severity": severity,
            "priority": priority,
            "priority_rank": priority_rank,
            "rescue_decision": decision,
            "nearest_hazard_type": nearest_hazard["type"] if nearest_hazard else "none",
            "nearest_hazard_dist_m": hazard_dist if nearest_hazard else None,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        }

        return enriched

# Standalone execution test
if __name__ == "__main__":
    engine = RescueRiskEngine()
    test_detection = {
        "drone_id": "DRONE01",
        "track_id": "12",
        "object_type": "person",
        "hazard_type": "fire",
        "confidence": 0.95,
        "thermal_detected": True,
        "latitude": 13.0835,
        "longitude": 80.2720
    }
    result = engine.evaluate(test_detection)
    import json
    print("Member 3 Risk Engine Output:")
    print(json.dumps(result, indent=2))
