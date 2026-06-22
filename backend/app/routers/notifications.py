from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Notificacion, NotificacionCanal, Usuario, UsuarioRol
from backend.app.routers.dependencies import require_roles
from backend.app.schemas.notificaciones import NotificacionTestResponse
from backend.app.services.notification_service import construir_mensaje_prueba, notificar_telegram


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/test", response_model=NotificacionTestResponse)
def test_notification(
    current_user: Usuario = Depends(require_roles(UsuarioRol.admin, UsuarioRol.operador)),
    db: Session = Depends(get_db),
) -> NotificacionTestResponse:
    """Envia un mensaje de prueba por Telegram usando la configuracion del usuario."""
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
