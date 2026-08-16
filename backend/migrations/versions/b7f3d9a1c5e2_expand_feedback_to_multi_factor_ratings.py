"""expand feedback to multi-factor ratings

Revision ID: b7f3d9a1c5e2
Revises: 9a1c2e4f7b3d
Create Date: 2026-08-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f3d9a1c5e2'
down_revision = '9a1c2e4f7b3d'
branch_labels = None
depends_on = None

_RATING_COLUMNS = ('overall_rating', 'tutor_quality_rating', 'ease_of_use_rating', 'value_rating')


def upgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.drop_constraint('ck_feedback_rating_range', type_='check')
        batch_op.alter_column('rating', new_column_name='overall_rating', nullable=True)
        batch_op.alter_column('category', nullable=True)
        batch_op.add_column(sa.Column('tutor_quality_rating', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ease_of_use_rating', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('value_rating', sa.Integer(), nullable=True))
        for col in _RATING_COLUMNS:
            batch_op.create_check_constraint(
                f'ck_feedback_{col}_range', f'{col} IS NULL OR ({col} >= 1 AND {col} <= 5)'
            )


def downgrade():
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        for col in _RATING_COLUMNS:
            batch_op.drop_constraint(f'ck_feedback_{col}_range', type_='check')
        batch_op.drop_column('value_rating')
        batch_op.drop_column('ease_of_use_rating')
        batch_op.drop_column('tutor_quality_rating')
        batch_op.alter_column('category', nullable=False)
        batch_op.alter_column('overall_rating', new_column_name='rating', nullable=False)
        batch_op.create_check_constraint('ck_feedback_rating_range', 'rating >= 1 AND rating <= 5')
