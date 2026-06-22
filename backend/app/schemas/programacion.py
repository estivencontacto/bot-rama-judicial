from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProgramacionRead(BaseModel):
    id: int
    habilitada: bool
    intervalo_horas: int
    proxima_ejecucion: datetime | None = None
    ultima_ejecucion: datetime | None = None

    model_config = {"from_attributes": True}


class ProgramacionUpdate(BaseModel):
    habilitada: bool
    intervalo_horas: int = Field(default=24, ge=1, le=168)
