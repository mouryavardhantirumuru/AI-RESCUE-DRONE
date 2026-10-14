from risk_engine import RescueRiskEngine

def test_risk_evaluation():
    engine = RescueRiskEngine()

    # Test Case 1: High risk survivor trapped near active fire
    p1 = {
        "drone_id": "DRONE01",
        "track_id": "12",
        "object_type": "person",
        "hazard_type": "fire",
        "confidence": 0.95,
        "thermal_detected": True,
        "latitude": 13.0835,
        "longitude": 80.2720
    }
    r1 = engine.evaluate(p1)
    assert r1["severity"] in ("CRITICAL", "HIGH"), f"Expected high severity, got {r1['severity']}"
    assert r1["risk_score"] >= 70, f"Expected high risk score, got {r1['risk_score']}"
    print("[PASS] Test Case 1 (Fire proximity victim):", r1["severity"], f"Risk: {r1['risk_score']}")

    # Test Case 2: Low risk survivor in clear zone
    p2 = {
        "drone_id": "DRONE01",
        "track_id": "14",
        "object_type": "person",
        "hazard_type": "none",
        "confidence": 0.88,
        "thermal_detected": True,
        "latitude": 13.0900,
        "longitude": 80.2900
    }
    r2 = engine.evaluate(p2)
    assert r2["risk_score"] < 50, f"Expected lower risk, got {r2['risk_score']}"
    print("[PASS] Test Case 2 (Safe zone victim):", r2["severity"], f"Risk: {r2['risk_score']}")

    # Test Case 3: Hypothermia risk (person with no thermal detection)
    p3 = {
        "drone_id": "DRONE01",
        "track_id": "15",
        "object_type": "person",
        "hazard_type": "none",
        "confidence": 0.85,
        "thermal_detected": False,
        "latitude": 13.0850,
        "longitude": 80.2750
    }
    r3 = engine.evaluate(p3)
    assert r3["risk_score"] > r2["risk_score"], "Hypothermia risk should exceed safe zone risk"
    print("[PASS] Test Case 3 (Hypothermia victim):", r3["severity"], f"Risk: {r3['risk_score']}")

    print("\nAll Member 3 Risk Engine tests passed successfully!")

if __name__ == "__main__":
    test_risk_evaluation()
