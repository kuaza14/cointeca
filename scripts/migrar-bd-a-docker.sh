#!/bin/sh
# ---------------------------------------------------------------------------
# Copia una base de datos PostgreSQL ya existente en tu maquina hacia el
# PostgreSQL que levanta docker compose.
#
#   ./scripts/migrar-bd-a-docker.sh [puerto] [nombre_bd] [usuario]
#
# Los datos de acceso se toman, en este orden:
#   1. los argumentos de la linea de comandos
#   2. el archivo .env de la raiz del proyecto, si existe
#   3. los valores por defecto: puerto 5432, base cointeca_db, usuario postgres
#
# La contrasena sale del .env (POSTGRES_PASSWORD) y, si no esta ahi, se pide
# por teclado. Nunca se escribe en pantalla ni queda en el historial.
#
# El volcado lo hace pg_dump desde DENTRO del contenedor, asi que no necesitas
# tener las herramientas de PostgreSQL en el PATH y no hay choques de version:
# pg_dump 18 sabe leer servidores mas antiguos.
#
# Tu base original NO se modifica: solo se lee.
# ---------------------------------------------------------------------------
set -e

RAIZ=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$RAIZ"

# ---- 1. Leer el .env si existe -------------------------------------------
if [ -f .env ]; then
    echo "Leyendo datos de acceso desde .env"
    # Se exporta solo lo que parece 'CLAVE=valor', ignorando comentarios
    while IFS= read -r linea || [ -n "$linea" ]; do
        case "$linea" in
            ''|\#*) continue ;;
        esac
        case "$linea" in
            *=*) export "$(printf '%s' "$linea" | sed 's/[[:space:]]*$//')" 2>/dev/null || true ;;
        esac
    done < .env
fi

# ---- 2. Resolver origen: argumento > .env > valor por defecto -------------
PUERTO_ORIGEN="${1:-${POSTGRES_PORT:-5432}}"
BD_ORIGEN="${2:-${POSTGRES_DB:-cointeca_db}}"
USUARIO_ORIGEN="${3:-${POSTGRES_USER:-postgres}}"
CLAVE_ORIGEN="${POSTGRES_PASSWORD:-}"

PUERTO_CONTENEDOR="${DB_HOST_PORT:-5433}"

# ---- 3. Evitar que el origen sea el propio contenedor ---------------------
if [ "$PUERTO_ORIGEN" = "$PUERTO_CONTENEDOR" ]; then
    echo
    echo "El puerto de origen (${PUERTO_ORIGEN}) es el mismo que publica el"
    echo "contenedor de docker compose, asi que estarias copiando esa base"
    echo "sobre si misma."
    echo
    echo "Indica el puerto de TU PostgreSQL local, por ejemplo:"
    echo "    ./scripts/migrar-bd-a-docker.sh 5432"
    exit 1
fi

echo "Origen : localhost:${PUERTO_ORIGEN}/${BD_ORIGEN} (usuario ${USUARIO_ORIGEN})"
echo "Destino: contenedor 'db' de docker compose"
echo

if [ -z "$CLAVE_ORIGEN" ]; then
    printf "Contrasena de %s en tu PostgreSQL local: " "$USUARIO_ORIGEN"
    stty -echo 2>/dev/null || true
    read CLAVE_ORIGEN
    stty echo 2>/dev/null || true
    echo
fi

ARCHIVO="respaldo-$(date +%Y%m%d-%H%M%S).sql"

echo "Verificando que el contenedor este arriba..."
docker compose up -d db >/dev/null

echo "1/3  Leyendo tu base local y generando el volcado..."
docker compose exec -T \
    -e PGPASSWORD="$CLAVE_ORIGEN" \
    db \
    pg_dump \
        -h host.docker.internal \
        -p "$PUERTO_ORIGEN" \
        -U "$USUARIO_ORIGEN" \
        -d "$BD_ORIGEN" \
        --no-owner \
        --no-privileges \
        --clean \
        --if-exists \
    > "$ARCHIVO"

TAMANO=$(wc -c < "$ARCHIVO")
if [ "$TAMANO" -lt 1000 ]; then
    echo
    echo "El volcado salio vacio o incompleto (${TAMANO} bytes). Revisa el puerto,"
    echo "el nombre de la base y la contrasena."
    echo "No se toco la base del contenedor."
    exit 1
fi

echo "     ${ARCHIVO}: ${TAMANO} bytes, $(grep -c 'CREATE TABLE' "$ARCHIVO") tablas."

echo "2/3  Restaurando dentro del contenedor..."
docker compose exec -T db \
    psql -U postgres -d "${POSTGRES_DB:-cointeca_db}" -v ON_ERROR_STOP=1 -q < "$ARCHIVO"

echo "3/3  Comprobando el resultado..."
docker compose exec -T db \
    psql -U postgres -d "${POSTGRES_DB:-cointeca_db}" -t -c \
    "SELECT 'tablas restauradas: ' || count(*) FROM information_schema.tables
     WHERE table_schema = 'public';"

echo
echo "Listo. El volcado quedo en ${ARCHIVO} por si necesitas repetirlo."
echo "Tu base original no fue modificada."
