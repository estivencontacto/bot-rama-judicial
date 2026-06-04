from datetime import datetime

from pydantic import BaseModel


class ReporteRead(BaseModel):
    id: int
    nombre_archivo: str
    ruta_archivo: str
    total_procesos: int
    total_errores: int
    created_at: datetime

    model_config = {"from_attributes": True}
