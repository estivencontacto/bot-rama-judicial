from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class BusquedaProcesoRequest(BaseModel):
    numero_proceso: str
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    tipo_publicacion: str | None = None
    despacho: str | None = None
    ciudad: str | None = None


class ResumenProcesoBusqueda(BaseModel):
    despacho: str | None = None
    clase_proceso: str | None = None
    partes: dict[str, str | None] = Field(default_factory=dict)
    ultima_actuacion: str | None = None
    fecha_ultima_actuacion: str | None = None
    enlace_consulta: str | None = None


class PublicacionBusqueda(BaseModel):
    tipo: str
    fecha_publicacion: str | None = None
    despacho: str | None = None
    actuacion: str | None = None
    coincidencia: str
    documento_descargado: bool = False
    archivo: str | None = None
    url_descarga: str | None = None
    fuente_url: str | None = None


class BusquedaProcesoResponse(BaseModel):
    numero_proceso: str
    encontrado: bool
    resumen_proceso: ResumenProcesoBusqueda | None = None
    publicaciones_confirmadas: list[PublicacionBusqueda] = Field(default_factory=list)
    posibles_coincidencias: list[PublicacionBusqueda] = Field(default_factory=list)
    zip_descarga: str | None = None
    observaciones: str
