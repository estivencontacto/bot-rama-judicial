"""Orquestacion principal del scraper.

Este servicio toma radicados activos, ejecuta Selenium con retries, guarda
procesos/historial, genera reportes y envia notificaciones Telegram cuando hay
novedades.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal
from backend.app.models import Actuacion, Consulta, ConsultaEstado, ErrorRegistro, Proceso, Radicado, Reporte, Usuario
from backend.app.services.hash_service import build_process_hash
from backend.app.services.job_queue import enqueue_job
from backend.app.services.notification_service import (
    construir_mensaje_nueva_actuacion,
    construir_resumen_consulta,
    notificar_usuario_telegram_seguro,
)
from backend.app.services.report_service import exportar_excel
from backend.app.services.scraper_service import configurar_driver, consultar_con_retries, crear_wait


def _parse_date(value: str | None) -> date | None:
    """Normaliza fechas del scraper a `date` cuando vienen en formato valido."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _upsert_proceso(db: Session, radicado: Radicado, datos: dict) -> tuple[Proceso, bool, bool]:
    """Crea o actualiza el proceso y registra actuacion si cambia el hash."""
    estado_hash = build_process_hash(datos)
    proceso = db.query(Proceso).filter(Proceso.radicado_id == radicado.id).first()
    es_primer_registro = proceso is None
    estado_anterior = proceso.estado_hash if proceso else None

    if not proceso:
        proceso = Proceso(radicado_id=radicado.id)
        db.add(proceso)

    proceso.juzgado = datos.get("Juzgado")
    proceso.demandante = datos.get("Demandante")
    proceso.demandado = datos.get("Demandado")
    proceso.partes = datos.get("Partes")
    proceso.fecha_radicacion = _parse_date(datos.get("Fecha_radicacion"))
    proceso.fecha_ultima_actuacion = _parse_date(datos.get("Fecha_ultima_actuacion"))
    proceso.estado_hash = estado_hash
    proceso.raw_data = datos

    tiene_novedad = es_primer_registro or estado_anterior != estado_hash
    if tiene_novedad:
        db.flush()
        db.add(
            Actuacion(
                proceso_id=proceso.id,
                fecha=proceso.fecha_ultima_actuacion,
                titulo="Proceso registrado" if es_primer_registro else "Nueva actuacion detectada",
                descripcion=datos.get("Partes") or "Cambio detectado por comparacion de estado",
                raw_data=datos,
            )
        )

    return proceso, tiene_novedad, es_primer_registro


def _guardar_captura_error(driver, radicado: str) -> str | None:
    """Guarda una captura de Selenium para diagnosticar errores de scraping."""
    if not driver:
        return None
    output_dir = os.path.join("output", "screenshots")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"error_{radicado}_{timestamp}.png")
    try:
        driver.save_screenshot(path)
        return path
    except Exception:
        return None


