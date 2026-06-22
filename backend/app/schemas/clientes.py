from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ClienteCreate(BaseModel):
    nombre: str
    descripcion: str | None = None


class ClienteRead(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}
