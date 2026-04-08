"""add beta provisioning fields and steps

Revision ID: b3e2c7f4a9d1
Revises: 75fa30b56ece
Create Date: 2026-04-07 18:00:00.000000

"""

from alembic import op
import models as models
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3e2c7f4a9d1"
down_revision = "75fa30b56ece"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("language", sa.String(length=20), nullable=True))
        batch_op.add_column(
            sa.Column("provision_attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0"))
        )
        batch_op.add_column(sa.Column("provision_started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("provision_finished_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("last_error_step", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("last_error_message", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("sso_subject_id", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("sso_username", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("filebay_username", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("filebay_repo", sa.String(length=200), nullable=True))

    op.create_table(
        "beta_application_steps",
        sa.Column("id", models.types.StringUUID(), nullable=False),
        sa.Column("application_id", models.types.StringUUID(), nullable=False),
        sa.Column("step_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("request_payload", models.types.LongText(), nullable=True),
        sa.Column("response_payload", models.types.LongText(), nullable=True),
        sa.Column("error_message", models.types.LongText(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="beta_application_step_pkey"),
        sa.UniqueConstraint("application_id", "step_key", name="beta_application_step_application_step_key_uq"),
    )
    with op.batch_alter_table("beta_application_steps", schema=None) as batch_op:
        batch_op.create_index("beta_application_steps_application_id_idx", ["application_id"], unique=False)
        batch_op.create_index("beta_application_steps_status_idx", ["status"], unique=False)


def downgrade():
    with op.batch_alter_table("beta_application_steps", schema=None) as batch_op:
        batch_op.drop_index("beta_application_steps_status_idx")
        batch_op.drop_index("beta_application_steps_application_id_idx")

    op.drop_table("beta_application_steps")

    with op.batch_alter_table("beta_applications", schema=None) as batch_op:
        batch_op.drop_column("filebay_repo")
        batch_op.drop_column("filebay_username")
        batch_op.drop_column("sso_username")
        batch_op.drop_column("sso_subject_id")
        batch_op.drop_column("last_error_message")
        batch_op.drop_column("last_error_step")
        batch_op.drop_column("provision_finished_at")
        batch_op.drop_column("provision_started_at")
        batch_op.drop_column("provision_attempt_count")
        batch_op.drop_column("language")
