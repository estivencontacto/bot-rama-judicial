from __future__ import annotations

from redis import Redis
from rq import Worker

from backend.app.core.settings import get_settings


def main() -> None:
    settings = get_settings()
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL es requerido para ejecutar el worker RQ.")

    connection = Redis.from_url(settings.redis_url)
    worker = Worker([settings.queue_name], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
