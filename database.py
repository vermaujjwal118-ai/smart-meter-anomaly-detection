"""
Database Module for Smart Meter Telemetry and Anomaly History
Uses SQLite (lightweight, zero-setup, built into Python)
"""

import sqlite3
import datetime
from config import DB_PATH

def init_db():
    """Initializes the SQLite tables for telemetry and anomalies if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Telemetry table: logs every reading
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meter_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            meter_id TEXT,
            voltage REAL,
            current REAL,
            power_kw REAL,
            energy_kwh REAL,
            power_factor REAL,
            frequency REAL
        )
    """)
    
    # Anomaly table: logs detected anomalies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            meter_id TEXT,
            power_kw REAL,
            voltage REAL,
            current REAL,
            anomaly_score REAL,
            anomaly_type TEXT,
            severity TEXT,
            description TEXT
        )
    """)
    
    # Security audit table: logs logins, tampering, and remote operations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            severity TEXT,
            user TEXT,
            details TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def log_telemetry(data: dict):
    """Inserts a single smart meter telemetry reading into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO meter_telemetry (
            timestamp, meter_id, voltage, current, power_kw, energy_kwh, power_factor, frequency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("meter_id", "SM001"),
        data.get("voltage", 230.0),
        data.get("current", 0.0),
        data.get("power_kw", 0.0),
        data.get("energy_kwh", 0.0),
        data.get("power_factor", 0.95),
        data.get("frequency", 50.0)
    ))
    conn.commit()
    conn.close()

def log_anomaly(anomaly_record: dict):
    """Inserts an anomaly incident record into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO anomaly_logs (
            timestamp, meter_id, power_kw, voltage, current, anomaly_score, anomaly_type, severity, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        anomaly_record.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        anomaly_record.get("meter_id", "SM001"),
        anomaly_record.get("power_kw", 0.0),
        anomaly_record.get("voltage", 230.0),
        anomaly_record.get("current", 0.0),
        anomaly_record.get("anomaly_score", 0.0),
        anomaly_record.get("anomaly_type", "Unknown Anomaly"),
        anomaly_record.get("severity", "MEDIUM"),
        anomaly_record.get("description", "")
    ))
    conn.commit()
    conn.close()

def log_security_event(event_type: str, severity: str, user: str, details: str):
    """Inserts a security audit record into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO security_logs (timestamp, event_type, severity, user, details)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        event_type,
        severity,
        user,
        details
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"SQLite database initialized successfully at: {DB_PATH}")
