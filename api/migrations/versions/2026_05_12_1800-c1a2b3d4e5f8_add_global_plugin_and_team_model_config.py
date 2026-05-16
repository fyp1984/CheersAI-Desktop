"""add_global_plugin_and_team_model_config

Revision ID: c1a2b3d4e5f8
Revises: db40c83cabd3
Create Date: 2026-05-12 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1a2b3d4e5f8"
down_revision = "db40c83cabd3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_plugins",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("plugin_code", sa.String(length=255), nullable=False),
        sa.Column("plugin_id", sa.String(length=255), nullable=False),
        sa.Column("plugin_unique_identifier", sa.String(length=255), nullable=False),
        sa.Column("source_tenant_id", sa.UUID(), nullable=False),
        sa.Column("source_account_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("install_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="system_plugin_pkey"),
        sa.UniqueConstraint("plugin_code", name="system_plugin_plugin_code_key"),
    )
    op.create_index("system_plugin_enabled_idx", "system_plugins", ["enabled"])

    op.create_table(
        "team_model_config",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("plugin_code", sa.String(length=255), nullable=False),
        sa.Column("api_key_enc", sa.Text(), nullable=False),
        sa.Column("base_url", sa.String(length=1024), nullable=False),
        sa.Column("max_concurrent", sa.Integer(), nullable=True),
        sa.Column("max_qps", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP(0)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="team_model_config_pkey"),
        sa.UniqueConstraint("team_id", "plugin_code", name="team_model_config_team_plugin_key"),
    )
    op.create_index("team_model_config_team_idx", "team_model_config", ["team_id"])


def downgrade():
    op.drop_index("team_model_config_team_idx", table_name="team_model_config")
    op.drop_table("team_model_config")

    op.drop_index("system_plugin_enabled_idx", table_name="system_plugins")
    op.drop_table("system_plugins")
