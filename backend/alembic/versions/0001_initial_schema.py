"""initial commercial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


consulta_estado = postgresql.ENUM("pendiente", "ejecutando", "completada", "fallida", name="consultaestado")
notificacion_canal = postgresql.ENUM("telegram", "email", "webhook", name="notificacioncanal")


def upgrade() -> None:
    consulta_estado.create(op.get_bind(), checkfirst=True)
    notificacion_canal.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "radicados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero", sa.String(length=64), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("etiqueta", sa.String(length=120), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_radicados_numero", "radicados", ["numero"])
    op.create_index("ix_radicados_usuario_id", "radicados", ["usuario_id"])
    op.create_index("ix_radicados_usuario_numero", "radicados", ["usuario_id", "numero"], unique=True)

    op.create_table(
        "procesos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("radicado_id", sa.Integer(), sa.ForeignKey("radicados.id"), nullable=False),
        sa.Column("juzgado", sa.String(length=255), nullable=True),
        sa.Column("demandante", sa.String(length=255), nullable=True),
        sa.Column("demandado", sa.String(length=255), nullable=True),
        sa.Column("partes", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=80), nullable=False),
        sa.Column("fecha_radicacion", sa.Date(), nullable=True),
        sa.Column("fecha_ultima_actuacion", sa.Date(), nullable=True),
        sa.Column("estado_hash", sa.String(length=64), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_procesos_radicado_id", "procesos", ["radicado_id"], unique=True)
    op.create_index("ix_procesos_estado_hash", "procesos", ["estado_hash"])

    op.create_table(
        "consultas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("radicado_id", sa.Integer(), sa.ForeignKey("radicados.id"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("estado", consulta_estado, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_procesados", sa.Integer(), nullable=False),
        sa.Column("total_errores", sa.Integer(), nullable=False),
    )
    op.create_index("ix_consultas_radicado_id", "consultas", ["radicado_id"])
    op.create_index("ix_consultas_usuario_id", "consultas", ["usuario_id"])

    op.create_table(
        "actuaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proceso_id", sa.Integer(), sa.ForeignKey("procesos.id"), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_actuaciones_proceso_id", "actuaciones", ["proceso_id"])

    op.create_table(
        "errores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consulta_id", sa.Integer(), sa.ForeignKey("consultas.id"), nullable=True),
        sa.Column("radicado", sa.String(length=64), nullable=False),
        sa.Column("tipo", sa.String(length=120), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_errores_consulta_id", "errores", ["consulta_id"])
    op.create_index("ix_errores_radicado", "errores", ["radicado"])

    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("canal", notificacion_canal, nullable=False),
        sa.Column("destino", sa.String(length=255), nullable=False),
        sa.Column("habilitada", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notificaciones_usuario_id", "notificaciones", ["usuario_id"])

    op.create_table(
        "reportes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("nombre_archivo", sa.String(length=255), nullable=False),
        sa.Column("ruta_archivo", sa.String(length=500), nullable=False),
        sa.Column("total_procesos", sa.Integer(), nullable=False),
        sa.Column("total_errores", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reportes_usuario_id", "reportes", ["usuario_id"])


def downgrade() -> None:
    for table in [
        "reportes",
        "notificaciones",
        "errores",
        "actuaciones",
        "consultas",
        "procesos",
        "radicados",
        "usuarios",
    ]:
        op.drop_table(table)
    notificacion_canal.drop(op.get_bind(), checkfirst=True)
    consulta_estado.drop(op.get_bind(), checkfirst=True)
