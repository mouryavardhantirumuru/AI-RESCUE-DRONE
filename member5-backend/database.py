import sqlite3
import os
import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rescue_drone.db")

class RescueDatabase:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Victims Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS victims (
            victim_id TEXT PRIMARY KEY,
            track_id TEXT,
            object_type TEXT,
            hazard_type TEXT,
            confidence REAL,
            thermal_detected INTEGER,
            latitude REAL,
            longitude REAL,
            risk_score INTEGER,
            severity TEXT,
            priority TEXT,
            rescue_decision TEXT,
            status TEXT DEFAULT 'Pending',
            first_seen TEXT,
            last_updated TEXT
        )
        """)

        # 2. Hazards Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hazards (
            hazard_id TEXT PRIMARY KEY,
            hazard_type TEXT,
            latitude REAL,
            longitude REAL,
            confidence REAL,
            radius_m REAL,
            timestamp TEXT
        )
        """)

        # 3. Telemetry Breadcrumbs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drone_id TEXT,
            latitude REAL,
            longitude REAL,
            altitude REAL,
            speed REAL,
            battery REAL,
            status TEXT,
            timestamp TEXT
        )
        """)

        # Seed initial realistic victim & hazard records if empty
        cursor.execute("SELECT COUNT(*) FROM victims")
        if cursor.fetchone()[0] == 0:
            now = datetime.datetime.now()
            cursor.execute("""
            INSERT INTO victims VALUES 
            ('V001', '12', 'person', 'fire', 0.94, 1, 13.083500, 80.272000, 88, 'CRITICAL', 'HIGH', 'IMMEDIATE_AIRLIFT_EXTRACTION', 'Pending', ?, ?),
            ('V002', '14', 'person', 'debris', 0.89, 1, 13.084120, 80.271850, 62, 'HIGH', 'HIGH', 'DISPATCH_FIRST_RESPONDER_TEAM', 'In Progress', ?, ?),
            ('V003', '15', 'person', 'none', 0.86, 0, 13.082150, 80.269800, 48, 'MEDIUM', 'MEDIUM', 'DEPLOY_DRONE_PAYLOAD_FIRST_AID', 'Pending', ?, ?),
            ('V004', '18', 'person', 'none', 0.91, 1, 13.081900, 80.270400, 24, 'LOW', 'LOW', 'CONTINUOUS_MONITORING', 'Rescued', ?, ?)
            """, (
                (now - datetime.timedelta(minutes=14)).strftime("%H:%M:%S"), now.strftime("%H:%M:%S"),
                (now - datetime.timedelta(minutes=10)).strftime("%H:%M:%S"), now.strftime("%H:%M:%S"),
                (now - datetime.timedelta(minutes=6)).strftime("%H:%M:%S"), now.strftime("%H:%M:%S"),
                (now - datetime.timedelta(minutes=2)).strftime("%H:%M:%S"), now.strftime("%H:%M:%S")
            ))

            cursor.execute("""
            INSERT INTO hazards VALUES
            ('H01', 'fire', 13.083700, 80.272300, 0.95, 30.0, ?),
            ('H02', 'debris', 13.084300, 80.271900, 0.90, 20.0, ?)
            """, (now.strftime("%H:%M:%S"), now.strftime("%H:%M:%S")))

        conn.commit()
        conn.close()

    def record_detection(self, enriched_detection):
        """Inserts or updates a persistent victim record from Member 3 enriched detection."""
        conn = self.get_connection()
        cursor = conn.cursor()

        track_id = str(enriched_detection.get("track_id", "0"))
        obj_type = enriched_detection.get("object_type", "person").lower()
        now_str = datetime.datetime.now().strftime("%H:%M:%S")

        if obj_type == "hazard":
            hz_id = f"H{track_id}" if not track_id.startswith("H") else track_id
            cursor.execute("""
            INSERT INTO hazards (hazard_id, hazard_type, latitude, longitude, confidence, radius_m, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hazard_id) DO UPDATE SET
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                timestamp=excluded.timestamp
            """, (
                hz_id,
                enriched_detection.get("hazard_type", "hazard"),
                enriched_detection.get("latitude"),
                enriched_detection.get("longitude"),
                enriched_detection.get("confidence", 0.9),
                35.0,
                now_str
            ))
            conn.commit()
            conn.close()
            return hz_id

        # For person: Check if track_id already mapped to a victim_id (e.g. V001)
        cursor.execute("SELECT victim_id, status FROM victims WHERE track_id = ?", (track_id,))
        row = cursor.fetchone()

        if row:
            victim_id = row["victim_id"]
            current_status = row["status"]
            cursor.execute("""
            UPDATE victims SET
                hazard_type = ?,
                confidence = ?,
                thermal_detected = ?,
                latitude = ?,
                longitude = ?,
                risk_score = ?,
                severity = ?,
                priority = ?,
                rescue_decision = ?,
                last_updated = ?
            WHERE victim_id = ?
            """, (
                enriched_detection.get("hazard_type", "none"),
                enriched_detection.get("confidence", 0.9),
                1 if enriched_detection.get("thermal_detected") else 0,
                enriched_detection.get("latitude"),
                enriched_detection.get("longitude"),
                enriched_detection.get("risk_score", 50),
                enriched_detection.get("severity", "MEDIUM"),
                enriched_detection.get("priority", "MEDIUM"),
                enriched_detection.get("rescue_decision", "DISPATCH_FIRST_RESPONDER_TEAM"),
                now_str,
                victim_id
            ))
        else:
            # Generate next V00X ID
            cursor.execute("SELECT COUNT(*) FROM victims")
            count = cursor.fetchone()[0] + 1
            victim_id = f"V{count:03d}"

            cursor.execute("""
            INSERT INTO victims (
                victim_id, track_id, object_type, hazard_type, confidence,
                thermal_detected, latitude, longitude, risk_score, severity,
                priority, rescue_decision, status, first_seen, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
            """, (
                victim_id,
                track_id,
                obj_type,
                enriched_detection.get("hazard_type", "none"),
                enriched_detection.get("confidence", 0.9),
                1 if enriched_detection.get("thermal_detected") else 0,
                enriched_detection.get("latitude"),
                enriched_detection.get("longitude"),
                enriched_detection.get("risk_score", 50),
                enriched_detection.get("severity", "MEDIUM"),
                enriched_detection.get("priority", "MEDIUM"),
                enriched_detection.get("rescue_decision", "DISPATCH_FIRST_RESPONDER_TEAM"),
                now_str,
                now_str
            ))

        conn.commit()
        conn.close()
        return victim_id

    def get_all_victims(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM victims ORDER BY risk_score DESC, victim_id ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def update_victim_status(self, victim_id: str, new_status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        cursor.execute("UPDATE victims SET status = ?, last_updated = ? WHERE victim_id = ?",
                       (new_status, now_str, victim_id))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_all_hazards(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hazards")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_summary_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM victims")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM victims WHERE status = 'Rescued'")
        rescued = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM victims WHERE status = 'Pending'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM victims WHERE severity = 'CRITICAL' AND status != 'Rescued'")
        critical = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM victims WHERE severity = 'HIGH' AND status != 'Rescued'")
        high = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM hazards")
        hazards = cursor.fetchone()[0]

        conn.close()
        return {
            "total_victims": total,
            "rescued_count": rescued,
            "pending_count": pending,
            "critical_count": critical,
            "high_count": high,
            "active_hazards": hazards
        }
