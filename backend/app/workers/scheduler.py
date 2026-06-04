from __future__ import annotations

import logging
from datetime import timedelta
from threading import Thread
from time import sleep

from backend.app.database.session import SessionLocal
from backend.app.models import Consulta, ConsultaEstado, ProgramacionConsulta, Usuario, utcnow
from backend.app.services.consulta_service import crear_consulta_pendiente, lanzar_consulta_background


logger = logging.getLogger(__name__)
_started = False


def _tick() -> None:
    db = SessionLocal()
    try:
        now = utcnow()
        programaciones = (
            db.query(ProgramacionConsulta)
            .filter(
                ProgramacionConsulta.habilitada.is_(True),
                ProgramacionConsulta.proxima_ejecucion <= now,
            )
            .all()
        )
        for item in programaciones:
            usuario = db.query(Usuario).filter(Usuario.id == item.usuario_id, Usuario.is_active.is_(True)).first()
            if not usuario:
                continue

            running = (
                db.query(Consulta)
                .filter(
                    Consulta.usuario_id == item.usuario_id,
                    Consulta.estado.in_([ConsultaEstado.pendiente, ConsultaEstado.ejecutando]),
                )
                .first()
            )
            if running:
                continue

            consulta = crear_consulta_pendiente(db=db, usuario=usuario)
            lanzar_consulta_background(consulta_id=consulta.id, usuario_id=item.usuario_id)
            item.ultima_ejecucion = now
            item.proxima_ejecucion = now + timedelta(hours=item.intervalo_horas)
            db.commit()
    except Exception as exc:
        logger.warning("Scheduler tick fallo: %s", exc)
    finally:
        db.close()


def _loop() -> None:
    while True:
        _tick()
        sleep(60)


def start_scheduler() -> None:
    global _started
    if _started:
        return
    _started = True
    Thread(target=_loop, daemon=True).start()
