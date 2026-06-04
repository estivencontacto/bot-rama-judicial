"""Endpoints de ejecucion y seguimiento de consultas.

Exponen el inicio del scraper, el progreso en tiempo real y el historial reciente
de ejecuciones para alimentar la barra del dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Consulta, Usuario, UsuarioRol
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.schemas.consultas import ConsultaEstadoResponse, EjecutarConsultaRequest, EjecutarConsultaResponse
from backend.app.services.consulta_service import crear_consulta_pendiente, lanzar_consulta_background
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/consultas", tags=["consultas"])


@router.post("/ejecutar", response_model=EjecutarConsultaResponse)
def ejecutar_consulta(
    payload: EjecutarConsultaRequest,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> EjecutarConsultaResponse:
    """Crea una consulta pendiente y la encola para ejecucion en background."""
    consulta = crear_consulta_pendiente(db=db, usuario=current_user, numeros=payload.radicados)
    lanzar_consulta_background(consulta_id=consulta.id, usuario_id=current_user.id, numeros=payload.radicados)
    registrar_auditoria(
        db,
        current_user,
        "consulta.ejecutada",
        f"Consulta encolada #{consulta.id}",
        "consulta",
        str(consulta.id),
        {"total_radicados": consulta.total_radicados},
    )
    return EjecutarConsultaResponse(
        consulta_id=consulta.id,
        estado=consulta.estado.value,
        total_procesados=consulta.total_procesados,
        total_errores=consulta.total_errores,
        total_novedades=consulta.total_novedades,
        total_radicados=consulta.total_radicados,
        radicado_actual=consulta.radicado_actual,
        ultimo_mensaje=consulta.ultimo_mensaje,
    )


def _consulta_response(consulta: Consulta) -> ConsultaEstadoResponse:
    """Convierte el modelo de consulta en respuesta con porcentaje de avance."""
    total = consulta.total_radicados or 0
    progreso = int((consulta.total_procesados / total) * 100) if total else 0
    return ConsultaEstadoResponse(
        consulta_id=consulta.id,
        estado=consulta.estado.value,
        total_procesados=consulta.total_procesados,
        total_errores=consulta.total_errores,
        total_novedades=consulta.total_novedades,
        total_radicados=consulta.total_radicados,
        radicado_actual=consulta.radicado_actual,
        ultimo_mensaje=consulta.ultimo_mensaje,
        progreso=min(progreso, 100),
    )


@router.get("/{consulta_id}", response_model=ConsultaEstadoResponse)
def get_consulta(
    consulta_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConsultaEstadoResponse:
    """Devuelve el estado de una consulta especifica de la organizacion."""
    consulta = (
        db.query(Consulta)
        .join(Usuario, Usuario.id == Consulta.usuario_id)
        .filter(Consulta.id == consulta_id, Usuario.organizacion_id == current_user.organizacion_id)
        .first()
    )
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return _consulta_response(consulta)


@router.get("", response_model=list[ConsultaEstadoResponse])
def list_consultas(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConsultaEstadoResponse]:
    """Lista las ultimas ejecuciones para monitoreo operativo."""
    consultas = (
        db.query(Consulta)
        .join(Usuario, Usuario.id == Consulta.usuario_id)
        .filter(Usuario.organizacion_id == current_user.organizacion_id)
        .order_by(Consulta.id.desc())
        .limit(20)
        .all()
    )
    return [_consulta_response(item) for item in consultas]
