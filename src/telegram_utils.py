import requests
from src.config import TELEGRAM_CHAT_ID, TELEGRAM_MAX, TELEGRAM_TOKEN


def dividir_mensaje(texto: str, limite: int = TELEGRAM_MAX) -> list:
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


def notificar_telegram(mensaje: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    partes = dividir_mensaje(mensaje)

    for parte in partes:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": parte
            },
            timeout=10
        )

        if not response.ok:
            raise RuntimeError(f"Error enviando mensaje a Telegram: {response.text}")