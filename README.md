# Sistema Judicial 2.0

Backend profesional en Python para monitorear procesos judiciales de la Rama Judicial de Colombia. El proyecto conserva el bot funcional original y lo evoluciona hacia una API REST con FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT, Selenium, Pandas/OpenPyXL, Telegram y Docker.

Proyecto de autoria de **Estiven (estivencontacto)**.

![Demo del flujo](docs/assets/demo-flujo.svg)

## Estado Actual Del Refactor

El repositorio ya contenia una base backend avanzada en `backend/app`. Esta iteracion mantiene esa funcionalidad y agrega una capa REST 2.0 con endpoints en ingles para portafolio:

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- CRUD `/processes`
- `POST /monitoring/run`
- `GET /monitoring/history`
- `GET /reports/excel`
- `POST /notifications/test`

Los endpoints historicos en espanol siguen disponibles para no romper el dashboard existente:

- `/radicados`
- `/consultas`
- `/procesos`
- `/reportes`
- `/notificaciones`
- `/programacion`

## Diagnostico Del Bot Original

La logica funcional existente se conserva:

- Scraping Selenium: `backend/app/services/scraper_service.py`
  - Inicializa Chrome/Edge.
  - Consulta la Rama Judicial por numero de radicado.
  - Extrae juzgado, partes, fechas y actuaciones.
  - Maneja retries y errores controlados por radicado.

- Orquestacion del monitoreo: `backend/app/services/consulta_service.py`
  - Toma radicados activos.
  - Ejecuta Selenium.
  - Persiste procesos, actuaciones, errores y reportes.
  - Envia Telegram cuando detecta novedades.

- Reportes Excel: `backend/app/services/report_service.py` y `backend/app/services/excel_service.py`
  - `report_service.py` exporta resultados con Pandas/OpenPyXL.
  - `excel_service.py` lee plantillas Excel para carga masiva.

- Estado JSON legado: `src/estado.py`
  - Construye hashes por radicado.
  - Guarda estado en JSON.
  - Se conserva como compatibilidad del bot local original.
  - La API nueva migra esa idea a PostgreSQL mediante `procesos.estado_hash`, `actuaciones`, `consultas` y `errores`.

- Telegram: `backend/app/services/notification_service.py`
  - Construye mensajes operativos.
  - Envia mensajes a Telegram.
  - Existe alias 2.0 en `backend/app/services/telegram_service.py`.

## Arquitectura

La aplicacion vive bajo `backend/app` para integrarse con Docker y con el frontend existente. Se agregaron archivos puente para coincidir con la arquitectura 2.0 propuesta sin romper imports existentes.

```text
backend/
  app/
    main.py
    core/
      config.py          alias 2.0 de settings.py
      security.py        JWT, hashing y refresh tokens
      settings.py        configuracion desde .env
    database/
      connection.py      alias 2.0 de session.py
      models.py          re-export de modelos ORM
      session.py         engine, SessionLocal y get_db
    models/
      entities.py        modelos SQLAlchemy existentes
    modules/
      auth/
      users/
      judicial_processes/
      monitoring/
      notifications/
      reports/
    routers/
      auth.py
      users.py
      processes.py
      monitoring.py
      reports.py
      notifications.py
      ...routers legacy
    services/
      scraper_service.py
      telegram_service.py
      notification_service.py
      excel_service.py
      report_service.py
      consulta_service.py
    repositories/
      __init__.py        preparado para extraer consultas compartidas
    schemas/
    utils/
  alembic/
    versions/

src/
  bot local original y compatibilidad JSON

data/
  listado_radicados_template.xlsx
```

## Modelo De Datos

La base usa PostgreSQL con SQLAlchemy y Alembic. Las tablas actuales estan en espanol porque vienen del proyecto funcional:

- `usuarios` cumple el rol de `users`.
- `radicados` almacena numeros monitoreados por usuario/organizacion.
- `procesos` cumple el rol de `judicial_processes`.
- `consultas` cumple el rol de `monitoring_runs`.
- `actuaciones` y `errores` complementan los resultados de monitoreo.
- `notificaciones` almacena configuracion Telegram.
- `reportes` registra archivos Excel generados.

Cada proceso expuesto por `/processes` incluye:

