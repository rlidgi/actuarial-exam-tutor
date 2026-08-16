"""add user auth events

Revision ID: d4e8f2a6c1b9
Revises: b7f3d9a1c5e2
Create Date: 2026-08-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e8f2a6c1b9'
down_revision = 'b7f3d9a1c5e2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_auth_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_user_auth_events_user_id_created_at',
        'user_auth_events',
        ['user_id', 'created_at'],
    )


def downgrade():
    op.drop_index('ix_user_auth_events_user_id_created_at', table_name='user_auth_events')
    op.drop_table('user_auth_events')
