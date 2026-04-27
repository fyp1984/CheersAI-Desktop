"""add app lifecycle

Revision ID: a1b2c3d4e5f7
Revises: 391923893f21
Create Date: 2026-04-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from models.types import StringUUID

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = '391923893f21'
branch_labels = None
depends_on = None

def upgrade():
    # apps table modifications
    op.add_column('apps', sa.Column('lifecycle_status', sa.String(length=32), server_default=sa.text("'unpublished'"), nullable=False))
    op.add_column('apps', sa.Column('lifecycle_status_changed_at', sa.DateTime(), nullable=True))
    op.add_column('apps', sa.Column('lifecycle_status_changed_by', StringUUID(), nullable=True))
    op.add_column('apps', sa.Column('lifecycle_status_reason', sa.Text(), nullable=True))
    op.add_column('apps', sa.Column('last_published_at', sa.DateTime(), nullable=True))
    op.add_column('apps', sa.Column('last_published_by', StringUUID(), nullable=True))
    op.add_column('apps', sa.Column('last_recalled_at', sa.DateTime(), nullable=True))
    op.add_column('apps', sa.Column('last_recalled_by', StringUUID(), nullable=True))
    op.add_column('apps', sa.Column('row_version', sa.Integer(), server_default=sa.text("0"), nullable=False))
    
    # Backfill lifecycle_status for existing data
    op.execute("""
        UPDATE apps 
        SET lifecycle_status = 'published' 
        WHERE enable_site = true OR enable_api = true
    """)
    
    # create app_lifecycle_events table
    op.create_table(
        'app_lifecycle_events',
        sa.Column('id', StringUUID(), nullable=False),
        sa.Column('tenant_id', StringUUID(), nullable=False),
        sa.Column('app_id', StringUUID(), nullable=False),
        sa.Column('from_status', sa.String(length=32), nullable=True),
        sa.Column('to_status', sa.String(length=32), nullable=True),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('validation_result', sa.Text(), nullable=True),
        sa.Column('draft_version', sa.String(length=64), nullable=True),
        sa.Column('published_version', sa.String(length=64), nullable=True),
        sa.Column('operator_id', StringUUID(), nullable=True),
        sa.Column('operator_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='app_lifecycle_event_pkey')
    )
    op.create_index('app_lifecycle_event_app_id_idx', 'app_lifecycle_events', ['app_id'], unique=False)
    op.create_index('app_lifecycle_event_tenant_id_idx', 'app_lifecycle_events', ['tenant_id'], unique=False)

def downgrade():
    op.drop_index('app_lifecycle_event_tenant_id_idx', table_name='app_lifecycle_events')
    op.drop_index('app_lifecycle_event_app_id_idx', table_name='app_lifecycle_events')
    op.drop_table('app_lifecycle_events')
    
    op.drop_column('apps', 'row_version')
    op.drop_column('apps', 'last_recalled_by')
    op.drop_column('apps', 'last_recalled_at')
    op.drop_column('apps', 'last_published_by')
    op.drop_column('apps', 'last_published_at')
    op.drop_column('apps', 'lifecycle_status_reason')
    op.drop_column('apps', 'lifecycle_status_changed_by')
    op.drop_column('apps', 'lifecycle_status_changed_at')
    op.drop_column('apps', 'lifecycle_status')
