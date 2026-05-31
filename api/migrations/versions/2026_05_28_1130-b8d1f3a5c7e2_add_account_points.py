"""add account points

Revision ID: b8d1f3a5c7e2
Revises: a7c9e2d4f6b1
Create Date: 2026-05-28 11:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

import models.types


revision = "b8d1f3a5c7e2"
down_revision = "a7c9e2d4f6b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_point_transactions",
        sa.Column("id", models.types.StringUUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("account_id", models.types.StringUUID(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="account_point_transaction_pkey"),
    )
    with op.batch_alter_table("account_point_transactions", schema=None) as batch_op:
        batch_op.create_index("account_point_transactions_account_idx", ["account_id"], unique=False)
        batch_op.create_index("account_point_transactions_source_idx", ["source", "source_id"], unique=False)

    op.create_table(
        "account_point_redemptions",
        sa.Column("id", models.types.StringUUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("account_id", models.types.StringUUID(), nullable=False),
        sa.Column("reward_id", sa.String(length=64), nullable=False),
        sa.Column("reward_name", sa.String(length=255), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'pending_activation'"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="account_point_redemption_pkey"),
    )
    with op.batch_alter_table("account_point_redemptions", schema=None) as batch_op:
        batch_op.create_index("account_point_redemptions_account_idx", ["account_id"], unique=False)


def downgrade():
    with op.batch_alter_table("account_point_redemptions", schema=None) as batch_op:
        batch_op.drop_index("account_point_redemptions_account_idx")
    op.drop_table("account_point_redemptions")

    with op.batch_alter_table("account_point_transactions", schema=None) as batch_op:
        batch_op.drop_index("account_point_transactions_source_idx")
        batch_op.drop_index("account_point_transactions_account_idx")
    op.drop_table("account_point_transactions")
