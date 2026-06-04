from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import AuditoriaEvento, Usuario


def registrar_auditoria(
    db: Session,
    usuario: Usuario | None,
    accion: str,
    descripcion: str,
    entidad: str | None = None,
    entidad_id: str | None = None,
    metadata: dict | None = None,
) -> AuditoriaEvento:
    evento = AuditoriaEvento(
        organizacion_id=usuario.organizacion_id if usuario else None,
        usuario_id=usuario.id if usuario else None,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        descripcion=descripcion,
        metadata_json=metadata,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento
