"""
AI-Based Smart Meter Consumption Anomaly Detector
Subscribes to HiveMQ smart meter telemetry, performs real-time AI/ML inference,
stores data in SQLite, and publishes anomaly alerts back to HiveMQ.
"""

import os
import json
import random
import datetime
import pandas as pd
import joblib
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USE_TLS,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TOPIC_RAW_DATA,
    TOPIC_ANOMALY_ALERTS,
    DB_PATH
)
from database import init_db, log_telemetry, log_anomaly
from train_baseline_model import train_and_save_model

MODEL_PATH = "isolation_forest_model.joblib"

class AnomalyDetector:
    def __init__(self):
        # 1. Initialize SQLite database
        init_db()
        print(f"[DB] SQLite database active at '{DB_PATH}'.")

        # 2. Load trained AI Isolation Forest model
        if not os.path.exists(MODEL_PATH):
            print(f"[AI] Model '{MODEL_PATH}' not found. Training baseline model now...")
            train_and_save_model(MODEL_PATH)

        self.model = joblib.load(MODEL_PATH)
        print(f"[AI] Scikit-Learn IsolationForest model loaded successfully.")

    def evaluate(self, telemetry: dict) -> dict:
        """
        Runs ML prediction and domain rule classification on incoming smart meter telemetry.
        Returns enriched alert/status dictionary.
        """
        v = float(telemetry.get("voltage", 230.0))
        c = float(telemetry.get("current", 0.0))
        p = float(telemetry.get("power_kw", 0.0))
        pf = float(telemetry.get("power_factor", 0.95))
        timestamp = telemetry.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        meter_id = telemetry.get("meter_id", "SM001")
        energy_kwh = float(telemetry.get("energy_kwh", 0.0))

        # 1. ML Feature Vector
        features = ["voltage", "current", "power_kw", "power_factor"]
        X = pd.DataFrame([{
            "voltage": v,
            "current": c,
            "power_kw": p,
            "power_factor": pf
        }], columns=features)

        # 2. Isolation Forest Inference
        ml_prediction = int(self.model.predict(X)[0])  # 1 = Normal, -1 = Anomaly
        ml_score = round(float(self.model.decision_function(X)[0]), 4)

        # 3. Transparent Domain Classification & Anomaly Typing
        is_anomaly = False
        anomaly_type = "Normal Operation"
        severity = "NORMAL"
        description = "Consumption within standard residential baseline."

        if p >= 7.0 or c >= 30.0:
            is_anomaly = True
            anomaly_type = "Overload / Power Surge"
            severity = "CRITICAL"
            description = f"Dangerous power spike ({p:.2f} kW, {c:.1f} A). Risk of line tripping or equipment fault."

        elif v <= 180.0:
            is_anomaly = True
            anomaly_type = "Severe Voltage Sag"
            severity = "HIGH"
            description = f"Line voltage dropped to {v:.1f} V. Brownout condition detected."

        elif v >= 265.0:
            is_anomaly = True
            anomaly_type = "Severe Over-Voltage Spike"
            severity = "HIGH"
            description = f"Line voltage exceeded safe threshold ({v:.1f} V)."

        elif p <= 0.08 and v >= 210.0:
            is_anomaly = True
            anomaly_type = "Power Theft / Meter Tamper"
            severity = "CRITICAL"
            description = f"Meter bypassed or shunt connected. Voltage present ({v:.1f}V) but consumption is near zero ({p:.3f} kW)."

        elif ml_prediction == -1:
            is_anomaly = True
            anomaly_type = "Unusual Consumption Pattern (AI Flag)"
            severity = "MEDIUM"
            description = f"Isolation Forest identified abnormal combination of power ({p:.2f} kW) and current ({c:.1f} A)."

        result = {
            "meter_id": meter_id,
            "timestamp": timestamp,
            "voltage": v,
            "current": c,
            "power_kw": p,
            "energy_kwh": energy_kwh,
            "power_factor": pf,
            "is_anomaly": is_anomaly,
            "anomaly_score": ml_score,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "description": description
        }
        return result

def run_detector():
    """Main subscriber loop: Listens to HiveMQ, evaluates with AI, logs to DB, publishes alert."""
    print("=" * 65)
    print("     AI SMART METER ANOMALY DETECTOR ENGINE (VS CODE)    ")
    print("=" * 65)
    print(f"HiveMQ Broker:      {MQTT_BROKER}:{MQTT_PORT} (TLS: {MQTT_USE_TLS})")
    print(f"Subscribed Topic:   {TOPIC_RAW_DATA}")
    print(f"Publish Alert Topic:{TOPIC_ANOMALY_ALERTS}")
    print(f"Database:           {DB_PATH}")
    print("-" * 65)

    detector = AnomalyDetector()

    # Configure MQTT Client
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"SmartMeter_AI_Engine_{random.randint(1000, 9999)}"
    )

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    if MQTT_USE_TLS:
        client.tls_set()

    def on_connect(c, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[OK] Connected to HiveMQ Broker! Subscribing to '{TOPIC_RAW_DATA}'...")
            c.subscribe(TOPIC_RAW_DATA, qos=0)
            print("[OK] Ready and waiting for smart meter telemetry...\n")
        else:
            print(f"[ERROR] MQTT connection failed with return code {rc}")

    def on_message(c, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            
            # 1. Run AI Evaluation
            result = detector.evaluate(payload)

            # 2. Log to SQLite (Layer 3 & 4 architecture)
            log_telemetry(payload)
            if result["is_anomaly"]:
                log_anomaly(result)

            # 3. Publish processed alert / status back to HiveMQ for Node-RED Dashboard
            c.publish(TOPIC_ANOMALY_ALERTS, json.dumps(result), qos=0)

            # 4. Print clean console status
            tag = " [!! ANOMALY !!] " if result["is_anomaly"] else " [   NORMAL   ] "
            print(f"{result['timestamp']} |{tag}| "
                  f"{result['power_kw']:>5.2f} kW | {result['voltage']:>5.1f} V | "
                  f"Score: {result['anomaly_score']:>6.3f} | {result['anomaly_type']}")

            if result["is_anomaly"]:
                print(f"      --> Alert: {result['description']} (Severity: {result['severity']})")

        except Exception as err:
            print(f"[ERROR] Failed processing MQTT message: {err}")

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping AI Anomaly Detector...")
    finally:
        client.disconnect()
        print("Disconnected from HiveMQ.")

def start_detector_background():
    """Non-blocking version for use inside Streamlit."""
    detector = AnomalyDetector()
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"SmartMeter_AI_Engine_{random.randint(1000, 9999)}"
    )
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    if MQTT_USE_TLS:
        client.tls_set()

    def on_connect(c, userdata, flags, rc, properties=None):
        if rc == 0:
            c.subscribe(TOPIC_RAW_DATA, qos=0)

    def on_message(c, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            result = detector.evaluate(payload)
            log_telemetry(payload)
            if result["is_anomaly"]:
                log_anomaly(result)
            c.publish(TOPIC_ANOMALY_ALERTS, json.dumps(result), qos=0)
        except Exception as err:
            print(f"[ERROR] Failed processing MQTT message: {err}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client

if __name__ == "__main__":
    run_detector()
