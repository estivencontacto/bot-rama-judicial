"""auth security fields

Revision ID: 0005_auth_security
Revises: 0004_saas_orgs_audit
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_auth_security"
down_revision = "0004_saas_orgs_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("usuarios", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_usuario_id", "refresh_tokens", ["usuario_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_column("usuarios", "password_changed_at")
    op.drop_column("usuarios", "last_login_at")
    op.drop_column("usuarios", "locked_until")
    op.drop_column("usuarios", "failed_login_attempts")
