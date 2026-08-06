"""add current_difficulty to mastery

Revision ID: 0c1a1bab967e
Revises: 764859ec028f
Create Date: 2026-08-05 23:15:41.186205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c1a1bab967e'
down_revision = '764859ec028f'
branch_labels = None
depends_on = None


def upgrade():
    # Note: the textbook_chunks HNSW index drop/recreate that autogenerate
    # detected here was spurious (it doesn't recognize the raw-SQL index
    # from the previous migration as matching the model) -- removed by hand
    # so this migration doesn't touch that index.
    with op.batch_alter_table('mastery', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('current_difficulty', sa.Integer(), nullable=False, server_default='5')
        )
        batch_op.create_check_constraint('ck_difficulty_range', 'current_difficulty >= 1 AND current_difficulty <= 10')


def downgrade():
    with op.batch_alter_table('mastery', schema=None) as batch_op:
        batch_op.drop_constraint('ck_difficulty_range', type_='check')
        batch_op.drop_column('current_difficulty')
