"""Compatibilidad de arquitectura 2.0 para la conexion de base de datos."""

from backend.app.database.session import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
