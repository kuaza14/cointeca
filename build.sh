#!/usr/bin/env bash
# Script de construcción y preparación para despliegue en la nube (Render / Railway / Koyeb)
set -o errexit

echo ">>> Instalando dependencias de Python..."
pip install -r requirements.txt

echo ">>> Recopilando archivos estáticos (Tailwind CSS, JS, imágenes)..."
python manage.py collectstatic --noinput

echo ">>> Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

echo ">>> ¡Construcción finalizada con éxito!"
