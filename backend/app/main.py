"""Punto de entrada de la API comercial.

Configura FastAPI, CORS, routers REST y el scheduler liviano para consultas
programadas. La logica de negocio vive en servicios para mantener los routers
delgados.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.settings import get_settings
from backend.app.routers import admin, auth, consultas, dashboard, notificaciones, procesos, programacion, radicados, reportes
from backend.app.workers.scheduler import start_scheduler


settings = get_settings()
logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)

# Aplicacion principal expuesta por Uvicorn y Docker.
app = FastAPI(title=settings.app_name)

# CORS permite conectar el frontend local, Docker o el dominio productivo definido en .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers agrupados por dominio funcional.
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(radicados.router)
app.include_router(consultas.router)
app.include_router(procesos.router)
app.include_router(reportes.router)
app.include_router(dashboard.router)
app.include_router(notificaciones.router)
app.include_router(programacion.router)


@app.on_event("startup")
def on_startup() -> None:
    """Activa el scheduler interno al iniciar la API."""
    start_scheduler()


@app.get("/health")
def health() -> dict:
    """Endpoint liviano para verificar disponibilidad desde Docker o monitoreo."""
    return {"status": "ok", "service": settings.app_name}
