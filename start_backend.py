import traceback

import uvicorn


def ensure_local_schema() -> None:
    from sqlalchemy import inspect, text

    from backend.app.core.settings import get_settings
    from backend.app.database.session import Base, engine
    from backend.app.models import entities  # noqa: F401

    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    existing = {column["name"] for column in inspector.get_columns("consultas")}
    columns = {
        "total_radicados": "INTEGER NOT NULL DEFAULT 0",
        "total_novedades": "INTEGER NOT NULL DEFAULT 0",
        "radicado_actual": "VARCHAR(64)",
        "ultimo_mensaje": "TEXT",
    }
    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE consultas ADD COLUMN {name} {definition}"))

        user_columns = {column["name"] for column in inspector.get_columns("usuarios")}
        if "organizacion_id" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN organizacion_id INTEGER"))
        if "rol" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN rol VARCHAR(20) NOT NULL DEFAULT 'admin'"))
        if "failed_login_attempts" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"))
        if "locked_until" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN locked_until DATETIME"))
        if "last_login_at" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN last_login_at DATETIME"))
        if "password_changed_at" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN password_changed_at DATETIME"))

        radicado_columns = {column["name"] for column in inspector.get_columns("radicados")}
        if "organizacion_id" not in radicado_columns:
            connection.execute(text("ALTER TABLE radicados ADD COLUMN organizacion_id INTEGER"))

        notificacion_columns = {column["name"] for column in inspector.get_columns("notificaciones")}
        if "bot_token" not in notificacion_columns:
            connection.execute(text("ALTER TABLE notificaciones ADD COLUMN bot_token VARCHAR(255)"))

        org_id = connection.execute(text("SELECT id FROM organizaciones ORDER BY id LIMIT 1")).scalar()
        if not org_id:
            connection.execute(
                text(
                    "INSERT INTO organizaciones (nombre, limite_radicados, activa, created_at) "
                    "VALUES ('Organizacion Demo', 500, 1, CURRENT_TIMESTAMP)"
                )
            )
            org_id = connection.execute(text("SELECT id FROM organizaciones ORDER BY id LIMIT 1")).scalar()

        connection.execute(text("UPDATE usuarios SET organizacion_id = :org_id WHERE organizacion_id IS NULL"), {"org_id": org_id})
        connection.execute(text("UPDATE usuarios SET rol = 'admin' WHERE rol IS NULL"), {"org_id": org_id})
        connection.execute(text("UPDATE radicados SET organizacion_id = :org_id WHERE organizacion_id IS NULL"), {"org_id": org_id})


if __name__ == "__main__":
    try:
        ensure_local_schema()
        uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000)
    except Exception:
        with open("backend-start-error.log", "w", encoding="utf-8") as file:
            file.write(traceback.format_exc())
        raise
