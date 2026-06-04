# Bot Rama Judicial

Sistema comercial de monitoreo de procesos judiciales de la Rama Judicial de Colombia. Permite cargar radicados masivamente, ejecutar scraping en segundo plano, detectar nuevas actuaciones, generar reportes en Excel y enviar notificaciones por Telegram desde un dashboard web.

Proyecto de autoria de **Estiven (estivencontacto)**.

![Demo del flujo](docs/assets/demo-flujo.svg)

## Que hace

- Consulta radicados judiciales usando Selenium.
- Mantiene la metodologia del bot original, pero con backend, frontend y base de datos.
- Carga radicados desde Excel o texto manual.
- Guarda procesos, actuaciones, consultas, errores, reportes y notificaciones.
- Muestra progreso del scraper en tiempo real.
- Envia mensajes a Telegram cuando detecta procesos nuevos o nuevas actuaciones.
- Genera reportes descargables en Excel.
- Incluye autenticacion JWT, roles, auditoria, scheduler y soporte Docker.

## Arquitectura

```text
backend/
  app/
    main.py              API FastAPI
    core/                configuracion y seguridad
    database/            SQLAlchemy y sesiones
    models/              modelos de base de datos
    schemas/             contratos Pydantic
    routers/             endpoints REST
    services/            scraping, Excel, Telegram, reportes y consultas
    workers/             scheduler y workers
    utils/               scripts de administracion
  alembic/               migraciones

frontend/
  index.html             dashboard web usado localmente
  app/                   version React en evolucion
  services/              cliente API

data/
  listado_radicados_template.xlsx

src/
  compatibilidad con el bot local original
```

## Flujo de uso

1. Inicia sesion en el dashboard.
2. Descarga la plantilla Excel desde la pantalla **Radicados**.
3. Completa la columna `Radicado`.
4. Carga el Excel en el dashboard.
5. Configura Telegram con el token del bot y el chat ID.
6. Ejecuta el scraper.
7. Revisa progreso, procesos, historial y reportes.
8. Recibe nuevas actuaciones por Telegram.

## Credenciales locales de prueba

```text
Email: admin@example.com
Password: admin123
```

Estas credenciales son solo para desarrollo local. En produccion deben cambiarse inmediatamente.

## Requisitos

- Python 3.9 o superior.
- PostgreSQL para uso productivo.
- Redis recomendado para colas comerciales.
- Microsoft Edge o Google Chrome para Selenium.
- Docker y Docker Compose si se usara contenedorizacion.

## Instalacion local rapida

1. Crear entorno virtual:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Crear archivo `.env` desde `.env.example`:

```powershell
copy .env.example .env
```

3. Configurar variables principales:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bot_rama_judicial
SECRET_KEY=cambia-esta-clave-en-produccion
SELENIUM_BROWSER=edge
SELENIUM_HEADLESS=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173
```

4. Ejecutar migraciones:

```powershell
alembic -c backend/alembic.ini upgrade head
```

5. Crear usuario administrador:

```powershell
python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

6. Ejecutar backend:

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

7. Ejecutar frontend estatico:

```powershell
py -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

8. Abrir:

```text
Frontend: http://127.0.0.1:5173/
Backend:  http://127.0.0.1:8000/docs
```

## Ejecucion local simplificada

El proyecto incluye un arranque local usado para verificacion:

```powershell
python start_backend.py
py -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

Este modo puede usar SQLite local para pruebas, pero para produccion se recomienda PostgreSQL.

## Uso de Telegram

En el dashboard abre **Configuracion** y completa:

- `Token del bot`: lo entrega BotFather al crear un bot con `/newbot`.
- `Chat ID`: se obtiene enviando un mensaje al bot y consultando:

```text
https://api.telegram.org/botTOKEN/getUpdates
```

Reemplaza `TOKEN` por el token real. En la respuesta busca `chat.id`.

Luego presiona **Guardar** y **Probar Telegram**. Si la prueba funciona, el scraper podra enviar:

- Nuevas actuaciones detectadas.
- Procesos registrados por primera vez.
- Resumen de consulta.

## Plantilla Excel

La plantilla esta en:

```text
data/listado_radicados_template.xlsx
```

Tambien se puede descargar desde el dashboard en **Radicados**.

La columna obligatoria es:

```text
Radicado
```

El sistema ignora duplicados y conserva solo radicados validos no vacios.

## Docker

1. Crear `.env`:

```bash
cp .env.example .env
```

2. Levantar servicios:

```bash
docker compose up --build
```

3. Ejecutar migraciones:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

4. Crear admin:

```bash
docker compose exec backend python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

Servicios:

```text
Frontend:   http://localhost:3000
Backend:    http://localhost:8000
PostgreSQL: localhost:5432
Redis:      localhost:6379
```

## Endpoints principales

```text
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me

GET  /radicados
POST /radicados
POST /radicados/upload
GET  /radicados/template

POST /consultas/ejecutar
GET  /consultas
GET  /consultas/{consulta_id}

GET  /procesos
GET  /procesos/{radicado}

GET  /reportes
GET  /reportes/{reporte_id}/download

GET  /dashboard/resumen

GET  /notificaciones
PUT  /notificaciones
POST /notificaciones/test

GET  /programacion
PUT  /programacion

GET  /admin/organizacion
PUT  /admin/organizacion
GET  /admin/usuarios
POST /admin/usuarios
PATCH /admin/usuarios/{usuario_id}
GET  /admin/auditoria
```

## Modelo de datos

- `organizaciones`: clientes o empresas.
- `usuarios`: cuentas, roles, seguridad y bloqueo de login.
- `radicados`: numeros judiciales monitoreados.
- `procesos`: estado actual normalizado.
- `actuaciones`: historial de cambios detectados.
- `consultas`: ejecuciones del scraper y progreso.
- `errores`: fallos por radicado o consulta.
- `notificaciones`: configuracion de Telegram.
- `reportes`: archivos Excel generados.
- `auditoria_eventos`: trazabilidad de acciones importantes.
- `refresh_tokens`: sesiones renovables almacenadas como hash.
- `programaciones_consulta`: ejecuciones automaticas por intervalo.

## Bot local original

La funcionalidad anterior se conserva para compatibilidad:

```powershell
python run.py
```

Este modo lee archivos locales, genera reportes y puede enviar Telegram segun la configuracion heredada. Para uso comercial se recomienda el dashboard con backend, base de datos y autenticacion.

## Problemas comunes

### No carga el frontend

Verifica que el servidor estatico este activo:

```powershell
py -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

Luego abre:

```text
http://127.0.0.1:5173/
```

Si el navegador conserva cache, usa `Ctrl + F5`.

### El Excel dice No autenticado

Inicia sesion de nuevo. El frontend renueva sesion automaticamente, pero si el refresh token expiro debe ingresarse otra vez.

### El Excel no carga radicados

Verifica que exista una columna llamada `Radicado`. Puede estar en la primera fila o dentro de la plantilla oficial.

### Telegram no envia

Revisa:

- El token del bot es correcto.
- El usuario escribio al bot antes de probar.
- El chat ID corresponde al chat donde quieres recibir alertas.
- El bot tiene permiso para escribir en ese chat.

### Selenium falla

Revisa:

- `SELENIUM_BROWSER=edge` o `SELENIUM_BROWSER=chrome`.
- El navegador esta instalado.
- `SELENIUM_HEADLESS=true` para ejecucion sin ventana.
- Capturas de error en `output/screenshots/`.

## Recomendaciones para produccion

- Usar PostgreSQL y Redis.
- Ejecutar el scraper con worker separado.
- Configurar backups de base de datos.
- Rotar `SECRET_KEY` y credenciales sensibles.
- Usar HTTPS y dominio propio.
- Agregar rate limiting por usuario.
- Centralizar logs en un servicio externo.
- Guardar reportes en S3, MinIO o almacenamiento equivalente.
- Agregar monitoreo de uptime y alertas.

## Licencia y autoria

Este proyecto es de autoria de **Estiven (estivencontacto)**. El codigo queda preparado para evolucionar como producto SaaS o herramienta comercial de automatizacion judicial.
