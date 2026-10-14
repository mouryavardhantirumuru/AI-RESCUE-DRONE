class DisasterTracker:
    def __init__(self):
        self.hazard_counter = 0
        self.hazard_registry = {}

    def resolve_track_id(self, detection):
        """
        Resolves track_id:
        - For 'person': returns persistent integer track_id as string (e.g. '12')
        - For hazards: returns structured disaster hazard ID (e.g. 'H01', 'H02')
        """
        obj_type = detection.get("object_type", "person")
        track_id = detection.get("track_id")
        
        if obj_type == "person":
            if track_id is not None:
                return str(track_id)
            return "1"
        else:
            # Spatial key based on coarse bbox grid
            bbox = detection.get("bbox", [0, 0, 0, 0])
            grid_key = (detection.get("hazard_type", "hazard"), bbox[0] // 40, bbox[1] // 40)
            if grid_key in self.hazard_registry:
                return self.hazard_registry[grid_key]
            
            self.hazard_counter += 1
            hid = f"H{self.hazard_counter:02d}"
            self.hazard_registry[grid_key] = hid
            return hid
