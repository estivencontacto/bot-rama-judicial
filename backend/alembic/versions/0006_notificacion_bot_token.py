"""Add Telegram bot token per notification.

Revision ID: 0006_notificacion_bot_token
Revises: 0005_auth_security
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_notificacion_bot_token"
down_revision = "0005_auth_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notificaciones", sa.Column("bot_token", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("notificaciones", "bot_token")
