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
backend/
  api/          Modelos, serializadores, vistas, autenticación, lógica de estados,
                integración de resúmenes, pruebas y migraciones Django
  config/       Configuración, rutas, middleware CORS y entradas ASGI/WSGI
  manage.py     Comandos de administración Django
  Dockerfile    Imagen de desarrollo del backend
frontend/
  src/
    components/ Componentes y pantallas React
    services/   Clientes de API y autenticación
  package.json  Dependencias y comandos Vite
  Dockerfile    Imagen de desarrollo del frontend
database/
  init.sql      Punto de entrada para inicialización SQL adicional (vacío actualmente)
.env.example    Plantilla de variables locales; copiar como .env
docker-compose.yml  Orquestación de MySQL, backend y frontend
```

## Arquitectura y decisiones

- **Aplicación separada en cliente y API:** React/Vite sirve la interfaz y Django REST Framework expone la API; el navegador accede al backend mediante `VITE_API_BASE_URL`.
- **Servicios locales en contenedores:** Docker Compose ejecuta MySQL, Django y Vite. Las comprobaciones de salud hacen que el backend espere a MySQL y el frontend al backend.
- **MySQL como persistencia:** Django usa `mysqlclient`; las migraciones versionadas administran el esquema y los datos iniciales del catálogo de estados.
- **Estado controlado por el backend:** al crear una solicitud, el servidor asigna el estado `created`. El cliente no puede enviar un estado arbitrario al crearla. El catálogo no tiene rutas de escritura.
- **Transiciones validadas:** los cambios de estado se restringen a las transiciones del dominio, no a cualquier estado existente.
- **Autenticación por token:** las rutas de negocio requieren token DRF. La API acepta los esquemas `Token` y `Bearer`; health check, esquema y documentación son públicos.
- **Integración de IA opcional:** la generación de resúmenes llama a Gemini solo cuando se solicita y se configura `GEMINI_API_KEY`; las solicitudes siguen disponibles sin esa clave.
- **Configuración explícita de CORS:** el middleware propio admite únicamente los orígenes definidos en `CORS_ALLOWED_ORIGINS`, sin comodines ni credenciales.
- **Documentación de API generada:** `drf-spectacular` publica el esquema OpenAPI y Swagger UI a partir de las rutas y serializadores.

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
- Generar resumen: `GET http://localhost:8000/api/requests/summary/`
- Editar título y descripción: `PUT http://localhost:8000/api/requests/{id}/`
- Cambiar estado: `PATCH http://localhost:8000/api/requests/{id}/`
- Consultar estados: `GET http://localhost:8000/api/statuses/`
- Iniciar sesión: `POST http://localhost:8000/api/auth/login/`
- Cerrar sesión: `POST http://localhost:8000/api/auth/logout/`
- Esquema OpenAPI: <http://localhost:8000/api/schema/>
- Swagger UI: <http://localhost:8000/api/docs/>
- MySQL: `127.0.0.1:3306` desde el host y `db:3306` desde la red de Compose. El puerto está enlazado a la interfaz local, no a todas las interfaces.

El esquema OpenAPI y Swagger UI permiten consultar y probar la API cuando Docker Compose está ejecutándose.

### Endpoints principales

| Método y ruta | Autenticación | Uso |
|---|---|---|
| `GET /api/health/` | Pública | Comprueba que el backend responde (`{"status":"ok"}`). |
| `POST /api/auth/login/` | Pública | Recibe `username` y `password`; devuelve un token. |
| `POST /api/auth/logout/` | Token | Elimina el token del usuario autenticado. |
| `GET /api/requests/` | Token | Lista solicitudes paginadas; admite búsqueda y filtros. |
| `POST /api/requests/` | Token | Crea una solicitud con `title` y `description`; el servidor asigna el estado inicial. |
| `PUT /api/requests/{id}/` | Token | Actualiza únicamente `title` y `description`. |
| `PATCH /api/requests/{id}/` | Token | Actualiza únicamente `status`, usando el `tag` del estado. |
| `GET /api/requests/summary/` | Token | Resume hasta 50 solicitudes recientes del rango consultado. |
| `GET /api/statuses/` | Token | Devuelve el catálogo de estados (`tag` y `name`). |
| `GET /api/schema/` | Pública | Devuelve el esquema OpenAPI. |
| `GET /api/docs/` | Pública | Abre Swagger UI. |

