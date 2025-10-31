"""add user authentication tables and fields

Revision ID: user_auth_20251030
Revises: add_user_auth_20251029
Create Date: 2025-10-30

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'user_auth_20251030'
down_revision = 'add_user_auth_20251029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('email', sa.String(length=255), nullable=True, unique=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('data_limit', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('subscription_plans.id'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'refunded', name='order_status'), nullable=False, default='pending'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Add role column to users table
    op.add_column('users', sa.Column('role', sa.Enum('user', 'admin', 'superadmin', name='user_role'), nullable=False, server_default='user'))


def downgrade() -> None:
    op.drop_column('users', 'role')
    op.drop_table('orders')
    op.drop_table('subscription_plans')
    op.drop_table('user_profiles')
    
    # Drop the enum types
    op.execute('DROP TYPE IF EXISTS order_status')
    op.execute('DROP TYPE IF EXISTS user_role')