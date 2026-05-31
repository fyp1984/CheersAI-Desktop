"""add account point expiration

Revision ID: d4f8a2b6c9e1
Revises: c9e4a1f2b8d6
Create Date: 2026-05-29 23:30:00.000000

"""

import sqlalchemy as sa
from alembic import op


revision = "d4f8a2b6c9e1"
down_revision = "c9e4a1f2b8d6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("account_point_transactions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("remaining_points", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(), nullable=True))

    op.execute(
        """
        UPDATE account_point_transactions
        SET remaining_points = CASE WHEN points > 0 THEN points ELSE 0 END
        WHERE remaining_points IS NULL
        """
    )
    op.execute(
        """
        UPDATE account_point_transactions
        SET expires_at = created_at + INTERVAL '180 days'
        WHERE points > 0 AND expires_at IS NULL
        """
    )

    with op.batch_alter_table("account_point_transactions", schema=None) as batch_op:
        batch_op.alter_column("remaining_points", existing_type=sa.Integer(), nullable=False, server_default=sa.text("0"))
        batch_op.create_index("account_point_transactions_account_expire_idx", ["account_id", "expires_at"], unique=False)


def downgrade():
    with op.batch_alter_table("account_point_transactions", schema=None) as batch_op:
        batch_op.drop_index("account_point_transactions_account_expire_idx")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("remaining_points")
