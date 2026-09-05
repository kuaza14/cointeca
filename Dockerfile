# ---- Etapa 1: compilar el CSS de Tailwind ----
FROM node:24-slim AS tailwind

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Tailwind v4 escanea las plantillas para detectar las clases en uso
COPY static/css/input.css ./static/css/input.css
COPY core ./core
COPY config ./config

RUN npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --minify

# ---- Etapa 2: la aplicacion Django ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=tailwind /app/static/css/output.css ./static/css/output.css

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
