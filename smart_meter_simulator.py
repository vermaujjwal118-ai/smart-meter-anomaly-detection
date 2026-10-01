"""
Smart Meter Synthetic Data Generator & MQTT Publisher
Publishes realistic IoT Smart Meter readings to HiveMQ broker.
Supports Normal Operation and Anomaly Injection modes:
- Normal residential consumption
- Sudden Power Surge / Overload
- Power Theft / Meter Tampering (Bypass)
- Voltage Sag / Brownout
"""

import time
import json
import random
import datetime
import paho.mqtt.client as mqtt
from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USE_TLS,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    TOPIC_RAW_DATA,
    METER_ID,
    PUBLISH_INTERVAL_SEC
)

class SmartMeterSimulator:
    def __init__(self, meter_id=METER_ID):
        self.meter_id = meter_id
        self.cumulative_kwh = 125.40  # initial cumulative reading
        self.last_time = time.time()
        
        # Simulation state
        self.mode = "AUTO"  # "AUTO", "NORMAL", "SURGE", "THEFT", "VOLTAGE_SAG"
        self.step_counter = 0

    def generate_reading(self):
        """Generates a realistic smart meter data packet based on the current mode."""
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        elapsed_hours = (time.time() - self.last_time) / 3600.0
        self.last_time = time.time()

        # In AUTO mode, rotate patterns: 10 normal -> 1 surge -> 10 normal -> 1 theft -> 10 normal -> 1 sag
        current_state = self.mode
        if self.mode == "AUTO":
            cycle = self.step_counter % 30
            if cycle == 10:
                current_state = "SURGE"
            elif cycle == 20:
                current_state = "THEFT"
            elif cycle == 28:
                current_state = "VOLTAGE_SAG"
            else:
                current_state = "NORMAL"

        self.step_counter += 1

        # Base electrical values
        frequency = round(random.gauss(50.0, 0.05), 2)
        power_factor = round(random.uniform(0.93, 0.98), 2)

        if current_state == "NORMAL":
            # Normal residential load: 0.4 kW to 3.5 kW
            voltage = round(random.gauss(230.0, 2.5), 1)
            power_kw = round(random.uniform(0.6, 2.8), 2)
            simulated_event = "Normal Operation"

        elif current_state == "SURGE":
            # Anomaly: Heavy Overload / Fault Spike (8.0 to 12.5 kW)
            voltage = round(random.gauss(226.0, 3.0), 1)
            power_kw = round(random.uniform(8.5, 12.0), 2)
            simulated_event = "Simulated Anomaly: Overload Surge"

        elif current_state == "THEFT":
            # Anomaly: Power Theft / Meter Bypass (Current bypassed, reads ~0 kW)
            voltage = round(random.gauss(231.0, 1.5), 1)
            power_kw = round(random.uniform(0.01, 0.05), 3)
            power_factor = 0.80
            simulated_event = "Simulated Anomaly: Power Theft / Meter Bypass"

        elif current_state == "VOLTAGE_SAG":
            # Anomaly: Grid Fault / Severe Voltage Drop (140V - 170V)
            voltage = round(random.uniform(145.0, 168.0), 1)
            power_kw = round(random.uniform(0.8, 1.5), 2)
            simulated_event = "Simulated Anomaly: Severe Voltage Sag"

        else:
            voltage = 230.0
            power_kw = 1.0
            simulated_event = "Normal Operation"

        # Calculate Current (Amperes): I = (P * 1000) / (V * PF)
        current = round((power_kw * 1000.0) / (voltage * power_factor), 2)
        
        # Accumulate energy (kWh)
        self.cumulative_kwh += round(power_kw * elapsed_hours, 5)

        payload = {
            "meter_id": self.meter_id,
            "timestamp": timestamp_str,
            "voltage": voltage,
            "current": current,
            "power_kw": power_kw,
            "energy_kwh": round(self.cumulative_kwh, 3),
            "power_factor": power_factor,
            "frequency": frequency,
            "simulated_event": simulated_event
        }
        return payload

def create_mqtt_client():
    """Configures and connects Paho MQTT client to HiveMQ."""
    # Using Paho MQTT v2 CallbackAPIVersion
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"SmartMeter_Sim_{random.randint(1000, 9999)}"
    )

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    if MQTT_USE_TLS:
        client.tls_set()

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[OK] Connected successfully to HiveMQ Broker ({MQTT_BROKER}:{MQTT_PORT})")
        else:
            print(f"[ERROR] Failed to connect to HiveMQ Broker. Return code: {rc}")

    client.on_connect = on_connect
    return client

def run_simulator(mode="AUTO"):
    """Main loop for publishing simulated smart meter data."""
    print("=" * 60)
    print(f"       SMART METER SIMULATOR (METER ID: {METER_ID})")
    print("=" * 60)
    print(f"Broker:    {MQTT_BROKER}:{MQTT_PORT} (TLS: {MQTT_USE_TLS})")
    print(f"Topic:     {TOPIC_RAW_DATA}")
    print(f"Interval:  {PUBLISH_INTERVAL_SEC} seconds")
    print(f"Mode:      {mode}")
    print("Press Ctrl+C to stop simulation.")
    print("-" * 60)

    meter = SmartMeterSimulator()
    meter.mode = mode

    client = create_mqtt_client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"[ERROR] Could not connect to HiveMQ: {e}")
        print("Tip: Check your internet connection or broker configuration in config.py")
        return

    try:
        while True:
            data = meter.generate_reading()
            json_payload = json.dumps(data)
            
            # Publish to HiveMQ
            client.publish(TOPIC_RAW_DATA, json_payload, qos=0)

            # Print to terminal
            event_tag = f"[{data['simulated_event']}]"
            print(f"{data['timestamp']} | {event_tag:<42} | "
                  f"{data['voltage']}V | {data['current']:>5}A | "
                  f"{data['power_kw']:>5} kW | Total: {data['energy_kwh']:.2f} kWh")

            time.sleep(PUBLISH_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\nStopping Smart Meter Simulator...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected from HiveMQ.")

if __name__ == "__main__":
    import sys
    selected_mode = "AUTO"
    if len(sys.argv) > 1:
        arg_mode = sys.argv[1].upper()
        if arg_mode in ["AUTO", "NORMAL", "SURGE", "THEFT", "VOLTAGE_SAG"]:
            selected_mode = arg_mode
    run_simulator(mode=selected_mode)