`GET /api/requests/` devuelve una página de hasta 10 resultados con `count`, `next`, `previous` y `results`. Se puede navegar con `page`, cambiar el tamaño con `page_size` (máximo 100), buscar en título y descripción con `search` (o `q`), filtrar por `status` usando su `tag` y filtrar fechas con `start_date`/`end_date`. Si se omiten ambas fechas, se muestran las solicitudes de los últimos siete días. Cada resultado contiene el estado como objeto `{ "tag": "...", "name": "..." }`. `POST /api/requests/` recibe únicamente `title` y `description`; el backend busca y asigna automáticamente el estado cuyo `tag` es `created`. Internamente, `Request` se relaciona con `Status` mediante su clave primaria numérica; la API no expone ese ID interno. `GET /api/statuses/` devuelve cada estado con `tag` y `name`; el catálogo se administra mediante migraciones y no ofrece operaciones de escritura por API.

Para cambiar el estado, envía `PATCH /api/requests/{id}/` con `{"status":"<tag>"}`. Las transiciones permitidas son:

| Estado actual | Siguientes estados permitidos |
|---|---|
| `created` | `in_review` |
| `in_review` | `in_progress`, `paused` |
| `in_progress` | `done`, `paused` |
| `paused` | `in_progress`, `in_review` |
| `done` | Ninguno (estado final) |

`PUT /api/requests/{id}/` reemplaza los campos editables y solo acepta `title` y `description`; para cambiar el estado usa `PATCH`. Ambos métodos devuelven la solicitud actualizada.

`GET /api/requests/summary/` usa por defecto los últimos siete días. Para un rango personalizado, envía ambos parámetros `start_date` y `end_date` con fechas ISO inclusivas (por ejemplo, `?start_date=2026-01-01&end_date=2026-01-07`). La respuesta exitosa contiene `success`, `summary` y `request_count`. Se procesan como máximo las 50 solicitudes más recientes del rango; si no hay solicitudes, devuelve un mensaje sin llamar a Gemini. Si falta la clave o Gemini no está disponible, responde `503`.

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

## Base de datos

- **Motor y base:** MySQL 8.4.8; por defecto la base se llama `requests_db`. El nombre, usuario y contraseñas se configuran con `DB_NAME`, `DB_USER`, `DB_PASSWORD` y `DB_ROOT_PASSWORD` en `.env`.
- **Conexión desde la aplicación:** Django se conecta al servicio Compose `db` en el puerto `3306`, con codificación `utf8mb4`. Desde el host, MySQL está disponible en `127.0.0.1:3306` para herramientas locales.
- **Persistencia:** el volumen Docker `mysql_data` conserva la información al detener o recrear los contenedores. `docker compose down` no elimina ese volumen.
- **Inicialización y esquema:** `database/init.sql` está reservado para SQL de inicialización adicional y actualmente no define tablas de negocio. Las migraciones Django crean y evolucionan el esquema; se ejecutan automáticamente al iniciar el backend.

Tablas principales de la aplicación:

| Tabla | Campos relevantes | Relación y reglas |
|---|---|---|
| `requests` | `id`, `title` (máx. 200), `description`, `status_id`, `created_at`, `updated_at` | Cada solicitud referencia un registro de `status`. La referencia está protegida: no se puede borrar un estado que esté en uso. |
| `status` | `id`, `tag` (único, máx. 20), `name` (máx. 100) | Catálogo cargado por migraciones: `created`, `in_review`, `in_progress`, `paused` y `done`. |

Django también crea las tablas que necesita para usuarios, sesiones, permisos y tokens de autenticación. La base no incluye solicitudes de ejemplo. No guardes credenciales reales en el repositorio ni compartas el archivo `.env`.

## Migraciones

Las migraciones se aplican al iniciar el servicio. La migración del catálogo crea automáticamente los cinco estados iniciales y convierte las solicitudes existentes sin eliminar sus datos. Para ejecutarlas manualmente:

```bash
docker compose exec backend python manage.py migrate
```

Para comprobar la configuración Django:

```bash
docker compose exec backend python manage.py check
```

## Uso de IA

- **Asistencia durante esta revisión y actualización de la documentación:** asistente de IA integrado en VS Code (GitHub Copilot, mediante Copilot SDK), para contrastar el README con la configuración y el código del repositorio.
- **IA integrada en la aplicación:** Gemini API de Google, llamada desde el backend; `GEMINI_API_KEY` es opcional. Para los resúmenes se envían a Gemini el título, el estado y la fecha de creación de hasta 50 solicitudes recientes; no se envía la descripción. No se realiza la llamada si no hay solicitudes que resumir.

La clave de Gemini se configura como variable de entorno y no debe incluirse en el repositorio.

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
