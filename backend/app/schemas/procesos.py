from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ActuacionRead(BaseModel):
    id: int
    fecha: date | None = None
    titulo: str
    descripcion: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcesoRead(BaseModel):
    radicado: str
    juzgado: str | None = None
    demandante: str | None = None
    demandado: str | None = None
    partes: str | None = None
    estado: str
    fecha_radicacion: date | None = None
    fecha_ultima_actuacion: date | None = None
    updated_at: datetime


class ProcesoDetail(ProcesoRead):
    historial: list[ActuacionRead] = []
