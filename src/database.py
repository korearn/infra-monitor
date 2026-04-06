import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from collector import SystemMetrics

DB_PATH = Path(__file__).parent.parent / 'data' / 'monitor.db'

def get_connection() -> sqlite3.Connection:
    """
    Establece una conexión a la base de datos SQLite.
    Si la base de datos no existe, se crea automáticamente.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

def init_db():
    """
    Inicializa la base de datos creando la tabla 'metrics' si no existe.
    Se pueden graficar tendencias o detectar patrones.
    """
    conn =  get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            cpu_percent     REAL NOT NULL,
            memory_percent  REAL NOT NULL,
            memory_used_gb  REAL NOT NULL,
            memory_total_gb REAL NOT NULL,
            disk_percent    REAL NOT NULL,
            disk_used_gb    REAL NOT NULL,
            disk_total_gb   REAL NOT NULL,
            net_bytes_sent  INTEGER NOT NULL,
            net_bytes_recv  INTEGER NOT NULL
            )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   DATETIME NOT NULL,
            level       TEXT NOT NULL,
            metric      TEXT NOT NULL,
            value       REAL NOT NULL,
            threshold   REAL NOT NULL,
            diagnosis   TEXT,
            resolved_at DATETIME
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)
    ''')
    conn.commit()
    conn.close()

def save_metrics(metrics: SystemMetrics):
    """Guarda un snapshot de las métricas del sistema en la base de datos."""
    conn = get_connection()
    conn.execute('''
        INSERT INTO metrics (
            timestamp, cpu_percent, memory_percent, memory_used_gb, memory_total_gb,
            disk_percent, disk_used_gb, disk_total_gb, net_bytes_sent, net_bytes_recv
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        metrics.timestamp.isoformat(),
        metrics.cpu_percent,
        metrics.memory_percent,
        metrics.memory_used_gb,
        metrics.memory_total_gb,
        metrics.disk_percent,
        metrics.disk_used_gb,
        metrics.disk_total_gb,
        metrics.net_bytes_sent,
        metrics.net_bytes_recv
    ))
    conn.commit()
    conn.close()

def save_alert(level: str, metric: str, value: float, threshold: float, diagnosis: str):
    """Guarda una alerta en la base de datos."""
    conn = get_connection()
    conn.execute('''
        INSERT INTO alerts (timestamp, level, metric, value, threshold, diagnosis)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.utcnow().isoformat(),
        level,
        metric,
        value,
        threshold,
        diagnosis
    ))
    conn.commit()
    conn.close()

def get_recent_alerts(limit: int = 10) -> list:
    """Retorna las alerta más recientes."""
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_last_alert_time(metric: str) -> Optional[datetime]:
    """Retorna la fecha y hora de la última alerta para una métrica específica."""
    conn = get_connection()
    row = conn.execute(
        'SELECT timestamp FROM alerts WHERE metric = ? ORDER BY timestamp DESC LIMIT 1',
        (metric,)
    ).fetchone()
    conn.close()
    if row:
        return datetime.fromisoformat(row['timestamp'])
    return None

def get_metrics_summary() -> dict:
    """Retorna un resumen de las métricas más recientes para mostrar en el dashboard."""
    conn = get_connection()
    row = conn.execute('''
        SELECT
            AVG(cpu_percent)    AS avg_cpu,
            AVG(memory_percent) AS avg_memory,
            AVG(disk_percent)   AS avg_disk,
            COUNT(*)            AS total_snapshots
        FROM  (SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10)
    ''').fetchone()
    conn.close()
    return dict(row) if row else {}