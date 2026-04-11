"""add model usage records table

Revision ID: c4f8a1b2d3e4
Revises: a2f4c7d9e5b1
Create Date: 2026-04-11 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import models

# revision identifiers, used by Alembic.
revision = "c4f8a1b2d3e4"
down_revision = "a2f4c7d9e5b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_usage_records",
        sa.Column("id", models.types.StringUUID(), nullable=False),
        sa.Column("tenant_id", models.types.StringUUID(), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("provider_type", sa.String(length=40), nullable=False),
        sa.Column("model_type", sa.String(length=40), nullable=False),
        sa.Column("input_unit_price", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("output_unit_price", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("input_price_unit", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("output_price_unit", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("input_price", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("output_price", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("total_price", sa.Numeric(20, 10), nullable=False, server_default=sa.text("0")),
        sa.Column("input_tokens", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_tokens", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_tokens", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=32), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("latency", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("user_id", models.types.StringUUID(), nullable=True),
        sa.Column("is_cloud", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("invocation_source", sa.String(length=64), nullable=True),
        sa.Column("request_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id", name="model_usage_record_pkey"),
    )

    with op.batch_alter_table("model_usage_records", schema=None) as batch_op:
        batch_op.create_index(
            "model_usage_record_tenant_created_idx",
            ["tenant_id", "created_at"],
            unique=False,
        )
        batch_op.create_index(
            "model_usage_record_provider_model_idx",
            ["provider", "model_name", "created_at"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("model_usage_records", schema=None) as batch_op:
        batch_op.drop_index("model_usage_record_provider_model_idx")
        batch_op.drop_index("model_usage_record_tenant_created_idx")

    op.drop_table("model_usage_records")
