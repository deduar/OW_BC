"""add content_hash to fileupload

Revision ID: 498c120bc0c7
Revises: 
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa


revision = '498c120bc0c7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('fileupload', sa.Column('content_hash', sa.String(), nullable=True))
    op.create_index('ix_fileupload_content_hash', 'fileupload', ['content_hash'])


def downgrade() -> None:
    op.drop_index('ix_fileupload_content_hash', 'fileupload')
    op.drop_column('fileupload', 'content_hash')
