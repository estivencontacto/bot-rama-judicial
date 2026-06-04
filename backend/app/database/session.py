"""Sesion SQLAlchemy compartida por la API.

Define la base declarativa, el engine y la dependencia `get_db` usada por los
routers para abrir y cerrar sesiones por request.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.settings import get_settings


class Base(DeclarativeBase):
    """Base comun para todos los modelos ORM."""
    pass


settings = get_settings()
# `pool_pre_ping` evita conexiones rotas en despliegues con PostgreSQL persistente.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesion por request y garantiza cierre al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
