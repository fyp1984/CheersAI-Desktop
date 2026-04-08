"""add beta rejection fields

Revision ID: 1a5e8c2f4b6d
Revises: b3e2c7f4a9d1
Create Date: 2026-04-07 19:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1a5e8c2f4b6d"
down_revision = "b3e2c7f4a9d1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("rejected_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("rejection_reason", sa.String(length=1000), nullable=True))


def downgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.drop_column("rejection_reason")
        batch_op.drop_column("rejected_at")
