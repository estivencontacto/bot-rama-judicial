from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from backend.app.services.document_downloader import generar_url_descarga


def crear_zip_documentos(numero_proceso: str, carpeta_proceso: Path, storage_root: Path) -> str | None:
    documentos = carpeta_proceso / "documentos"
    if not documentos.exists():
        return None

    archivos = [item for item in documentos.iterdir() if item.is_file()]
    if not archivos:
        return None

    zip_path = carpeta_proceso / f"{numero_proceso}_documentos.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_file:
        for archivo in archivos:
            zip_file.write(archivo, arcname=archivo.name)
    return generar_url_descarga(zip_path, storage_root)
