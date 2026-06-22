from sqlalchemy.orm import Session

from backend.app.models import Usuario
from backend.app.services.consulta_service import ejecutar_consulta_sincrona


def run_user_consultation(db: Session, usuario: Usuario) -> None:
    ejecutar_consulta_sincrona(db=db, usuario=usuario)
