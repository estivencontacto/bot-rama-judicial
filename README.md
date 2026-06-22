# Sistema Judicial 2.0

Sistema Judicial 2.0 es una aplicacion backend/frontend en Python para monitorear procesos judiciales de la Rama Judicial de Colombia, detectar novedades, guardar historial, generar reportes Excel y enviar alertas por Telegram.

El proyecto nace de un bot funcional de scraping y fue evolucionado a una aplicacion profesional para portafolio, con FastAPI, arquitectura por servicios, autenticacion JWT, clientes/bases de trabajo, reportes, Docker y una interfaz operativa propia.

Autor: **Estiven Agudelo**  
Contacto: **estivencontacto@gmail.com**

![Demo del flujo](docs/assets/demo-flujo.svg)

## Que Problema Resuelve

Revisar manualmente procesos judiciales consume tiempo y es facil pasar por alto actuaciones importantes. Este sistema permite:

- Cargar radicados por cliente, carpeta o base de trabajo.
- Ejecutar consultas automatizadas en la Rama Judicial.
- Guardar cada proceso y sus actuaciones en base de datos.
- Comparar ejecuciones nuevas contra el historial anterior.
- Alertar solo cuando hay cambios nuevos.
- Marcar actuaciones con la palabra `AUTO` como `IMPORTANTE AUTO`.
- Generar reportes Excel por cliente o generales.
- Consultar hojas de vida de procesos desde una interfaz web.

## Funcionalidades Principales

### Monitoreo judicial

- Scraper con Selenium y Chrome.
- Consulta por numero de radicado.
- Extraccion de juzgado, partes, fechas, ultima actuacion y actuaciones procesales.
- Manejo de errores por radicado para que una falla no detenga toda la ejecucion.
- Reintentos configurables desde `.env`.

### Clientes y bases separadas

- Creacion de clientes/carpetas.
- Carga de radicados por cliente.
- Busqueda sectorizada por cliente/base.
- Reportes filtrados por cliente.
- Ejecucion del scraper por todos los radicados o por cliente seleccionado.

### Historial inteligente

- La primera consulta crea la linea base del proceso.
- Las siguientes consultas comparan contra el historial guardado.
- Si no hay cambios, no se envia alerta.
- Si hay una actuacion nueva, se guarda y se notifica.
- Las actuaciones con `AUTO` se resaltan como `IMPORTANTE AUTO`.

### Interfaz web

- Dashboard operativo con metricas del sistema.
- Busqueda por radicado, demandante, demandado, despacho, tipo y cliente/base.
- Hoja de vida de proceso con historial de actuaciones.
- Gestion de radicados: agregar, editar, asignar cliente y eliminar.
- Configuracion de Telegram.
- Descarga de reportes Excel.
- Boton de soporte por WhatsApp.

### Reportes

- Reporte general en Excel.
- Reporte por cliente/base.
- Uso de Pandas y OpenPyXL.
- Descarga desde la API y desde el frontend.

### Notificaciones

- Integracion con Telegram.
- Token y chat ID configurables desde `.env` o desde el panel.
- Mensajes solo para novedades nuevas.
- Alertas especiales cuando la actuacion contiene `AUTO`.

## Stack Tecnico

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- SQLite para pruebas locales rapidas
- Selenium
- Pandas
- OpenPyXL
- JWT Authentication
- Docker y Docker Compose
- Telegram API
- HTML, CSS y JavaScript vanilla para el panel web

## Arquitectura

```text
backend/
  app/
    main.py
    core/
      settings.py
      config.py
      security.py
    database/
      session.py
      connection.py
      models.py
    models/
      entities.py
    routers/
      auth.py
      clientes.py
      radicados.py
      consultas.py
      procesos.py
      busqueda.py
      reportes.py
      notificaciones.py
      users.py
      processes.py
      monitoring.py
      reports.py
      notifications.py
    schemas/
    services/
      scraper_service.py
      consulta_service.py
      telegram_service.py
      notification_service.py
      excel_service.py
      report_service.py
      rama_judicial_service.py
      publicaciones_service.py
      document_downloader.py
      zip_service.py
      matching_service.py
    validators/
      process_validator.py
    workers/
  alembic/

frontend/
  index.html
  app/
  services/

src/
  bot original compatible con estado JSON

data/
  plantilla Excel para radicados
```

## Flujo De Uso

1. Crear o iniciar sesion.
2. Crear un cliente/base de trabajo.
3. Cargar radicados manualmente o por Excel.
4. Ejecutar el scraper.
5. Revisar procesos consultados.
6. Abrir la hoja de vida del proceso.
7. Descargar reporte Excel.
8. Configurar Telegram para recibir nuevas actuaciones.

## Instalacion Local

### 1. Crear entorno virtual

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Crear archivo de entorno

```powershell
copy .env.example .env
```

Para pruebas rapidas puedes usar SQLite:

```env
DATABASE_URL=sqlite:///./local_sistema_judicial.db
REDIS_URL=
SELENIUM_BROWSER=chrome
SELENIUM_HEADLESS=false
```

Para PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bot_rama_judicial
```

### 4. Ejecutar migraciones

```powershell
alembic -c backend/alembic.ini upgrade head
```

### 5. Crear administrador

```powershell
python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

### 6. Levantar backend

```powershell
python start_backend.py
```

Backend:

```text
http://127.0.0.1:8010
```

Swagger:

```text
http://127.0.0.1:8010/docs
```

### 7. Levantar frontend estatico

```powershell
python -m http.server 5173 --bind 0.0.0.0 --directory frontend
```

Frontend:

```text
http://127.0.0.1:5173
```

Si quieres verlo desde otro dispositivo en la misma red, usa la IP local:

```text
http://TU_IP_LOCAL:5173
```

