from __future__ import annotations

import re

from fastapi import HTTPException


def limpiar_numero_proceso(numero: str) -> str:
    """Deja solo digitos para comparar radicados de forma exacta."""
    return re.sub(r"\D+", "", numero or "")


def validar_numero_proceso(numero: str) -> str:
    """Valida el formato colombiano esperado para numero de proceso."""
    limpio = limpiar_numero_proceso(numero)
    if not limpio:
        raise HTTPException(status_code=422, detail="Ingresa un numero de proceso.")
    if not limpio.isdigit():
        raise HTTPException(status_code=422, detail="El numero de proceso solo debe contener digitos.")
    if len(limpio) != 23:
        raise HTTPException(
            status_code=422,
            detail="El numero de proceso debe tener 23 digitos despues de limpiar espacios, puntos o guiones.",
        )
    return limpio
