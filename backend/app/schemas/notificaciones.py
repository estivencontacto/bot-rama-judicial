from __future__ import annotations

from pydantic import BaseModel


class NotificacionRead(BaseModel):
    id: int
    canal: str
    destino: str
    habilitada: bool
    bot_token_configurado: bool = False

    model_config = {"from_attributes": True}


class NotificacionUpsert(BaseModel):
    canal: str = "telegram"
    destino: str
    bot_token: str | None = None
    habilitada: bool = True


class NotificacionTestResponse(BaseModel):
    enviado: bool
    mensaje: str
