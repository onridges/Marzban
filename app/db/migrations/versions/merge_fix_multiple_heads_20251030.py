"""merge fix_multiple_heads_20251029 and user_auth_20251030

Revision ID: merge_heads_20251030
Revises: fix_multiple_heads_20251029, user_auth_20251030
Create Date: 2025-10-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_20251030'
down_revision = ('fix_multiple_heads_20251029', 'user_auth_20251030')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge migration; no schema changes are required.
    pass


def downgrade() -> None:
    # Downgrade would re-split branches; keep empty.
    pass