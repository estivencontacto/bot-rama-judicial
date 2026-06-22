from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import requests


MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024


def sanitizar_nombre_archivo(nombre: str) -> str:
    limpio = re.sub(r"[^A-Za-z0-9_.-]+", "_", nombre or "documento")
    return limpio.strip("._")[:140] or "documento"


def generar_url_descarga(ruta_archivo: Path, storage_root: Path) -> str:
    relativo = ruta_archivo.resolve().relative_to(storage_root.resolve())
    return "/downloads/" + "/".join(relativo.parts)


def descargar_documento(url: str, carpeta_destino: Path, nombre_base: str, storage_root: Path) -> dict:
    """Descarga un documento de forma limitada y devuelve metadatos publicos."""
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    extension = Path(urlparse(url).path).suffix or ".html"
    archivo = sanitizar_nombre_archivo(f"{nombre_base}{extension}")
    destino = carpeta_destino / archivo

    with requests.get(url, timeout=25, stream=True) as response:
        response.raise_for_status()
        total = 0
        with destino.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    handle.close()
                    destino.unlink(missing_ok=True)
                    raise ValueError("El documento supera el tamano maximo permitido.")
                handle.write(chunk)

    return {
        "archivo": archivo,
        "ruta": str(destino),
        "url_descarga": generar_url_descarga(destino, storage_root),
    }


def verificar_numero_en_documento(ruta_archivo: Path, numero_proceso: str) -> bool:
    """Verifica coincidencia en documentos de texto; PDFs binarios se dejan como no verificables."""
    try:
        if ruta_archivo.suffix.lower() not in {".txt", ".html", ".htm", ".csv"}:
            return False
        contenido = ruta_archivo.read_text(encoding="utf-8", errors="ignore")
        return numero_proceso in re.sub(r"\D+", "", contenido)
    except OSError:
        return False
