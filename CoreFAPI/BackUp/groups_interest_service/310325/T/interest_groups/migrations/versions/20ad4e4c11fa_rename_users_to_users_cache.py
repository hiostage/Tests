"""rename users to users_cache

Revision ID: 20ad4e4c11fa
Revises: 7458db68b8c3
Create Date: 2025-04-01 05:20:04.380822

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20ad4e4c11fa'
down_revision = '7458db68b8c3'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('users', 'users_cache')

def downgrade():
    op.rename_table('users_cache', 'users')  # Откат