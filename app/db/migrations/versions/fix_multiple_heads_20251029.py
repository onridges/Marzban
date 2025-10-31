"""fix multiple heads

Revision ID: fix_multiple_heads_20251029
Revises: 2b231de97dc3, add_user_auth_20251029
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_multiple_heads_20251029'
down_revision = ('2b231de97dc3', 'add_user_auth_20251029')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass