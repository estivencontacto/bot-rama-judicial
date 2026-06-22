from __future__ import annotations

from pathlib import Path

from backend.app.core.settings import get_settings
from backend.app.schemas.busqueda import BusquedaProcesoRequest, BusquedaProcesoResponse, ResumenProcesoBusqueda
from backend.app.services.publicaciones_service import FiltrosPublicaciones, buscar_publicaciones
from backend.app.services.rama_judicial_service import buscar_proceso_cpnu
from backend.app.services.zip_service import crear_zip_documentos


def consultar_y_preparar_descarga(numero_proceso: str, filtros_request: BusquedaProcesoRequest) -> BusquedaProcesoResponse:
    settings = get_settings()
    storage_root = Path(settings.storage_dir)
    carpeta_proceso = storage_root / "procesos" / numero_proceso
    carpeta_proceso.mkdir(parents=True, exist_ok=True)

    observaciones: list[str] = []
    resumen = None
    encontrado = False
    try:
        datos = buscar_proceso_cpnu(numero_proceso)
        encontrado = True
        resumen = ResumenProcesoBusqueda(
            despacho=datos.get("Juzgado"),
            clase_proceso=datos.get("Clase_proceso") or "No identificado",
            partes={
                "demandante": datos.get("Demandante"),
                "demandado": datos.get("Demandado"),
            },
            ultima_actuacion=datos.get("Ultima_actuacion"),
            fecha_ultima_actuacion=str(datos.get("Fecha_ultima_actuacion") or "") or None,
            enlace_consulta=settings.rama_judicial_url,
        )
    except Exception as exc:
        observaciones.append(f"No se pudo consultar la CPNJ: {exc}")

    filtros = FiltrosPublicaciones(
        fecha_desde=filtros_request.fecha_desde,
        fecha_hasta=filtros_request.fecha_hasta,
        tipo_publicacion=filtros_request.tipo_publicacion,
        despacho=filtros_request.despacho,
        ciudad=filtros_request.ciudad,
    )
    confirmadas, parciales, obs_publicaciones = buscar_publicaciones(
        numero_proceso,
        filtros,
        carpeta_proceso,
        storage_root,
    )
    observaciones.extend(obs_publicaciones)
    zip_descarga = crear_zip_documentos(numero_proceso, carpeta_proceso, storage_root)

    if confirmadas:
        observaciones.append("Se encontraron publicaciones relacionadas con coincidencia exacta.")
    elif not observaciones:
        observaciones.append("No se encontraron publicaciones procesales relacionadas con este numero de proceso.")

    return BusquedaProcesoResponse(
        numero_proceso=numero_proceso,
        encontrado=encontrado or bool(confirmadas),
        resumen_proceso=resumen,
        publicaciones_confirmadas=confirmadas,
        posibles_coincidencias=parciales,
        zip_descarga=zip_descarga,
        observaciones=" ".join(observaciones),
    )
