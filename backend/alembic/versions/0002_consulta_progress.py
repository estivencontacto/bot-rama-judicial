"""consulta progress fields

Revision ID: 0002_consulta_progress
Revises: 0001_initial_schema
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_consulta_progress"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("consultas", sa.Column("total_radicados", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("consultas", sa.Column("total_novedades", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("consultas", sa.Column("radicado_actual", sa.String(length=64), nullable=True))
    op.add_column("consultas", sa.Column("ultimo_mensaje", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("consultas", "ultimo_mensaje")
    op.drop_column("consultas", "radicado_actual")
    op.drop_column("consultas", "total_novedades")
    op.drop_column("consultas", "total_radicados")
