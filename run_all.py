import os
import sys
import time
import subprocess
import webbrowser
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def print_banner():
    print("""
========================================================================
   ___   ____   ____  ____ _____ _   _ _____   ____  ____   ___  _   _ _____ 
  / _ \ |_  /  |  _ \| ____/ ___| | | | ____| |  _ \|  _ \ / _ \| \ | | ____|
 / /_\ \ / /   | |_) |  _| \___ \| | | |  _|   | | | | |_) | | | |  \| |  _|  
|  _  |/ /___  |  _ <| |___ ___) | |_| | |___  | |_| |  _ <| |_| | |\  | |___ 
|_| |_/_____|  |_| \_\_____|____/ \___/|_____| |____/|_| \_\\___/|_| \_|_____|
                                                                                
      DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING • SIH PROJECT
========================================================================
    [*] Member 2: Vision & Sensing (YOLOv8 + ByteTrack + Simulated IR)
    [*] Member 3: Severity, Risk & Priority Engine (Active in Backend)
    [*] Member 4: Drone Dynamics & Flight Telemetry Simulator
    [*] Member 5: Central FastAPI Platform & SQLite Database
    [*] Web Dashboard: Interactive Satellite GPS Map & Dual Feeds
========================================================================
""")

def main():
    print_banner()

    server_dir = os.path.join(BASE_DIR, "member5-backend")
    vision_dir = os.path.join(BASE_DIR, "member2-vision")

    # 1. Start Member 5 Backend & Web Dashboard Server
    print("[1/3] Starting Central FastAPI Platform & Database (Member 5)...")
    server_cmd = [sys.executable, "server.py"]
    server_proc = subprocess.Popen(
        server_cmd,
        cwd=server_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Wait for server to bind port
    time.sleep(2.0)
    print("      >> Server online at: http://localhost:8000")
    print("      >> API Documentation: http://localhost:8000/docs")

    # 2. Launch Web Dashboard in default browser
    print("[2/3] Launching Mission Control Web Dashboard...")
    try:
        webbrowser.open("http://localhost:8000")
    except Exception as e:
        print(f"      [Notice] Open http://localhost:8000 manually in browser: {e}")

    # 3. Start Member 2 Vision Subsystem (with Member 3 Risk integration)
    print("[3/3] Starting Member 2 Vision & Tracking Pipeline...")
    vision_cmd = [sys.executable, "main.py", "--host", "127.0.0.1", "--port", "8000"]
    # If run in background or headless, user can pass --headless
    if "--headless" in sys.argv:
        vision_cmd.append("--headless")

    vision_proc = subprocess.Popen(
        vision_cmd,
        cwd=vision_dir
    )

    print("\n========================================================================")
    print("  ALL SUBSYSTEMS RUNNING! Press Ctrl+C anytime to stop all services.")
    print("========================================================================\n")

    try:
        while True:
            # Poll if server is still alive
            if server_proc.poll() is not None:
                print("[Warning] Server process terminated.")
                break
            if vision_proc.poll() is not None:
                print("[Warning] Vision process completed or closed.")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down AI Rescue Drone subsystems gracefully...")
    finally:
        try:
            vision_proc.terminate()
            vision_proc.wait(timeout=3)
        except Exception:
            try:
                vision_proc.kill()
            except Exception:
                pass

        try:
            server_proc.terminate()
            server_proc.wait(timeout=3)
        except Exception:
            try:
                server_proc.kill()
            except Exception:
                pass

        print("[*] All processes terminated cleanly. Goodbye!\n")

if __name__ == "__main__":
    main()
