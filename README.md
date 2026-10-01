# AI-Based Smart Meter Consumption Anomaly Detection

A clean, modular, and beginner-friendly IoT + AI project that detects electricity consumption anomalies (such as power theft, overload surges, and grid voltage sags) in real time.

Built according to the standard IoT layered architecture demonstrated in your lab:
```
[Layer 1-3] Synthetic Meter (SD) ──MQTT──> [HiveMQ Broker] ──> [SQLite DB]
                                                  │
                                                  ▼
[Layer 4-5]                            [AI / ML Engine] (Isolation Forest)
                                                  │
                                                  ▼ (Alerts)
                                       [Node-RED Dashboard] (http://localhost:1880/ui)
                                         ├── Live Gauges (kW, V, A)
                                         ├── Real-Time Trend Charts
                                         ├── Anomaly Alert Banners
                                         └── Incident History Table
```

---

## 📁 Project Structure

```
smartttt meter/
├── .vscode/
│   └── launch.json              # 1-Click Run configurations for VS Code
├── config.py                    # HiveMQ broker, port, MQTT topics, settings
├── database.py                  # SQLite database handler (telemetry & anomaly logs)
├── train_baseline_model.py      # Generates normal baseline data & trains AI model
├── smart_meter_simulator.py     # Generates realistic smart meter telemetry & publishes to HiveMQ
├── ai_anomaly_detector.py       # Real-time AI engine: subscribes, detects anomalies, stores in DB, publishes alerts
├── main.py                      # Interactive menu to launch any part of the project easily
├── node_red_flows.json          # Pre-built Node-RED dashboard flows (auto-installed in ~/.node-red)
├── requirements.txt             # Required Python libraries
└── README.md                    # Complete project guide and viva notes
```

---

## 🚀 How to Run the Project in VS Code (Step-by-Step)

### Step 1: Open the Project in VS Code
1. Open **VS Code**.
2. Click **File -> Open Folder...** and select `smartttt meter` (`c:\Users\hp\Downloads\smartttt meter`).

### Step 2: Start the System via `main.py`
Open the VS Code Terminal (`Ctrl + ~`) and run:
```bash
python main.py
```
You will see the interactive menu:
```
======================================================================
     AI-BASED SMART METER CONSUMPTION ANOMALY DETECTION SYSTEM
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
```
- Choose **Option `[1]`** to start the full system (Simulator + AI Detector).
- Choose **Option `[7]`** to launch the interactive Streamlit Web Dashboard!
- You will see live telemetry and colored anomaly alerts printing in the console!

---

## 📊 Viewing the Node-RED Dashboard

The dashboard flows are **already imported and configured** in your Node-RED setup!

1. Open a new terminal in VS Code and start Node-RED:
   ```bash
   node-red
   ```
