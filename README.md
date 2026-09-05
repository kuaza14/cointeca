# Cointeca S.A.S

Sistema de gestión empresarial (Django 5.2 + PostgreSQL + Tailwind CSS v4).

Módulos: gerencia, contabilidad, RRHH, logística e ingeniería.

---

## Si ya venías trabajando en el proyecto

**Nada de lo que tenías deja de funcionar.** Docker es una opción que se suma,
no un reemplazo: puedes seguir con tu entorno virtual y tu PostgreSQL local
exactamente igual que antes.

La configuración de la base de datos ahora se lee de variables de entorno, pero
**los valores por defecto son los de siempre**: `localhost:5432`, base
`cointeca_db`, usuario `postgres`. Si eso es lo que tienes, no debes cambiar nada.

```bash
python manage.py runserver
```

Solo necesitas un archivo `.env` si tu instalación se sale de esos valores —
por ejemplo, si el puerto 5432 está ocupado por otro proyecto. Copia
`.env.example` a `.env` y ajusta lo que aplique. El `.env` no se versiona, y lo
leen tanto `docker compose` como Django al correr con el venv.

---

## Levantar el proyecto con Docker

Requisito: Docker Desktop. No hace falta instalar Python, PostgreSQL ni Node.

```bash
docker compose up -d --build
```

La aplicación queda en **http://localhost:8001**. El contenedor espera a que
PostgreSQL responda y aplica las migraciones solo.

La primera vez, crea tu usuario:

```bash
docker compose exec web python manage.py createsuperuser
```

### Puertos

| Servicio   | Host   | Motivo |
|------------|--------|--------|
| Aplicación | `8001` | El 8000 suele estar ocupado por otros proyectos |
| PostgreSQL | `5433` | Deja libre el 5432 para tu PostgreSQL nativo |

Elegir el 5433 es deliberado: así el PostgreSQL del contenedor **convive** con
el que ya tienes instalado, sin que se peleen el puerto. Se cambian con
`WEB_HOST_PORT` y `DB_HOST_PORT` en el `.env`.

### Comandos habituales

```bash
docker compose logs -f web                  # ver el log de Django
docker compose exec web python manage.py …  # cualquier comando de Django
docker compose down                         # apagar (los datos se conservan)
docker compose --profile dev up -d          # ademas, recompilar Tailwind al vuelo
```

Solo hay que reconstruir la imagen (`--build`) al cambiar `requirements.txt`,
`Dockerfile`, `docker-entrypoint.sh` o `package.json`. Editar código Python o
plantillas no lo requiere: el proyecto está montado y `runserver` recarga solo.

---

## Llevar tus datos actuales al PostgreSQL de Docker

Al levantar Docker por primera vez, su PostgreSQL arranca **vacío**: es una
instalación nueva e independiente de la que ya tienes. Tus empleados, actas y
demás registros siguen intactos en tu PostgreSQL local, pero el contenedor no
los ve.

Para copiarlos:

```bash
./scripts/migrar-bd-a-docker.sh
```

El script lee tu base local y la reproduce dentro del contenedor.

Los datos de acceso los toma, en este orden: **los argumentos** que le pases,
luego **tu `.env`** si existe, y si no, los valores estándar (`5432`,
`cointeca_db`, `postgres`). La contraseña sale de `POSTGRES_PASSWORD` en el
`.env` y, si no está ahí, **te la pide por teclado** sin mostrarla en pantalla.

Si el puerto de origen coincide con el que publica el contenedor, el script se
detiene: estarías copiando esa base sobre sí misma.

Acepta argumentos si tu instalación no usa los valores por defecto:

```bash
./scripts/migrar-bd-a-docker.sh 5432 cointeca_db postgres
#                               │    │           └── usuario
#                               │    └── nombre de la base
#                               └── puerto de tu PostgreSQL local
```

**Tu base original solo se lee, nunca se modifica.** El volcado queda guardado
como `respaldo-AAAAMMDD-HHMMSS.sql` por si necesitas repetir la operación.

El `pg_dump` corre dentro del contenedor, así que no necesitas las herramientas
de PostgreSQL en el PATH y no hay conflictos de versión: `pg_dump` 18 sabe leer
servidores más antiguos.

> En Windows, ejecuta el script desde Git Bash.

### Si prefieres hacerlo a mano

```bash
# 1. Volcar tu base local (ajusta puerto, base y usuario)
docker compose exec -T -e PGPASSWORD=tu_clave db \
    pg_dump -h host.docker.internal -p 5432 -U postgres -d cointeca_db \
            --no-owner --no-privileges --clean --if-exists > respaldo.sql

# 2. Restaurar dentro del contenedor
docker compose exec -T db psql -U postgres -d cointeca_db < respaldo.sql
```

### Si te pasan un volcado desde otra máquina

Mismo segundo paso: `docker compose exec -T db psql -U postgres -d cointeca_db < archivo.sql`

---

## Catálogo de materiales

Los materiales viven en la base de datos, no en el Excel. El archivo
`materiales.xlsx` es la carga inicial y se importa una sola vez:

```bash
docker compose exec web python manage.py importar_materiales materiales.xlsx
```

El comando usa `get_or_create`, así que repetirlo no duplica nada.

---

## Estilos

Tailwind v4 con tokens semánticos declarados en `@theme` dentro de
`static/css/input.css`. En las plantillas se usan las clases del sistema
(`bg-primary`, `text-muted-foreground`, `btn btn-primario`, `tabla-caja`) en
lugar de colores crudos, de modo que la paleta se cambia en un solo archivo.

```bash
npm run dev     # recompila mientras editas
npm run build   # compila minificado
```

Dentro de Docker lo hace el servicio `tailwind` del perfil `dev`.
