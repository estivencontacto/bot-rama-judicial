from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Consulta, Usuario, UsuarioRol
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.schemas.consultas import ConsultaEstadoResponse, EjecutarConsultaRequest, EjecutarConsultaResponse
from backend.app.services.audit_service import registrar_auditoria
from backend.app.services.consulta_service import crear_consulta_pendiente, lanzar_consulta_background


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def _consulta_response(consulta: Consulta) -> ConsultaEstadoResponse:
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


@router.post("/run", response_model=EjecutarConsultaResponse)
def run_monitoring(
    payload: EjecutarConsultaRequest | None = None,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> EjecutarConsultaResponse:
    """Encola una ejecucion del scraper reutilizando el flujo estable actual."""
    numeros = payload.radicados if payload else None
    cliente = (payload.cliente or "").strip() if payload else None
    cliente = cliente or None
    consulta = crear_consulta_pendiente(db=db, usuario=current_user, numeros=numeros, etiqueta=cliente)
    lanzar_consulta_background(consulta_id=consulta.id, usuario_id=current_user.id, numeros=numeros, etiqueta=cliente)
    registrar_auditoria(
        db,
        current_user,
        "monitoring.run",
        f"Monitoreo encolado #{consulta.id}",
        "consulta",
        str(consulta.id),
        {"total_radicados": consulta.total_radicados, "cliente": cliente},
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


@router.get("/history", response_model=list[ConsultaEstadoResponse])
def monitoring_history(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConsultaEstadoResponse]:
    """Lista las ultimas ejecuciones del usuario autenticado."""
    consultas = (
        db.query(Consulta)
        .filter(Consulta.usuario_id == current_user.id)
        .order_by(Consulta.id.desc())
        .limit(50)
        .all()
    )
    return [_consulta_response(item) for item in consultas]
