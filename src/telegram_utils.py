import requests

from src.config import TELEGRAM_CHAT_ID, TELEGRAM_MAX, TELEGRAM_TOKEN


# ===============================
# FRAGMENTACIÓN DE MENSAJES
# ===============================

def dividir_mensaje(texto: str, limite: int = TELEGRAM_MAX) -> list:
    """
    Divide un mensaje largo en varias partes para respetar el límite de Telegram.

    La división se hace por bloques de proceso para conservar la legibilidad.

    Args:
        texto: Mensaje completo a enviar.
        limite: Longitud máxima por parte.

    Returns:
        Lista de fragmentos listos para envío.
    """
    bloques = texto.split("────────────────────\n")
    partes = []
    actual = ""

    for i, bloque in enumerate(bloques):
        if i > 0:
            bloque = "────────────────────\n" + bloque

        if len(actual) + len(bloque) <= limite:
            actual += bloque
        else:
            if actual:
                partes.append(actual)
            actual = bloque

    if actual:
        partes.append(actual)

    return partes


# ===============================
# ENVÍO DE NOTIFICACIONES
# ===============================

def notificar_telegram(mensaje: str) -> None:
    """
    Envía un mensaje a Telegram usando la configuración definida en .env.

    Si el mensaje supera el límite permitido, se envía en varias partes.

    Args:
        mensaje: Texto completo a enviar.

    Raises:
        RuntimeError: Si Telegram responde con error.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    partes = dividir_mensaje(mensaje)

    for parte in partes:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": parte,
            },
            timeout=10
        )

        if not response.ok:
            raise RuntimeError(f"Error enviando mensaje a Telegram: {response.text}")