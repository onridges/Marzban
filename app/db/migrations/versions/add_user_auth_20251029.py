"""add user hashed_password and refresh_tokens table

Revision ID: add_user_auth_20251029
Revises: 9d5a518ae432
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_user_auth_20251029'
down_revision = '2b231de97dc3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # add hashed_password column to users (nullable to allow smooth migration)
    op.add_column('users', sa.Column('hashed_password', sa.String(length=128), nullable=True))

    # create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='0', default=False)
    )


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_column('users', 'hashed_password')