2. Open your web browser and navigate to:
   - **Node-RED Dashboard UI:** [http://localhost:1880/ui](http://localhost:1880/ui)
   - **Node-RED Flow Editor:** [http://localhost:1880](http://localhost:1880)

### What the Dashboard Displays:
- **Live Electrical Gauges:** Active Power (`kW`), Line Voltage (`V`), Current (`A`), and Total Energy (`kWh`).
- **AI Anomaly Status Banner:**
  - 🟢 **Green ("SYSTEM NORMAL"):** When power is within normal consumption limits.
  - 🔴 **Red ("ANOMALY DETECTED"):** When an anomaly occurs (with description & severity).
- **Consumption Trend Chart:** Real-time line chart tracking power over time.
- **Incident History Table:** Running log of recent anomalies with timestamp, power, voltage, and severity.

---

## 📈 Viewing the Streamlit Dashboard (Alternative UI)

As noted on the whiteboard (`XYZ. Streamlit (alt)`), a modern Streamlit web dashboard is also included!

1. In VS Code terminal (or select Option `7` in `main.py`), run:
   ```bash
   python -m streamlit run dashboard_streamlit.py
   ```
2. The browser will automatically open at: **`http://localhost:8501`**

### Key Features of the Streamlit Dashboard:
- **Real-Time KPI Cards:** Active Power ($kW$), Voltage ($V$), Current ($A$), Total Energy ($kWh$), Power Factor.
- **Dynamic AI Alert Banner:** Instant Red/Green visual indicator for anomalies with severity.
- **Interactive Plotly Charts:** Zoomable, hoverable time-series charts for Power and Voltage.
- **1-Click Anomaly Injection Buttons:** Click buttons in the sidebar (Surge, Power Theft, Voltage Sag, Normal) to inject test packets into HiveMQ and see the AI detector react live!
- **SQLite Anomaly Log Table:** Real-time table of recent detected incidents.

---

### 1. The Machine Learning Model: `Isolation Forest`
- **Why Isolation Forest?** Unlike standard classifiers that require thousands of labeled anomaly examples, `IsolationForest` (from `scikit-learn`) is an unsupervised algorithm. It builds decision trees to "isolate" abnormal points that deviate from normal residential consumption patterns.
- **Features Used:**
  1. `Voltage (V)`: Normal ~230V
  2. `Current (A)`: Normal residential 1A - 15A
  3. `Power (kW)`: Active load 0.3kW - 4.5kW
  4. `Power Factor (PF)`: 0.92 - 0.98

### 2. Semantic Anomaly Classification
When an anomaly is flagged, the AI engine labels it with human-readable causes:
1. **Power Theft / Meter Tamper (Bypass):**
   - *Condition:* Normal voltage (~230V) but consumption drops to near zero (< 0.08 kW) unexpectedly.
   - *Real-world meaning:* Illegal shunt wire bypassed the meter to steal electricity.
2. **Overload Surge / Equipment Fault:**
   - *Condition:* Sudden spike exceeding 7.0 kW or 30 Amperes.
   - *Real-world meaning:* Motor stall, short circuit, or unauthorized industrial load.
3. **Severe Voltage Sag / Brownout:**
   - *Condition:* Line voltage drops below 180V.
   - *Real-world meaning:* Grid instability or localized transformer overloading.

---

## 📡 HiveMQ MQTT Broker Details

- **Default Broker:** `broker.hivemq.com` (Port 1883, No TLS required, Zero credentials needed).
- **Topics:**
  - `smartmeter/SM001/data`: Raw telemetry from smart meter.
  - `smartmeter/SM001/alerts`: Enriched telemetry with AI anomaly analysis.
- **Switching to HiveMQ Cloud (Optional):**
  If you wish to use HiveMQ Cloud cluster, simply edit `config.py`:
  ```python
  MQTT_BROKER = "your-cluster-url.hivemq.cloud"
  MQTT_PORT = 8883
  MQTT_USE_TLS = True
  MQTT_USERNAME = "your_username"
  MQTT_PASSWORD = "your_password"
  ```

---

## 🎓 Viva / Presentation Cheat Sheet

**Q1: What is the main objective of this project?**
> *Answer:* To detect abnormal electricity consumption patterns (such as energy theft, equipment fault surges, or voltage sags) in real time using Machine Learning (Isolation Forest) on smart meter telemetry streamed over HiveMQ MQTT, visualized through a Node-RED dashboard.

**Q2: Why did you choose Isolation Forest over Deep Learning (LSTM/CNN)?**
> *Answer:* Isolation Forest is lightweight, computationally efficient (< 2ms inference), does not require heavy GPU hardware, works effectively without needing massive labeled anomaly training sets, and is ideal for real-time edge/IoT devices.

**Q3: How does MQTT differ from HTTP in IoT?**
> *Answer:* MQTT is a lightweight publish-subscribe protocol with minimal packet headers (2 bytes), ideal for continuous telemetry transmission over low-bandwidth IoT networks, whereas HTTP is request-response with heavy header overhead.

**Q4: How does the system detect Electricity Theft?**
> *Answer:* Electricity theft typically occurs via meter bypassing or tampering. The system monitors voltage and power simultaneously. If line voltage is present (230V) but reported power drops to near zero during active hours, the AI and rule engine flag a "Power Theft / Meter Bypass" anomaly alert.
