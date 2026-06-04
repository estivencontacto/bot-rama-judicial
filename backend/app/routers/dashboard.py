from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Consulta, ErrorRegistro, Notificacion, Proceso, Radicado, Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.dashboard import DashboardResumen


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumen", response_model=DashboardResumen)
def resumen(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResumen:
    total_radicados = db.query(Radicado).filter(Radicado.organizacion_id == current_user.organizacion_id).count()
    total_procesos = db.query(Proceso).join(Radicado).filter(Radicado.organizacion_id == current_user.organizacion_id).count()
    org_user_ids = [row.id for row in db.query(Usuario.id).filter(Usuario.organizacion_id == current_user.organizacion_id).all()]
    total_consultas = db.query(Consulta).filter(Consulta.usuario_id.in_(org_user_ids)).count() if org_user_ids else 0
    total_errores = (
        db.query(ErrorRegistro).join(Consulta).filter(Consulta.usuario_id.in_(org_user_ids)).count()
        if org_user_ids
        else 0
    )
    notificaciones = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id.in_(org_user_ids), Notificacion.habilitada.is_(True))
        .count()
    )
    return DashboardResumen(
        total_radicados=total_radicados,
        total_procesos=total_procesos,
        total_consultas=total_consultas,
        total_errores=total_errores,
        notificaciones_activas=notificaciones,
    )