- `id`
- `user_id`
- `numero_radicado`
- `demandante`
- `demandado`
- `juzgado`
- `ultima_actuacion`
- `fecha_ultima_actuacion`
- `estado`
- `created_at`
- `updated_at`

## Requisitos

- Python 3.10 o superior.
- PostgreSQL 14+.
- Docker y Docker Compose para ejecucion contenerizada.
- Chrome/Chromium o Edge para Selenium.
- Token y chat ID de Telegram si se usaran notificaciones.

## Instalacion Local

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Configura `.env` y ejecuta migraciones:

```powershell
alembic -c backend/alembic.ini upgrade head
```

Crear usuario administrador opcional:

```powershell
python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

Levantar API:

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Documentacion interactiva:

```text
http://127.0.0.1:8000/docs
```

## Uso Con Docker

```bash
cp .env.example .env
docker compose up --build
```

Ejecutar migraciones:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

Crear admin:

```bash
docker compose exec backend python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

Servicios:

```text
Backend:    http://localhost:8000
Docs:       http://localhost:8000/docs
Frontend:   http://localhost:3000
PostgreSQL: localhost:5432
Redis:      localhost:6379
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

CORS_ORIGINS=http://localhost:3000,http://localhost:5173

RAMA_JUDICIAL_URL=https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicacion
SELENIUM_BROWSER=edge
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT_SECONDS=20
SCRAPER_MAX_RETRIES=3
SCRAPER_RETRY_DELAY_SECONDS=2

TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID
TELEGRAM_MAX_CHARS=4000
```

## Ejemplos De Endpoints

Registrar usuario:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"demo@example.com\",\"password\":\"demo12345\",\"nombre\":\"Demo\"}"
```

Login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"demo@example.com\",\"password\":\"demo12345\"}"
```

Crear proceso judicial:

```bash
curl -X POST http://localhost:8000/processes \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"numero_radicado\":\"11001310300120240000100\",\"demandante\":\"Persona A\",\"demandado\":\"Persona B\",\"juzgado\":\"Juzgado 1\",\"estado\":\"monitoreado\"}"
```

Listar procesos:

```bash
curl -H "Authorization: Bearer ACCESS_TOKEN" http://localhost:8000/processes
```

Ejecutar monitoreo:

```bash
curl -X POST http://localhost:8000/monitoring/run \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}"
```

Descargar Excel:

```bash
curl -L -H "Authorization: Bearer ACCESS_TOKEN" http://localhost:8000/reports/excel -o reporte.xlsx
```

Probar Telegram:

```bash
curl -X POST -H "Authorization: Bearer ACCESS_TOKEN" http://localhost:8000/notifications/test
```

## Seguridad

- Autenticacion JWT con access token.
- Refresh tokens persistidos como hash.
- Hash de password con Passlib.
- Rutas de procesos, monitoreo, reportes y notificaciones requieren usuario autenticado.
- `/processes` filtra por `usuario_id` para que cada usuario vea solo sus procesos.
- Las credenciales sensibles se leen desde `.env`.

## Scraping Y Manejo De Errores

El scraper mantiene la logica Selenium existente. Cada radicado se consulta con retries y, si falla, se registra el error sin detener toda la ejecucion. Cuando hay cambios, `consulta_service.py` actualiza el hash del proceso, registra actuaciones y envia notificaciones Telegram de forma segura.

## Reportes

Los reportes se generan con Pandas/OpenPyXL. La API permite descargar un Excel desde:

```text
GET /reports/excel
```

Los archivos se guardan en:

```text
output/reports/
```

## Proximas Mejoras

- Extraer consultas SQLAlchemy repetidas hacia `repositories/`.
- Crear migraciones con nombres de tablas en ingles para una version 3.0, si se decide abandonar compatibilidad con tablas actuales.
- Agregar tests unitarios para auth, procesos y servicios.
- Agregar tests de integracion con base de datos temporal.
- Implementar permisos por organizacion mas finos.
- Agregar observabilidad con logs estructurados y metricas.
- Crear pipeline CI para lint, tests y build Docker.

## Commits Sugeridos

```text
feat(auth): add public register endpoint
feat(api): expose judicial system 2.0 REST routes
refactor(architecture): add compatibility layers for config, database and telegram services
docs(readme): document Sistema Judicial 2.0 architecture and usage
```
