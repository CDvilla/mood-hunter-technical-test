# Technical Test

Infraestructura inicial de desarrollo para un backend Django REST Framework, un frontend React/Vite y MySQL. No contiene todavía funcionalidades de solicitudes ni integración con LLM.

## Tecnologías y versiones

| Componente | Versión |
|---|---|
| Python | 3.14.10 (imagen `python:3.14.10-slim`) |
| Django | 6.1.3 |
| Django REST Framework | 3.18.1 |
| mysqlclient | 2.2.8 |
| MySQL | 8.4.8 |
| Node.js | 26.13.0 LTS |
| React / React DOM | 19.3.1 |
| Vite | 8.3.7 |
| `@vitejs/plugin-react` | 6.3.0 |

Las versiones se comprobaron en los metadatos de PyPI, npm y Docker Hub disponibles al preparar esta base. DRF 3.18.1 declara soporte para Django 6.1 y Python 3.14. `mysqlclient` 2.2.8 declara Python 3.14; el Dockerfile compila su extensión con las bibliotecas de desarrollo MySQL/MariaDB y deja solo la biblioteca de ejecución en la imagen final.

`django-cors-headers` 4.9.0 todavía declara soporte hasta Django 6.0, por lo que no se incorpora para Django 6.1.3. En su lugar hay un middleware CORS mínimo que solo permite los orígenes enumerados en `CORS_ALLOWED_ORIGINS`; no habilita credenciales ni orígenes comodín.

## Requisitos previos

- Ubuntu en WSL2 con Docker Engine y el plugin Docker Compose.
- Usuario con permisos para acceder al daemon Docker (normalmente, miembro del grupo `docker`).
- No se necesita instalar Python ni Node.js en Ubuntu: ambos se ejecutan dentro de contenedores.

## Estructura

```text
backend/       Proyecto Django, API existente y configuración Docker
frontend/      Aplicación React/Vite y configuración Docker
database/      SQL inicial (sin tablas de negocio)
.env           Variables locales de desarrollo (no se versiona)
.env.example   Plantilla de variables
docker-compose.yml
```

El backend conserva el modelo y CRUD genérico `Item` y ofrece la creación de solicitudes en `POST /api/requests/`. El endpoint asigna el estado inicial en el servidor.

## Preparar y levantar el entorno

Desde Ubuntu/WSL2:

```bash
cd /home/carlos/projects/technical_test
if [ ! -f .env ]; then cp .env.example .env; fi
docker compose up --build
```

El `.env` incluido contiene valores ilustrativos exclusivos para desarrollo local. La copia protege esos valores de Git, pero no son adecuados para producción. Cambia las claves y contraseñas y configura `DJANGO_DEBUG=false` antes de desplegar.

Compose espera a que el health check de MySQL termine antes de iniciar Django. Django ejecuta `migrate` al arrancar; si una migración falla, el contenedor no continúa como si hubiera iniciado correctamente. Los cambios en `backend/` y `frontend/` se reflejan mediante bind mounts y hot reload.

## Acceso

- Frontend React/Vite: <http://localhost:5173>
- Backend: <http://localhost:8000>
- Health check: <http://localhost:8000/api/health/>
- API browsable existente: <http://localhost:8000/api/>
- Crear solicitud: `POST http://localhost:8000/api/requests/`
- Esquema OpenAPI: <http://localhost:8000/api/schema/>
- Swagger UI: <http://localhost:8000/api/docs/>
- MySQL: solo en la red privada de Compose, en `db:3306`; no se publica un puerto en el host.

El esquema OpenAPI y Swagger UI permiten consultar y probar la API cuando Docker Compose está ejecutándose.

La URL que usa el navegador para la API se configura con `VITE_API_BASE_URL`. Los orígenes del frontend permitidos por el backend se configuran con `CORS_ALLOWED_ORIGINS`.

## Migraciones

Las migraciones se aplican al iniciar el servicio. Para ejecutarlas manualmente:

```bash
docker compose exec backend python manage.py migrate
```

Para comprobar la configuración Django:

```bash
docker compose exec backend python manage.py check
```

## Logs y detención

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose down
```

`docker compose down` conserva el volumen de MySQL. Para borrar los datos persistidos habría que eliminar el volumen explícitamente; no lo hagas si deseas conservarlos.

## Cambios de dependencias

Después de modificar `backend/requirements.txt`, reconstruye el backend:

```bash
docker compose build backend
docker compose up
```

Después de modificar `frontend/package.json`, reconstruye el frontend:

```bash
docker compose build frontend
docker compose up
```

Las dependencias directas y transitivas del frontend están fijadas en `frontend/package-lock.json`; la imagen instala mediante `npm ci`. Al cambiar dependencias, actualiza y versiona conjuntamente `package.json` y `package-lock.json`.
