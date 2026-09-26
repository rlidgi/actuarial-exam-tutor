"""add feedback request email fields to users

Revision ID: c5d1e7a3b9f2
Revises: f2a6c9d1e8b4
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5d1e7a3b9f2'
down_revision = 'f2a6c9d1e8b4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('feedback_request_sent_at', sa.DateTime(), nullable=True))
    op.add_column(
        'users',
        sa.Column('email_opt_out', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('users', 'email_opt_out')
    op.drop_column('users', 'feedback_request_sent_at')
