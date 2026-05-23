"""add barrel_picker table and bottle_barrel_picker association (#357)

Revision ID: a2518713654b
Revises: 6e2b70a98128
Create Date: 2026-05-22 17:16:00.570349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2518713654b'
down_revision = '6e2b70a98128'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('barrel_picker',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=65), nullable=False),
    sa.Column('user_num', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('url', sa.String(length=64), nullable=True),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'user_num', name='uq_barrel_picker_user_num')
    )
    op.create_table('bottle_barrel_picker',
    sa.Column('bottle_id', sa.String(length=36), nullable=False),
    sa.Column('barrel_picker_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['bottle_id'], ['bottle.id'], ),
    sa.ForeignKeyConstraint(['barrel_picker_id'], ['barrel_picker.id'], ),
    sa.PrimaryKeyConstraint('bottle_id', 'barrel_picker_id')
    )


def downgrade():
    op.drop_table('bottle_barrel_picker')
    op.drop_table('barrel_picker')
