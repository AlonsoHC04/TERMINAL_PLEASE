#!/bin/sh
# Lanzador para macOS / Linux:  sh jugar.sh
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    exec python3 ingress_monitor.py "$@"
elif command -v python >/dev/null 2>&1; then
    exec python ingress_monitor.py "$@"
else
    echo "No se encontro Python. Instalalo desde https://www.python.org/downloads/"
    exit 1
fi
