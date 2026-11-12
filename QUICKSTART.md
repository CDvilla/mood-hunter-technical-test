# Levantamiento rápido

Guía directa para ejecutar el proyecto en desarrollo local.

## Requisitos

Docker Desktop con Docker Compose. En Windows, puedes ejecutar los comandos desde PowerShell o Windows Terminal; no es trictamente necesario abrir Ubuntu/WSL, pero es recomendable.

## Pasos

1. Clona el repositorio y entra en su carpeta:

   ```bash
   git clone https://github.com/CDvilla/mood-hunter-technical-test.git
   cd mood-hunter-technical-test
   ```

2. Crea y configura el archivo de entorno:

   ```bash
   cp .env.example .env
   ```

   Edita `.env` y define `DJANGO_SECRET_KEY`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DB_PASSWORD` y `DB_ROOT_PASSWORD`. `GEMINI_API_KEY` es opcional; se necesita para generar resúmenes con IA. No compartas ni subas `.env` a Git.

3. Opcional: si tienes problemas de conexión de red desde WSL, agrega a `%UserProfile%\.wslconfig` en Windows:

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

   Luego ejecuta `wsl --shutdown` en PowerShell y vuelve a abrir Ubuntu. Este ajuste es específico de algunos entornos; no es un requisito del proyecto.

4. Desde la carpeta del repositorio, construye e inicia los servicios:

   ```bash
   docker compose up --build
   ```

5. Abre <http://localhost:5173> e inicia sesión con el usuario y la contraseña definidos en `DJANGO_SUPERUSER_USERNAME` y `DJANGO_SUPERUSER_PASSWORD` en `.env`.

6. Para probar la API con Swagger, abre <http://localhost:8000/api/docs/>. Ejecuta `POST /api/auth/login/` con las mismas credenciales del paso anterior y copia el `token` de la respuesta. Pulsa **Authorize**, pega únicamente el token (sin escribir `Bearer`) y confirma. Swagger lo usará en las siguientes peticiones protegidas.
