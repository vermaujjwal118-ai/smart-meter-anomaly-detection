import json, paho.mqtt.publish as publish
from config import *

print("Broker:", MQTT_BROKER, MQTT_PORT, "TLS:", MQTT_USE_TLS)
publish.single(
    TOPIC_RAW_DATA,
    json.dumps({"meter_id": "SM001", "timestamp": "2026-10-01 10:00:00",
                "voltage": 226.0, "current": 44.2, "power_kw": 9.5,
                "energy_kwh": 125.6, "power_factor": 0.95, "frequency": 50.0}),
    qos=1, hostname=MQTT_BROKER, port=MQTT_PORT,
    auth={"username": MQTT_USERNAME, "password": MQTT_PASSWORD},
    tls={},
)
print("PUBLISHED OK")