"""add amount_cents to referral_rewards

Revision ID: 16a9a5f9d49f
Revises: d4e8f2a6c1b9
Create Date: 2026-09-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16a9a5f9d49f'
down_revision = 'd4e8f2a6c1b9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'referral_rewards',
        sa.Column('amount_cents', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column('referral_rewards', 'amount_cents')
