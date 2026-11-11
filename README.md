# Technical Test

Entorno de desarrollo con backend Django REST Framework, frontend React/Vite y MySQL. El backend ofrece autenticación por token, gestión de solicitudes, consulta del catálogo de estados y generación opcional de resúmenes con Gemini.

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

Clona el repositorio y ejecuta estos pasos desde su directorio raíz. Se requiere Docker Engine y Docker Compose; en Windows puedes usar Docker Desktop con integración WSL2. No es necesario instalar Python, Node.js ni MySQL en el host.

```bash
git clone https://github.com/CDvilla/mood-hunter-technical-test.git
cd mood-hunter-technical-test
cp .env.example .env
```

Edita `.env` antes del primer arranque:

- Define `DJANGO_SECRET_KEY` con un valor aleatorio fuerte (por ejemplo, `openssl rand -hex 32`).
- Define `DJANGO_SUPERUSER_USERNAME` y `DJANGO_SUPERUSER_PASSWORD` con credenciales únicas. La contraseña debe satisfacer los validadores de Django.
- Define valores no vacíos y únicos para `DB_PASSWORD` y `DB_ROOT_PASSWORD`.
- `GEMINI_API_KEY` es opcional para levantar la aplicación. Déjala vacía si no necesitas resúmenes con IA; para esa función, proporciona una clave válida de Gemini.

No compartas ni subas `.env` a Git. La plantilla `.env.example` no contiene credenciales válidas.

```bash
docker compose up --build
```

La primera ejecución construye las imágenes, crea el esquema de base de datos, aplica las migraciones y crea el usuario administrador. Los cambios en `backend/` y `frontend/` se reflejan mediante bind mounts y hot reload. La base empieza sin solicitudes de ejemplo; crea solicitudes desde la interfaz para probar el flujo.

La aplicación puede usarse sin `GEMINI_API_KEY`, pero la generación de resúmenes con IA no estará disponible. El backend necesita conectividad saliente para llamar a Gemini cuando esa función se usa. El modo de red `mirrored` de WSL, si se necesita en una máquina concreta, es una configuración local de Windows/WSL y no una dependencia del repositorio. Si Gemini no conecta, verifica primero la conectividad desde el contenedor del backend; cambia la configuración de red de WSL solo si tu entorno lo requiere.

Esta configuración es para desarrollo local, no para producción. Antes de desplegar en producción, configura secretos seguros, `DJANGO_DEBUG=false` y revisa hosts, orígenes permitidos, exposición de puertos y el servidor de aplicaciones.

Compose espera a que el health check de MySQL termine antes de iniciar Django. Si falta una variable, la contraseña no cumple las validaciones o una migración falla, el backend no continúa como si hubiera iniciado correctamente. Al reiniciar, el usuario administrador existente se conserva.

## Acceso

- Frontend React/Vite: <http://localhost:5173>
- Backend: <http://localhost:8000>
- Health check: <http://localhost:8000/api/health/>
- API browsable existente: <http://localhost:8000/api/>
- Listar solicitudes: `GET http://localhost:8000/api/requests/`
- Crear solicitud: `POST http://localhost:8000/api/requests/`
- Consultar estados: `GET http://localhost:8000/api/statuses/`
- Iniciar sesión: `POST http://localhost:8000/api/auth/login/`
- Cerrar sesión: `POST http://localhost:8000/api/auth/logout/`
- Esquema OpenAPI: <http://localhost:8000/api/schema/>
- Swagger UI: <http://localhost:8000/api/docs/>
- MySQL: solo en la red privada de Compose, en `db:3306`; no se publica un puerto en el host.

El esquema OpenAPI y Swagger UI permiten consultar y probar la API cuando Docker Compose está ejecutándose.

`GET /api/requests/` devuelve una página de hasta 10 resultados con `count`, `next`, `previous` y `results`. Se puede navegar con `page`, cambiar el tamaño con `page_size` (máximo 100), buscar en título y descripción con `search` (o `q`), filtrar por `status` usando su `tag` y filtrar fechas con `start_date`/`end_date`. Si se omiten ambas fechas, se muestran las solicitudes de los últimos siete días. Cada resultado contiene el estado como objeto `{ "tag": "...", "name": "..." }`. `POST /api/requests/` recibe únicamente `title` y `description`; el backend busca y asigna automáticamente el estado cuyo `tag` es `created`. Internamente, `Request` se relaciona con `Status` mediante su clave primaria numérica; la API no expone ese ID interno. `GET /api/statuses/` devuelve cada estado con `tag` y `name`; el catálogo se administra mediante migraciones y no ofrece operaciones de escritura por API.

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

La respuesta contiene `{"token":"..."}`. En las siguientes peticiones, incluye el token como `Authorization: Bearer <token>` o `Authorization: Token <token>`. Por ejemplo:

```bash
curl http://localhost:8000/api/statuses/ \
  -H 'Authorization: Bearer TU_TOKEN'
```

Para invalidar el token actual:

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H 'Authorization: Bearer TU_TOKEN'
```

Swagger UI en `/api/docs/` ofrece el botón **Authorize** para introducir únicamente el valor del token; Swagger añade el prefijo `Bearer` al encabezado `Authorization`. El health check, el esquema OpenAPI y Swagger UI permanecen públicos; los endpoints de negocio requieren token.

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
