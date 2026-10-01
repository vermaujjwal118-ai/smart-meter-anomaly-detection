"""
Main Launcher for Smart Meter Anomaly Detection Project
Provides an interactive menu to run the Simulator, AI Detector, or both in VS Code.
"""

import sys
import os
import time
import subprocess
import threading
import sqlite3
from config import DB_PATH

def print_banner():
    print("""
======================================================================
     AI-BASED SMART METER CONSUMPTION ANOMALY DETECTION SYSTEM
======================================================================
 Architecture:
  Synthetic Meter -> HiveMQ MQTT -> AI Engine (ML) -> SQLite -> Node-RED
======================================================================
 [1] Run Complete System (Simulator + AI Detector together)
 [2] Run Smart Meter Simulator Only (Publishes to HiveMQ)
 [3] Run AI Anomaly Detector Only (Scikit-Learn ML Inference)
 [4] Train / Re-train AI Baseline Model (Isolation Forest)
 [5] View SQLite Anomaly History & Statistics
 [6] Start Node-RED Server
 [7] Start Streamlit Dashboard Web App
 [0] Exit
======================================================================
""")

def run_both():
    """Runs the simulator and AI detector concurrently."""
    print("\nStarting AI Detector and Simulator concurrently...\n")
    detector_process = subprocess.Popen([sys.executable, "-u", "ai_anomaly_detector.py"])
    time.sleep(2)  # Give detector a moment to connect and subscribe
    sim_process = subprocess.Popen([sys.executable, "-u", "smart_meter_simulator.py"])

    try:
        detector_process.wait()
        sim_process.wait()
    except KeyboardInterrupt:
        print("\nTerminating processes...")
        detector_process.terminate()
        sim_process.terminate()
        print("Done.")

def view_history():
    """Reads and displays recent anomaly events stored in SQLite."""
    if not os.path.exists(DB_PATH):
        print(f"\n[!] Database '{DB_PATH}' does not exist yet. Run the system to log data.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM meter_telemetry")
    total_telemetry = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM anomaly_logs")
    total_anomalies = cursor.fetchone()[0]

    print(f"\n--- SQLite Database Summary ---")
    print(f"Total Telemetry Readings Logged: {total_telemetry}")
    print(f"Total Anomalies Detected:        {total_anomalies}")
    print("-" * 70)

    cursor.execute("""
        SELECT timestamp, power_kw, voltage, anomaly_type, severity, description
        FROM anomaly_logs
        ORDER BY id DESC LIMIT 10
    """)
    rows = cursor.fetchall()
    if not rows:
        print("No anomalies logged yet.")
    else:
        print(f"{'Timestamp':<20} | {'Power':<7} | {'Volt':<6} | {'Severity':<8} | {'Anomaly Type'}")
        print("-" * 70)
        for r in rows:
            print(f"{r[0]:<20} | {r[1]:>5.2f}kW | {r[2]:>4.1f}V | {r[4]:<8} | {r[3]}")

    print("\n--- Recent Security Audit Trail (Layer 5) ---")
    cursor.execute("""
        SELECT timestamp, event_type, severity, user, details
        FROM security_logs
        ORDER BY id DESC LIMIT 5
    """)
    s_rows = cursor.fetchall()
    if not s_rows:
        print("No security audit logs recorded yet.")
    else:
        print(f"{'Timestamp':<20} | {'Event':<18} | {'User':<10} | {'Details'}")
        print("-" * 70)
        for sr in s_rows:
            print(f"{sr[0]:<20} | {sr[1]:<18} | {sr[3]:<10} | {sr[4]}")

    conn.close()

def start_nodered():
    """Starts Node-RED from terminal."""
    print("\nStarting Node-RED...")
    print("Once started, open your browser at: http://localhost:1880")
    print("Dashboard UI is available at:       http://localhost:1880/ui\n")
    subprocess.call("cmd.exe /c node-red", shell=True)

def start_streamlit():
    """Starts Streamlit web dashboard."""
    print("\nStarting Streamlit Dashboard...")
    print("Dashboard will open in your browser automatically at: http://localhost:8501\n")
    subprocess.call([sys.executable, "-m", "streamlit", "run", "dashboard_streamlit.py"])

def main():
    while True:
        print_banner()
        choice = input("Select an option (0-7): ").strip()

        if choice == "1":
            run_both()
        elif choice == "2":
            subprocess.run([sys.executable, "smart_meter_simulator.py"])
        elif choice == "3":
            subprocess.run([sys.executable, "ai_anomaly_detector.py"])
        elif choice == "4":
            subprocess.run([sys.executable, "train_baseline_model.py"])
        elif choice == "5":
            view_history()
            input("\nPress Enter to return to menu...")
        elif choice == "6":
            start_nodered()
        elif choice == "7":
            start_streamlit()
        elif choice == "0":
            print("\nExiting. Thank you!")
            break
        else:
            print("\n[!] Invalid choice. Please select 0 to 7.")

if __name__ == "__main__":
    main()
