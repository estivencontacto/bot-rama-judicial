from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import ProgramacionConsulta, Usuario, UsuarioRol, utcnow
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.schemas.programacion import ProgramacionRead, ProgramacionUpdate
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/programacion", tags=["programacion"])


def _get_or_create(db: Session, usuario_id: int) -> ProgramacionConsulta:
    item = db.query(ProgramacionConsulta).filter(ProgramacionConsulta.usuario_id == usuario_id).first()
    if item:
        return item
    item = ProgramacionConsulta(
        usuario_id=usuario_id,
        habilitada=False,
        intervalo_horas=24,
        proxima_ejecucion=utcnow() + timedelta(hours=24),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=ProgramacionRead)
def get_programacion(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> ProgramacionConsulta:
    return _get_or_create(db, current_user.id)


@router.put("", response_model=ProgramacionRead)
def update_programacion(
    payload: ProgramacionUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgramacionConsulta:
    item = _get_or_create(db, current_user.id)
    item.habilitada = payload.habilitada
    item.intervalo_horas = payload.intervalo_horas
    item.proxima_ejecucion = utcnow() + timedelta(hours=payload.intervalo_horas)
    db.commit()
    db.refresh(item)
    registrar_auditoria(
        db,
        current_user,
        "programacion.actualizada",
        "Programacion de consultas actualizada",
        "programacion",
        str(item.id),
        {"habilitada": payload.habilitada, "intervalo_horas": payload.intervalo_horas},
    )
    return item
