"""add app instructions

Revision ID: d4f7a9c2b8e1
Revises: c1a2b3d4e5f8
Create Date: 2026-05-22 15:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "d4f7a9c2b8e1"
down_revision = "c1a2b3d4e5f8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_instructions",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("app_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_file_name", sa.String(length=255), nullable=True),
        sa.Column("source_file_size", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="app_instruction_pkey"),
    )
    op.create_index("app_instruction_app_id_idx", "app_instructions", ["app_id"], unique=True)
    op.create_index("app_instruction_tenant_id_idx", "app_instructions", ["tenant_id"])


def downgrade():
    op.drop_index("app_instruction_tenant_id_idx", table_name="app_instructions")
    op.drop_index("app_instruction_app_id_idx", table_name="app_instructions")
    op.drop_table("app_instructions")
