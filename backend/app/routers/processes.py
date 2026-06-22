from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Actuacion, Proceso, Radicado, Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.procesos import JudicialProcessCreate, JudicialProcessRead, JudicialProcessUpdate
from backend.app.services.hash_service import build_process_hash


router = APIRouter(prefix="/processes", tags=["judicial processes"])


def _raw_data(proceso: Proceso) -> dict:
    return proceso.raw_data or {}


def _to_response(proceso: Proceso) -> JudicialProcessRead:
    raw_data = dict(_raw_data(proceso))
    return JudicialProcessRead(
        id=proceso.id,
        user_id=proceso.radicado.usuario_id,
        numero_radicado=proceso.radicado.numero,
        demandante=proceso.demandante,
        demandado=proceso.demandado,
        juzgado=proceso.juzgado,
        ultima_actuacion=raw_data.get("Ultima_actuacion"),
        fecha_ultima_actuacion=proceso.fecha_ultima_actuacion,
        estado=proceso.estado,
        created_at=proceso.radicado.created_at,
        updated_at=proceso.updated_at,
    )


def _get_owned_process(db: Session, process_id: int, user: Usuario) -> Proceso:
    proceso = (
        db.query(Proceso)
        .join(Radicado)
        .filter(Proceso.id == process_id, Radicado.usuario_id == user.id)
        .first()
    )
    if not proceso:
        raise HTTPException(status_code=404, detail="Proceso judicial no encontrado")
    return proceso


@router.post("", response_model=JudicialProcessRead, status_code=status.HTTP_201_CREATED)
def create_process(
    payload: JudicialProcessCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JudicialProcessRead:
    numero = payload.numero_radicado.strip()
    if not numero:
        raise HTTPException(status_code=400, detail="El numero_radicado es obligatorio")

    existing = db.query(Radicado).filter(Radicado.usuario_id == current_user.id, Radicado.numero == numero).first()
    if existing and existing.proceso:
        raise HTTPException(status_code=409, detail="El proceso ya existe para este usuario")

    radicado = existing or Radicado(
        usuario_id=current_user.id,
        organizacion_id=current_user.organizacion_id,
        numero=numero,
    )
    if not existing:
        db.add(radicado)
        db.flush()

    raw_data = {"Ultima_actuacion": payload.ultima_actuacion}
    proceso = Proceso(
        radicado_id=radicado.id,
        demandante=payload.demandante,
        demandado=payload.demandado,
        juzgado=payload.juzgado,
        estado=payload.estado,
        fecha_ultima_actuacion=payload.fecha_ultima_actuacion,
        raw_data=raw_data,
        estado_hash=build_process_hash(
            {
                "Radicado": numero,
                "Demandante": payload.demandante,
                "Demandado": payload.demandado,
                "Juzgado": payload.juzgado,
                "Fecha_ultima_actuacion": str(payload.fecha_ultima_actuacion or ""),
                "Ultima_actuacion": payload.ultima_actuacion,
            }
        ),
    )
    db.add(proceso)
    db.commit()
    db.refresh(proceso)
    return _to_response(proceso)


@router.get("", response_model=list[JudicialProcessRead])
def list_processes(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JudicialProcessRead]:
    procesos = (
        db.query(Proceso)
        .join(Radicado)
        .filter(Radicado.usuario_id == current_user.id)
        .order_by(Proceso.updated_at.desc())
        .all()
    )
    return [_to_response(item) for item in procesos]


@router.get("/{process_id}", response_model=JudicialProcessRead)
def get_process(
    process_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JudicialProcessRead:
    return _to_response(_get_owned_process(db, process_id, current_user))


@router.put("/{process_id}", response_model=JudicialProcessRead)
def update_process(
    process_id: int,
    payload: JudicialProcessUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JudicialProcessRead:
    proceso = _get_owned_process(db, process_id, current_user)

    if payload.numero_radicado is not None:
        numero = payload.numero_radicado.strip()
        if not numero:
            raise HTTPException(status_code=400, detail="El numero_radicado no puede estar vacio")
        duplicate = (
            db.query(Radicado)
            .filter(Radicado.usuario_id == current_user.id, Radicado.numero == numero, Radicado.id != proceso.radicado_id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe otro proceso con ese numero_radicado")
        proceso.radicado.numero = numero

    for field in ("demandante", "demandado", "juzgado", "fecha_ultima_actuacion", "estado"):
        value = getattr(payload, field)
        if value is not None:
            setattr(proceso, field, value)

    raw_data = dict(_raw_data(proceso))
    if payload.ultima_actuacion is not None:
        raw_data["Ultima_actuacion"] = payload.ultima_actuacion
    proceso.raw_data = raw_data
    proceso.estado_hash = build_process_hash(
        {
            "Radicado": proceso.radicado.numero,
            "Demandante": proceso.demandante,
            "Demandado": proceso.demandado,
            "Juzgado": proceso.juzgado,
            "Fecha_ultima_actuacion": str(proceso.fecha_ultima_actuacion or ""),
            "Ultima_actuacion": raw_data.get("Ultima_actuacion"),
        }
    )
    db.commit()
    db.refresh(proceso)
    return _to_response(proceso)


@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process(
    process_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    proceso = _get_owned_process(db, process_id, current_user)
    radicado = proceso.radicado
    db.query(Actuacion).filter(Actuacion.proceso_id == proceso.id).delete()
    db.delete(proceso)
    radicado.activo = False
    db.commit()
    return None
