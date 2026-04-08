"""add beta notification and provision task tables

Revision ID: a2f4c7d9e5b1
Revises: 4d9a2f6c8b1e
Create Date: 2026-04-08 18:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

import models

# revision identifiers, used by Alembic.
revision = "a2f4c7d9e5b1"
down_revision = "4d9a2f6c8b1e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "beta_application_notifications",
        sa.Column("id", models.types.StringUUID(), nullable=False),
        sa.Column("application_id", models.types.StringUUID(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("event", sa.String(length=50), nullable=False),
        sa.Column("receiver", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("provider_message_id", sa.String(length=155), nullable=True),
        sa.Column("error_message", models.types.LongText(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="beta_application_notification_pkey"),
    )
    with op.batch_alter_table("beta_application_notifications", schema=None) as batch_op:
        batch_op.create_index("beta_application_notifications_application_id_idx", ["application_id"], unique=False)
        batch_op.create_index("beta_application_notifications_channel_idx", ["channel"], unique=False)
        batch_op.create_index("beta_application_notifications_event_idx", ["event"], unique=False)
        batch_op.create_index("beta_application_notifications_status_idx", ["status"], unique=False)

    op.create_table(
        "beta_application_provision_tasks",
        sa.Column("id", models.types.StringUUID(), nullable=False),
        sa.Column("application_id", models.types.StringUUID(), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("celery_task_id", sa.String(length=155), nullable=True),
        sa.Column("requested_by", models.types.StringUUID(), nullable=True),
        sa.Column("requested_tenant_id", models.types.StringUUID(), nullable=True),
        sa.Column("requested_ip", sa.String(length=255), nullable=True),
        sa.Column("error_message", models.types.LongText(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="beta_application_provision_task_pkey"),
    )
    with op.batch_alter_table("beta_application_provision_tasks", schema=None) as batch_op:
        batch_op.create_index("beta_application_provision_tasks_action_idx", ["action"], unique=False)
        batch_op.create_index("beta_application_provision_tasks_application_id_idx", ["application_id"], unique=False)
        batch_op.create_index("beta_application_provision_tasks_celery_task_id_idx", ["celery_task_id"], unique=False)
        batch_op.create_index("beta_application_provision_tasks_requested_by_idx", ["requested_by"], unique=False)
        batch_op.create_index(
            "beta_application_provision_tasks_requested_tenant_id_idx", ["requested_tenant_id"], unique=False
        )
        batch_op.create_index("beta_application_provision_tasks_status_idx", ["status"], unique=False)


def downgrade():
    with op.batch_alter_table("beta_application_provision_tasks", schema=None) as batch_op:
        batch_op.drop_index("beta_application_provision_tasks_status_idx")
        batch_op.drop_index("beta_application_provision_tasks_requested_tenant_id_idx")
        batch_op.drop_index("beta_application_provision_tasks_requested_by_idx")
        batch_op.drop_index("beta_application_provision_tasks_celery_task_id_idx")
        batch_op.drop_index("beta_application_provision_tasks_application_id_idx")
        batch_op.drop_index("beta_application_provision_tasks_action_idx")
    op.drop_table("beta_application_provision_tasks")

    with op.batch_alter_table("beta_application_notifications", schema=None) as batch_op:
        batch_op.drop_index("beta_application_notifications_status_idx")
        batch_op.drop_index("beta_application_notifications_event_idx")
        batch_op.drop_index("beta_application_notifications_channel_idx")
        batch_op.drop_index("beta_application_notifications_application_id_idx")
    op.drop_table("beta_application_notifications")
