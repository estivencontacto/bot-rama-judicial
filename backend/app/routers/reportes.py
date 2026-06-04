from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Reporte, Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.reportes import ReporteRead


router = APIRouter(prefix="/reportes", tags=["reportes"])


@router.get("", response_model=list[ReporteRead])
def list_reportes(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Reporte]:
    org_user_ids = [row.id for row in db.query(Usuario.id).filter(Usuario.organizacion_id == current_user.organizacion_id).all()]
    return (
        db.query(Reporte)
        .filter(Reporte.usuario_id.in_(org_user_ids))
        .order_by(Reporte.created_at.desc())
        .all()
    )


@router.get("/{reporte_id}/download")
def download_reporte(
    reporte_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    reporte = (
        db.query(Reporte)
        .filter(Reporte.id == reporte_id)
        .first()
    )
    org_user_ids = [row.id for row in db.query(Usuario.id).filter(Usuario.organizacion_id == current_user.organizacion_id).all()]
    if reporte and reporte.usuario_id not in org_user_ids:
        reporte = None
    if not reporte or not Path(reporte.ruta_archivo).exists():
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return FileResponse(
        reporte.ruta_archivo,
        filename=reporte.nombre_archivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
