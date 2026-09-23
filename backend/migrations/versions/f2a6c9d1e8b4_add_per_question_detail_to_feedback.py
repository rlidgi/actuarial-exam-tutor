"""add per-question detail text to feedback

Revision ID: f2a6c9d1e8b4
Revises: 16a9a5f9d49f
Create Date: 2026-09-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2a6c9d1e8b4'
down_revision = '16a9a5f9d49f'
branch_labels = None
depends_on = None

_DETAIL_COLUMNS = ('overall_detail', 'tutor_quality_detail', 'ease_of_use_detail', 'value_detail')


def upgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        for col in _DETAIL_COLUMNS:
            batch_op.add_column(sa.Column(col, sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        for col in reversed(_DETAIL_COLUMNS):
            batch_op.drop_column(col)
