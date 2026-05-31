"""add beta application invite code

Revision ID: c9e4a1f2b8d6
Revises: b8d1f3a5c7e2
Create Date: 2026-05-29 22:10:00.000000

"""

import sqlalchemy as sa
from alembic import op


revision = "c9e4a1f2b8d6"
down_revision = "b8d1f3a5c7e2"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("invite_code", sa.String(length=32), nullable=True))


def downgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.drop_column("invite_code")
