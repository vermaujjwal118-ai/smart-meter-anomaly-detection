"""
Replays REAL building readings (Kaggle LEAD dataset) through the existing
MQTT pipeline, in the same message format as smart_meter_simulator.py.
Voltage, power factor and frequency are not in the dataset, so they are simulated.
Runs forever: when the data ends, it starts again from the beginning.
"""
import os
import json
import time
import random
import datetime
import pandas as pd
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_USE_TLS,
    MQTT_USERNAME, MQTT_PASSWORD, TOPIC_RAW_DATA, METER_ID
)

# ---------- settings you can change ----------
BUILDING_ID = 55        # which building to replay
DELAY_SEC = 0.5         # seconds between messages (smaller = faster)
LEAD_IN = 30            # normal readings shown before the first anomaly
DEMO_BOOST_ANOMALIES = False   # True = replace anomaly readings with fake 8-12 kW spikes
# ---------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "sample.csv"), parse_dates=["timestamp"])
b = df[df["building_id"] == BUILDING_ID].sort_values("timestamp").reset_index(drop=True)

# Scale so a typical hour is about 1.5 kW (like the simulator's normal range)
median = b.loc[b["meter_reading"] > 0, "meter_reading"].median()
scale = 1.5 / median

# Start a little before the first anomaly, then go through ALL rows
first_anomaly = int(b.index[b["anomaly"] == 1][0])
start = max(0, first_anomaly - LEAD_IN)
b = pd.concat([b.iloc[start:], b.iloc[:start]]).reset_index(drop=True)

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"SmartMeter_Replay_{random.randint(1000, 9999)}"
)
if MQTT_USERNAME and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
if MQTT_USE_TLS:
    client.tls_set()
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_start()

energy = 125.40
print(f"Replaying {len(b)} real readings of building {BUILDING_ID} in a loop (scale x{scale:.4f})")

try:
    while True:
        for _, row in b.iterrows():
            power_kw = max(round(float(row["meter_reading"]) * scale, 2), 0.30)
            if DEMO_BOOST_ANOMALIES and row["anomaly"] == 1:
                power_kw = round(random.uniform(8.5, 12.0), 2)
            voltage = round(random.gauss(230.0, 2.5), 1)
            pf = round(random.uniform(0.93, 0.98), 2)
            current = round((power_kw * 1000.0) / (voltage * pf), 2)
            energy += power_kw          # one reading = one hour of data
            msg = {
                "meter_id": METER_ID,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            label = "REAL ANOMALY" if msg["true_anomaly"] else "normal"
            print(f"{row['timestamp']} | {power_kw:>6.2f} kW | {label}")
            time.sleep(DELAY_SEC)
        print("--- reached the end of the data, starting again ---")
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    client.loop_stop()
    client.disconnect()