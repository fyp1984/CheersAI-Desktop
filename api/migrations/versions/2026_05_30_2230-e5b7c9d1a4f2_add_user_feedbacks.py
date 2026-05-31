"""add user feedbacks

Revision ID: e5b7c9d1a4f2
Revises: d4f8a2b6c9e1
Create Date: 2026-05-30 22:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from models.types import StringUUID


revision = "e5b7c9d1a4f2"
down_revision = "d4f8a2b6c9e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_feedbacks",
        sa.Column("id", StringUUID(), nullable=False),
        sa.Column("ticket_no", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", StringUUID(), nullable=True),
        sa.Column("account_id", StringUUID(), nullable=True),
        sa.Column("user_name", sa.String(length=255), nullable=True),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=64), server_default=sa.text("'customer_service'"), nullable=False),
        sa.Column("channel", sa.String(length=32), server_default=sa.text("'ai'"), nullable=False),
        sa.Column("category", sa.String(length=64), server_default=sa.text("'general'"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'open'"), nullable=False),
        sa.Column("priority", sa.String(length=16), server_default=sa.text("'normal'"), nullable=False),
        sa.Column("assigned_to", StringUUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("page_url", sa.String(length=2048), nullable=True),
        sa.Column("app_id", StringUUID(), nullable=True),
        sa.Column("conversation_id", StringUUID(), nullable=True),
        sa.Column("message_id", StringUUID(), nullable=True),
        sa.Column("contact_allowed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="user_feedback_pkey"),
        sa.UniqueConstraint("ticket_no", name="unique_user_feedback_ticket_no"),
    )
    op.create_index("user_feedbacks_account_idx", "user_feedbacks", ["account_id"], unique=False)
    op.create_index("user_feedbacks_source_idx", "user_feedbacks", ["source", "channel"], unique=False)
    op.create_index("user_feedbacks_tenant_status_idx", "user_feedbacks", ["tenant_id", "status"], unique=False)


def downgrade():
    op.drop_index("user_feedbacks_tenant_status_idx", table_name="user_feedbacks")
    op.drop_index("user_feedbacks_source_idx", table_name="user_feedbacks")
    op.drop_index("user_feedbacks_account_idx", table_name="user_feedbacks")
    op.drop_table("user_feedbacks")
