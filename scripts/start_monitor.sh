#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0") $$ pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
PID_FILE="$PROJECT_ROOT/monitor.pid"
LOG_FILE="$PROJECT_ROOT/data/monitor.log"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color]

# Verifica si ya está corriendo el monitor
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" > /dev/null 2>&1; then
        echo -e "${RED}El monitor ya está corriendo (PID $PID)${NC}"
        exit 1
    fi
fi

# Verifica entorno virtual
if [ ! -f "$PYTHON_BIN" ]; then
    echo -e "${RED}Error: No se encontró el entorno virtual.${NC}"
    exit 1
fi

echo -e "${GREEN}Iniciando el monitor en background...${NC}"

# Corre el monitor en background y redirige la salida a un archivo de log
# $! captura el pid del proceso recién iniciado
nohup "$PYTHON_BIN" "$PROJECT_ROOT/src/main.py" \ >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo -e "${GREEN}✓ Monitor iniciado (PID $(cat $PID_FILE))${NC}"
echo -e "Log: $LOG_FILE"