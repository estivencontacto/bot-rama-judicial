from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.models import Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.busqueda import BusquedaProcesoRequest, BusquedaProcesoResponse
from backend.app.services.proceso_busqueda_service import consultar_y_preparar_descarga
from backend.app.validators.process_validator import validar_numero_proceso


router = APIRouter(prefix="/api/procesos", tags=["busqueda-procesos"])


@router.post("/buscar", response_model=BusquedaProcesoResponse)
def buscar_proceso(
    payload: BusquedaProcesoRequest,
    current_user: Usuario = Depends(get_current_user),
) -> BusquedaProcesoResponse:
    """Busca un proceso y publicaciones relacionadas para descarga."""
    numero_proceso = validar_numero_proceso(payload.numero_proceso)
    return consultar_y_preparar_descarga(numero_proceso, payload)
