#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
PID_FILE="$PROJECT_ROOT/monitor.pid"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================"
echo " INFRA MONITOR - Estado actual"
echo "================================"

# Estado del daemo
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "Daemon: ${GREEN}CORRIENDO (PID $PID)${NC}"
    else
        echo -e "Daemon: ${RED}DETENIDO (PID file obsoleto)${NC}"
    fi
else
    echo -e "Daemon: ${YELLOW}NO INICIADO${NC}"
fi

echo ""
echo "Métricas actuales:"

# Snapshot rápido del sistema sin iniciar el daemon
"$PYTHON_BIN" - << 'EOF'
import psutil
cpu     = psutil.cpu_percent(interval=1)
mem     = psutil.virtual_memory()
disk    = psutil.disk_usage('/')
print(f"  CPU:    {cpu}%")
print(f"  Memoria: {mem.percent}% ({mem.used/(1024**3):.1f}GB / {mem.total/(1024**3):.1f}GB)")
print(f"  Disco:  {disk.percent}% ({disk.used/(1024**3):.1f}GB / {disk.total/(1024**3):.1f}GB)")
EOF