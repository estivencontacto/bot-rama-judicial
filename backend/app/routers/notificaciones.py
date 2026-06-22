"""Endpoints de configuracion de notificaciones.

Permiten guardar Telegram por usuario, probar el envio y responder sin exponer
el token completo al frontend.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Notificacion, NotificacionCanal, Usuario, UsuarioRol
from backend.app.routers.dependencies import get_current_user, require_roles
from backend.app.schemas.notificaciones import NotificacionRead, NotificacionTestResponse, NotificacionUpsert
from backend.app.services.notification_service import construir_mensaje_prueba, notificar_telegram
from backend.app.services.audit_service import registrar_auditoria


router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.get("", response_model=list[NotificacionRead])
def list_notificaciones(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> list[Notificacion]:
    """Lista las configuraciones del usuario autenticado."""
    return db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id).all()


@router.put("", response_model=NotificacionRead)
def upsert_notificacion(
    payload: NotificacionUpsert,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Notificacion:
    """Crea o actualiza el canal de Telegram conservando el token si se deja vacio."""
    try:
        canal = NotificacionCanal(payload.canal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Canal de notificacion no soportado.") from exc

    destino = payload.destino.strip()
    bot_token = payload.bot_token.strip() if payload.bot_token else None
    if canal == NotificacionCanal.telegram and payload.habilitada:
        if not destino:
            raise HTTPException(status_code=400, detail="El Chat ID de Telegram es obligatorio.")
        if not bot_token:
            existing_token = (
                db.query(Notificacion.bot_token)
                .filter(Notificacion.usuario_id == current_user.id, Notificacion.canal == canal)
                .scalar()
            )
            if not existing_token:
                raise HTTPException(status_code=400, detail="El token del bot de Telegram es obligatorio.")

    item = (
        db.query(Notificacion)
        .filter(Notificacion.usuario_id == current_user.id, Notificacion.canal == canal)
        .first()
    )
    if not item:
        item = Notificacion(usuario_id=current_user.id, canal=canal, destino=destino)
        db.add(item)
    item.destino = destino
    if bot_token:
        item.bot_token = bot_token
    item.habilitada = payload.habilitada
    db.commit()
    db.refresh(item)
    registrar_auditoria(
        db,
        current_user,
        "notificacion.actualizada",
        f"Notificacion {payload.canal} actualizada",
        "notificacion",
        str(item.id),
        {"habilitada": payload.habilitada, "bot_token_configurado": bool(item.bot_token)},
    )
    return item


@router.post("/test", response_model=NotificacionTestResponse)
def test_notificacion(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> NotificacionTestResponse:
    """Envia un mensaje real de prueba al chat configurado."""
    item = (
        db.query(Notificacion)
        .filter(
            Notificacion.usuario_id == current_user.id,
            Notificacion.canal == NotificacionCanal.telegram,
            Notificacion.habilitada.is_(True),
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=400, detail="Configura y habilita Telegram primero.")

    try:
        notificar_telegram(construir_mensaje_prueba(), chat_id=item.destino, bot_token=item.bot_token)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo enviar Telegram: {exc}") from exc

    return NotificacionTestResponse(enviado=True, mensaje="Mensaje de prueba enviado.")