## Uso Con Docker

```bash
cp .env.example .env
docker compose up --build
```

Servicios esperados:

```text
Backend:    http://localhost:8000
Docs:       http://localhost:8000/docs
Frontend:   http://localhost:3000
PostgreSQL: localhost:5432
Redis:      localhost:6379
```

Migraciones dentro de Docker:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

Crear admin:

```bash
docker compose exec backend python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

## Variables De Entorno

```env
APP_NAME=Sistema Judicial 2.0 API
ENVIRONMENT=local
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bot_rama_judicial
REDIS_URL=redis://localhost:6379/0
QUEUE_NAME=scraper_jobs

SECRET_KEY=change-me-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=14
ALGORITHM=HS256

FRONTEND_ORIGIN=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

RAMA_JUDICIAL_URL=https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicacion
SELENIUM_BROWSER=chrome
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT_SECONDS=20
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY_SECONDS=2
STORAGE_DIR=backend/storage

TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
TELEGRAM_MAX_CHARS=4000
```

## Endpoints Principales

### Autenticacion

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
```

### Usuarios

```text
GET /users/me
```

### Procesos judiciales

```text
POST   /processes
GET    /processes
GET    /processes/{id}
PUT    /processes/{id}
DELETE /processes/{id}
```

### Operacion legacy del sistema

```text
GET    /clientes
POST   /clientes
DELETE /clientes/{id}

GET    /radicados
POST   /radicados
PUT    /radicados/{id}
DELETE /radicados/{id}
POST   /radicados/upload

POST   /consultas/ejecutar
GET    /consultas
GET    /consultas/{id}

GET    /procesos
GET    /procesos/{radicado}

GET    /reportes
GET    /reportes/excel

GET    /notificaciones
PUT    /notificaciones
POST   /notificaciones/test
```

### Busqueda oficial y descargas

```text
POST /api/procesos/buscar
GET  /downloads/{archivo}
```

Ejemplo:

```bash
curl -X POST http://localhost:8010/api/procesos/buscar \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"numero_proceso\":\"11001310300120240012300\",\"tipo_publicacion\":\"auto\"}"
```

## Ejemplos Rapidos

Login:

```bash
curl -X POST http://localhost:8010/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}"
```

Cargar radicado:

```bash
curl -X POST http://localhost:8010/radicados \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"numeros\":[\"11001310300120240012300\"],\"etiqueta\":\"Cliente Demo\"}"
```

Ejecutar monitoreo:

```bash
curl -X POST http://localhost:8010/consultas/ejecutar \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"cliente\":\"Cliente Demo\"}"
```

Descargar reporte por cliente:

```bash
curl -L "http://localhost:8010/reportes/excel?cliente=Cliente%20Demo" -o reporte_cliente.xlsx
```

## Modelo De Datos

Tablas principales:

- `usuarios`
- `organizaciones`
- `clientes`
- `radicados`
- `procesos`
- `actuaciones`
- `consultas`
- `errores`
- `notificaciones`
- `reportes`
- `auditoria`

Campos relevantes de proceso:

- `id`
- `radicado_id`
- `juzgado`
- `demandante`
- `demandado`
- `partes`
- `fecha_radicacion`
- `fecha_ultima_actuacion`
- `estado`
- `estado_hash`
- `raw_data`
- `created_at`
- `updated_at`

## Seguridad

- Autenticacion JWT.
- Refresh tokens persistidos como hash.
- Passwords protegidos con Passlib.
- Rutas operativas protegidas por usuario autenticado.
- Separacion por organizacion/usuario.
- Variables sensibles fuera del repositorio mediante `.env`.
- `.gitignore` evita subir `.env`, `.venv`, bases locales, `output/` y `backend/storage/`.

## Scraping

Archivo principal:

```text
backend/app/services/scraper_service.py
```

Caracteristicas:

- Selenium con Chrome.
- Timeouts configurables.
- Reintentos por radicado.
- Extraccion de actuaciones.
- Manejo de errores controlados.
- Compatible con ejecucion local visible o headless.

## Telegram

Servicios:

```text
backend/app/services/telegram_service.py
backend/app/services/notification_service.py
```

El sistema envia mensajes cuando encuentra nuevas actuaciones. Si no hay cambios frente al historial anterior, no envia alerta.

## Compatibilidad Con El Bot Original

El bot inicial se conserva en:

```text
src/
```

Ese modulo mantiene compatibilidad con estado JSON y ejecucion local original. La nueva aplicacion migra progresivamente esa persistencia a base de datos.

## Estado Del Proyecto

Completado:

- API REST con FastAPI.
- Auth JWT.
- Modelos SQLAlchemy.
- Migraciones Alembic.
- Scraper Selenium reutilizado.
- Clientes/bases de trabajo.
- Historial de actuaciones.
- Alertas por nuevas actuaciones.
- Deteccion de `IMPORTANTE AUTO`.
- Reportes Excel.
- Telegram.
- Docker.
- Frontend operativo.
- README profesional.

En progreso:

- Endurecer scraping de Publicaciones Procesales cuando el portal cambie HTML o requiera navegacion dinamica avanzada.
- Agregar suite de tests automatizados.
- Crear CI/CD en GitHub Actions.
- Mejorar roles y permisos por organizacion.
- Agregar busqueda full text en base de datos.

## Roadmap

- Tests unitarios para auth, procesos, clientes y reportes.
- Tests de integracion con base temporal.
- Worker de monitoreo con cola robusta.
- Panel de auditoria mas visual.
- Exportacion PDF de hoja de vida.
- Deploy productivo con dominio y HTTPS.
- Observabilidad con logs estructurados.

## Licencia

Proyecto con licencia MIT. Ver `LICENSE`.
