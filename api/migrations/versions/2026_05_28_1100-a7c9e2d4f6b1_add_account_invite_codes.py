"""add account invite codes

Revision ID: a7c9e2d4f6b1
Revises: d4f7a9c2b8e1
Create Date: 2026-05-28 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import models.types


revision = "a7c9e2d4f6b1"
down_revision = "d4f7a9c2b8e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_invite_codes",
        sa.Column("id", models.types.StringUUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("owner_account_id", models.types.StringUUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), server_default=sa.text("'unused'"), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("used_by_account_id", models.types.StringUUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="account_invite_code_pkey"),
        sa.UniqueConstraint("code", name="unique_account_invite_code"),
    )
    with op.batch_alter_table("account_invite_codes", schema=None) as batch_op:
        batch_op.create_index("account_invite_codes_owner_idx", ["owner_account_id"], unique=False)
        batch_op.create_index("account_invite_codes_status_idx", ["status"], unique=False)


def downgrade():
    with op.batch_alter_table("account_invite_codes", schema=None) as batch_op:
        batch_op.drop_index("account_invite_codes_status_idx")
        batch_op.drop_index("account_invite_codes_owner_idx")
    op.drop_table("account_invite_codes")
