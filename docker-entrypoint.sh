#!/bin/sh
set -e

echo "Esperando a PostgreSQL en ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432} ..."
python <<'PY'
import os, socket, sys, time

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL disponible")
            sys.exit(0)
    except OSError:
        time.sleep(1)

print(f"No se pudo conectar a {host}:{port} tras 60s", file=sys.stderr)
sys.exit(1)
PY

echo "Aplicando migraciones ..."
python manage.py migrate --noinput

# Sincronizar archivos multimedia iniciales al volumen de media si no existen
if [ -d "/app/documentos_rrhh" ]; then
    mkdir -p /app/media/documentos_rrhh
    cp -rn /app/documentos_rrhh/* /app/media/documentos_rrhh/ 2>/dev/null || true
fi

exec "$@"
