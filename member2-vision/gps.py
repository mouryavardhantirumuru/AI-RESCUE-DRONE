import math

class GPSTracker:
    def __init__(self, base_lat=13.0827, base_lon=80.2707):
        self.base_lat = base_lat
        self.base_lon = base_lon
        
    def get_drone_position(self, frame_index):
        """Simulates realistic drone hover / circular patrol path."""
        t = frame_index * 0.015
        drone_lat = round(self.base_lat + 0.00012 * math.sin(t), 6)
        drone_lon = round(self.base_lon + 0.00015 * math.cos(t), 6)
        return drone_lat, drone_lon

    def calculate_object_location(self, drone_lat, drone_lon, bbox, frame_shape):
        """
        Converts bounding box offset relative to frame center into estimated GPS coordinates.
        """
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        
        # Pixel delta from frame center
        dx = cx - (w / 2.0)
        dy = cy - (h / 2.0)
        
        # Ground sampling: ~0.05 meters per pixel at ~25m drone altitude
        meters_per_pixel = 0.05
        offset_east_m = dx * meters_per_pixel
        offset_north_m = -dy * meters_per_pixel
        
        # 1 deg latitude ~ 111,000 meters
        deg_lat_per_m = 1.0 / 111000.0
        deg_lon_per_m = 1.0 / (111000.0 * math.cos(math.radians(drone_lat)))
        
        obj_lat = round(drone_lat + (offset_north_m * deg_lat_per_m), 6)
        obj_lon = round(drone_lon + (offset_east_m * deg_lon_per_m), 6)
        
        return obj_lat, obj_lon
