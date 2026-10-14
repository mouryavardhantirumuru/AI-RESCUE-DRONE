import cv2
import json
import time
import os
import argparse
import config
from detector import RescueDetector
from tracker import DisasterTracker
from thermal import simulate_thermal, check_thermal_confirmation
from gps import GPSTracker
from api_client import Member5Client

def parse_args():
    parser = argparse.ArgumentParser(description="AI Rescue Drone - Member 2 Vision Subsystem")
    parser.add_argument("--source", type=str, default=None, help="Path to video file or webcam index (0)")
    parser.add_argument("--model", type=str, default=config.MODEL_PATH, help="Path to YOLO best.pt weights")
    parser.add_argument("--host", type=str, default=config.MEMBER5_HOST, help="Member 5 FastAPI Host IP")
    parser.add_argument("--port", type=int, default=config.MEMBER5_PORT, help="Member 5 FastAPI Port")
    parser.add_argument("--headless", action="store_true", help="Run without GUI display window")
    parser.add_argument("--max-frames", type=int, default=None, help="Stop after N frames (useful for automated testing)")
    return parser.parse_args()

def main():
    args = parse_args()

    # Configure FastAPI endpoint from CLI or config
    api_url = f"http://{args.host}:{args.port}/detection/"

    print("=" * 65)
    print("  AI RESCUE DRONE - MEMBER 2: VISION & SENSING SUBSYSTEM")
    print(f"  Drone ID:         {config.DRONE_ID}")
    print(f"  Model Path:       {args.model}")
    print(f"  Member 5 FastAPI: {api_url}")
    print(f"  Headless Mode:    {args.headless}")
    print("=" * 65)

    # 1. Initialize Subsystems
    detector = RescueDetector(args.model)
    tracker = DisasterTracker()
    gps = GPSTracker(config.BASE_LATITUDE, config.BASE_LONGITUDE)
    api_client = Member5Client(api_url)

    # 2. Determine Video Source
    if args.source is not None:
        video_src = int(args.source) if args.source.isdigit() else args.source
    elif os.path.exists(config.TEST_VIDEO_PATH):
        video_src = config.TEST_VIDEO_PATH
    else:
        video_src = 0

    print(f"[Vision] Initializing video source: {video_src}")
    cap = cv2.VideoCapture(video_src)
    if not cap.isOpened():
        print(f"[Error] Failed to open video source: {video_src}")
        return

    frame_idx = 0
    fps_start_time = time.time()
    fps = 0.0

    print("\n[Vision] Pipeline running. (Press 'q' in video window or Ctrl+C in terminal to stop)\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                # Loop video for continuous presentation
                if isinstance(video_src, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                if not ret:
                    break

            frame_idx += 1
            if args.max_frames and frame_idx > args.max_frames:
                print(f"[Vision] Reached maximum frame count ({args.max_frames}).")
                break

            h, w = frame.shape[:2]

            # Calculate FPS
            if frame_idx % 10 == 0:
                elapsed = time.time() - fps_start_time
                if elapsed > 0:
                    fps = 10.0 / elapsed
                fps_start_time = time.time()

            # Step 8: Simulated Thermal / Infrared Feed
            thermal_frame = simulate_thermal(frame)

            # Step 10: Drone GPS update
            drone_lat, drone_lon = gps.get_drone_position(frame_idx)

            # Step 4, 6 & 7: YOLO Tracking & Class Detection
            detections = detector.track(frame)

            # Process Detections
            for det in detections:
                class_name = det["class_name"].lower()
                confidence = det["confidence"]
                bbox = det["bbox"]
                track_id_raw = det.get("track_id")

                # Step 7: Classify Person vs Hazard
                if class_name == "person":
                    object_type = "person"
                    hazard_type = "none"
                elif class_name in config.HAZARD_CLASSES or "fire" in class_name or "smoke" in class_name:
                    object_type = "hazard"
                    hazard_type = class_name
                else:
                    object_type = class_name
                    hazard_type = "none"

                # Step 9: Thermal Confirmation
                thermal_confirmed = check_thermal_confirmation(frame, bbox)

                # Step 10: Object GPS Location
                obj_lat, obj_lon = gps.calculate_object_location(drone_lat, drone_lon, bbox, (h, w))

                # Step 6: Persistent Tracking ID Resolution
                det_info = {
                    "object_type": object_type,
                    "hazard_type": hazard_type,
                    "track_id": track_id_raw,
                    "bbox": bbox
                }
                track_id = tracker.resolve_track_id(det_info)

                # Step 11: Member 2 JSON Output
                member2_json = {
                    "drone_id": config.DRONE_ID,
                    "track_id": str(track_id),
                    "object_type": object_type,
                    "hazard_type": hazard_type,
                    "confidence": confidence,
                    "thermal_detected": thermal_confirmed,
                    "latitude": obj_lat,
                    "longitude": obj_lon
                }

                # Print formatted JSON as required by Step 11
                print(f"[MEMBER 2 JSON] {json.dumps(member2_json)}")

                # Step 12: Send payload to Member 5 FastAPI (throttled every 5 frames)
                if frame_idx % 5 == 0:
                    api_client.send_detection(member2_json)

                # Visual annotations on RGB
                x1, y1, x2, y2 = bbox
                color = (0, 255, 0) if object_type == "person" else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{track_id} {object_type} {confidence:.2f} [IR:{'YES' if thermal_confirmed else 'NO'}]"
                cv2.putText(frame, label, (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

                # Visual annotations on Thermal Frame
                cv2.rectangle(thermal_frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
                cv2.putText(thermal_frame, f"IR ID:{track_id}", (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Display GUI if not in headless mode
            if not args.headless:
                # Telemetry HUD on RGB
                cv2.rectangle(frame, (10, 10), (370, 95), (15, 23, 42), -1)
                cv2.putText(frame, f"AI RESCUE DRONE - {config.DRONE_ID}", (20, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (59, 130, 246), 2)
                cv2.putText(frame, f"GPS: {drone_lat:.6f}, {drone_lon:.6f} | FPS: {fps:.1f}", (20, 56),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (203, 213, 225), 1)
                api_text = "API: Member 5 CONNECTED" if api_client.connected else "API: Standalone / Offline"
                api_color = (34, 197, 94) if api_client.connected else (245, 158, 11)
                cv2.putText(frame, api_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, api_color, 1)

                # Side-by-Side Dual Display (RGB | Thermal)
                display_w = 640
                display_h = 360
                rgb_resized = cv2.resize(frame, (display_w, display_h))
                thermal_resized = cv2.resize(thermal_frame, (display_w, display_h))

                cv2.putText(rgb_resized, "RGB CAMERA / YOLOv8 TRACKING", (15, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                cv2.putText(thermal_resized, "SIMULATED IR THERMAL (INFERNO)", (15, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 215, 255), 2)

                dual_view = cv2.hconcat([rgb_resized, thermal_resized])
                try:
                    cv2.imshow("AI Rescue Drone - Member 2 Vision Subsystem", dual_view)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except cv2.error:
                    pass

    except KeyboardInterrupt:
        print("\n[Vision] Interrupted by user.")
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        print("[Vision] Pipeline shutdown cleanly.")

if __name__ == "__main__":
    main()
