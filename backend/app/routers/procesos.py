from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Actuacion, Proceso, Radicado, Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.procesos import ActuacionRead, ProcesoDetail, ProcesoRead


router = APIRouter(prefix="/procesos", tags=["procesos"])


def _es_auto_importante(actuacion: Actuacion) -> bool:
    texto = f"{actuacion.titulo or ''} {actuacion.descripcion or ''}".upper()
    return "AUTO" in texto


def _auto_importante(proceso: Proceso) -> Actuacion | None:
    actuaciones = sorted(
        [item for item in proceso.actuaciones if _es_auto_importante(item)],
        key=lambda item: (item.fecha is not None, item.fecha, item.created_at),
        reverse=True,
    )
    return actuaciones[0] if actuaciones else None


def _actuacion_read(actuacion: Actuacion) -> ActuacionRead:
    importante = _es_auto_importante(actuacion)
    return ActuacionRead(
        id=actuacion.id,
        fecha=actuacion.fecha,
        titulo=actuacion.titulo,
        descripcion=actuacion.descripcion,
        importancia="IMPORTANTE AUTO" if importante else None,
        importante_auto=importante,
        created_at=actuacion.created_at,
    )


def _to_read(proceso: Proceso) -> ProcesoRead:
    raw_data = proceso.raw_data or {}
    auto = _auto_importante(proceso)
    return ProcesoRead(
        radicado=proceso.radicado.numero,
        cliente=proceso.radicado.etiqueta,
        juzgado=proceso.juzgado,
        demandante=proceso.demandante,
        demandado=proceso.demandado,
        partes=proceso.partes,
        ultima_actuacion=raw_data.get("Ultima_actuacion"),
        ultima_anotacion=raw_data.get("Ultima_anotacion"),
        estado=proceso.estado,
        fecha_radicacion=proceso.fecha_radicacion,
        fecha_ultima_actuacion=proceso.fecha_ultima_actuacion,
        auto_importante=auto is not None,
        fecha_auto_importante=auto.fecha if auto else None,
        titulo_auto_importante=auto.titulo if auto else None,
        updated_at=proceso.updated_at,
    )


@router.get("", response_model=list[ProcesoRead])
def list_procesos(
    radicado: str | None = None,
    cliente: str | None = None,
    juzgado: str | None = None,
    estado: str | None = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProcesoRead]:
    query = db.query(Proceso).join(Radicado).filter(Radicado.organizacion_id == current_user.organizacion_id)
    if radicado:
        query = query.filter(Radicado.numero.ilike(f"%{radicado}%"))
    if cliente:
        query = query.filter(Radicado.etiqueta == cliente)
    if juzgado:
        query = query.filter(Proceso.juzgado.ilike(f"%{juzgado}%"))
    if estado:
        query = query.filter(Proceso.estado == estado)
    return [_to_read(item) for item in query.order_by(Proceso.updated_at.desc()).all()]


@router.get("/{radicado}", response_model=ProcesoDetail)
def get_proceso(
    radicado: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProcesoDetail:
    proceso = (
        db.query(Proceso)
        .join(Radicado)
        .filter(Radicado.organizacion_id == current_user.organizacion_id, Radicado.numero == radicado)
        .first()
    )
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")

    historial = (
        db.query(Actuacion)
        .filter(Actuacion.proceso_id == proceso.id)
        .order_by(Actuacion.fecha.desc().nullslast(), Actuacion.created_at.desc())
        .all()
    )
    base = _to_read(proceso).model_dump()
    return ProcesoDetail(**base, historial=[_actuacion_read(item) for item in historial])
