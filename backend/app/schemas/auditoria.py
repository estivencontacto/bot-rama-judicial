from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditoriaRead(BaseModel):
    id: int
    usuario_id: int | None = None
    accion: str
    entidad: str | None = None
    entidad_id: str | None = None
    descripcion: str
    metadata_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
