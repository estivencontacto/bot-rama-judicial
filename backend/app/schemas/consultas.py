from __future__ import annotations

from pydantic import BaseModel


class EjecutarConsultaRequest(BaseModel):
    radicados: list[str] | None = None


class EjecutarConsultaResponse(BaseModel):
    consulta_id: int
    estado: str
    total_procesados: int
    total_errores: int
    total_novedades: int = 0
    total_radicados: int = 0
    radicado_actual: str | None = None
    ultimo_mensaje: str | None = None


class ConsultaEstadoResponse(EjecutarConsultaResponse):
    progreso: int = 0
