from __future__ import annotations

import logging
from threading import Thread
from typing import Any, Callable

from backend.app.core.settings import get_settings


logger = logging.getLogger(__name__)


def enqueue_job(func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
    settings = get_settings()
    if settings.redis_url:
        try:
            from redis import Redis
            from rq import Queue

            connection = Redis.from_url(settings.redis_url)
            queue = Queue(settings.queue_name, connection=connection)
            job = queue.enqueue(func, *args, **kwargs)
            return job.id
        except Exception as exc:
            logger.warning("No se pudo encolar en Redis/RQ, usando thread local: %s", exc)

    thread = Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return f"local-thread-{thread.ident}"
