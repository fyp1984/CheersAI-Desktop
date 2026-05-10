"""add_token_quota_tables

Revision ID: db40c83cabd3
Revises: a1b2c3d4e5f7
Create Date: 2026-05-09 15:05:46.617881

"""
from alembic import op
import models as models
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db40c83cabd3'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 token_quota_configs 表
    op.create_table(
        'token_quota_configs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.UUID(), nullable=True, comment='用户ID（为空表示租户级配置）'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='配置名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='配置描述'),
        sa.Column('interval_type', sa.String(length=20), server_default='daily', nullable=False, comment='时间间隔类型'),
        sa.Column('interval_value', sa.Integer(), nullable=True, comment='自定义间隔值（秒数）'),
        sa.Column('token_limit', sa.Integer(), nullable=False, comment='Token 配额上限'),
        sa.Column('cloud_models', sa.dialects.postgresql.JSONB(), server_default='[]', nullable=False, comment='云端模型列表'),
        sa.Column('local_models', sa.dialects.postgresql.JSONB(), server_default='[]', nullable=False, comment='本地模型列表'),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False, comment='配额状态'),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False, comment='优先级'),
        sa.Column('extra_config', sa.dialects.postgresql.JSONB(), server_default='{}', nullable=False, comment='额外配置'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False, comment='创建人ID'),
        sa.Column('updated_by', sa.UUID(), nullable=False, comment='更新人ID'),
        sa.PrimaryKeyConstraint('id', name='token_quota_config_pkey'),
        sa.UniqueConstraint('tenant_id', 'user_id', 'name', name='token_quota_config_unique')
    )
    op.create_index('token_quota_config_tenant_idx', 'token_quota_configs', ['tenant_id'])
    op.create_index('token_quota_config_user_idx', 'token_quota_configs', ['user_id'])

    # 创建 token_quota_usages 表
    op.create_table(
        'token_quota_usages',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('quota_config_id', sa.UUID(), nullable=False, comment='关联的配额配置ID'),
        sa.Column('tenant_id', sa.UUID(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.UUID(), nullable=True, comment='用户ID'),
        sa.Column('period_start', sa.DateTime(), nullable=False, comment='时间窗口开始时间'),
        sa.Column('period_end', sa.DateTime(), nullable=False, comment='时间窗口结束时间'),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False, comment='总 Token 数'),
        sa.Column('input_tokens', sa.Integer(), server_default='0', nullable=False, comment='输入 Token 数'),
        sa.Column('output_tokens', sa.Integer(), server_default='0', nullable=False, comment='输出 Token 数'),
        sa.Column('request_count', sa.Integer(), server_default='0', nullable=False, comment='请求次数'),
        sa.Column('model_usage_details', sa.dialects.postgresql.JSONB(), server_default='{}', nullable=False, comment='各模型使用详情'),
        sa.Column('is_exceeded', sa.Boolean(), server_default='false', nullable=False, comment='是否已超额'),
        sa.Column('exceeded_at', sa.DateTime(), nullable=True, comment='超额时间'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='token_quota_usage_pkey')
    )
    op.create_index('token_quota_usage_config_idx', 'token_quota_usages', ['quota_config_id'])
    op.create_index('token_quota_usage_period_idx', 'token_quota_usages', ['period_start', 'period_end'])
    op.create_index('token_quota_usage_tenant_period_idx', 'token_quota_usages', ['tenant_id', 'period_start'])

    # 创建 token_quota_logs 表
    op.create_table(
        'token_quota_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('usage_id', sa.UUID(), nullable=False, comment='关联的使用记录ID'),
        sa.Column('tenant_id', sa.UUID(), nullable=False, comment='租户ID'),
        sa.Column('user_id', sa.UUID(), nullable=True, comment='用户ID'),
        sa.Column('request_id', sa.String(length=255), nullable=True, comment='请求ID'),
        sa.Column('model_provider', sa.String(length=255), nullable=False, comment='模型提供商'),
        sa.Column('model_name', sa.String(length=255), nullable=False, comment='模型名称'),
        sa.Column('tokens_used', sa.Integer(), nullable=False, comment='本次使用的 Token 数'),
        sa.Column('tokens_before', sa.Integer(), nullable=False, comment='使用前的累计 Token 数'),
        sa.Column('tokens_after', sa.Integer(), nullable=False, comment='使用后的累计 Token 数'),
        sa.Column('quota_limit', sa.Integer(), nullable=False, comment='配额上限'),
        sa.Column('is_within_quota', sa.Boolean(), nullable=False, comment='是否在配额内'),
        sa.Column('switched_to_local', sa.Boolean(), server_default='false', nullable=False, comment='是否切换到本地模型'),
        sa.Column('extra_info', sa.dialects.postgresql.JSONB(), server_default='{}', nullable=False, comment='额外信息'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP(0)'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='token_quota_log_pkey')
    )
    op.create_index('token_quota_log_usage_idx', 'token_quota_logs', ['usage_id'])
    op.create_index('token_quota_log_created_idx', 'token_quota_logs', ['created_at'])


def downgrade():
    # 删除表（按相反顺序）
    op.drop_index('token_quota_log_created_idx', table_name='token_quota_logs')
    op.drop_index('token_quota_log_usage_idx', table_name='token_quota_logs')
    op.drop_table('token_quota_logs')
    
    op.drop_index('token_quota_usage_tenant_period_idx', table_name='token_quota_usages')
    op.drop_index('token_quota_usage_period_idx', table_name='token_quota_usages')
    op.drop_index('token_quota_usage_config_idx', table_name='token_quota_usages')
    op.drop_table('token_quota_usages')
    
    op.drop_index('token_quota_config_user_idx', table_name='token_quota_configs')
    op.drop_index('token_quota_config_tenant_idx', table_name='token_quota_configs')
    op.drop_table('token_quota_configs')
