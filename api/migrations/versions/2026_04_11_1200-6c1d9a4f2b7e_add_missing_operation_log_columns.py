"""add missing operation log columns

Revision ID: 6c1d9a4f2b7e
Revises: a2f4c7d9e5b1
Create Date: 2026-04-11 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import context, op


revision = "6c1d9a4f2b7e"
down_revision = "a2f4c7d9e5b1"
branch_labels = None
depends_on = None


def _has_column(conn, table_name: str, column_name: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def _has_index(conn, table_name: str, index_name: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade():
    conn = op.get_bind()

    column_defs = [
        ("account_name", sa.String(length=255), ""),
        ("operation_type", sa.String(length=16), None),
        ("request_content", sa.Text(), None),
        ("response_content", sa.Text(), None),
        ("desensitize_status", sa.String(length=16), None),
        ("device_info", sa.String(length=255), None),
        ("duration", sa.Integer(), None),
        ("sync_status", sa.String(length=16), "pending"),
        ("sync_time", sa.DateTime(), None),
        ("is_expired", sa.Boolean(), False),
        ("error_message", sa.Text(), None),
        ("nexus_sync_id", sa.String(length=64), None),
    ]

    for column_name, column_type, default_value in column_defs:
        if _has_column(conn, "operation_logs", column_name):
            continue

        if default_value is None:
            with op.batch_alter_table("operation_logs", schema=None) as batch_op:
                batch_op.add_column(sa.Column(column_name, column_type, nullable=True))
        else:
            with op.batch_alter_table("operation_logs", schema=None) as batch_op:
                batch_op.add_column(sa.Column(column_name, column_type, nullable=True, server_default=sa.text(repr(default_value).lower() if isinstance(default_value, bool) else repr(default_value))))

            if column_name == "account_name":
                op.execute("UPDATE operation_logs SET account_name = '' WHERE account_name IS NULL")
            elif column_name == "sync_status":
                op.execute("UPDATE operation_logs SET sync_status = 'pending' WHERE sync_status IS NULL")
            elif column_name == "is_expired":
                op.execute("UPDATE operation_logs SET is_expired = false WHERE is_expired IS NULL")

    if not _has_index(conn, "operation_logs", "operation_log_sync_idx"):
        with op.batch_alter_table("operation_logs", schema=None) as batch_op:
            batch_op.create_index("operation_log_sync_idx", ["tenant_id", "sync_status", "is_expired"], unique=False)

    if not _has_index(conn, "operation_logs", "operation_log_type_idx"):
        with op.batch_alter_table("operation_logs", schema=None) as batch_op:
            batch_op.create_index("operation_log_type_idx", ["tenant_id", "operation_type", "created_at"], unique=False)


def downgrade():
    with op.batch_alter_table("operation_logs", schema=None) as batch_op:
        batch_op.drop_index("operation_log_type_idx")
        batch_op.drop_index("operation_log_sync_idx")
        batch_op.drop_column("nexus_sync_id")
        batch_op.drop_column("error_message")
        batch_op.drop_column("is_expired")
        batch_op.drop_column("sync_time")
        batch_op.drop_column("sync_status")
        batch_op.drop_column("duration")
        batch_op.drop_column("device_info")
        batch_op.drop_column("desensitize_status")
        batch_op.drop_column("response_content")
        batch_op.drop_column("request_content")
        batch_op.drop_column("operation_type")
        batch_op.drop_column("account_name")
