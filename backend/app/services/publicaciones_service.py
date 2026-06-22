from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests

from backend.app.services.document_downloader import descargar_documento
from backend.app.services.matching_service import (
    clasificar_publicacion,
    normalizar_texto_busqueda,
    tiene_coincidencia_parcial,
    validar_coincidencia_exacta,
)


PUBLICACIONES_URL = "https://publicacionesprocesales.ramajudicial.gov.co/web/publicaciones-procesales"


@dataclass
class FiltrosPublicaciones:
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    tipo_publicacion: str | None = None
    despacho: str | None = None
    ciudad: str | None = None


def _extraer_links(html: str) -> list[tuple[str, str]]:
    patron = re.compile(r"<a[^>]+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
    links: list[tuple[str, str]] = []
    for href, texto_html in patron.findall(html):
        texto = re.sub(r"<[^>]+>", " ", texto_html)
        links.append((urljoin(PUBLICACIONES_URL, href), normalizar_texto_busqueda(texto)))
    return links


def _pasa_filtros(texto: str, filtros: FiltrosPublicaciones) -> bool:
    upper = texto.upper()
    if filtros.tipo_publicacion and filtros.tipo_publicacion.upper() not in upper:
        return False
    if filtros.despacho and filtros.despacho.upper() not in upper:
        return False
    if filtros.ciudad and filtros.ciudad.upper() not in upper:
        return False
    return True


def buscar_publicaciones(
    numero_proceso: str,
    filtros: FiltrosPublicaciones,
    carpeta_proceso: Path,
    storage_root: Path,
) -> tuple[list[dict], list[dict], list[str]]:
    """Consulta publicaciones y prepara documentos cuando hay enlaces directos.

    El portal de publicaciones puede cargar resultados por JavaScript. Esta funcion
    deja el contrato listo y devuelve observaciones cuando el HTML publico no trae
    resultados descargables directamente.
    """
    observaciones: list[str] = []
    try:
        response = requests.get(PUBLICACIONES_URL, timeout=25)
        response.raise_for_status()
    except requests.RequestException as exc:
        return [], [], [f"No se pudo consultar Publicaciones Procesales: {exc}"]

    html = response.text
    links = _extraer_links(html)
    textos = [normalizar_texto_busqueda(item) for item in re.split(r"<tr|</tr>|<li|</li>", html)]
    candidatos = [texto for texto in textos if numero_proceso[:12] in re.sub(r"\D+", "", texto) or numero_proceso[-8:] in re.sub(r"\D+", "", texto)]

    if not candidatos and numero_proceso not in html:
        observaciones.append(
            "Publicaciones Procesales no retorno coincidencias visibles en el HTML inicial; puede requerir navegacion dinamica para filtros avanzados."
        )

    confirmadas: list[dict] = []
    parciales: list[dict] = []
    documentos_dir = carpeta_proceso / "documentos"
    for texto in candidatos:
        if not _pasa_filtros(texto, filtros):
            continue
        exacta = validar_coincidencia_exacta(texto, numero_proceso) or numero_proceso in re.sub(r"\D+", "", texto)
        parcial = not exacta and tiene_coincidencia_parcial(texto, numero_proceso)
        if not exacta and not parcial:
            continue

        tipo = clasificar_publicacion(texto)
        publicacion = {
            "tipo": tipo,
            "fecha_publicacion": _extraer_fecha(texto),
            "despacho": filtros.despacho or None,
            "actuacion": texto[:500],
            "coincidencia": "exacta" if exacta else "parcial",
            "documento_descargado": False,
            "archivo": None,
            "url_descarga": None,
            "fuente_url": PUBLICACIONES_URL,
        }

        link_documento = _buscar_link_documento(links, texto)
        if link_documento:
            try:
                nombre_base = f"{numero_proceso}_{tipo.lower()}_{publicacion['fecha_publicacion'] or 'sin_fecha'}"
                descarga = descargar_documento(link_documento, documentos_dir, nombre_base, storage_root)
                publicacion.update(
                    {
                        "documento_descargado": True,
                        "archivo": descarga["archivo"],
                        "url_descarga": descarga["url_descarga"],
                        "fuente_url": link_documento,
                    }
                )
            except Exception as exc:
                observaciones.append(f"No se pudo descargar un documento relacionado: {exc}")

        if exacta:
            confirmadas.append(publicacion)
        else:
            parciales.append(publicacion)

    return confirmadas, parciales, observaciones


def _extraer_fecha(texto: str) -> str | None:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b", texto)
    return match.group(1) if match else None


def _buscar_link_documento(links: list[tuple[str, str]], texto: str) -> str | None:
    extensiones = (".pdf", ".docx", ".xlsx", ".xls", ".doc", ".html")
    for href, label in links:
        if href.lower().endswith(extensiones) and (not label or label in texto or "descargar" in label.lower()):
            return href
    return None
