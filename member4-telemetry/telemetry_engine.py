import math
import time
import datetime

class DroneTelemetryEngine:
    """
    Member 4 - AI Rescue Drone
    Flight Telemetry & Mission Control Engine.
    Simulates:
    - Real-time GPS flight path with autonomous lawnmower search grid
    - Altitude, Ground Speed, Heading, Pitch & Roll
    - Battery power management & consumption curves
    - Flight Modes (SEARCH_AND_RESCUE, HOVER, RTL, EMERGENCY_LAND)
    - Breadcrumb trajectory tracking for interactive satellite map
    """

    def __init__(self, base_lat=13.0827, base_lon=80.2707, base_alt=30.0):
        self.drone_id = "DRONE01"
        self.home_lat = base_lat
        self.home_lon = base_lon
        self.current_lat = base_lat
        self.current_lon = base_lon
        self.altitude_m = base_alt
        self.target_altitude_m = base_alt
        self.speed_mps = 7.5
        self.heading_deg = 45.0
        self.battery_pct = 88.0
        self.battery_voltage = 22.8 # 6S LiPo
        self.flight_mode = "SEARCH_AND_RESCUE"
        self.gps_satellites = 14
        self.signal_strength_dbm = -64
        self.is_armed = True
        self.is_searching = True
        self.flight_time_sec = 0
        self.breadcrumbs = [] # [(lat, lon, alt)]
        self.step_counter = 0

    def set_flight_mode(self, mode: str):
        valid_modes = ["SEARCH_AND_RESCUE", "HOVER", "RTL", "MANUAL", "EMERGENCY_LAND"]
        if mode.upper() in valid_modes:
            self.flight_mode = mode.upper()
            if self.flight_mode == "RTL":
                self.is_searching = False
            elif self.flight_mode == "SEARCH_AND_RESCUE":
                self.is_searching = True
            return True, f"Flight mode set to {self.flight_mode}"
        return False, "Invalid flight mode"

    def toggle_search(self):
        self.is_searching = not self.is_searching
        if self.is_searching:
            self.flight_mode = "SEARCH_AND_RESCUE"
        else:
            self.flight_mode = "HOVER"
        return self.is_searching

    def return_to_launch(self):
        self.flight_mode = "RTL"
        self.is_searching = False
        return "RTL Mode Activated. Navigating to Home Coordinates."

    def tick(self, dt=1.0):
        """Advances physical telemetry state by dt seconds."""
        self.step_counter += 1
        self.flight_time_sec += int(dt)

        # Battery consumption model: ~0.04% per second in flight
        if self.battery_pct > 5.0:
            drain = 0.035 * dt
            if self.speed_mps > 10.0:
                drain *= 1.3
            self.battery_pct = max(0.0, round(self.battery_pct - drain, 2))
            self.battery_voltage = round(19.5 + (self.battery_pct / 100.0) * 4.5, 2)

        # Flight dynamics according to Mode
        if self.flight_mode == "SEARCH_AND_RESCUE":
            # Lawnmower sweeping search pattern over disaster sector
            t = self.step_counter * 0.03
            sweep_x = 0.00035 * math.sin(t)
            sweep_y = 0.00025 * math.cos(t * 0.5)
            self.current_lat = round(self.home_lat + sweep_y, 6)
            self.current_lon = round(self.home_lon + sweep_x, 6)
            self.altitude_m = round(self.target_altitude_m + 0.8 * math.sin(t * 1.5), 1)
            self.speed_mps = round(6.5 + 1.2 * math.cos(t * 0.8), 1)
            # Heading aligns with velocity vector
            self.heading_deg = round((math.degrees(math.atan2(sweep_x, sweep_y)) + 360) % 360, 1)

        elif self.flight_mode == "RTL":
            # Smoothly interpolate back to home
            d_lat = self.home_lat - self.current_lat
            d_lon = self.home_lon - self.current_lon
            dist_to_home = math.sqrt(d_lat**2 + d_lon**2)

            if dist_to_home > 0.00005:
                step_rate = 0.00003 * dt
                self.current_lat += (d_lat / dist_to_home) * step_rate
                self.current_lon += (d_lon / dist_to_home) * step_rate
                self.speed_mps = 9.0
                self.heading_deg = round((math.degrees(math.atan2(d_lon, d_lat)) + 360) % 360, 1)
            else:
                self.current_lat = self.home_lat
                self.current_lon = self.home_lon
                self.speed_mps = 0.0
                self.flight_mode = "HOVER"

        elif self.flight_mode == "HOVER":
            # Subtle hovering micro-drift
            t = self.step_counter * 0.05
            self.current_lat = round(self.current_lat + 0.000005 * math.sin(t), 6)
            self.current_lon = round(self.current_lon + 0.000005 * math.cos(t), 6)
            self.speed_mps = round(0.2 + 0.1 * math.sin(t), 1)

        # Record breadcrumb every 5 seconds (cap at 120 points for fast rendering)
        if self.step_counter % 5 == 0:
            self.breadcrumbs.append([self.current_lat, self.current_lon, self.altitude_m])
            if len(self.breadcrumbs) > 120:
                self.breadcrumbs.pop(0)

        return self.get_telemetry()

    def get_telemetry(self):
        """Returns standard telemetry packet."""
        return {
            "drone_id": self.drone_id,
            "status": "Searching" if self.is_searching else self.flight_mode.capitalize(),
            "flight_mode": self.flight_mode,
            "armed": self.is_armed,
            "latitude": self.current_lat,
            "longitude": self.current_lon,
            "home_latitude": self.home_lat,
            "home_longitude": self.home_lon,
            "altitude_m": self.altitude_m,
            "speed_mps": self.speed_mps,
            "heading_deg": self.heading_deg,
            "battery_pct": round(self.battery_pct, 1),
            "battery_voltage": self.battery_voltage,
            "satellites": self.gps_satellites,
            "signal_dbm": self.signal_strength_dbm,
            "flight_time_sec": self.flight_time_sec,
            "formatted_flight_time": f"{self.flight_time_sec // 60:02d}:{self.flight_time_sec % 60:02d}",
            "breadcrumbs": self.breadcrumbs[-40:],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == "__main__":
    t = DroneTelemetryEngine()
    print("Initial Telemetry:")
    import json
    print(json.dumps(t.tick(), indent=2))
