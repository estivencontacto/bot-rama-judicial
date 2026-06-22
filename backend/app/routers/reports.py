from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Proceso, Radicado, Reporte, Usuario
from backend.app.routers.dependencies import get_current_user
from backend.app.services.report_service import exportar_excel


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/excel")
def download_excel_report(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Genera y descarga un Excel con los procesos visibles del usuario."""
    procesos = (
        db.query(Proceso)
        .join(Radicado)
        .filter(Radicado.usuario_id == current_user.id)
        .order_by(Proceso.updated_at.desc())
        .all()
    )
    resultados = []
    for proceso in procesos:
        raw_data = proceso.raw_data or {}
        resultados.append(
            {
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

    output_dir = Path("output") / "reports"
    archivo, _ = exportar_excel(resultados, [], str(output_dir))
    reporte = Reporte(
        usuario_id=current_user.id,
        nombre_archivo=Path(archivo).name,
        ruta_archivo=archivo,
        total_procesos=len(resultados),
        total_errores=0,
    )
    db.add(reporte)
    db.commit()

    return FileResponse(
        archivo,
        filename=Path(archivo).name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
