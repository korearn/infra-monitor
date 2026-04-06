import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collector import SystemMetrics, format_metrics_summary
from database import get_last_alert_time

load_dotenv()

LMSTUDIO_URL     = os.getenv('LMSTUDIO_URL', 'http://localhost:1234/v1/chat/completions')
CPU_THRESHOLD    = float(os.getenv('CPU_THRESHOLD', '80'))  # Umbral de CPU para alertas
MEMORY_THRESHOLD = float(os.getenv('MEMORY_THRESHOLD', '85'))  # Umbral de RAM para alertas
DISK_THRESHOLD   = float(os.getenv('DISK_THRESHOLD', '90'))  # Umbral de disco para alertas
COOLDOWN_MINUTES = int(os.getenv('ALERT_COOLDOWN_MINUTES', '5'))  # Tiempo de espera entre alertas

def is_in_cooldown(metric: str) -> bool:
    """
    Verifica si el sistema está en período de enfriamiento para un tipo de métrica específica.
    Esto evita enviar alertas repetidas en un corto período de tiempo.
    """
    last_alert = get_last_alert_time(metric)
    if not last_alert:
        return False
    cooldown_end = last_alert + timedelta(minutes=COOLDOWN_MINUTES)
    return datetime.utcnow() < cooldown_end

def check_thresholds(metrics: SystemMetrics) -> list:
    """
    Verifica si alguna de las métricas supera los umbrales definidos.
    Devuelve una lista de alertas para las métricas que exceden los límites.
    """
    anomalies = []

    checks = [
        ('cpu', metrics.cpu_percent, CPU_THRESHOLD, 'WARNING'),
        ('memory', metrics.memory_percent, MEMORY_THRESHOLD, 'WARNING'),
        ('disk', metrics.disk_percent, DISK_THRESHOLD, 'CRITICAL')
    ]

    for metric, value, threshold, level in checks:
        if value >= threshold and not is_in_cooldown(metric):
                anomalies.append({
                    'metric':    metric,
                    'value':     value,
                    'threshold': threshold,
                    'level':     level
                })
    return anomalies

def build_diagnosis_prompt(metrics: SystemMetrics, anomalies: list) -> str:
    """
    Construye un prompt detallado para LM Studio que incluye las métricas actuales del sistema
    y las anomalías detectadas. El prompt solicita un diagnóstico y recomendaciones.
    """
    anomaly_text = "\n".join([f"- {a['metric'].upper()} al {a['value']}% (threshold: {a['threshold']}%)" for a in anomalies])

    summary = format_metrics_summary(metrics)

    return f"""Eres un ingeniero SRE experto analizando el estado de un servidor Linux.
Se han detectado las siguientes anomalías en el sistema:

{anomaly_text}

Estado actual del sistema:
{summary}

Proporciona un diagnóstico conciso (máximo 3 párrafos) que incluya:
1. Qué podría estar causando el problema
2. Impacto potencial en el sistema
3. Acciones inmediatas recomendadas para mitigar el problema

Responde en español, de forma técnica pero clara."""

def get_llm_diagnosis(metrics: SystemMetrics, anomalies: list) -> str:
    """
    Envía el prompt construido a LM Studio y obtiene la respuesta del modelo.
    Maneja errores de conexión y formatea la respuesta para su presentación.
    """
    prompt = build_diagnosis_prompt(metrics, anomalies)

    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "system", 
                "content": "Eres un experto en sistemas Linux y DevOps. Das diagnósticos técnicos precisos y accionables."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 400
    }
    
    try:
        response = requests.post(
            LMSTUDIO_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.ConnectionError:
        # fallback simple si no se puede conectar a LM Studio
        anomaly_names = [a['metric'] for a in anomalies]
        return (
            f"Alerta automática: {', '.join(anomaly_names)} superaron el threshold."
            f"LMStudio no disponible para diagnóstico detallado."
        )
    except Exception as e:
        return f"Error al obtener diagnóstico de LM Studio: {str(e)}"

def analyze(metrics: SystemMetrics) -> list:
    """
    Función principal de análisis que verifica las métricas contra los thresholds,
    obtiene un diagnóstico del LLM si se detectan anomalías, y devuelve el resultado.
    """
    anomalies = check_thresholds(metrics)

    if not anomalies:
        return []

    # Generamos un solo diagnóstico para todas las anomalías detectadas en esta iteración
    diagnosis = get_llm_diagnosis(metrics, anomalies)

    alerts = []
    for anomaly in anomalies:
        alerts.append({
            "level": anomaly['level'],
            "metric": anomaly['metric'],
            "value": anomaly['value'],
            "threshold": anomaly['threshold'],
            "diagnosis": diagnosis
        })

    return alerts