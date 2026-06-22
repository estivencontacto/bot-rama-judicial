"""saas organizations roles audit

Revision ID: 0004_saas_orgs_audit
Revises: 0003_programaciones
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_saas_orgs_audit"
down_revision = "0003_programaciones"
branch_labels = None
depends_on = None


usuario_rol = postgresql.ENUM("admin", "operador", "lectura", name="usuariorol")


def upgrade() -> None:
    usuario_rol.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "organizaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("limite_radicados", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizaciones_nombre", "organizaciones", ["nombre"], unique=True)

    op.add_column("usuarios", sa.Column("organizacion_id", sa.Integer(), nullable=True))
    op.add_column("usuarios", sa.Column("rol", usuario_rol, nullable=False, server_default="admin"))
    op.create_index("ix_usuarios_organizacion_id", "usuarios", ["organizacion_id"])
    op.create_foreign_key("fk_usuarios_organizacion_id", "usuarios", "organizaciones", ["organizacion_id"], ["id"])

    op.add_column("radicados", sa.Column("organizacion_id", sa.Integer(), nullable=True))
    op.create_index("ix_radicados_organizacion_id", "radicados", ["organizacion_id"])
    op.create_foreign_key("fk_radicados_organizacion_id", "radicados", "organizaciones", ["organizacion_id"], ["id"])

    op.create_table(
        "auditoria_eventos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organizacion_id", sa.Integer(), sa.ForeignKey("organizaciones.id"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("accion", sa.String(length=120), nullable=False),
        sa.Column("entidad", sa.String(length=120), nullable=True),
        sa.Column("entidad_id", sa.String(length=80), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auditoria_eventos_organizacion_id", "auditoria_eventos", ["organizacion_id"])
    op.create_index("ix_auditoria_eventos_usuario_id", "auditoria_eventos", ["usuario_id"])
    op.create_index("ix_auditoria_eventos_accion", "auditoria_eventos", ["accion"])


def downgrade() -> None:
    op.drop_table("auditoria_eventos")
    op.drop_column("radicados", "organizacion_id")
    op.drop_constraint("fk_usuarios_organizacion_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "rol")
    op.drop_column("usuarios", "organizacion_id")
    op.drop_table("organizaciones")
    usuario_rol.drop(op.get_bind(), checkfirst=True)
