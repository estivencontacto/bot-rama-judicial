from __future__ import annotations

import re


def normalizar_texto_busqueda(texto: str | None) -> str:
    return re.sub(r"\s+", " ", (texto or "").strip())


def validar_coincidencia_exacta(texto: str | None, numero_proceso: str) -> bool:
    """Evita falsos positivos por fragmentos del radicado."""
    if not texto:
        return False
    digitos = re.sub(r"\D+", "", texto)
    return numero_proceso in re.findall(r"\d{23}", digitos)


def tiene_coincidencia_parcial(texto: str | None, numero_proceso: str) -> bool:
    if not texto:
        return False
    digitos = re.sub(r"\D+", "", texto)
    return numero_proceso[:12] in digitos or numero_proceso[-8:] in digitos


def clasificar_publicacion(texto: str | None) -> str:
    upper = (texto or "").upper()
    reglas = [
        ("Auto", "AUTO"),
        ("Estado", "ESTADO"),
        ("Traslado", "TRASLADO"),
        ("Fijacion", "FIJACI"),
        ("Aviso", "AVISO"),
    ]
    for nombre, palabra in reglas:
        if palabra in upper:
            return nombre
    return "Otro"
