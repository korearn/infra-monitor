#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/monitor.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}No se encontró el archivo PID. El monitor no parece estar corriendo.${NC}"
    exit 1
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null 2>&1; then
    # SIGTERM para apagado limpio - le da tiempo al proceso para cerrar recursos
    kill -TERM "$PID"
    echo -e "${GREEN}✓ Monitor detenido (PID $PID)${NC}"
    rm -f "$PID_FILE"
else
    echo -e "${RED}No se encontró un proceso con PID $PID. Eliminando archivo PID...${NC}"
    rm -f "$PID_FILE"
fi