def crear_consulta_pendiente(
    db: Session,
    usuario: Usuario,
    numeros: list[str] | None = None,
) -> Consulta:
    """Crea una consulta en cola para mostrar progreso antes de iniciar el trabajo."""
    query = db.query(Radicado).filter(Radicado.organizacion_id == usuario.organizacion_id, Radicado.activo.is_(True))
    if numeros:
        query = query.filter(Radicado.numero.in_(numeros))
    total = query.count()

    consulta = Consulta(
        usuario_id=usuario.id,
        estado=ConsultaEstado.pendiente,
        total_radicados=total,
        ultimo_mensaje="Consulta en cola.",
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    return consulta


def ejecutar_consulta_sincrona(
    db: Session,
    usuario: Usuario,
    numeros: list[str] | None = None,
    consulta: Consulta | None = None,
) -> Consulta:
    """Ejecuta la consulta completa y persiste resultados, errores y reportes."""
    query = db.query(Radicado).filter(Radicado.organizacion_id == usuario.organizacion_id, Radicado.activo.is_(True))
    if numeros:
        query = query.filter(Radicado.numero.in_(numeros))
    radicados = query.order_by(Radicado.created_at.asc()).all()

    if consulta is None:
        consulta = Consulta(usuario_id=usuario.id)
        db.add(consulta)
        db.commit()
        db.refresh(consulta)

    consulta.estado = ConsultaEstado.ejecutando
    consulta.total_radicados = len(radicados)
    consulta.total_procesados = 0
    consulta.total_errores = 0
    consulta.total_novedades = 0
    consulta.radicado_actual = None
    consulta.ultimo_mensaje = "Iniciando Selenium."
    db.commit()

    resultados: list[dict] = []
    errores: list[dict] = []
    novedades: list[dict] = []
    driver = None

    if not radicados:
        consulta.estado = ConsultaEstado.completada
        consulta.ultimo_mensaje = "No hay radicados activos para consultar."
        consulta.radicado_actual = None
        archivo, _ = exportar_excel(resultados, errores, "output")
        db.add(
            Reporte(
                usuario_id=usuario.id,
                nombre_archivo=archivo.split("\\")[-1].split("/")[-1],
                ruta_archivo=archivo,
                total_procesos=0,
                total_errores=0,
            )
        )
        db.commit()
        db.refresh(consulta)
        return consulta

    try:
        driver = configurar_driver()
        wait = crear_wait(driver)

        for radicado in radicados:
            try:
                consulta.radicado_actual = radicado.numero
                consulta.ultimo_mensaje = f"Consultando radicado {radicado.numero}"
                db.commit()

                datos = consultar_con_retries(driver, wait, radicado.numero)
                resultados.append(datos)
                _, tiene_novedad, es_primer_registro = _upsert_proceso(db, radicado, datos)

                consulta.total_procesados += 1
                consulta.ultimo_mensaje = f"Radicado {radicado.numero} consultado."
                if tiene_novedad:
                    novedades.append(datos)
                    consulta.total_novedades = len(novedades)
                db.commit()

                if tiene_novedad:
                    notificar_usuario_telegram_seguro(
                        db,
                        usuario.id,
                        construir_mensaje_nueva_actuacion(
                            datos,
                            es_primer_registro=es_primer_registro,
                        ),
                    )
            except Exception as exc:
                mensaje = str(exc).split("\n")[0][:500] or exc.__class__.__name__
                screenshot = _guardar_captura_error(driver, radicado.numero)
                if screenshot:
                    mensaje = f"{mensaje} | captura: {screenshot}"
                errores.append({"Radicado": radicado.numero, "Error": mensaje})
                db.add(
                    ErrorRegistro(
                        consulta_id=consulta.id,
                        radicado=radicado.numero,
                        tipo=exc.__class__.__name__,
                        mensaje=mensaje,
                    )
                )
                consulta.total_errores += 1
                consulta.total_procesados += 1
                consulta.ultimo_mensaje = f"Error consultando {radicado.numero}: {mensaje}"
                db.commit()
    finally:
        if driver:
            driver.quit()

    archivo, _ = exportar_excel(resultados, errores, "output")
    db.add(
        Reporte(
            usuario_id=usuario.id,
            nombre_archivo=archivo.split("\\")[-1].split("/")[-1],
            ruta_archivo=archivo,
            total_procesos=len(resultados),
            total_errores=len(errores),
        )
    )
    consulta.estado = ConsultaEstado.completada if not errores else ConsultaEstado.fallida
    consulta.radicado_actual = None
    consulta.ultimo_mensaje = "Consulta finalizada." if not errores else "Consulta finalizada con errores."
    db.commit()
    db.refresh(consulta)

    notificar_usuario_telegram_seguro(
        db,
        usuario.id,
        construir_resumen_consulta(
            total_procesados=consulta.total_procesados,
            total_errores=consulta.total_errores,
            total_novedades=consulta.total_novedades,
        ),
    )
    return consulta


def ejecutar_consulta_background(consulta_id: int, usuario_id: int, numeros: list[str] | None = None) -> None:
    """Wrapper para ejecutar consultas desde threads locales o colas RQ."""
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        consulta = db.query(Consulta).filter(Consulta.id == consulta_id, Consulta.usuario_id == usuario_id).first()
        if not usuario or not consulta:
            return
        ejecutar_consulta_sincrona(db=db, usuario=usuario, numeros=numeros, consulta=consulta)
    except Exception as exc:
        consulta = db.query(Consulta).filter(Consulta.id == consulta_id).first()
        if consulta:
            consulta.estado = ConsultaEstado.fallida
            consulta.ultimo_mensaje = f"Fallo general: {str(exc).splitlines()[0][:500]}"
            db.commit()
    finally:
        db.close()


def lanzar_consulta_background(consulta_id: int, usuario_id: int, numeros: list[str] | None = None) -> None:
    """Encola la consulta en Redis/RQ o fallback local segun configuracion."""
    enqueue_job(ejecutar_consulta_background, consulta_id, usuario_id, numeros)
