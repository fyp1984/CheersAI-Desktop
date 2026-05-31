"""add user feedback messages

Revision ID: f6c8d2e4a9b3
Revises: e5b7c9d1a4f2
Create Date: 2026-05-30 22:55:00.000000

"""

import sqlalchemy as sa
from alembic import op
from models.types import StringUUID


revision = "f6c8d2e4a9b3"
down_revision = "e5b7c9d1a4f2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_feedback_messages",
        sa.Column("id", StringUUID(), nullable=False),
        sa.Column("feedback_id", StringUUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sender_type", sa.String(length=32), server_default=sa.text("'system'"), nullable=False),
        sa.Column("sender_id", sa.String(length=255), nullable=True),
        sa.Column("sender_name", sa.String(length=255), nullable=True),
        sa.Column("is_internal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="user_feedback_message_pkey"),
    )
    op.create_index(
        "user_feedback_messages_feedback_idx",
        "user_feedback_messages",
        ["feedback_id", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("user_feedback_messages_feedback_idx", table_name="user_feedback_messages")
    op.drop_table("user_feedback_messages")
