import os
import datetime

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def now_ist_str():
    """Current India time as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

def _secret(name, default=""):
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)

MQTT_BROKER = _secret("MQTT_BROKER", "")
MQTT_PORT = int(_secret("MQTT_PORT", 8883))
MQTT_USE_TLS = str(_secret("MQTT_USE_TLS", "True")).lower() == "true"
MQTT_USERNAME = _secret("MQTT_USERNAME", "")
MQTT_PASSWORD = _secret("MQTT_PASSWORD", "")
# MQTT Topics
# Topic where simulated smart meter publishes raw sensor readings
TOPIC_RAW_DATA = "smartmeter/SM001/data"

# Topic where AI/ML detector publishes processed anomaly results & alerts
TOPIC_ANOMALY_ALERTS = "smartmeter/SM001/alerts"

# Database Configuration (SQLite as per Whiteboard Architecture Layer 3-5)
DB_PATH = "smartmeter_history.db"

# Simulation Settings
METER_ID = "SM001"
PUBLISH_INTERVAL_SEC = 2.0  # Send reading every 2 seconds
