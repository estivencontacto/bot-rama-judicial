from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RadicadoRead(BaseModel):
    id: int
    numero: str
    etiqueta: str | None = None
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadResult(BaseModel):
    total_recibidos: int
    total_creados: int
    total_existentes: int


class RadicadoCreate(BaseModel):
    numeros: list[str]
