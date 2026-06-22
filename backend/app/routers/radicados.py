"""Endpoints de radicados.

Permiten carga manual, carga masiva por Excel, descarga de plantilla y listado
por organizacion.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Actuacion, Consulta, Proceso, Radicado, Usuario, UsuarioRol
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.routers.clientes import ensure_cliente
from backend.app.schemas.radicados import RadicadoCreate, RadicadoRead, RadicadoUpdate, UploadResult
from backend.app.services.excel_service import parse_radicados_excel
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/radicados", tags=["radicados"])
TEMPLATE_PATH = Path(__file__).resolve().parents[3] / "data" / "listado_radicados_template.xlsx"


def _limpiar_etiqueta(etiqueta: str | None) -> str | None:
    valor = (etiqueta or "").strip()
    return valor or None


def _crear_radicados(db: Session, usuario: Usuario, numeros: list[str], etiqueta: str | None = None) -> UploadResult:
    """Normaliza, deduplica y persiste radicados dentro de la organizacion."""
    limpios = []
    for numero in numeros:
        valor = str(numero).strip()
        if valor and valor not in limpios:
            limpios.append(valor)

    created = 0
    existing = 0
    etiqueta_limpia = _limpiar_etiqueta(etiqueta)
    ensure_cliente(db, usuario, etiqueta_limpia)
    for numero in limpios:
        exists = (
            db.query(Radicado)
            .filter(Radicado.organizacion_id == usuario.organizacion_id, Radicado.numero == numero)
            .first()
        )
        if exists:
            if etiqueta_limpia and not exists.etiqueta:
                exists.etiqueta = etiqueta_limpia
            existing += 1
            continue
        db.add(Radicado(usuario_id=usuario.id, organizacion_id=usuario.organizacion_id, numero=numero, etiqueta=etiqueta_limpia))
        created += 1

    db.commit()
    registrar_auditoria(
        db,
        usuario,
        "radicados.cargados",
        f"Radicados cargados: {created}; existentes: {existing}",
        "radicados",
        metadata={"total_recibidos": len(limpios), "total_creados": created, "total_existentes": existing, "cliente": etiqueta_limpia},
    )
    return UploadResult(total_recibidos=len(limpios), total_creados=created, total_existentes=existing)


@router.post("/upload", response_model=UploadResult)
async def upload_radicados(
    file: UploadFile = File(...),
    etiqueta: str | None = Form(None),
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Recibe un Excel y registra los radicados encontrados."""
    try:
        radicados = parse_radicados_excel(await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _crear_radicados(db, current_user, radicados, etiqueta=etiqueta)


@router.get("/template")
def download_template() -> FileResponse:
    """Entrega la plantilla publica para carga masiva."""
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Plantilla de radicados no disponible.")
    return FileResponse(
        TEMPLATE_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="listado_radicados_template.xlsx",
    )


@router.post("", response_model=UploadResult)
def create_radicados(
    payload: RadicadoCreate,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Crea radicados desde una lista enviada como JSON."""
    return _crear_radicados(db, current_user, payload.numeros, etiqueta=payload.etiqueta)


@router.get("", response_model=list[RadicadoRead])
def list_radicados(
    etiqueta: str | None = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Radicado]:
    """Lista los radicados visibles para la organizacion del usuario."""
    query = db.query(Radicado).filter(Radicado.organizacion_id == current_user.organizacion_id)
    if etiqueta:
        query = query.filter(Radicado.etiqueta == etiqueta)
    return query.order_by(Radicado.created_at.desc()).all()


@router.get("/clientes", response_model=list[str])
def list_clientes(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[str]:
    """Lista clientes/carpetas creados a partir de la etiqueta de radicados."""
    rows = (
        db.query(Radicado.etiqueta)
        .filter(Radicado.organizacion_id == current_user.organizacion_id, Radicado.etiqueta.isnot(None))
        .distinct()
        .order_by(Radicado.etiqueta.asc())
        .all()
    )
    return [row.etiqueta for row in rows if row.etiqueta]


@router.put("/{radicado_id}", response_model=RadicadoRead)
def update_radicado(
    radicado_id: int,
    payload: RadicadoUpdate,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> Radicado:
    """Edita numero, cliente/carpeta o estado activo de un radicado."""
    item = (
        db.query(Radicado)
        .filter(Radicado.id == radicado_id, Radicado.organizacion_id == current_user.organizacion_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Radicado no encontrado")
    if payload.numero is not None:
        numero = payload.numero.strip()
        if not numero:
            raise HTTPException(status_code=400, detail="El radicado no puede estar vacio")
        exists = (
            db.query(Radicado)
            .filter(Radicado.organizacion_id == current_user.organizacion_id, Radicado.numero == numero, Radicado.id != item.id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=409, detail="Ya existe un radicado con ese numero")
        item.numero = numero
    if payload.etiqueta is not None:
        item.etiqueta = _limpiar_etiqueta(payload.etiqueta)
        ensure_cliente(db, current_user, item.etiqueta)
    if payload.activo is not None:
        item.activo = payload.activo
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{radicado_id}")
def delete_radicado(
    radicado_id: int,
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> dict:
    """Elimina un radicado y su proceso asociado si existe."""
    item = (
        db.query(Radicado)
        .filter(Radicado.id == radicado_id, Radicado.organizacion_id == current_user.organizacion_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Radicado no encontrado")
    proceso = db.query(Proceso).filter(Proceso.radicado_id == item.id).first()
    if proceso:
        db.query(Actuacion).filter(Actuacion.proceso_id == proceso.id).delete()
        db.delete(proceso)
    db.query(Consulta).filter(Consulta.radicado_id == item.id).update({"radicado_id": None})
    db.delete(item)
    db.commit()
    return {"ok": True}
