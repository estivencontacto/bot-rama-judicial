"""Endpoints de radicados.

Permiten carga manual, carga masiva por Excel, descarga de plantilla y listado
por organizacion.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Radicado, Usuario, UsuarioRol
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.schemas.radicados import RadicadoCreate, RadicadoRead, UploadResult
from backend.app.services.excel_service import parse_radicados_excel
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/radicados", tags=["radicados"])
TEMPLATE_PATH = Path(__file__).resolve().parents[3] / "data" / "listado_radicados_template.xlsx"


def _crear_radicados(db: Session, usuario: Usuario, numeros: list[str]) -> UploadResult:
    """Normaliza, deduplica y persiste radicados dentro de la organizacion."""
    limpios = []
    for numero in numeros:
        valor = str(numero).strip()
        if valor and valor not in limpios:
            limpios.append(valor)

    created = 0
    existing = 0
    for numero in limpios:
        exists = (
            db.query(Radicado)
            .filter(Radicado.organizacion_id == usuario.organizacion_id, Radicado.numero == numero)
            .first()
        )
        if exists:
            existing += 1
            continue
        db.add(Radicado(usuario_id=usuario.id, organizacion_id=usuario.organizacion_id, numero=numero))
        created += 1

    db.commit()
    registrar_auditoria(
        db,
        usuario,
        "radicados.cargados",
        f"Radicados cargados: {created}; existentes: {existing}",
        "radicados",
        metadata={"total_recibidos": len(limpios), "total_creados": created, "total_existentes": existing},
    )
    return UploadResult(total_recibidos=len(limpios), total_creados=created, total_existentes=existing)


@router.post("/upload", response_model=UploadResult)
async def upload_radicados(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Recibe un Excel y registra los radicados encontrados."""
    try:
        radicados = parse_radicados_excel(await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _crear_radicados(db, current_user, radicados)


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
    return _crear_radicados(db, current_user, payload.numeros)


@router.get("", response_model=list[RadicadoRead])
def list_radicados(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Radicado]:
    """Lista los radicados visibles para la organizacion del usuario."""
    return (
        db.query(Radicado)
        .filter(Radicado.organizacion_id == current_user.organizacion_id)
        .order_by(Radicado.created_at.desc())
        .all()
    )
