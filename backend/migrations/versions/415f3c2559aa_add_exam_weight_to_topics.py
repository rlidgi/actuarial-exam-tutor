"""add exam_weight to topics

Revision ID: 415f3c2559aa
Revises: 0c1a1bab967e
Create Date: 2026-08-05 23:21:09.710930

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '415f3c2559aa'
down_revision = '0c1a1bab967e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('topics', schema=None) as batch_op:
        batch_op.add_column(sa.Column('exam_weight', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('topics', schema=None) as batch_op:
        batch_op.drop_column('exam_weight')
