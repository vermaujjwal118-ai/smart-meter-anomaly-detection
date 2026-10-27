"""
Background replay of REAL LEAD readings for the cloud dashboard.
Started by dashboard_streamlit.py only when the Streamlit secret CLOUD_REPLAY is "true".
"""
import os
import json
import time
import random
import threading
import pandas as pd
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_USE_TLS,
    MQTT_USERNAME, MQTT_PASSWORD, TOPIC_RAW_DATA, METER_ID, now_ist_str
)

BUILDING_ID = 55
DELAY_SEC = 0.5
LEAD_IN = 6                    # normal readings before the first anomaly
DEMO_BOOST_ANOMALIES = True    # anomaly readings become 8-12 kW spikes (demo only)


def _loop():
    here = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(here, "sample.csv"), parse_dates=["timestamp"])
    b = df[df["building_id"] == BUILDING_ID].sort_values("timestamp").reset_index(drop=True)
    median = b.loc[b["meter_reading"] > 0, "meter_reading"].median()
    scale = 1.5 / median
    first = int(b.index[b["anomaly"] == 1][0])
    start = max(0, first - LEAD_IN)
    b = pd.concat([b.iloc[start:], b.iloc[:start]]).reset_index(drop=True)

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"CloudReplay_{random.randint(1000, 9999)}"
    )
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    if MQTT_USE_TLS:
        client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    energy = 125.40
    while True:
        for _, row in b.iterrows():
            power_kw = max(round(float(row["meter_reading"]) * scale, 2), 0.30)
            if DEMO_BOOST_ANOMALIES and row["anomaly"] == 1:
                power_kw = round(random.uniform(8.5, 12.0), 2)
            voltage = round(random.gauss(230.0, 2.5), 1)
            pf = round(random.uniform(0.93, 0.98), 2)
            current = round((power_kw * 1000.0) / (voltage * pf), 2)
            energy += power_kw
            msg = {
                "meter_id": METER_ID,
                "timestamp": now_ist_str(),
                "voltage": voltage,
                "current": current,
                "power_kw": power_kw,
                "energy_kwh": round(energy, 3),
                "power_factor": pf,
                "frequency": round(random.gauss(50.0, 0.05), 2),
                "simulated_event": "Real data (LEAD building %d)" % BUILDING_ID,
                "true_anomaly": int(row["anomaly"]),
                "data_timestamp": row["timestamp"].isoformat(),
            }
            client.publish(TOPIC_RAW_DATA, json.dumps(msg), qos=0)
            time.sleep(DELAY_SEC)


def start_cloud_replay():
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t