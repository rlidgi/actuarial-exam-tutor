"""add textbook_chunks with pgvector

Revision ID: 764859ec028f
Revises: 3212eb9db6f6
Create Date: 2026-08-05 22:45:59.833467

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '764859ec028f'
down_revision = '3212eb9db6f6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table('textbook_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('exam_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('book_key', sa.String(length=64), nullable=False),
    sa.Column('book_title', sa.String(length=255), nullable=False),
    sa.Column('chapter_number', sa.Integer(), nullable=False),
    sa.Column('chapter_title', sa.String(length=255), nullable=False),
    sa.Column('citation', sa.String(length=512), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', Vector(1536), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute(
        'CREATE INDEX textbook_chunks_embedding_hnsw_idx ON textbook_chunks '
        'USING hnsw (embedding vector_cosine_ops)'
    )


def downgrade():
    op.execute('DROP INDEX IF EXISTS textbook_chunks_embedding_hnsw_idx')
    op.drop_table('textbook_chunks')
