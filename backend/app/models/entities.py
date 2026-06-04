"""Modelos SQLAlchemy del dominio comercial.

Las tablas cubren multiempresa, usuarios, radicados, procesos, consultas,
historial, errores, notificaciones, reportes y auditoria.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


def utcnow() -> datetime:
    """Fecha UTC consistente para auditoria y timestamps."""
    return datetime.now(timezone.utc)


class ConsultaEstado(str, enum.Enum):
    pendiente = "pendiente"
    ejecutando = "ejecutando"
    completada = "completada"
    fallida = "fallida"


class NotificacionCanal(str, enum.Enum):
    telegram = "telegram"
    email = "email"
    webhook = "webhook"


class UsuarioRol(str, enum.Enum):
    admin = "admin"
    operador = "operador"
    lectura = "lectura"


class Organizacion(Base):
    """Cliente o empresa que agrupa usuarios y radicados."""
    __tablename__ = "organizaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    limite_radicados: Mapped[int] = mapped_column(Integer, default=500)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="organizacion")


class Usuario(Base):
    """Cuenta autenticada con rol y controles basicos de seguridad."""
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizaciones.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[UsuarioRol] = mapped_column(Enum(UsuarioRol), default=UsuarioRol.admin)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    organizacion: Mapped[Optional[Organizacion]] = relationship(back_populates="usuarios")
    radicados: Mapped[List["Radicado"]] = relationship(back_populates="usuario")


class Radicado(Base):
    """Numero judicial monitoreado dentro de una organizacion."""
    __tablename__ = "radicados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(64), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    organizacion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizaciones.id"), index=True)
    etiqueta: Mapped[Optional[str]] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    usuario: Mapped[Usuario] = relationship(back_populates="radicados")
    proceso: Mapped[Optional["Proceso"]] = relationship(back_populates="radicado")
    consultas: Mapped[List["Consulta"]] = relationship(back_populates="radicado")

    __table_args__ = (Index("ix_radicados_org_numero", "organizacion_id", "numero", unique=True),)


class Proceso(Base):
    """Estado normalizado actual de un radicado consultado."""
    __tablename__ = "procesos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado_id: Mapped[int] = mapped_column(ForeignKey("radicados.id"), unique=True, index=True)
    juzgado: Mapped[Optional[str]] = mapped_column(String(255))
    demandante: Mapped[Optional[str]] = mapped_column(String(255))
    demandado: Mapped[Optional[str]] = mapped_column(String(255))
    partes: Mapped[Optional[str]] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(80), default="monitoreado")
    fecha_radicacion: Mapped[Optional[datetime]] = mapped_column(Date)
    fecha_ultima_actuacion: Mapped[Optional[datetime]] = mapped_column(Date)
    estado_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    radicado: Mapped[Radicado] = relationship(back_populates="proceso")
    actuaciones: Mapped[List["Actuacion"]] = relationship(back_populates="proceso")


class Consulta(Base):
    """Ejecucion del scraper con progreso, totales y estado."""
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado_id: Mapped[Optional[int]] = mapped_column(ForeignKey("radicados.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    estado: Mapped[ConsultaEstado] = mapped_column(Enum(ConsultaEstado), default=ConsultaEstado.pendiente)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_procesados: Mapped[int] = mapped_column(Integer, default=0)
    total_errores: Mapped[int] = mapped_column(Integer, default=0)
    total_radicados: Mapped[int] = mapped_column(Integer, default=0)
    total_novedades: Mapped[int] = mapped_column(Integer, default=0)
    radicado_actual: Mapped[Optional[str]] = mapped_column(String(64))
    ultimo_mensaje: Mapped[Optional[str]] = mapped_column(Text)

    radicado: Mapped[Optional[Radicado]] = relationship(back_populates="consultas")
    errores: Mapped[List["ErrorRegistro"]] = relationship(back_populates="consulta")


class Actuacion(Base):
    """Historial de cambios detectados por comparacion de estado."""
    __tablename__ = "actuaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proceso_id: Mapped[int] = mapped_column(ForeignKey("procesos.id"), index=True)
    fecha: Mapped[Optional[datetime]] = mapped_column(Date)
    titulo: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    proceso: Mapped[Proceso] = relationship(back_populates="actuaciones")


class ErrorRegistro(Base):
    """Error asociado a una consulta y radicado especifico."""
    __tablename__ = "errores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consulta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("consultas.id"), index=True)
    radicado: Mapped[str] = mapped_column(String(64), index=True)
    tipo: Mapped[str] = mapped_column(String(120))
    mensaje: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    consulta: Mapped[Optional[Consulta]] = relationship(back_populates="errores")


class Notificacion(Base):
    """Configuracion de canales de salida como Telegram."""
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    canal: Mapped[NotificacionCanal] = mapped_column(Enum(NotificacionCanal), default=NotificacionCanal.telegram)
    destino: Mapped[str] = mapped_column(String(255))
    bot_token: Mapped[Optional[str]] = mapped_column(String(255))
    habilitada: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @property
    def bot_token_configurado(self) -> bool:
        return bool(self.bot_token)


class Reporte(Base):
    """Archivo Excel generado despues de una consulta."""
    __tablename__ = "reportes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    ruta_archivo: Mapped[str] = mapped_column(String(500))
    total_procesos: Mapped[int] = mapped_column(Integer, default=0)
    total_errores: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditoriaEvento(Base):
    """Trazabilidad de acciones relevantes para operacion comercial."""
    __tablename__ = "auditoria_eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organizacion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("organizaciones.id"), index=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"), index=True)
    accion: Mapped[str] = mapped_column(String(120), index=True)
    entidad: Mapped[Optional[str]] = mapped_column(String(120))
    entidad_id: Mapped[Optional[str]] = mapped_column(String(80))
    descripcion: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RefreshToken(Base):
    """Refresh token persistido como hash para renovar sesiones."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProgramacionConsulta(Base):
    """Configuracion de ejecuciones recurrentes por usuario."""
    __tablename__ = "programaciones_consulta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True, index=True)
    habilitada: Mapped[bool] = mapped_column(Boolean, default=False)
    intervalo_horas: Mapped[int] = mapped_column(Integer, default=24)
    proxima_ejecucion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ultima_ejecucion: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
