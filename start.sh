#!/bin/bash
set -e

# Usar el puerto de Render o 5005 por defecto
PORT=${PORT:-5005}

# Ejecutar Rasa
exec rasa run --enable-api --cors "*" --port "$PORT" --debug
