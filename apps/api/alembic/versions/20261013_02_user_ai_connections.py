"""Add user-scoped AI provider connections, settings, and OAuth state tables.

Revision ID: 20261013_02
Revises: 20261013_01
Create Date: 2026-10-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261013_02"
down_revision: Union[str, Sequence[str], None] = "20261013_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_ai_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("connection_method", sa.String(length=20), nullable=False, server_default="api_key"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="connected"),
        sa.Column("status_message", sa.Text(), nullable=True),
        sa.Column("selected_model", sa.String(length=100), nullable=True),
        sa.Column("available_models", sa.JSON(), nullable=True),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column("key_preview", sa.String(length=30), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_ai_provider"),
    )
    op.create_index("ix_user_ai_connections_user_id", "user_ai_connections", ["user_id"])

    op.create_table(
        "user_ai_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("default_provider", sa.String(length=50), nullable=True),
        sa.Column("default_model", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_ai_settings_user_id", "user_ai_settings", ["user_id"])

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False, unique=True),
        sa.Column("code_verifier", sa.String(length=256), nullable=True),
        sa.Column("redirect_uri", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_oauth_states_state", "oauth_states", ["state"])
    op.create_index("ix_oauth_states_user_id", "oauth_states", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_oauth_states_user_id", table_name="oauth_states")
    op.drop_index("ix_oauth_states_state", table_name="oauth_states")
    op.drop_table("oauth_states")

    op.drop_index("ix_user_ai_settings_user_id", table_name="user_ai_settings")
    op.drop_table("user_ai_settings")

    op.drop_index("ix_user_ai_connections_user_id", table_name="user_ai_connections")
    op.drop_table("user_ai_connections")
