#!/bin/sh
set -e

python <<'PY'
import os, socket, sys, time
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL")
if db_url:
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
    except Exception:
        host = os.environ.get("POSTGRES_HOST", "db")
        port = int(os.environ.get("POSTGRES_PORT", "5432"))
else:
    host = os.environ.get("POSTGRES_HOST", "db")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))

print(f"Esperando a PostgreSQL en {host}:{port} ...")
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

echo "Recopilando archivos estáticos ..."
python manage.py collectstatic --noinput

# Sincronizar archivos multimedia iniciales al volumen de media si no existen
if [ -d "/app/documentos_rrhh" ]; then
    mkdir -p /app/media/documentos_rrhh
    cp -rn /app/documentos_rrhh/* /app/media/documentos_rrhh/ 2>/dev/null || true
fi

exec "$@"
