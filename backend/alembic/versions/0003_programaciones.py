"""programaciones consulta

Revision ID: 0003_programaciones
Revises: 0002_consulta_progress
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_programaciones"
down_revision = "0002_consulta_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "programaciones_consulta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("habilitada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("intervalo_horas", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("proxima_ejecucion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultima_ejecucion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_programaciones_consulta_usuario_id", "programaciones_consulta", ["usuario_id"], unique=True)


def downgrade() -> None:
    op.drop_table("programaciones_consulta")
