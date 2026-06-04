"""Mensajeria Telegram.

Construye los mensajes con el formato operativo del bot original y envia por
Telegram usando la configuracion guardada por usuario.
"""

from __future__ import annotations

import logging

import requests

from backend.app.core.settings import get_settings
from backend.app.models import Notificacion, NotificacionCanal


logger = logging.getLogger(__name__)
SEPARADOR = "--------------------"


def construir_mensaje_nueva_actuacion(datos: dict, es_primer_registro: bool = False) -> str:
    """Formato de alerta enviado cuando aparece un proceso nuevo o cambia una actuacion."""
    titulo = "PROCESO REGISTRADO" if es_primer_registro else "NUEVA ACTUACION DETECTADA"
    fecha_ultima = datos.get("Fecha_ultima_actuacion") or "Sin fecha"
    lineas = [
        SEPARADOR,
        titulo,
        "",
        f"Radicado: {datos.get('Radicado', 'Sin radicado')}",
        f"Juzgado: {datos.get('Juzgado') or 'No identificado'}",
    ]

    demandante = datos.get("Demandante") or "No identificado"
    demandado = datos.get("Demandado") or "No identificado"
    lineas.append(f"Demandante: {demandante}")

    if isinstance(demandado, str) and " | " in demandado:
        for parte in demandado.split(" | "):
            lineas.append(f"Demandado: {parte.strip()}")
    else:
        lineas.append(f"Demandado: {demandado}")

    lineas.extend(["", f"Fecha ultima actuacion: {fecha_ultima}"])
    return "\n".join(lineas)


def construir_resumen_consulta(
    total_procesados: int,
    total_errores: int,
    total_novedades: int,
) -> str:
    """Resumen final de cada ejecucion del scraper."""
    return "\n".join(
        [
            SEPARADOR,
            "RESUMEN DE CONSULTA",
            "",
            f"Procesados: {total_procesados}",
            f"Novedades detectadas: {total_novedades}",
            f"Fallidos: {total_errores}",
        ]
    )


def construir_mensaje_prueba() -> str:
    """Mensaje usado por el boton de prueba de la configuracion Telegram."""
    return "\n".join(
        [
            SEPARADOR,
            "PRUEBA DE NOTIFICACION",
            "",
            "Telegram esta configurado correctamente.",
            "El sistema podra enviar novedades cuando el scraper detecte cambios.",
        ]
    )


def dividir_mensaje(texto: str, limite: int | None = None) -> list[str]:
    """Divide textos largos para respetar el limite de caracteres de Telegram."""
    settings = get_settings()
    max_chars = limite or settings.telegram_max_chars
    partes = []
    actual = ""
    for bloque in texto.split("\n\n"):
        bloque = f"{bloque}\n\n"
        if len(actual) + len(bloque) <= max_chars:
            actual += bloque
        else:
            if actual:
                partes.append(actual)
            actual = bloque
    if actual:
        partes.append(actual)
    return partes


def notificar_telegram(mensaje: str, chat_id: str | None = None, bot_token: str | None = None) -> None:
    """Envia un mensaje a Telegram con token de usuario o fallback de entorno."""
    settings = get_settings()
    destino = chat_id or settings.telegram_chat_id
    token = bot_token or settings.telegram_token
    if not token or not destino:
        raise RuntimeError("Falta TELEGRAM_TOKEN o chat_id de Telegram.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for parte in dividir_mensaje(mensaje):
        response = requests.post(
            url,
            json={"chat_id": destino, "text": parte},
            timeout=10,
        )
        response.raise_for_status()


def notificar_telegram_seguro(mensaje: str, chat_id: str | None = None, bot_token: str | None = None) -> bool:
    """Envia Telegram sin romper la consulta si el canal falla."""
    try:
        notificar_telegram(mensaje, chat_id=chat_id, bot_token=bot_token)
        return True
    except Exception as exc:
        logger.warning("No se pudo enviar Telegram: %s", exc)
        return False


def obtener_configuracion_telegram_usuario(db, usuario_id: int) -> tuple[str | None, str | None]:
    """Obtiene chat ID y token del usuario para notificaciones multiempresa."""
    item = (
        db.query(Notificacion)
        .filter(
            Notificacion.usuario_id == usuario_id,
            Notificacion.canal == NotificacionCanal.telegram,
            Notificacion.habilitada.is_(True),
        )
        .first()
    )
    return (item.destino, item.bot_token) if item else (None, None)


def obtener_chat_telegram_usuario(db, usuario_id: int) -> str | None:
    """Helper de compatibilidad para codigo que solo requiere chat ID."""
    chat_id, _ = obtener_configuracion_telegram_usuario(db, usuario_id)
    return chat_id


def notificar_usuario_telegram_seguro(db, usuario_id: int, mensaje: str) -> bool:
    """Envia un mensaje usando la configuracion Telegram activa del usuario."""
    chat_id, bot_token = obtener_configuracion_telegram_usuario(db, usuario_id)
    if not chat_id:
        logger.info("Usuario %s no tiene Telegram habilitado.", usuario_id)
        return False
    return notificar_telegram_seguro(mensaje, chat_id=chat_id, bot_token=bot_token)
