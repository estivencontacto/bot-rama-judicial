from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ActuacionRead(BaseModel):
    id: int
    fecha: date | None = None
    titulo: str
    descripcion: str | None = None
    importancia: str | None = None
    importante_auto: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcesoRead(BaseModel):
    radicado: str
    cliente: str | None = None
    juzgado: str | None = None
    demandante: str | None = None
    demandado: str | None = None
    partes: str | None = None
    ultima_actuacion: str | None = None
    ultima_anotacion: str | None = None
    estado: str
    fecha_radicacion: date | None = None
    fecha_ultima_actuacion: date | None = None
    auto_importante: bool = False
    fecha_auto_importante: date | None = None
    titulo_auto_importante: str | None = None
    updated_at: datetime


class ProcesoDetail(ProcesoRead):
    historial: list[ActuacionRead] = []


class JudicialProcessBase(BaseModel):
    numero_radicado: str
    demandante: str | None = None
    demandado: str | None = None
    juzgado: str | None = None
    ultima_actuacion: str | None = None
    fecha_ultima_actuacion: date | None = None
    estado: str = "monitoreado"


class JudicialProcessCreate(JudicialProcessBase):
    pass


class JudicialProcessUpdate(BaseModel):
    numero_radicado: str | None = None
    demandante: str | None = None
    demandado: str | None = None
    juzgado: str | None = None
    ultima_actuacion: str | None = None
    fecha_ultima_actuacion: date | None = None
    estado: str | None = None


class JudicialProcessRead(JudicialProcessBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
