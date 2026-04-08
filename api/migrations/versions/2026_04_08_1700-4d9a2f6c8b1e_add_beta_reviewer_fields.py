"""add beta reviewer fields

Revision ID: 4d9a2f6c8b1e
Revises: 1a5e8c2f4b6d
Create Date: 2026-04-08 17:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import models

# revision identifiers, used by Alembic.
revision = "4d9a2f6c8b1e"
down_revision = "1a5e8c2f4b6d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("reviewer_id", models.types.StringUUID(), nullable=True))
        batch_op.add_column(sa.Column("reviewed_at", sa.DateTime(), nullable=True))
        batch_op.create_index("beta_application_reviewer_id_idx", ["reviewer_id"], unique=False)


def downgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.drop_index("beta_application_reviewer_id_idx")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("reviewer_id")
