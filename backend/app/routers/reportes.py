from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Proceso, Radicado, Reporte, Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.schemas.reportes import ReporteRead
from backend.app.services.report_service import exportar_excel


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


@router.get("/excel")
def download_reporte_cliente(
    cliente: str | None = None,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Genera un Excel actual filtrado por cliente/carpeta cuando se indique."""
    query = db.query(Proceso).join(Radicado).filter(Radicado.organizacion_id == current_user.organizacion_id)
    cliente_limpio = (cliente or "").strip()
    if cliente_limpio:
        query = query.filter(Radicado.etiqueta == cliente_limpio)

    resultados = []
    for proceso in query.order_by(Proceso.updated_at.desc()).all():
        raw_data = proceso.raw_data or {}
        resultados.append(
            {
                "Cliente": proceso.radicado.etiqueta or "Sin cliente",
                "Radicado": proceso.radicado.numero,
                "Juzgado": proceso.juzgado,
                "Demandante": proceso.demandante,
                "Demandado": proceso.demandado,
                "Partes": proceso.partes,
                "Fecha_radicacion": proceso.fecha_radicacion,
                "Fecha_ultima_actuacion": proceso.fecha_ultima_actuacion,
                "Ultima_actuacion": raw_data.get("Ultima_actuacion"),
                "Ultima_anotacion": raw_data.get("Ultima_anotacion"),
            }
        )

    archivo, _ = exportar_excel(resultados, [], "output")
    suffix = f"_{cliente_limpio.replace(' ', '_')}" if cliente_limpio else ""
    path = Path(archivo)
    filename = f"{path.stem}{suffix}{path.suffix}" if suffix else path.name
    return FileResponse(
        archivo,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
