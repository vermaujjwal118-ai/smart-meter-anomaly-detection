"""
AI Model Training Script: Baseline Smart Meter Normal Profile
Model: Isolation Forest (Scikit-Learn)

Why Isolation Forest?
- It is the most standard, intuitive ML algorithm for anomaly detection.
- It isolates outliers instead of profiling normal points.
- Extremely lightweight, fast to train, and runs in real time (< 2ms per inference).
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

def generate_normal_meter_data(num_samples=2500):
    """
    Generates synthetic smart meter readings representing typical residential load:
    - Base loads: Refrigerator, standby electronics (0.2 - 0.8 kW)
    - Active loads: TV, lights, computer, fans (0.5 - 2.0 kW)
    - Heavy intermittent loads: AC, microwave, washing machine, heater (1.5 - 4.5 kW)
    - Voltage: Stable grid around 230V (+/- 5V)
    - Power Factor: 0.90 to 0.99
    """
    np.random.seed(42)
    
    # 1. Voltage (V): Normal grid variation around 230V
    voltage = np.random.normal(loc=230.0, scale=3.5, size=num_samples)
    
    # 2. Realistic power consumption in kW (typical household: 0.3kW to 4.5kW)
    # Mixture of standby, medium, and higher loads
    load_choice = np.random.choice([0.5, 1.8, 3.2], size=num_samples, p=[0.5, 0.35, 0.15])
    power_kw = load_choice + np.random.normal(loc=0.0, scale=0.25, size=num_samples)
    power_kw = np.clip(power_kw, 0.15, 5.0)  # Bound to normal residential range
    
    # 3. Power Factor (PF): Inductive/resistive typical 0.92 - 0.98
    power_factor = np.random.uniform(0.92, 0.98, size=num_samples)
    
    # 4. Current (A): I = (P * 1000) / (V * PF)
    current = (power_kw * 1000.0) / (voltage * power_factor)
    
    df = pd.DataFrame({
        "voltage": voltage,
        "current": current,
        "power_kw": power_kw,
        "power_factor": power_factor
    })
    return df

def train_and_save_model(model_filename="isolation_forest_model.joblib"):
    print("==================================================")
    print("  Training AI Smart Meter Anomaly Detector (ML)   ")
    print("==================================================")
    
    # 1. Generate normal training baseline
    print("[1/3] Generating synthetic normal baseline meter data...")
    df_train = generate_normal_meter_data(num_samples=3000)
    print(f"      Created {len(df_train)} normal baseline records.")
    print("      Sample normal stats:")
    print(f"      - Voltage: {df_train['voltage'].mean():.1f}V (range {df_train['voltage'].min():.1f} - {df_train['voltage'].max():.1f})")
    print(f"      - Power:   {df_train['power_kw'].mean():.2f}kW (range {df_train['power_kw'].min():.2f} - {df_train['power_kw'].max():.2f})")
    print(f"      - Current: {df_train['current'].mean():.2f}A (range {df_train['current'].min():.2f} - {df_train['current'].max():.2f})")
    
    # 2. Train Isolation Forest
    # contamination=0.01 indicates ~1% outlier assumption in training baseline
    print("\n[2/3] Fitting Scikit-Learn IsolationForest model...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.02,
        random_state=42
    )
    features = ["voltage", "current", "power_kw", "power_factor"]
    model.fit(df_train[features])
    
    # 3. Save model to disk
    joblib.dump(model, model_filename)
    print(f"[3/3] Model saved successfully to: {model_filename}")
    
    # 4. Quick Validation Test
    print("\n---------------- Quick Validation ----------------")
    test_cases = [
        {"name": "Normal Daytime Load", "voltage": 231.2, "current": 5.2, "power_kw": 1.15, "power_factor": 0.95},
        {"name": "Power Surge / Overload", "voltage": 228.0, "current": 38.5, "power_kw": 8.50, "power_factor": 0.97},
        {"name": "Power Theft (Meter Bypass)", "voltage": 232.0, "current": 0.05, "power_kw": 0.01, "power_factor": 0.85},
        {"name": "Severe Voltage Sag", "voltage": 160.0, "current": 12.0, "power_kw": 1.80, "power_factor": 0.94}
    ]
    
    for case in test_cases:
        X = pd.DataFrame([{
            "voltage": case["voltage"],
            "current": case["current"],
            "power_kw": case["power_kw"],
            "power_factor": case["power_factor"]
        }])
        pred = model.predict(X)[0]  # 1 = Normal, -1 = Anomaly
        score = model.decision_function(X)[0]
        result = "ANOMALY DETECTED" if pred == -1 else "NORMAL"
        print(f"  [{result:^16}] {case['name']:<28} | Score: {score:.3f}")
    
    print("==================================================")
    print("Model is ready for real-time inference!")

if __name__ == "__main__":
    train_and_save_model()
