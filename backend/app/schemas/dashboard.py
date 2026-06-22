from pydantic import BaseModel


class DashboardResumen(BaseModel):
    total_radicados: int
    total_procesos: int
    total_consultas: int
    total_errores: int
    notificaciones_activas: int
