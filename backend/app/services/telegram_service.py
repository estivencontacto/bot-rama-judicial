"""Servicio Telegram 2.0.

La implementacion estable vive en `notification_service.py`. Este modulo
mantiene un nombre explicito para la arquitectura por capas solicitada.
"""

from backend.app.services.notification_service import (
    construir_mensaje_nueva_actuacion,
    construir_mensaje_prueba,
    construir_resumen_consulta,
    dividir_mensaje,
    notificar_telegram,
    notificar_telegram_seguro,
    notificar_usuario_telegram_seguro,
    obtener_chat_telegram_usuario,
    obtener_configuracion_telegram_usuario,
)

__all__ = [
    "construir_mensaje_nueva_actuacion",
    "construir_mensaje_prueba",
    "construir_resumen_consulta",
    "dividir_mensaje",
    "notificar_telegram",
    "notificar_telegram_seguro",
    "notificar_usuario_telegram_seguro",
    "obtener_chat_telegram_usuario",
    "obtener_configuracion_telegram_usuario",
]
