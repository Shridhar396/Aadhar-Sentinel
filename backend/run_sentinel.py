import subprocess
import time
import sys
import os

def run_sentinel():
    print("🛰️ INITIALIZING AADHAAR SENTINEL SYSTEM...")
    
    # 1. Start the Flask Backend (app.py)
    # This runs the API that handles all the data merging and orchestration logic
    print("🚀 Starting Sentinel API (app.py)...")
    backend_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Give the backend a few seconds to load the large CSV files
    time.sleep(5)
    
    # Check if backend is running
    if backend_process.poll() is not None:
        print("❌ Error: app.py failed to start. Check your CSV file paths.")
        return

    print("✅ Backend is Live.")

    # 2. Start the Streamlit Dashboard (dashboard.py)
    # This launches the Command Center UI
    print("🌍 Launching Sentinel Command Center (dashboard.py)...")
    try:
        subprocess.run(["streamlit", "run", "dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Sentinel System...")
    finally:
        # Cleanup: Ensure backend is killed when you close the dashboard
        backend_process.terminate()
        print("✅ System offline.")

if __name__ == "__main__":
    run_sentinel()