# Technical Test

Entorno de desarrollo con backend Django REST Framework, frontend React/Vite y MySQL. El backend ofrece autenticación por token, creación de solicitudes y consulta del catálogo de estados; no incluye integración con LLM.

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

El backend permite crear solicitudes en `POST /api/requests/` y consultar el catálogo de estados en `GET /api/statuses/`. El estado inicial se asigna en el servidor.

## Preparar y levantar el entorno

Desde Ubuntu/WSL2, antes de levantar el proyecto por primera vez, completa `.env` con una clave secreta fuerte para Django y configura `DJANGO_SUPERUSER_USERNAME` y `DJANGO_SUPERUSER_PASSWORD` con credenciales iniciales únicas y robustas. No guardes ni compartas esos valores en Git. La contraseña del administrador debe satisfacer los validadores de contraseñas de Django.

```bash
cd /home/carlos/projects/technical_test
if [ ! -f .env ]; then cp .env.example .env; fi
docker compose up --build
```

El `.env` incluido contiene valores ilustrativos exclusivos para desarrollo local. La copia protege esos valores de Git, pero no son adecuados para producción. Cambia las claves y contraseñas y configura `DJANGO_DEBUG=false` antes de desplegar.

Compose espera a que el health check de MySQL termine antes de iniciar Django. Django ejecuta `migrate` y luego `ensure_admin_user` al arrancar. Este comando crea el superusuario nativo una sola vez; en arranques posteriores conserva la cuenta existente. Si falta una variable, la contraseña no cumple las validaciones o una migración falla, el contenedor no continúa como si hubiera iniciado correctamente. Los cambios en `backend/` y `frontend/` se reflejan mediante bind mounts y hot reload.

## Acceso

- Frontend React/Vite: <http://localhost:5173>
- Backend: <http://localhost:8000>
- Health check: <http://localhost:8000/api/health/>
- API browsable existente: <http://localhost:8000/api/>
- Crear solicitud: `POST http://localhost:8000/api/requests/`
- Consultar estados: `GET http://localhost:8000/api/statuses/`
- Iniciar sesión: `POST http://localhost:8000/api/auth/login/`
- Cerrar sesión: `POST http://localhost:8000/api/auth/logout/`
- Esquema OpenAPI: <http://localhost:8000/api/schema/>
- Swagger UI: <http://localhost:8000/api/docs/>
- MySQL: solo en la red privada de Compose, en `db:3306`; no se publica un puerto en el host.

El esquema OpenAPI y Swagger UI permiten consultar y probar la API cuando Docker Compose está ejecutándose.

`POST /api/requests/` recibe únicamente `title` y `description`; el backend busca y asigna automáticamente el estado cuyo `tag` es `created`. Internamente, `Request` se relaciona con `Status` mediante su clave primaria numérica; la API identifica el estado únicamente por su `tag` y no expone el ID interno. `GET /api/statuses/` devuelve cada estado con `tag` y `name`; el catálogo se administra mediante migraciones y no ofrece operaciones de escritura por API.

La respuesta del catálogo tiene esta estructura:

```json
[
  { "tag": "created", "name": "Creada" },
  { "tag": "in_review", "name": "En revisión" },
  { "tag": "in_progress", "name": "En progreso" },
  { "tag": "paused", "name": "Pausada" },
  { "tag": "done", "name": "Finalizada" }
]
```

### Autenticación por token

Los endpoints de negocio requieren autenticación DRF por token. Inicia sesión con las credenciales definidas en `.env`:

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"TU_USUARIO_ADMIN","password":"TU_CONTRASEÑA"}'
```

La respuesta contiene `{"token":"..."}`. En las siguientes peticiones, incluye el token como `Authorization: Token <token>`. Por ejemplo:

```bash
curl http://localhost:8000/api/statuses/ \
  -H 'Authorization: Token TU_TOKEN'
```

Para invalidar el token actual:

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H 'Authorization: Token TU_TOKEN'
```

Swagger UI en `/api/docs/` ofrece el botón **Authorize** para introducir únicamente el valor del token; Swagger añade el prefijo `Token` al encabezado `Authorization`. El health check, el esquema OpenAPI y Swagger UI permanecen públicos; los endpoints de negocio requieren token.

La URL que usa el navegador para la API se configura con `VITE_API_BASE_URL`. Los orígenes del frontend permitidos por el backend se configuran con `CORS_ALLOWED_ORIGINS`.

## Migraciones

Las migraciones se aplican al iniciar el servicio. La migración del catálogo crea automáticamente los cinco estados iniciales y convierte las solicitudes existentes sin eliminar sus datos. Para ejecutarlas manualmente:

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
