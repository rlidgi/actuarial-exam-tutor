"""add referral program

Revision ID: 424facd3e1d4
Revises: b3482a27727b
Create Date: 2026-08-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '424facd3e1d4'
down_revision = 'b3482a27727b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('referral_code', sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column('referred_by_id', sa.Integer(), nullable=True))
        # server_default so existing rows backfill to false instead of
        # failing the NOT NULL constraint -- same reason free_turns_used
        # needed one in migration 8192c7252875.
        batch_op.add_column(
            sa.Column('has_ever_subscribed', sa.Boolean(), nullable=False, server_default='false')
        )
        batch_op.create_unique_constraint('uq_users_referral_code', ['referral_code'])
        batch_op.create_index('ix_users_referral_code', ['referral_code'])
        batch_op.create_foreign_key(
            'fk_users_referred_by_id_users', 'users', ['referred_by_id'], ['id']
        )

    op.create_table(
        'referral_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('referred_user_id', sa.Integer(), nullable=True),
        sa.Column('reward_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('stripe_coupon_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    # Partial unique index: every referred user can trigger at most one
    # referrer-side reward, ever -- but referred_user_id is null for a
    # referred user's own reward row, and multiple nulls must stay allowed.
    op.create_index(
        'uq_referral_rewards_referred_user_id',
        'referral_rewards',
        ['referred_user_id'],
        unique=True,
        postgresql_where=sa.text('referred_user_id IS NOT NULL'),
        sqlite_where=sa.text('referred_user_id IS NOT NULL'),
    )


def downgrade():
    op.drop_index('uq_referral_rewards_referred_user_id', table_name='referral_rewards')
    op.drop_table('referral_rewards')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_referred_by_id_users', type_='foreignkey')
        batch_op.drop_index('ix_users_referral_code')
        batch_op.drop_constraint('uq_users_referral_code', type_='unique')
        batch_op.drop_column('has_ever_subscribed')
        batch_op.drop_column('referred_by_id')
        batch_op.drop_column('referral_code')
