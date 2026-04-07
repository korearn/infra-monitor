# Infra Monitor 🖥️

Daemon de monitoreo de infraestructura que recolecta métricas del sistema
en tiempo real y usa un LLM local para generar diagnósticos inteligentes
cuando se detectan anomalías. Sin servicios externos — 100% local.

## ¿Qué hace?

- Monitorea CPU, RAM, disco y red cada N segundos configurable
- Guarda métricas históricas en SQLite como serie temporal
- Detecta anomalías comparando contra thresholds configurables
- Genera diagnósticos en lenguaje natural usando un LLM local via LMStudio
- Exporta alertas a archivos de texto con timestamp
- Corre como daemon en background con scripts Bash

## Stack técnico

- **Python 3.12** — lenguaje principal
- **psutil** — lectura de métricas del sistema operativo
- **LMStudio** — servidor local de LLM para diagnósticos
- **SQLite** — persistencia de métricas y alertas
- **Rich** — visualización de métricas y alertas en terminal
- **Bash** — control del daemon (start/stop/status)
- **WSL/Arch Linux** — entorno de ejecución

## Estructura del Proyecto

```text
infra-monitor/
├── data/
│   ├── alerts/             # Alertas exportadas con timestamp
│   └── metrics/            # Referencia de métricas históricas
├── scripts/
│   ├── start_monitor.sh    # Inicia el daemon en background
│   ├── stop_monitor.sh     # Detiene el daemon limpiamente
│   └── status.sh           # Muestra estado actual del sistema
├── src/
│   ├── collector.py        # Recolección de métricas con psutil
│   ├── analyzer.py         # Detección de anomalías + diagnóstico LLM
│   ├── alerter.py          # Visualización y exportación de alertas
│   ├── database.py         # Persistencia SQLite
│   └── main.py             # Loop principal del daemon
└── requirements.txt        # Dependencias del proyecto
```

## Instalación

```bash
git clone https://github.com/korearn/infra-monitor
cd infra-monitor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Edita `.env` para ajustar los parámetros:

```env
LMSTUDIO_URL=http://localhost:1234/v1/chat/completions
MONITOR_INTERVAL_SECONDS=30
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
ALERT_COOLDOWN_MINUTES=5
```

## Uso

### Modo interactivo
```bash
cd src
python main.py
```

### Modo daemon (background)
```bash
bash scripts/start_monitor.sh
bash scripts/status.sh
bash scripts/stop_monitor.sh
```

## Ejemplo de alerta
🔴 CRITICAL — CPU al 85.3%
─────────────────────────────
Threshold superado: 80%
Diagnóstico IA:
Se detecta un pico de CPU sostenido posiblemente causado por
un proceso en bucle infinito o una tarea de compilación intensiva.
Impacto potencial: degradación del tiempo de respuesta en servicios
activos. Acción recomendada: ejecutar 'top' para identificar el
proceso responsable y evaluar si debe ser terminado.

## Notas técnicas

- El cooldown evita spam de alertas para la misma métrica
- El daemon usa `nohup` para sobrevivir al cierre de la terminal
- Las señales SIGTERM y SIGINT se manejan para apagado limpio
- La serie temporal en SQLite permite análisis histórico de tendencias