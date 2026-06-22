# Despliegue comercial

Este proyecto ya funciona como scraper operable desde frontend, con backend FastAPI, PostgreSQL, Redis/RQ, JWT, reportes, Telegram, consultas en segundo plano y programacion basica.

## Arquitectura recomendada

```text
Usuario -> HTTPS -> Frontend
Frontend -> API HTTPS -> FastAPI
FastAPI -> PostgreSQL
FastAPI -> Redis/RQ -> Worker Selenium headless
FastAPI -> Telegram API
```

Para un primer cliente real:

- VPS: Hetzner, DigitalOcean, AWS Lightsail o similar.
- Dominio: `app.tumarca.com`.
- HTTPS: Cloudflare + Caddy o Nginx.
- Base de datos: PostgreSQL administrado o contenedor con backups.
- Scraper: worker con navegador headless instalado.
- Cola: Redis + RQ.
- Logs: archivo + Sentry para errores.

## URLs sugeridas

```text
https://app.tumarca.com
https://api.tumarca.com
```

En una sola VPS tambien puede usarse:

```text
https://app.tumarca.com
https://app.tumarca.com/api
```

## Variables criticas

```env
DATABASE_URL=postgresql+psycopg://user:password@postgres:5432/bot_rama_judicial
REDIS_URL=redis://redis:6379/0
QUEUE_NAME=scraper_jobs
SECRET_KEY=clave-larga-aleatoria
SELENIUM_BROWSER=chrome
SELENIUM_HEADLESS=true
TELEGRAM_TOKEN=token-del-bot
CORS_ORIGINS=https://app.tumarca.com
```

## Checklist antes de vender

- Cambiar `SECRET_KEY`.
- Usar PostgreSQL, no SQLite.
- Configurar backups diarios.
- Activar HTTPS.
- Crear usuario admin real.
- Probar Telegram con el boton del frontend.
- Ejecutar consulta con pocos radicados antes de lotes grandes.
- Revisar capturas de error en `output/screenshots`.
- Definir limites por cliente: radicados, frecuencia y usuarios.
- Revisar roles por usuario: `admin`, `operador`, `lectura`.
- Revisar eventos en auditoria despues de acciones criticas.

## Escalamiento

El sistema usa Redis/RQ cuando `REDIS_URL` esta configurado. En local, si `REDIS_URL` esta vacio, usa threads como fallback para pruebas.

Para levantar el stack productivo:

```bash
docker compose up --build
docker compose exec backend alembic -c backend/alembic.ini upgrade head
docker compose exec backend python -m backend.app.utils.create_admin --email admin@example.com --password admin123 --nombre Admin
```

Para muchos clientes o miles de radicados, evaluar:

- Celery + Redis.
- RQ + Redis.
- Temporal.
- Dramatiq.

La UI ya esta preparada para consultar progreso por `consulta_id`, por lo que cambiar de RQ a otro motor de jobs no deberia romper el frontend.
